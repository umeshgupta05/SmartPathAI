import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
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
import axios from "axios";
import { motion } from "framer-motion";

// ✅ Backend API URL
const API_BASE_URL = "https://smartpathai-1.onrender.com";

// ✅ Fix schema validation issues
const authSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").optional(),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().optional(),
  interests: z.array(z.string()).optional(),
});

const Login = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const navigate = useNavigate();

  const form = useForm({
    resolver: zodResolver(authSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      interests: [],
    },
  });

  // Reset form when switching between login and signup
  useEffect(() => {
    form.reset({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      interests: [],
    });
    setSelectedInterests([]);
  }, [isSignUp, form]);

  // Handle interest selection
  const handleInterestChange = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  // ✅ Handle form submission
  const onSubmit = async (values) => {
  try {
    console.log("Submitting form:", values);

    const payload = {
      email: values.email,
      password: values.password,
      signup: isSignUp,
      name: isSignUp ? values.name : undefined,
      confirmPassword: isSignUp ? values.confirmPassword : undefined,
      interests: isSignUp ? selectedInterests : undefined,
    };

    console.log("Payload sent to API:", payload);

    const response = await axios.post(
      "https://smartpathai-1.onrender.com/auth",
      payload,
      {
        headers: { "Content-Type": "application/json" },
        withCredentials: true,  // ✅ Fix: Send credentials
      }
    );

    console.log("API Response:", response.data);

    if (!response.data.token) {
      throw new Error("Token missing from API response");
    }

    const { token, user } = response.data;
    localStorage.setItem("token", token);
    toast.success(`Welcome ${user.name || user.email}! Redirecting to dashboard...`);

    navigate("/dashboard");
  } catch (error) {
    console.error("Auth error:", error);
    toast.error(error.response?.data?.message || "❌ Authentication failed!");
  }
};


  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 to-accent/5 p-6">
      <Card className="w-full max-w-md p-8 animate-fade-up shadow-xl relative">
        <motion.div
          key={isSignUp ? "signup" : "login"}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {isSignUp ? "Create Account" : "Welcome Back"}
            </h1>
            <p className="text-gray-500 mt-2">
              {isSignUp
                ? "Sign up to start your learning journey"
                : "Sign in to continue learning"}
            </p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {isSignUp && (
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Full Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter your name" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your email" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="Enter your password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {isSignUp && (
                <>
                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Confirm Password</FormLabel>
                        <FormControl>
                          <Input type="password" placeholder="Re-enter password" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="space-y-4">
                    <h3 className="font-medium text-sm">Select Your Interests</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {["Web Development", "AI/ML", "Data Science", "Cloud Computing"].map((interest) => (
                        <div key={interest} className="flex items-center space-x-2">
                          <Checkbox
                            id={interest}
                            checked={selectedInterests.includes(interest)}
                            onCheckedChange={() => handleInterestChange(interest)}
                          />
                          <label htmlFor={interest} className="text-sm font-medium leading-none">
                            {interest}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <Button type="submit" className="w-full">
                {isSignUp ? "Sign Up" : "Sign In"}
              </Button>
            </form>
          </Form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsSignUp((prev) => !prev)}
              className="text-sm text-primary hover:underline"
            >
              {isSignUp
                ? "Already have an account? Sign in"
                : "Don't have an account? Sign up"}
            </button>
          </div>
        </motion.div>
      </Card>
    </div>
  );
};

export default Login;
