import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlayCircle, CheckCircle, RefreshCw, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { motion } from "framer-motion";

const CourseRecommendations = () => {
  const [courses, setCourses] = useState([]);
  const [completedCourses, setCompletedCourses] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const token = localStorage.getItem("token");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [coursesRes, progressRes] = await Promise.all([
        axios.get("/api/recommend_courses", { headers: { Authorization: `Bearer ${token}` } }),
        axios.get("/api/user_progress", { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      setCourses(coursesRes.data);
      setCompletedCourses(new Set(progressRes.data?.completed_courses || []));
    } catch (error) {
      const msg = error.response?.status === 404
        ? "No courses found. Try refreshing."
        : "Failed to load courses.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [token]);

  const handleMarkComplete = async (title) => {
    try {
      await axios.post("/api/mark_completed", { courseTitle: title }, { headers: { Authorization: `Bearer ${token}` } });
      setCompletedCourses((prev) => new Set([...prev, title]));
      toast.success(`Marked "${title}" as completed!`);
    } catch { toast.error("Failed to update course status"); }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Loading courses…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-4">
        <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
        <Button onClick={fetchData} className="gap-2"><RefreshCw className="h-4 w-4" /> Try Again</Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Courses</h1>
          <p className="text-gray-500 text-sm mt-0.5">AI-personalised recommendations</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm" className="gap-2 rounded-xl border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-all">
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </motion.div>

      {courses.length === 0 ? (
        <Alert><AlertDescription>No courses found. Try refreshing or check back later.</AlertDescription></Alert>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {courses.map((course, index) => {
            const isComplete = completedCourses.has(course.Title);
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.06 }}
              >
                <Card className={`p-5 border transition-all duration-300 hover:shadow-lg group ${
                  isComplete ? "border-teal-200 bg-teal-50/30" : "border-gray-100 bg-white hover:border-blue-100"
                }`}>
                  <h3 className="font-semibold text-gray-900 text-sm mb-2 truncate group-hover:text-blue-600 transition-colors">
                    {course.Title}
                  </h3>
                  <p className="text-gray-500 text-xs mb-3 line-clamp-2">{course["Short Intro"]}</p>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {course.Skills?.split(",").slice(0, 3).map((skill, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-medium">
                        {skill.trim()}
                      </span>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-gray-500 mb-4">
                    <span>📁 {course.Category}</span>
                    <span>⏱ {course.Duration}</span>
                    <span>⭐ {course.Rating}</span>
                    <span>🌐 {course.Site}</span>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="flex-1 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-xs h-8 transition-colors"
                      onClick={() => window.open(course.URL, "_blank")}
                    >
                      <PlayCircle className="mr-1.5 h-3.5 w-3.5" /> View
                    </Button>
                    <Button
                      size="sm"
                      variant={isComplete ? "secondary" : "outline"}
                      onClick={() => handleMarkComplete(course.Title)}
                      disabled={isComplete}
                      className={`flex-1 rounded-xl text-xs h-8 transition-colors ${isComplete ? "bg-teal-100 text-teal-700 border-teal-200" : "border-gray-200 hover:bg-teal-50 hover:text-teal-600 hover:border-teal-200"}`}
                    >
                      <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
                      {isComplete ? "Done" : "Complete"}
                    </Button>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CourseRecommendations;
