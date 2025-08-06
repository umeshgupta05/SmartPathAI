import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Brain, Star, RefreshCw, AlertTriangle } from "lucide-react";

interface Question {
  question: string;
  options: string[];
  correct_answer: string;
}

interface QuizData {
  questions: Question[];
  topic?: string;
}

const Quiz = () => {
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [score, setScore] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 3;

  const fetchQuiz = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem("token");
      if (!token) {
        setError("Please log in to access the quiz.");
        setLoading(false);
        return;
      }

      const response = await fetch("http://localhost:5000/generate_quiz", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("token");
          throw new Error("Session expired. Please log in again.");
        }
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      if (!data.questions || !Array.isArray(data.questions)) {
        throw new Error("Invalid quiz data received");
      }

      setQuiz(data);
      setUserAnswers({});
      setScore(null);
      setProgress(0);
      setRetryCount(0);
    } catch (err) {
      setError(err.message);
      if (retryCount < MAX_RETRIES) {
        setRetryCount((prev) => prev + 1);
        setTimeout(fetchQuiz, 2000); // Retry after 2 seconds
      }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);

  useEffect(() => {
    fetchQuiz();
  }, [fetchQuiz]);

  const handleAnswerChange = (question, answer) => {
    setUserAnswers((prev) => {
      const updatedAnswers = { ...prev, [question]: answer };
      setProgress(
        (Object.keys(updatedAnswers).length / (quiz?.questions?.length || 1)) *
          100
      );
      return updatedAnswers;
    });
  };

  const handleSubmit = async () => {
    try {
      setError(null);
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Please log in to submit answers.");
        return;
      }

      const correctAnswers = quiz.questions.reduce((acc, q) => {
        acc[q.question] = q.correct_answer;
        return acc;
      }, {});

      const response = await fetch("http://localhost:5000/check_answers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        credentials: "include",
        body: JSON.stringify({
          answers: userAnswers,
          correct_answers: correctAnswers,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit answers");
      }

      const data = await response.json();
      setScore(data.score);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <Card className="max-w-3xl mx-auto p-6">
        <CardContent className="text-center">
          <RefreshCw className="animate-spin h-8 w-8 mx-auto mb-4" />
          <p className="text-lg">Loading quiz...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="max-w-3xl mx-auto p-6">
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="ml-2">{error}</AlertDescription>
          </Alert>
          <Button onClick={fetchQuiz} className="mt-4 w-full" variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-10">
      <Card>
        <CardHeader className="text-center">
          <Brain className="w-10 h-10 text-primary mx-auto" />
          <CardTitle className="text-xl mt-2">
            Quiz on {quiz?.topic || "Loading..."}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="mb-4" />
          {quiz?.questions?.map((q, idx) => (
            <div key={idx} className="mb-6">
              <h3 className="font-medium text-lg mb-2">
                {idx + 1}. {q.question}
              </h3>
              <RadioGroup
                onValueChange={(value) => handleAnswerChange(q.question, value)}
                value={userAnswers[q.question]}
              >
                {q.options.map((option, optionIdx) => (
                  <div
                    key={optionIdx}
                    className="flex items-center space-x-2 mb-2"
                  >
                    <RadioGroupItem
                      value={option}
                      id={`q${idx}-${optionIdx}`}
                    />
                    <Label htmlFor={`q${idx}-${optionIdx}`}>{option}</Label>
                  </div>
                ))}
              </RadioGroup>
            </div>
          ))}
          <div className="flex flex-col gap-4 mt-6">
            <Button
              onClick={handleSubmit}
              disabled={
                !quiz?.questions ||
                Object.keys(userAnswers).length !== quiz?.questions?.length
              }
              className="w-full"
            >
              Submit Answers
            </Button>
            {score !== null && (
              <Alert className={score >= 70 ? "bg-green-50" : "bg-yellow-50"}>
                <AlertDescription className="flex items-center gap-2">
                  <Star
                    className={
                      score >= 70 ? "text-green-500" : "text-yellow-500"
                    }
                  />
                  Your score: {score}%
                </AlertDescription>
              </Alert>
            )}
            <Button
              variant="outline"
              onClick={fetchQuiz}
              className="w-full flex items-center justify-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Try Another Quiz
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Quiz;
