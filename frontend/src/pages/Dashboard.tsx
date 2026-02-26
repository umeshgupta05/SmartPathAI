import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import {
  Brain,
  BookOpen,
  Trophy,
  TrendingUp,
  MessageCircle,
  Send,
  X,
  Loader2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

interface DashboardData {
  currentCourse: string;
  completedCourses: number;
  certifications: number;
  overallProgress: number;
  recommendedCourses: Array<{
    Title?: string;
    "Short Intro"?: string;
    Skills?: string;
    Category?: string;
    Duration?: string;
    Rating?: string;
    Site?: string;
    URL?: string;
    // backwards compat with old shape
    title?: string;
    description?: string;
  }>;
}

interface Message {
  sender: string;
  text: string;
}

const STAT_CARDS = [
  {
    key: "course",
    label: "Current Course",
    icon: Brain,
    gradient: "from-blue-500 to-blue-600",
    shadow: "shadow-blue-500/20",
    getValue: (d: DashboardData) => d.currentCourse,
  },
  {
    key: "completed",
    label: "Courses Completed",
    icon: BookOpen,
    gradient: "from-teal-500 to-emerald-600",
    shadow: "shadow-teal-500/20",
    getValue: (d: DashboardData) => `${d.completedCourses} Courses`,
  },
  {
    key: "certs",
    label: "Certifications",
    icon: Trophy,
    gradient: "from-amber-500 to-orange-500",
    shadow: "shadow-amber-500/20",
    getValue: (d: DashboardData) => `${d.certifications} Earned`,
  },
  {
    key: "progress",
    label: "Overall Progress",
    icon: TrendingUp,
    gradient: "from-violet-500 to-purple-600",
    shadow: "shadow-violet-500/20",
    getValue: (d: DashboardData) => `${d.overallProgress}%`,
  },
];

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    currentCourse: "No active course",
    completedCourses: 0,
    certifications: 0,
    overallProgress: 0,
    recommendedCourses: [],
  });
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) { navigate("/auth"); return; }

        const response = await axios.get("/api/dashboard", {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          withCredentials: true,
        });
        if (response.data) setDashboardData(response.data);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          localStorage.removeItem("token");
          navigate("/auth");
        } else {
          toast.error("Failed to load dashboard data.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [navigate]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const token = localStorage.getItem("token");
    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");
    setSending(true);
    try {
      const response = await axios.post(
        "/api/chatbot",
        { message: input },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setMessages([...newMessages, { sender: "bot", text: response.data.response }]);
    } catch {
      toast.error("Failed to send message.");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-0.5">Your learning overview</p>
        </div>
        <Button
          variant="outline"
          onClick={() => setChatOpen(!chatOpen)}
          className="gap-2 rounded-xl border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-all"
        >
          <MessageCircle className="h-4 w-4" />
          <span className="hidden sm:inline">AI Chat</span>
        </Button>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {STAT_CARDS.map(({ key, label, icon: Icon, gradient, shadow, getValue }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.4, ease: "easeOut" }}
          >
            <Card className={`p-5 border-0 bg-gradient-to-br ${gradient} text-white shadow-lg ${shadow} hover:shadow-xl transition-shadow group`}>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-white/70 text-xs font-medium uppercase tracking-wider">{label}</p>
                  <p className="text-lg font-bold leading-snug">{getValue(dashboardData)}</p>
                </div>
                <div className="p-2 bg-white/15 rounded-xl group-hover:bg-white/25 transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Recommended Courses */}
      {dashboardData.recommendedCourses.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="space-y-4"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-gray-900">Recommended for you</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {dashboardData.recommendedCourses.map((course, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 + idx * 0.08 }}
              >
                <Card className="p-5 border border-gray-100 bg-white hover:shadow-lg hover:border-blue-100 transition-all duration-300 group">
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-100 transition-colors">
                      <BookOpen className="h-5 w-5 text-blue-500" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 text-sm group-hover:text-blue-600 transition-colors leading-snug truncate">
                        {course.Title || course.title || "Untitled"}
                      </h3>
                      <p className="text-gray-500 text-xs mt-1 line-clamp-2">
                        {course["Short Intro"] || course.description || "Start learning now"}
                      </p>
                    </div>
                  </div>

                  {course.Skills && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {course.Skills.split(",").slice(0, 3).map((s, i) => (
                        <span key={i} className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-medium">
                          {s.trim()}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>{course.Category || ""}</span>
                    {course.URL ? (
                      <button
                        onClick={() => window.open(course.URL, "_blank")}
                        className="text-blue-500 hover:text-blue-600 font-medium transition-colors"
                      >
                        View →
                      </button>
                    ) : (
                      <button
                        onClick={() => navigate("/courses")}
                        className="text-blue-500 hover:text-blue-600 font-medium transition-colors"
                      >
                        View →
                      </button>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* AI Chatbot Panel */}
      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.95 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="fixed bottom-6 right-6 w-[360px] bg-white rounded-2xl shadow-2xl shadow-gray-300/50 border border-gray-200/80 z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-blue-600 to-teal-500 text-white">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                <span className="font-semibold text-sm">AI Assistant</span>
              </div>
              <button onClick={() => setChatOpen(false)} className="hover:bg-white/20 p-1 rounded-lg transition-colors">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Messages */}
            <div className="h-64 overflow-y-auto p-4 space-y-2.5">
              {messages.length === 0 && (
                <p className="text-gray-400 text-xs text-center pt-20">
                  Ask me anything about your learning path!
                </p>
              )}
              {messages.map((msg, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`max-w-[80%] px-3 py-2 rounded-xl text-sm ${
                    msg.sender === "user"
                      ? "ml-auto bg-blue-500 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {msg.text}
                </motion.div>
              ))}
              {sending && (
                <div className="flex items-center gap-1.5 text-gray-400 text-xs">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Thinking…
                </div>
              )}
            </div>

            {/* Input */}
            <div className="flex items-center gap-2 p-3 border-t border-gray-100">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                className="flex-1 text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-200 transition-all"
                placeholder="Type a message…"
              />
              <Button
                size="icon"
                onClick={sendMessage}
                disabled={!input.trim() || sending}
                className="rounded-xl bg-blue-500 hover:bg-blue-600 h-9 w-9 transition-colors"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;
