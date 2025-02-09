import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Brain, Star, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";

const Quiz = () => {
  const [quiz, setQuiz] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    fetchQuiz();
  }, []);

  const fetchQuiz = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem("token"); // Retrieve token
      if (!token) {
        setError("Authentication required. Please log in.");
        setLoading(false);
        return;
      }
  
      const response = await axios.get("http://localhost:5000/generate_quiz", {
        headers: { Authorization: `Bearer ${token}` }, // Pass JWT token
      });
  
      setQuiz(response.data);
      setUserAnswers({});
      setScore(null);
      setProgress(0);
    } catch (err) {
      setError("Failed to load quiz. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  

  const handleAnswerChange = (question, answer) => {
    setUserAnswers((prev) => {
      const updatedAnswers = { ...prev, [question]: answer };
      setProgress((Object.keys(updatedAnswers).length / quiz.questions.length) * 100);
      return updatedAnswers;
    });
  };

  const handleSubmit = async () => {
    try {
      const correctAnswers = quiz.questions.reduce((acc, q) => {
        acc[q.question] = q.correct_answer;
        return acc;
      }, {});

      const response = await axios.post("http://localhost:5000/check_answers", {
        answers: userAnswers,
        correct_answers: correctAnswers,
      });

      setScore(response.data.score);
    } catch (err) {
      setError("Failed to submit answers. Please try again.");
    }
  };

  if (loading) return <div className="text-lg text-center py-10">Loading quiz...</div>;
  if (error) return <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-3xl mx-auto py-10"
    >
      <Card>
        <CardHeader className="text-center">
          <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: Infinity, duration: 2 }}>
            <Brain className="w-10 h-10 text-primary mx-auto" />
          </motion.div>
          <CardTitle className="text-xl mt-2">Quiz on {quiz.topic}</CardTitle>
           
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="mb-4" />
          {quiz.questions.map((q, idx) => (
            <div key={idx} className="mb-6">
              <h3 className="font-medium text-lg mb-2">{idx + 1}. {q.question}</h3>
              <RadioGroup onValueChange={(value) => handleAnswerChange(q.question, value)}>
                {q.options.map((option, optionIdx) => (
                  <div key={optionIdx} className="flex items-center space-x-2">
                    <RadioGroupItem value={option} id={`q${idx}-${optionIdx}`} />
                    <Label htmlFor={`q${idx}-${optionIdx}`}>{option}</Label>
                  </div>
                ))}
              </RadioGroup>
            </div>
          ))}
          <div className="flex flex-col gap-4 mt-6">
            <Button onClick={handleSubmit} disabled={Object.keys(userAnswers).length !== quiz.questions.length}>
              Submit Answers
            </Button>
            {score !== null && (
              <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: 1, duration: 0.5 }}>
                <Alert>
                  <AlertDescription className="flex items-center gap-2">
                    <Star className="text-yellow-500 h-5 w-5" /> Your score: {score}%
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}
            <Button variant="outline" onClick={fetchQuiz} className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" /> Try Another Quiz
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default Quiz;