import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Brain, Target, Award, TrendingUp, Lightbulb } from "lucide-react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PerformanceData {
  learning_hours: number;
  average_score: number;
  skills_mastered: number;
  recent_activity: Array<{
    date: string;
    learning_hours: number;
    score: number;
  }>;
  skill_progress: Array<{
    skill?: string;
    progress?: number;
  }>;
}

// Default empty state with proper data structure
const defaultPerformance: PerformanceData = {
  learning_hours: 0,
  average_score: 0,
  skills_mastered: 0,
  recent_activity: [],
  skill_progress: [],
};

const Performance = () => {
  const [performance, setPerformance] =
    useState<PerformanceData>(defaultPerformance);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Validate and sanitize performance data
  const validatePerformanceData = (data: unknown): PerformanceData => {
    const validData = data as Record<string, unknown>;
    // Ensure all required fields exist with correct types
    const validated: PerformanceData = {
      learning_hours: Number(validData?.learning_hours ?? 0),
      average_score: Number(validData?.average_score ?? 0),
      skills_mastered: Number(validData?.skills_mastered ?? 0),
      recent_activity: Array.isArray(validData?.recent_activity)
        ? validData.recent_activity
        : [],
      skill_progress: Array.isArray(validData?.skill_progress)
        ? validData.skill_progress
        : [],
    };

    // Ensure each activity has required properties
    validated.recent_activity = validated.recent_activity.map(
      (activity: unknown) => {
        const act = activity as Record<string, unknown>;
        return {
          date: String(act?.date ?? ""),
          learning_hours: Number(act?.learning_hours ?? 0),
          score: Number(act?.score ?? 0),
        };
      }
    );

    return validated;
  };

  const fetchPerformance = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5000/performance", {
        headers: { Authorization: `Bearer ${token}` },
      });

      const validatedData = validatePerformanceData(response.data);
      setPerformance(validatedData);
      setError(null);
    } catch (error) {
      console.error("Error fetching performance data:", error);
      setError(
        error.response?.data?.error || "Failed to fetch performance data"
      );
      setPerformance(defaultPerformance); // Reset to default state on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPerformance();
    const intervalId = setInterval(fetchPerformance, 60 * 1000);
    return () => clearInterval(intervalId);
  }, [fetchPerformance]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" as const },
      tooltip: {
        mode: "nearest" as const,
        intersect: false,
        backgroundColor: "rgba(255, 255, 255, 0.9)",
        titleColor: "#111827",
        bodyColor: "#111827",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        padding: 10,
      },
    },
    scales: {
      x: { grid: { display: false } },
      y: { beginAtZero: true, grid: { color: "rgba(0, 0, 0, 0.1)" } },
    },
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-6 bg-red-50">
          <p className="text-red-600">{error}</p>
        </Card>
      </div>
    );
  }

  const chartData = {
    labels: performance.recent_activity.map((activity) => activity.date),
    datasets: [
      {
        label: "Learning Hours",
        data: performance.recent_activity.map(
          (activity) => activity.learning_hours
        ),
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.4,
      },
      {
        label: "Score",
        data: performance.recent_activity.map((activity) => activity.score),
        borderColor: "rgb(139, 92, 246)",
        backgroundColor: "rgba(139, 92, 246, 0.1)",
        fill: true,
        tension: 0.4,
        hidden: true,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Performance Analytics
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6 hover:shadow-lg transition-all">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Learning Hours</p>
                <h3 className="font-semibold">
                  {performance.learning_hours.toFixed(1)} Hours
                </h3>
              </div>
            </div>
          </Card>
          <Card className="p-6 hover:shadow-lg transition-all">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-accent/10 rounded-lg">
                <Target className="h-6 w-6 text-accent" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Average Score</p>
                <h3 className="font-semibold">{performance.average_score}%</h3>
              </div>
            </div>
          </Card>
          <Card className="p-6 hover:shadow-lg transition-all">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Award className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Skills Mastered</p>
                <h3 className="font-semibold">
                  {performance.skills_mastered} Skills
                </h3>
              </div>
            </div>
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Learning Progress</h2>
          <div className="h-[400px]">
            {performance.recent_activity.length > 0 ? (
              <Line data={chartData} options={chartOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                No activity data available
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Performance;
