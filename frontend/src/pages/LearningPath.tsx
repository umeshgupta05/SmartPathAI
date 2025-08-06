import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Brain, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

const LearningPath = () => {
  const [learningPath, setLearningPath] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchLearningPath = async () => {
      try {
        const response = await axios.get(
          "http://localhost:5000/learning_path",
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setLearningPath(response.data);
      } catch (error) {
        console.error("Error fetching learning path:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchLearningPath();
  }, [token]);

  if (loading)
    return (
      <div className="text-center py-10 text-xl font-medium">
        Loading learning path...
      </div>
    );

  return (
    <div
      className="min-h-screen p-6 bg-cover bg-center bg-fixed"
      style={{
        backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), url(https://images.unsplash.com/photo-1487058792275-0ad4aaf24ca7)`,
      }}
    >
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex justify-between items-center mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900">Learning Path</h1>
          <Button className="gap-2 hover:scale-105 transition-transform">
            <Brain className="h-4 w-4" />
            Optimize Path
          </Button>
        </motion.div>

        <div className="relative">
          {learningPath.length > 0 ? (
            learningPath.map((course, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{
                  duration: 0.5,
                  delay: index * 0.2,
                  ease: "easeOut",
                }}
                className="relative pl-8 pb-8"
              >
                <div className="absolute left-0 top-0 h-full w-0.5 bg-primary/20">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: "100%" }}
                    transition={{ duration: 0.5, delay: index * 0.2 }}
                    className="w-full bg-primary"
                  />
                </div>

                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.2 }}
                  className="absolute left-[-8px] top-0 w-4 h-4 rounded-full bg-primary"
                />

                <motion.div
                  whileHover={{
                    scale: 1.02,
                    boxShadow:
                      "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                  }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Card className="p-6 backdrop-blur-sm bg-white/80 hover:bg-white/90 transition-colors border border-gray-200/50">
                    <h3 className="font-semibold mb-2">{course.title}</h3>
                    <p className="text-sm text-gray-500 mb-4">
                      {course.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: "easeInOut",
                          }}
                          className={`h-2 w-2 rounded-full ${course.status === "Completed" ? "bg-green-500" : "bg-yellow-500"}`}
                        />
                        <span className="text-sm text-gray-500">
                          {course.status}
                        </span>
                      </div>
                      <Button
                        variant="outline"
                        className="gap-2 hover:gap-3 transition-all duration-300"
                        onClick={() => window.open(course.url, "_blank")}
                      >
                        Continue
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              </motion.div>
            ))
          ) : (
            <p className="text-center text-gray-500">
              No learning path available.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LearningPath;
