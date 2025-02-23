import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Award, CheckCircle, Search, Star, Loader2 } from "lucide-react";
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

      const processedCerts = certRes.data
        .map((cert) => {
          if (typeof cert === "string") {
            const [title, provider = "Various", duration = "3-6 months"] = cert.split(" - ");
            return {
              title: title.trim(),
              provider,
              duration,
              url: "#",
              level: "Intermediate",
              prerequisites: "None",
            };
          }
          return cert;
        })
        .filter((cert) => cert && cert.title);

      setCertifications(processedCerts);
      setEarnedCertifications(new Set(earnedRes.data));
    } catch (error) {
      console.error("Error fetching certifications:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
      } else {
        toast.error("Failed to fetch certifications. Please try again.");
      }
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
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
      } else {
        toast.error("Failed to mark certification as completed. Please try again.");
      }
    }
  };

  const filteredCertifications = certifications.filter((cert) => {
    const searchTerm = searchQuery.toLowerCase();
    const certTitle = cert?.title?.toLowerCase() || "";
    return certTitle.includes(searchTerm);
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 animate-fade-up">
          📜 Certifications
        </h1>

        {/* Search Input */}
        <div className="relative mb-8 animate-fade-up">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <Input
            aria-label="Search certifications"
            placeholder="Search certifications..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Handle No Certifications Found */}
        {!loading && certifications.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            No certifications found. Please try again later.
          </div>
        )}

        {/* Handle No Search Results */}
        {filteredCertifications.length === 0 && !loading && (
          <div className="text-center text-gray-500 mt-8">
            No certifications match your search.
          </div>
        )}

        {/* Certifications Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {loading ? (
            <div className="flex justify-center items-center col-span-full">
              <Loader2 className="h-12 w-12 text-gray-400 animate-spin" />
            </div>
          ) : (
            filteredCertifications.map((cert, index) => (
              <Card
                key={index}
                className={`p-6 hover:shadow-lg transition-all animate-fade-up ${
                  earnedCertifications.has(cert.title) ? "border-green-400" : ""
                }`}
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <Award className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold flex items-center gap-2">
                      {cert.title}
                      {earnedCertifications.has(cert.title) && (
                        <Badge className="bg-green-100 text-green-700">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Completed
                        </Badge>
                      )}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {cert.provider} | ⏳ {cert.duration}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      🔥 Level: {cert.level}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      📋 Prerequisites: {cert.prerequisites}
                    </p>
                  </div>
                </div>

                {/* Start Certification Button */}
                <Button
                  className="w-full"
                  onClick={() => cert.url && cert.url !== "#" && window.open(cert.url, "_blank")}
                  disabled={!cert.url || cert.url === "#"}
                  aria-label={`Start ${cert.title} certification`}
                >
                  Start Certification
                </Button>

                {/* Mark as Complete Button */}
                <Button
                  className={`w-full mt-2 flex gap-2 ${
                    earnedCertifications.has(cert.title)
                      ? "bg-green-500 cursor-not-allowed"
                      : ""
                  }`}
                  disabled={earnedCertifications.has(cert.title)}
                  onClick={() => markAsCompleted(cert.title)}
                  aria-label={`Mark ${cert.title} as completed`}
                >
                  {earnedCertifications.has(cert.title) ? "Completed" : "Mark Complete"}
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
