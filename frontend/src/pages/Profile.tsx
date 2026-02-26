import { useEffect, useState, useMemo } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  User,
  Edit3,
  Save,
  X,
  Mail,
  Loader2,
  AlertTriangle,
  Code2,
  Cpu,
  Globe,
  Layers,
  Lightbulb,
  Rocket,
  Zap,
  BookOpen,
  GraduationCap,
  Palette,
  Database,
  Shield,
  Smartphone,
  Terminal,
  GitBranch,
  Cloud,
} from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";

const INTEREST_OPTIONS = [
  "Web Development",
  "AI / Machine Learning",
  "Data Science",
  "Cloud Computing",
  "Cybersecurity",
  "Mobile Development",
  "DevOps & CI/CD",
  "Blockchain",
  "Game Development",
  "UI/UX Design",
  "Database & SQL",
  "Python",
  "Java",
  "JavaScript",
  "System Design",
  "DSA & Competitive",
];

const FLOAT_ICONS = [
  Code2, Cpu, Globe, Layers, Lightbulb, Rocket, Zap,
  BookOpen, Palette, Database, Shield, Smartphone, Terminal, GitBranch, Cloud,
];

function FloatingIcons() {
  const icons = useMemo(() =>
    FLOAT_ICONS.map((Icon, i) => ({
      Icon,
      size: 14 + Math.random() * 12,
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: 22 + Math.random() * 18,
      delay: Math.random() * -20,
      driftX: (Math.random() - 0.5) * 80,
      driftY: (Math.random() - 0.5) * 80,
      key: i,
    })), []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {icons.map(({ Icon, size, left, top, duration, delay, driftX, driftY, key }) => (
        <motion.div
          key={key}
          className="absolute text-blue-200/40"
          style={{ left: `${left}%`, top: `${top}%` }}
          animate={{
            x: [0, driftX, -driftX * 0.5, 0],
            y: [0, driftY * 0.5, -driftY, 0],
            rotate: [0, 180, 360],
            opacity: [0.1, 0.25, 0.1],
          }}
          transition={{ duration, delay, repeat: Infinity, ease: "easeInOut" }}
        >
          <Icon size={size} strokeWidth={1.2} />
        </motion.div>
      ))}
    </div>
  );
}

const sectionFade = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.1, duration: 0.4, ease: "easeOut" },
  }),
};

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) { setError("No token found. Please log in."); setLoading(false); return; }
        const response = await axios.get("/api/profile", { headers: { Authorization: `Bearer ${token}` } });
        setProfile(response.data);
      } catch { setError("Failed to load profile."); }
      finally { setLoading(false); }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem("token");
      await axios.put("/api/profile", profile, { headers: { Authorization: `Bearer ${token}` } });
      toast.success("Profile updated!");
      setEditing(false);
    } catch { toast.error("Failed to update profile."); }
    finally { setSaving(false); }
  };

  const toggleInterest = (interest: string) => {
    const current = profile?.interests || [];
    setProfile({ ...profile, interests: current.includes(interest) ? current.filter((i) => i !== interest) : [...current, interest] });
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="text-gray-400 text-sm">Loading profile…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <AlertTriangle className="h-8 w-8 text-red-500" />
        <p className="text-red-500 font-medium">{error}</p>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="min-h-screen relative p-6">
      <FloatingIcons />

      <div className="max-w-2xl mx-auto space-y-6 relative z-10">
        {/* Header */}
        <motion.div custom={0} variants={sectionFade} initial="hidden" animate="show"
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Profile</h1>
            <p className="text-gray-500 text-sm mt-0.5">Manage your account and preferences</p>
          </div>
          {!editing ? (
            <Button onClick={() => setEditing(true)} variant="outline"
              className="gap-2 rounded-xl border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-all">
              <Edit3 className="h-4 w-4" /> Edit
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setEditing(false)} className="gap-2 text-gray-500">
                <X className="h-4 w-4" /> Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving}
                className="gap-2 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white rounded-xl shadow-md shadow-blue-500/20 transition-all active:scale-95">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save
              </Button>
            </div>
          )}
        </motion.div>

        {/* Avatar Card */}
        <motion.div custom={1} variants={sectionFade} initial="hidden" animate="show">
          <Card className="p-6 border-gray-100 bg-white/80 backdrop-blur-sm hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-5">
              <motion.div
                className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center shadow-lg shadow-blue-500/20"
                whileHover={{ rotate: 5, scale: 1.05 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <User className="h-7 w-7 text-white" />
              </motion.div>
              <div className="flex-1">
                {editing ? (
                  <Input value={profile.name || ""} onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="text-lg font-medium h-10 border-gray-200 focus:border-blue-400" placeholder="Your name" />
                ) : (
                  <h2 className="text-xl font-bold text-gray-900">{profile.name || "No Name"}</h2>
                )}
                <div className="flex items-center gap-1.5 mt-1 text-gray-400">
                  <Mail className="h-3.5 w-3.5" />
                  <span className="text-sm">{profile.email}</span>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Preferences */}
        <motion.div custom={2} variants={sectionFade} initial="hidden" animate="show">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Preferences</h3>
            <Card className="p-5 border-gray-100 bg-white/80 backdrop-blur-sm hover:shadow-lg transition-shadow">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 mb-1.5 block">Learning Pace</label>
                  <select
                    className="w-full p-2.5 border border-gray-200 rounded-xl bg-white text-sm focus:ring-1 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    value={profile.preferences?.pace || "Moderate"}
                    disabled={!editing}
                    onChange={(e) => setProfile({ ...profile, preferences: { ...(profile.preferences || {}), pace: e.target.value } })}
                  >
                    <option>Fast</option><option>Moderate</option><option>Slow</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 mb-1.5 block">Content Format</label>
                  <select
                    className="w-full p-2.5 border border-gray-200 rounded-xl bg-white text-sm focus:ring-1 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    value={profile.preferences?.content_format || "Video"}
                    disabled={!editing}
                    onChange={(e) => setProfile({ ...profile, preferences: { ...(profile.preferences || {}), content_format: e.target.value } })}
                  >
                    <option>Video</option><option>Text</option><option>Interactive</option>
                  </select>
                </div>
              </div>
            </Card>
          </div>
        </motion.div>

        {/* Interests */}
        <motion.div custom={3} variants={sectionFade} initial="hidden" animate="show">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Interests</h3>
              <span className="text-xs text-gray-400 tabular-nums">{(profile.interests || []).length} selected</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {INTEREST_OPTIONS.map((label) => {
                const isSelected = (profile.interests || []).includes(label);
                return (
                  <motion.button
                    key={label}
                    type="button"
                    disabled={!editing}
                    onClick={() => editing && toggleInterest(label)}
                    whileHover={editing ? { scale: 1.04 } : {}}
                    whileTap={editing ? { scale: 0.96 } : {}}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 border
                      ${editing ? "cursor-pointer" : "cursor-default"}
                      ${isSelected
                        ? "bg-blue-500 border-blue-500 text-white shadow-sm shadow-blue-500/20"
                        : "bg-white border-gray-200 text-gray-500"}
                      ${editing && !isSelected ? "hover:border-blue-300 hover:text-blue-600" : ""}
                    `}
                    layout
                  >
                    {label}
                  </motion.button>
                );
              })}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Profile;
