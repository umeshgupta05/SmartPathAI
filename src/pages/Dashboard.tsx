import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Brain, Book, Trophy, ChartBar, MessageCircle, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    currentCourse: "No active course",
    completedCourses: 0,
    certifications: 0,
    overallProgress: 0,
    recommendedCourses: [],
  });
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          navigate("/login");
          return;
        }

        const response = await axios.get("http://localhost:5000/dashboard", {
          headers: { Authorization: `Bearer ${token}` },
        });

        setDashboardData(response.data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
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

    try {
      const response = await axios.post("http://localhost:5000/chatbot", { message: input }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages([...newMessages, { sender: "bot", text: response.data.response }]);
    } catch (error) {
      console.error("Error fetching chatbot response:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 animate-fade-up">Dashboard</h1>
          <Button variant="outline" size="icon" className="rounded-full hover:bg-primary/10 hover:text-primary" onClick={() => setChatOpen(!chatOpen)}>
            <MessageCircle className="h-5 w-5" />
          </Button>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 hover:shadow-lg transition-all animate-fade-up">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Current Course</p>
                <h3 className="font-semibold">{dashboardData.currentCourse}</h3>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all animate-fade-up">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-accent/10 rounded-lg">
                <Book className="h-6 w-6 text-accent" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Courses Completed</p>
                <h3 className="font-semibold">{dashboardData.completedCourses} Courses</h3>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all animate-fade-up">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Trophy className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Certifications</p>
                <h3 className="font-semibold">{dashboardData.certifications} Earned</h3>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-all animate-fade-up">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-accent/10 rounded-lg">
                <ChartBar className="h-6 w-6 text-accent" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Overall Progress</p>
                <h3 className="font-semibold">{dashboardData.overallProgress}%</h3>
              </div>
            </div>
          </Card>
        </div>

        {/* Chatbot */}
        {chatOpen && (
          <motion.div initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
            className="fixed bottom-16 right-6 bg-white shadow-lg rounded-lg w-80 p-4 border border-gray-200">
            <div className="h-60 overflow-y-auto mb-4 p-2 border-b">
              {messages.map((msg, index) => (
                <div key={index} className={`p-2 my-1 rounded-lg ${msg.sender === "user" ? "bg-blue-100" : "bg-gray-100"}`}>
                  {msg.text}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input type="text" value={input} onChange={(e) => setInput(e.target.value)} className="flex-1 border rounded p-2" placeholder="Type a message..." />
              <Button onClick={sendMessage}><Send className="h-4 w-4" /></Button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
