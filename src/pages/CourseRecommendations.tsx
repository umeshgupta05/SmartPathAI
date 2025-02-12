import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlayCircle, CheckCircle } from "lucide-react";
import { toast } from "sonner";

const CourseRecommendations = () => {
  const [courses, setCourses] = useState([]);
  const [completedCourses, setCompletedCourses] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [coursesRes, progressRes] = await Promise.all([
          axios.get("https://smartpathai-1.onrender.com/recommend_courses", {
            headers: { Authorization: `Bearer ${token}` }
          }),
          axios.get("https://smartpathai-1.onrender.com/user_progress", {
            headers: { Authorization: `Bearer ${token}` }
          })
        ]);

        setCourses(coursesRes.data);
        setCompletedCourses(new Set(progressRes.data?.completed_courses || []));
      } catch (error) {
        toast.error("Failed to load courses");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  const handleMarkComplete = async (title) => {
    try {
      await axios.post(
        "https://smartpathai-1.onrender.com/mark_completed",
        { courseTitle: title },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCompletedCourses(prev => new Set([...prev, title]));
      toast.success(`Marked "${title}" as completed!`);
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  if (loading) return <div className="p-8 text-center">Loading courses...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Recommended Courses</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {courses.map((course, index) => (
          <Card key={index} className="p-6 shadow-sm">
            <h3 className="font-semibold text-lg mb-2">{course.Title}</h3>
            <p className="text-sm text-gray-600 mb-4">{course["Short Intro"]}</p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {course.Skills.split(",").map((skill, i) => (
                <span key={i} className="text-xs px-2 py-1 bg-gray-100 rounded">
                  {skill.trim()}
                </span>
              ))}
            </div>

            <div className="space-y-1 text-sm mb-4">
              <p>🏷️ {course.Category}</p>
              <p>⏱️ {course.Duration}</p>
              <p>⭐ {course.Rating}</p>
              <p>🌐 {course.Site}</p>
            </div>

            <div className="flex gap-2 mt-4">
              <Button 
                className="flex-1" 
                onClick={() => window.open(course.URL, "_blank")}
              >
                <PlayCircle className="mr-2 h-4 w-4" />
                View Course
              </Button>
              
              <Button
                variant={completedCourses.has(course.Title) ? "secondary" : "default"}
                onClick={() => handleMarkComplete(course.Title)}
                disabled={completedCourses.has(course.Title)}
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                {completedCourses.has(course.Title) ? "Completed" : "Mark Done"}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default CourseRecommendations;
