import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Brain,
  ArrowRight,
  Loader2,
  CheckCircle,
  Clock,
  BookOpen,
  Trophy,
  Target,
} from "lucide-react";
import { motion } from "framer-motion";
import { Progress } from "@/components/ui/progress";

interface CourseItem {
  title: string;
  description: string;
  skills: string;
  category: string;
  duration: string;
  status: string;
  url: string;
}

interface PathStats {
  total: number;
  completed: number;
  progress: number;
}

const LearningPath = () => {
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [stats, setStats] = useState<PathStats>({ total: 0, completed: 0, progress: 0 });
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchLearningPath = async () => {
      try {
        const response = await axios.get("/api/learning_path", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = response.data;
        // Handle both old (array) and new ({courses, stats}) formats
        if (Array.isArray(data)) {
          setCourses(data);
          const done = data.filter((c) => c.status === "Completed").length;
          setStats({ total: data.length, completed: done, progress: data.length ? Math.round((done / data.length) * 100) : 0 });
        } else {
          setCourses(data.courses || []);
          setStats(data.stats || { total: 0, completed: 0, progress: 0 });
        }
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
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Loading learning path…</p>
      </div>
    );

  const completedCount = courses.filter((c) => c.status === "Completed").length;
  const inProgressCount = courses.filter((c) => c.status !== "Completed").length;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-start"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Learning Path</h1>
          <p className="text-gray-500 text-sm mt-0.5">Your optimised course sequence</p>
        </div>
        <Button className="gap-2 rounded-xl bg-blue-500 hover:bg-blue-600 text-white transition-colors">
          <Brain className="h-4 w-4" /> Optimize
        </Button>
      </motion.div>

      {/* Progress overview */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
      >
        <Card className="p-5 border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                  <Target className="h-4 w-4 text-blue-500" />
                </div>
                <div>
                  <p className="text-xl font-bold text-gray-900 leading-none">{stats.progress}%</p>
                  <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider mt-0.5">Complete</p>
                </div>
              </div>
              <div className="h-8 w-px bg-gray-100" />
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="h-3.5 w-3.5 text-teal-500" />
                  <span className="text-gray-600 font-medium">{completedCount} Done</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-amber-500" />
                  <span className="text-gray-600 font-medium">{inProgressCount} Remaining</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <BookOpen className="h-3.5 w-3.5 text-blue-500" />
                  <span className="text-gray-600 font-medium">{stats.total} Total</span>
                </div>
              </div>
            </div>
          </div>
          <Progress value={stats.progress} className="h-2 rounded-full" />
        </Card>
      </motion.div>

      {/* Timeline */}
      <div className="relative ml-4">
        {/* Vertical line */}
        <div className="absolute left-0 top-2 bottom-2 w-px bg-gradient-to-b from-blue-400 via-teal-400 to-gray-200" />

        {courses.length > 0 ? (
          courses.map((course, index) => {
            const isCompleted = course.status === "Completed";
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -24 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + index * 0.08, duration: 0.4, ease: "easeOut" }}
                className="relative pl-8 pb-6 last:pb-0"
              >
                {/* Timeline dot */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.15 + index * 0.08 + 0.1, type: "spring", stiffness: 400 }}
                  className={`absolute left-[-6px] top-3 w-3 h-3 rounded-full ring-[3px] ring-white ${
                    isCompleted ? "bg-teal-500" : "bg-blue-500"
                  }`}
                />

                <Card className={`p-5 border transition-all duration-300 hover:shadow-lg group ${
                  isCompleted
                    ? "border-teal-200 bg-teal-50/20"
                    : "border-gray-100 bg-white hover:border-blue-100"
                }`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 text-sm group-hover:text-blue-600 transition-colors truncate">
                          {course.title}
                        </h3>
                        {isCompleted && (
                          <span className="flex items-center gap-0.5 text-[10px] font-semibold text-teal-700 bg-teal-100 px-1.5 py-0.5 rounded-full flex-shrink-0">
                            <CheckCircle className="h-2.5 w-2.5" /> Done
                          </span>
                        )}
                      </div>
                      <p className="text-gray-500 text-xs line-clamp-2 mb-2.5">
                        {course.description}
                      </p>

                      {/* Meta row */}
                      <div className="flex flex-wrap items-center gap-2">
                        {course.category && (
                          <span className="text-[10px] px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full font-medium">
                            {course.category}
                          </span>
                        )}
                        {course.duration && (
                          <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                            <Clock className="h-2.5 w-2.5" /> {course.duration}
                          </span>
                        )}
                        {course.skills && course.skills.split(",").slice(0, 3).map((s, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-medium">
                            {s.trim()}
                          </span>
                        ))}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-xl text-xs gap-1.5 border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 hover:gap-2.5 transition-all flex-shrink-0"
                      onClick={() => window.open(course.url, "_blank")}
                    >
                      {isCompleted ? "Review" : "Continue"} <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </Card>
              </motion.div>
            );
          })
        ) : (
          <div className="text-center py-16">
            <Trophy className="h-12 w-12 text-gray-200 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">No learning path available yet.</p>
            <p className="text-gray-300 text-xs mt-1">Complete a quiz to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningPath;
