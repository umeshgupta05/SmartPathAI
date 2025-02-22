import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Award, CheckCircle, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
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
      const headers = { Authorization: `Bearer ${token}` };
      const [certRes, earnedRes] = await Promise.all([
        axios.get("https://smartpathai-1.onrender.com/recommend_certifications", { headers }),
        axios.get("https://smartpathai-1.onrender.com/earned_certifications", { headers }),
      ]);

      // Process and validate certification data
      const processedCerts = certRes.data.map(cert => {
        // If cert is a string, convert it to an object
        if (typeof cert === 'string') {
          const [title, provider = 'Various', duration = '3-6 months'] = cert.split(' - ');
          return {
            title: title.trim(),
            provider,
            duration,
            url: '#'  // Default URL
          };
        }
        return cert;
      }).filter(cert => cert && cert.title); // Filter out any invalid entries

      setCertifications(processedCerts);
      setEarnedCertifications(new Set(earnedRes.data));
    } catch (error) {
      console.error("Error fetching certifications:", error);
      toast.error("Failed to fetch certifications");
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
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setEarnedCertifications((prev) => new Set([...prev, title]));
      toast.success(`✅ "${title}" marked as completed!`);
    } catch (error) {
      console.error("Error marking certification:", error);
      toast.error("❌ Failed to mark certification as completed.");
    }
  };

  const filteredCertifications = certifications.filter((cert) => {
    const searchTerm = searchQuery.toLowerCase();
    const certTitle = cert?.title?.toLowerCase() || '';
    return certTitle.includes(searchTerm);
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 animate-fade-up">📜 Certifications</h1>

        {/* Search Bar */}
        <div className="relative mb-8 animate-fade-up">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <Input 
            placeholder="Search certifications..." 
            className="pl-10" 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Error State */}
        {!loading && certifications.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            No certifications found. Please try again later.
          </div>
        )}

        {/* Certifications Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {loading ? (
            [...Array(6)].map((_, index) => (
              <Skeleton key={index} className="h-40 rounded-lg" />
            ))
          ) : (
            filteredCertifications.map((cert, index) => (
              <Card 
                key={index} 
                className="p-6 hover:shadow-lg transition-all animate-fade-up"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <Award className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{cert.title}</h3>
                    <p className="text-sm text-gray-500">
                      {cert.provider} | ⏳ {cert.duration}
                    </p>
                  </div>
                </div>
                <Button 
                  className="w-full" 
                  onClick={() => window.open(cert.url, "_blank")}
                >
                  Start Certification
                </Button>
                <Button 
                  className="w-full mt-2 flex gap-2" 
                  disabled={earnedCertifications.has(cert.title)}
                  onClick={() => markAsCompleted(cert.title)}
                >
                  {earnedCertifications.has(cert.title) && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
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
