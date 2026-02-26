import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import {
  Brain,
  Target,
  Award,
  Loader2,
  Flame,
  Trophy,
  BookOpen,
  GraduationCap,
  Zap,
} from "lucide-react";
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
import { motion } from "framer-motion";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface PerformanceData {
  learning_hours: number;
  average_score: number;
  skills_mastered: number;
  streak: number;
  quizzes_taken: number;
  best_score: number;
  completed_courses: number;
  earned_certifications: number;
  recent_activity: Array<{ date: string; learning_hours: number; score: number }>;
  skill_progress: Array<{ skill?: string; progress?: number }>;
}

const defaultPerformance: PerformanceData = {
  learning_hours: 0,
  average_score: 0,
  skills_mastered: 0,
  streak: 0,
  quizzes_taken: 0,
  best_score: 0,
  completed_courses: 0,
  earned_certifications: 0,
  recent_activity: [],
  skill_progress: [],
};

const Performance = () => {
  const [performance, setPerformance] = useState<PerformanceData>(defaultPerformance);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const validatePerformanceData = (data: unknown): PerformanceData => {
    const d = data as Record<string, unknown>;
    return {
      learning_hours: Number(d?.learning_hours ?? 0),
      average_score: Number(d?.average_score ?? 0),
      skills_mastered: Number(d?.skills_mastered ?? 0),
      streak: Number(d?.streak ?? 0),
      quizzes_taken: Number(d?.quizzes_taken ?? 0),
      best_score: Number(d?.best_score ?? 0),
      completed_courses: Number(d?.completed_courses ?? 0),
      earned_certifications: Number(d?.earned_certifications ?? 0),
      recent_activity: (Array.isArray(d?.recent_activity) ? d.recent_activity : []).map((a: unknown) => {
        const act = a as Record<string, unknown>;
        return { date: String(act?.date ?? ""), learning_hours: Number(act?.learning_hours ?? 0), score: Number(act?.score ?? 0) };
      }),
      skill_progress: Array.isArray(d?.skill_progress) ? d.skill_progress : [],
    };
  };

  const fetchPerformance = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const response = await axios.get("/api/performance", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPerformance(validatePerformanceData(response.data));
      setError(null);
    } catch (error) {
      setError(error.response?.data?.error || "Failed to fetch performance data");
      setPerformance(defaultPerformance);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPerformance();
    const id = setInterval(fetchPerformance, 60000);
    return () => clearInterval(id);
  }, [fetchPerformance]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" as const, labels: { usePointStyle: true, padding: 20, font: { family: "Inter", size: 12 } } },
      tooltip: {
        mode: "nearest" as const,
        intersect: false,
        backgroundColor: "#fff",
        titleColor: "#111",
        bodyColor: "#555",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        cornerRadius: 10,
        padding: 12,
        titleFont: { family: "Inter", weight: "600" },
        bodyFont: { family: "Inter" },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { font: { family: "Inter", size: 11 }, color: "#9ca3af" } },
      y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.04)" }, ticks: { font: { family: "Inter", size: 11 }, color: "#9ca3af" } },
    },
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Loading performance…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <p className="text-red-500 font-medium">{error}</p>
      </div>
    );
  }

  const chartData = {
    labels: performance.recent_activity.map((a) => a.date),
    datasets: [
      {
        label: "Learning Hours",
        data: performance.recent_activity.map((a) => a.learning_hours),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59,130,246,0.08)",
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#3b82f6",
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: "Score",
        data: performance.recent_activity.map((a) => a.score),
        borderColor: "#14b8a6",
        backgroundColor: "rgba(20,184,166,0.08)",
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#14b8a6",
        pointRadius: 4,
        pointHoverRadius: 6,
        hidden: true,
      },
    ],
  };

  const STAT_CARDS = [
    { label: "Study Streak", value: `${performance.streak} days`, icon: Flame, gradient: "from-orange-500 to-red-500", shadow: "shadow-orange-500/20" },
    { label: "Learning Hours", value: `${performance.learning_hours.toFixed(1)} hrs`, icon: Brain, gradient: "from-blue-500 to-blue-600", shadow: "shadow-blue-500/20" },
    { label: "Average Score", value: `${performance.average_score}%`, icon: Target, gradient: "from-teal-500 to-emerald-600", shadow: "shadow-teal-500/20" },
    { label: "Best Quiz Score", value: `${performance.best_score}%`, icon: Zap, gradient: "from-amber-500 to-orange-500", shadow: "shadow-amber-500/20" },
    { label: "Quizzes Taken", value: performance.quizzes_taken, icon: BookOpen, gradient: "from-violet-500 to-purple-600", shadow: "shadow-violet-500/20" },
    { label: "Skills Mastered", value: `${performance.skills_mastered}`, icon: Award, gradient: "from-pink-500 to-rose-600", shadow: "shadow-pink-500/20" },
  ];

  const MINI_STATS = [
    { label: "Courses Done", value: performance.completed_courses, icon: BookOpen },
    { label: "Certs Earned", value: performance.earned_certifications, icon: GraduationCap },
    { label: "Best Score", value: `${performance.best_score}%`, icon: Trophy },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Performance</h1>
        <p className="text-gray-500 text-sm mt-0.5">Track your learning analytics</p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {STAT_CARDS.map(({ label, value, icon: Icon, gradient, shadow }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Card className={`p-4 border-0 bg-gradient-to-br ${gradient} text-white shadow-lg ${shadow} hover:shadow-xl transition-shadow`}>
              <div className="flex items-center justify-between mb-2">
                <div className="p-1.5 bg-white/15 rounded-lg">
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <p className="text-xl font-bold leading-none">{value}</p>
              <p className="text-white/70 text-[10px] font-medium uppercase tracking-wider mt-1.5">{label}</p>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Summary row */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
        <div className="flex items-center gap-6 p-4 rounded-xl bg-white border border-gray-100">
          {MINI_STATS.map(({ label, value, icon: Icon }) => (
            <div key={label} className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                <Icon className="h-4 w-4 text-blue-500" />
              </div>
              <div>
                <p className="text-lg font-bold text-gray-900 leading-none">{value}</p>
                <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider mt-0.5">{label}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Chart */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="p-6 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Learning Progress</h2>
          <div className="h-[380px]">
            {performance.recent_activity.length > 0 ? (
              <Line data={chartData} options={chartOptions} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                <BookOpen className="h-10 w-10 text-gray-200" />
                <p className="text-sm">Complete quizzes and courses to see your progress here</p>
              </div>
            )}
          </div>
        </Card>
      </motion.div>
    </div>
  );
};

export default Performance;
