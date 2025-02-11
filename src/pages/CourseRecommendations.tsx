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
    const fetchCourses = async () => {
      try {
        const response = await axios.get("https://smartpathai-1.onrender.com/recommend_courses", {
          headers: { Authorization: `Bearer ${token}` },
        });

        console.log("Courses received:", response.data);
        setCourses(response.data);

        // Fetch user progress (completed courses)
        const progressResponse = await axios.get("http://localhost:5000/user_progress", {
          headers: { Authorization: `Bearer ${token}` },
        });

        setCompletedCourses(new Set(progressResponse.data.completed_courses || []));
      } catch (error) {
        console.error("Error fetching courses:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, [token]);

  const markAsComplete = async (courseTitle) => {
    try {
      await axios.post(
        "http://localhost:5000/mark_completed",
        { courseTitle },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setCompletedCourses((prev) => new Set([...prev, courseTitle]));
      toast.success(`✅ "${courseTitle}" marked as completed!`);
    } catch (error) {
      console.error("Error marking course as complete:", error);
      toast.error("❌ Failed to mark as completed. Try again.");
    }
  };

  if (loading) return <div className="text-center py-10 text-xl font-medium">Loading courses...</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🎓 Personalized Course Recommendations</h1>
        </div>

        {/* Course Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.length > 0 ? (
            courses.map((course, index) => (
              <Card key={index} className="p-6 shadow-lg hover:shadow-xl transition-all bg-white rounded-xl">
                {/* Course Image */}
                {course.image ? (
                  <img src={course.image} alt={course.Title} className="w-full h-40 object-cover rounded-md mb-4" />
                ) : (
                  <img src="/fallback_course_image.png" alt="Fallback" className="w-full h-40 object-cover rounded-md mb-4" />
                )}

                {/* Course Title */}
                <h3 className="font-semibold text-lg mb-2 text-gray-800">{course.Title || "No Title Available"}</h3>

                {/* Short Intro */}
                <p className="text-sm text-gray-500 mb-4">{course["Short Intro"] || "No description available"}</p>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {(course.Skills || "No Skills").split(",").map((tag, idx) => (
                    <span key={idx} className="text-xs px-2 py-1 bg-primary/10 text-primary rounded">
                      {tag.trim()}
                    </span>
                  ))}
                </div>

                {/* Course Info */}
                <p className="text-sm text-gray-500 mb-2">📌 {course.Category} | {course["Course Type"] || "General"}</p>
                <p className="text-sm text-gray-500 mb-2">🕒 {course.Duration || "N/A"}</p>
                <p className="text-sm text-gray-500 mb-2">⭐ {course.Rating || "N/A"}</p>

                {/* Buttons */}
                <div className="flex justify-between gap-2 mt-4">
                  {/* Go to Course Button */}
                  <Button className="flex-1 flex items-center justify-center gap-2" onClick={() => window.open(course.URL, "_blank")}>
                    <PlayCircle className="h-4 w-4" />
                    Go to Course
                  </Button>

                  {/* Mark as Complete Button */}
                  <Button
                    className="flex-1 flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600"
                    disabled={completedCourses.has(course.Title)}
                    onClick={() => markAsComplete(course.Title)}
                  >
                    <CheckCircle className="h-4 w-4" />
                    {completedCourses.has(course.Title) ? "Completed" : "Mark Complete"}
                  </Button>
                </div>
              </Card>
            ))
          ) : (
            <p className="text-center col-span-3 text-gray-500">No courses found.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CourseRecommendations;
