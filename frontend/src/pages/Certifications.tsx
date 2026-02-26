import { useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Award, Search, CheckCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";

const Certifications = () => {
  const [certifications, setCertifications] = useState([]);
  const [earnedCertifications, setEarnedCertifications] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [certRes, earnedRes] = await Promise.all([
          axios.get("/api/recommend_certifications", { headers: { Authorization: `Bearer ${token}` } }),
          axios.get("/api/earned_certifications", { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        setCertifications(certRes.data || []);
        setEarnedCertifications(new Set((earnedRes.data || []).map((c) => c.name)));
      } catch {
        toast.error("Failed to load certifications.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [token]);

  const handleMarkComplete = async (name) => {
    try {
      await axios.post("/api/mark_certification_completed", { certificationName: name }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEarnedCertifications((prev) => new Set([...prev, name]));
      toast.success(`"${name}" marked as completed!`);
    } catch {
      toast.error("Failed to update certification.");
    }
  };

  const filtered = certifications.filter((c) =>
    c.name?.toLowerCase().includes(search.toLowerCase()) ||
    c.provider?.toLowerCase().includes(search.toLowerCase()),
  );

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Loading certifications…</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-end justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Certifications</h1>
          <p className="text-gray-500 text-sm mt-0.5">Recommended certifications for your path</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search certifications…"
            className="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-200 w-64 transition-all"
          />
        </div>
      </motion.div>

      {filtered.length === 0 ? (
        <p className="text-center text-gray-400 py-12 text-sm">No certifications found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((cert, index) => {
            const isEarned = earnedCertifications.has(cert.name);
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.06 }}
              >
                <Card className={`p-5 border transition-all duration-300 hover:shadow-lg group ${
                  isEarned ? "border-amber-200 bg-amber-50/30" : "border-gray-100 bg-white hover:border-blue-100"
                }`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      isEarned ? "bg-amber-100" : "bg-blue-50 group-hover:bg-blue-100"
                    } transition-colors`}>
                      <Award className={`h-5 w-5 ${isEarned ? "text-amber-600" : "text-blue-500"}`} />
                    </div>
                    {isEarned && (
                      <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                        <CheckCircle className="h-3 w-3" /> Earned
                      </span>
                    )}
                  </div>

                  <h3 className="font-semibold text-gray-900 text-sm mb-1 group-hover:text-blue-600 transition-colors">{cert.name}</h3>
                  <p className="text-gray-400 text-xs mb-3">{cert.provider}</p>
                  {cert.skills && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {(typeof cert.skills === "string" ? cert.skills.split(",") : cert.skills).slice(0, 3).map((s, i) => (
                        <span key={i} className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-medium">
                          {String(s).trim()}
                        </span>
                      ))}
                    </div>
                  )}

                  <Button
                    size="sm"
                    onClick={() => handleMarkComplete(cert.name)}
                    disabled={isEarned}
                    className={`w-full rounded-xl text-xs h-8 transition-colors ${
                      isEarned
                        ? "bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-100"
                        : "bg-blue-500 hover:bg-blue-600 text-white"
                    }`}
                  >
                    {isEarned ? "Completed" : "Mark Complete"}
                  </Button>
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Certifications;
