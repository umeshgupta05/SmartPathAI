import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Brain, Star, RefreshCw, AlertTriangle, Loader2, Trophy, CheckCircle, XCircle } from "lucide-react";
import { motion } from "framer-motion";

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
      if (!token) { setError("Please log in to access the quiz."); setLoading(false); return; }

      const response = await fetch("/api/generate_quiz", {
        method: "GET",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      });
      if (!response.ok) {
        if (response.status === 401) { localStorage.removeItem("token"); throw new Error("Session expired."); }
        throw new Error(`Server error: ${response.status}`);
      }
      const data = await response.json();
      if (!data.questions || !Array.isArray(data.questions)) throw new Error("Invalid quiz data");

      setQuiz(data);
      setUserAnswers({});
      setScore(null);
      setProgress(0);
      setRetryCount(0);
    } catch (err) {
      setError(err.message);
      if (retryCount < MAX_RETRIES) { setRetryCount((p) => p + 1); setTimeout(fetchQuiz, 2000); }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);

  useEffect(() => { fetchQuiz(); }, [fetchQuiz]);

  const handleAnswerChange = (question: string, answer: string) => {
    setUserAnswers((prev) => {
      const updated = { ...prev, [question]: answer };
      setProgress((Object.keys(updated).length / (quiz?.questions?.length || 1)) * 100);
      return updated;
    });
  };

  const handleSubmit = async () => {
    try {
      setError(null);
      const token = localStorage.getItem("token");
      if (!token) { setError("Please log in."); return; }

      const correctAnswers = quiz.questions.reduce((acc, q) => { acc[q.question] = q.correct_answer; return acc; }, {});
      const response = await fetch("/api/check_answers", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ answers: userAnswers, correct_answers: correctAnswers }),
      });
      if (!response.ok) throw new Error("Failed to submit answers");
      const data = await response.json();
      setScore(data.score);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Generating quiz…</p>
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <Alert variant="destructive" className="rounded-xl">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={fetchQuiz} className="mt-4 gap-2 rounded-xl">
          <RefreshCw className="h-4 w-4" /> Try Again
        </Button>
      </div>
    );
  }

  if (!quiz) return null;

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Quiz</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {quiz.topic ? `Topic: ${quiz.topic}` : "Test your knowledge"}
          </p>
        </div>
        <Button onClick={fetchQuiz} variant="outline" size="sm" className="gap-2 rounded-xl border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-all">
          <RefreshCw className="h-4 w-4" /> New Quiz
        </Button>
      </motion.div>

      {/* Progress bar */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1.5">
          <span>{Object.keys(userAnswers).length} / {quiz.questions.length} answered</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} className="h-2 rounded-full" />
      </motion.div>

      {/* Score Banner */}
      {score !== null && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`p-5 rounded-2xl text-center ${
            score >= 70
              ? "bg-gradient-to-br from-teal-500 to-emerald-600 text-white shadow-lg shadow-teal-500/20"
              : "bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/20"
          }`}
        >
          <Trophy className="h-8 w-8 mx-auto mb-2 opacity-90" />
          <p className="text-2xl font-bold">{score}%</p>
          <p className="text-white/80 text-sm mt-1">{score >= 70 ? "Great work! 🎉" : "Keep practicing!"}</p>
        </motion.div>
      )}

      {/* Questions */}
      <div className="space-y-5">
        {quiz.questions.map((q, index) => {
          const userAnswer = userAnswers[q.question];
          const isCorrect = score !== null && userAnswer === q.correct_answer;
          const isWrong = score !== null && userAnswer && userAnswer !== q.correct_answer;

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + index * 0.06 }}
            >
              <Card className={`border transition-all duration-300 ${
                isCorrect ? "border-teal-200 bg-teal-50/40" :
                isWrong ? "border-red-200 bg-red-50/40" :
                "border-gray-100 bg-white"
              }`}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-gray-900 flex items-start gap-2">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </span>
                    <span className="pt-0.5">{q.question}</span>
                    {isCorrect && <CheckCircle className="h-5 w-5 text-teal-500 flex-shrink-0 ml-auto" />}
                    {isWrong && <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 ml-auto" />}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <RadioGroup
                    value={userAnswers[q.question] || ""}
                    onValueChange={(val) => handleAnswerChange(q.question, val)}
                    className="space-y-2"
                  >
                    {q.options.map((option, optIdx) => {
                      const isThisCorrect = score !== null && option === q.correct_answer;
                      return (
                        <div
                          key={optIdx}
                          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-all cursor-pointer
                            ${isThisCorrect ? "border-teal-300 bg-teal-50" :
                              userAnswer === option && isWrong ? "border-red-300 bg-red-50" :
                              userAnswer === option ? "border-blue-300 bg-blue-50" :
                              "border-gray-100 hover:border-gray-200 hover:bg-gray-50"}
                          `}
                        >
                          <RadioGroupItem value={option} id={`${index}-${optIdx}`} disabled={score !== null} />
                          <Label htmlFor={`${index}-${optIdx}`} className="text-sm text-gray-700 cursor-pointer flex-1">
                            {option}
                          </Label>
                        </div>
                      );
                    })}
                  </RadioGroup>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Submit */}
      {score === null && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <Button
            onClick={handleSubmit}
            disabled={Object.keys(userAnswers).length !== quiz.questions.length}
            className="w-full h-11 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium transition-colors"
          >
            Submit Answers
          </Button>
        </motion.div>
      )}
    </div>
  );
};

export default Quiz;
