import axios, { AxiosResponse } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token and redirect to login
      localStorage.removeItem("token");
      window.location.href = "/auth";
    }
    return Promise.reject(error);
  }
);

// API service methods
export const apiService = {
  // Authentication
  login: (email: string, password: string) =>
    api.post("/auth", { email, password, signup: false }),

  signup: (data: {
    name: string;
    email: string;
    password: string;
    interests: string[];
  }) => api.post("/auth", { ...data, signup: true }),

  // Dashboard
  getDashboard: () => api.get("/dashboard"),

  // Performance
  getPerformance: () => api.get("/performance"),

  // Quiz
  generateQuiz: () => api.get("/generate_quiz"),
  checkAnswers: (data: {
    answers: Record<string, string>;
    correct_answers: Record<string, string>;
  }) => api.post("/check_answers", data),

  // Learning Path
  getLearningPath: () => api.get("/learning_path"),

  // Certifications
  getCertifications: () => api.get("/recommend_certifications"),
  getEarnedCertifications: () => api.get("/earned_certifications"),
  markCertificationCompleted: (title: string) =>
    api.post("/mark_certification_completed", { title }),

  // Profile
  getProfile: () => api.get("/profile"),
  updateProfile: (data: Record<string, unknown>) => api.put("/profile", data),

  // Chatbot
  sendMessage: (message: string) => api.post("/chatbot", { message }),

  // Courses
  getCourseRecommendations: () => api.get("/recommend_courses"),
};

export default api;
