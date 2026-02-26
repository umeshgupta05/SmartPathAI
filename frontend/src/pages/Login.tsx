import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import {
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  GraduationCap,
  Code2,
  Cpu,
  Globe,
  Layers,
  Lightbulb,
  Rocket,
  Zap,
  BookOpen,
  Palette,
  Database,
  Shield,
  Smartphone,
  Terminal,
  GitBranch,
  Cloud,
} from "lucide-react";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

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
      size: 16 + Math.random() * 14,
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: 20 + Math.random() * 20,
      delay: Math.random() * -25,
      driftX: (Math.random() - 0.5) * 100,
      driftY: (Math.random() - 0.5) * 100,
      key: i,
    })), []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {icons.map(({ Icon, size, left, top, duration, delay, driftX, driftY, key }) => (
        <motion.div
          key={key}
          className="absolute text-blue-200/50"
          style={{ left: `${left}%`, top: `${top}%` }}
          animate={{
            x: [0, driftX, -driftX * 0.5, 0],
            y: [0, driftY * 0.5, -driftY, 0],
            rotate: [0, 180, 360],
            opacity: [0.15, 0.35, 0.15],
          }}
          transition={{ duration, delay, repeat: Infinity, ease: "easeInOut" }}
        >
          <Icon size={size} strokeWidth={1.2} />
        </motion.div>
      ))}
    </div>
  );
}

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } };
const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

const Login = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();

  const authSchema = z
    .object({
      name: isSignUp ? z.string().min(2, "Name must be at least 2 characters") : z.string().optional(),
      email: z.string().email("Invalid email address"),
      password: z.string().min(6, "Password must be at least 6 characters"),
      confirmPassword: isSignUp ? z.string().min(6, "Confirm password is required") : z.string().optional(),
    })
    .refine((data) => { if (isSignUp) return data.password === data.confirmPassword; return true; },
      { message: "Passwords do not match", path: ["confirmPassword"] });

  const form = useForm({
    resolver: zodResolver(authSchema),
    defaultValues: { name: "", email: "", password: "", confirmPassword: "" },
  });

  useEffect(() => {
    form.reset({ name: "", email: "", password: "", confirmPassword: "" });
    setSelectedInterests([]);
  }, [isSignUp, form]);

  const toggleInterest = (interest: string) =>
    setSelectedInterests((prev) => prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]);

  const onSubmit = async (values) => {
    try {
      setIsLoading(true);
      const payload = {
        email: values.email, password: values.password, signup: isSignUp,
        ...(isSignUp && { name: values.name, interests: selectedInterests }),
      };
      const response = await api.post("/auth", payload);
      localStorage.setItem("token", response.data.token);
      api.defaults.headers.common["Authorization"] = `Bearer ${response.data.token}`;
      toast.success(isSignUp ? "Account created!" : "Welcome back!");
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.message || "Authentication failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f0f4ff] via-white to-[#e8faf5] p-4 relative">
      <FloatingIcons />

      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-blue-500/5 p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={isSignUp ? "signup" : "login"}
              variants={stagger}
              initial="hidden"
              animate="show"
              exit={{ opacity: 0, x: -20 }}
            >
              <motion.div variants={fadeUp} className="mb-7">
                <div className="flex items-center gap-3 mb-3">
                  <motion.div
                    className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center shadow-md shadow-blue-500/20"
                    whileHover={{ rotate: 10, scale: 1.05 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <GraduationCap className="h-5 w-5 text-white" />
                  </motion.div>
                  <span className="text-sm font-semibold text-gray-400 tracking-wide uppercase">SmartPathAI</span>
                </div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                  {isSignUp ? "Create your account" : "Welcome back"}
                </h1>
                <p className="text-gray-500 text-sm mt-1">
                  {isSignUp ? "Start your personalised learning journey" : "Continue where you left off"}
                </p>
              </motion.div>

              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  {isSignUp && (
                    <motion.div variants={fadeUp}>
                      <FormField control={form.control} name="name" render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-gray-600 text-sm">Full Name</FormLabel>
                          <FormControl>
                            <Input placeholder="Your name" className="h-10 border-gray-200 bg-gray-50/50 focus:bg-white focus:border-blue-400 transition-colors" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )} />
                    </motion.div>
                  )}

                  <motion.div variants={fadeUp}>
                    <FormField control={form.control} name="email" render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-gray-600 text-sm">Email</FormLabel>
                        <FormControl>
                          <Input type="email" placeholder="you@example.com" className="h-10 border-gray-200 bg-gray-50/50 focus:bg-white focus:border-blue-400 transition-colors" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )} />
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    <FormField control={form.control} name="password" render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-gray-600 text-sm">Password</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input type={showPassword ? "text" : "password"} placeholder="••••••••" className="h-10 border-gray-200 bg-gray-50/50 focus:bg-white focus:border-blue-400 transition-colors pr-10" {...field} />
                            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )} />
                  </motion.div>

                  {isSignUp && (
                    <>
                      <motion.div variants={fadeUp}>
                        <FormField control={form.control} name="confirmPassword" render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-gray-600 text-sm">Confirm Password</FormLabel>
                            <FormControl>
                              <div className="relative">
                                <Input type={showConfirmPassword ? "text" : "password"} placeholder="••••••••" className="h-10 border-gray-200 bg-gray-50/50 focus:bg-white focus:border-blue-400 transition-colors pr-10" {...field} />
                                <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                              </div>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )} />
                      </motion.div>

                      <motion.div variants={fadeUp} className="space-y-2.5 pt-1">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600 text-sm font-medium">Pick your interests</span>
                          <span className="text-gray-400 text-xs tabular-nums">{selectedInterests.length} / {INTEREST_OPTIONS.length}</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {INTEREST_OPTIONS.map((label) => {
                            const isSelected = selectedInterests.includes(label);
                            return (
                              <motion.button
                                key={label}
                                type="button"
                                onClick={() => toggleInterest(label)}
                                whileHover={{ scale: 1.04 }}
                                whileTap={{ scale: 0.96 }}
                                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 border ${
                                  isSelected
                                    ? "bg-blue-500 border-blue-500 text-white shadow-sm shadow-blue-500/20"
                                    : "bg-white border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-600"
                                }`}
                                layout
                              >
                                {label}
                              </motion.button>
                            );
                          })}
                        </div>
                      </motion.div>
                    </>
                  )}

                  <motion.div variants={fadeUp} className="pt-1">
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-10 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white rounded-xl transition-all duration-200 shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 active:scale-[0.98]"
                    >
                      {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ArrowRight className="h-4 w-4 mr-2" />}
                      {isLoading ? "Please wait…" : isSignUp ? "Create Account" : "Sign In"}
                    </Button>
                  </motion.div>
                </form>
              </Form>

              <motion.div variants={fadeUp} className="mt-6 text-center">
                <button type="button" onClick={() => setIsSignUp(!isSignUp)} className="text-sm text-gray-400 hover:text-blue-600 transition-colors">
                  {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
                </button>
              </motion.div>
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
