import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Award, CheckCircle, Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

const Certifications = () => {
  const [certifications, setCertifications] = useState([]);
  const [earnedCertifications, setEarnedCertifications] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchCertifications();
  }, []);

  const fetchCertifications = async () => {
    try {
      const requestConfig = {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        withCredentials: true,
      };

      const [certRes, earnedRes] = await Promise.all([
        axios.get("https://smartpathai-1.onrender.com/recommend_certifications", requestConfig),
        axios.get("https://smartpathai-1.onrender.com/earned_certifications", requestConfig),
      ]);

      setCertifications(certRes.data);
      setEarnedCertifications(new Set(earnedRes.data));
    } catch (error) {
      console.error("Error fetching certifications:", error);
      toast.error("Failed to fetch certifications. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const markAsCompleted = async (title) => {
    if (!title) {
      toast.error("Invalid certification title");
      return;
    }

    try {
      await axios.post(
        "https://smartpathai-1.onrender.com/mark_certification_completed",
        { title },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          withCredentials: true,
        }
      );

      setEarnedCertifications((prev) => new Set([...prev, title]));
      toast.success(`✅ "${title}" marked as completed!`);
    } catch (error) {
      console.error("Error marking certification:", error);
      toast.error("Failed to mark certification as completed.");
    }
  };

  const filteredCertifications = certifications.filter((cert) =>
    cert.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">📜 Certifications</h1>

        {/* Search Input */}
        <div className="relative mb-8">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <Input
            aria-label="Search certifications"
            placeholder="Search certifications..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Certifications Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div className="flex justify-center items-center col-span-full">
              <Loader2 className="h-12 w-12 text-gray-400 animate-spin" />
            </div>
          ) : (
            filteredCertifications.map((cert, index) => (
              <Card
                key={index}
                className={`p-6 hover:shadow-lg transition-all ${
                  earnedCertifications.has(cert.name) ? "border-green-400" : ""
                }`}
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <Award className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold flex items-center gap-2">
                      {cert.name}
                      {earnedCertifications.has(cert.name) && (
                        <Badge className="bg-green-100 text-green-700">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Completed
                        </Badge>
                      )}
                    </h3>
                    <p className="text-sm text-gray-500">
                      🔥 Level: {cert.difficulty}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">{cert.description}</p>
                  </div>
                </div>

                {/* Start Certification Button */}
                <Button
                  className="w-full"
                  onClick={() => window.open(cert.link, "_blank")}
                  disabled={!cert.link}
                  aria-label={`Start ${cert.name} certification`}
                >
                  Start Certification
                </Button>

                {/* Mark as Complete Button */}
                <Button
                  className={`w-full mt-2 ${
                    earnedCertifications.has(cert.name) ? "bg-green-500 cursor-not-allowed" : ""
                  }`}
                  disabled={earnedCertifications.has(cert.name)}
                  onClick={() => markAsCompleted(cert.name)}
                  aria-label={`Mark ${cert.name} as completed`}
                >
                  {earnedCertifications.has(cert.name) ? "Completed" : "Mark Complete"}
                </Button>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Certifications;
