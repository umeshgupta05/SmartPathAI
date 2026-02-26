import { useState, useEffect } from "react";
import { useNavigate, useLocation, NavLink } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  BookOpen,
  Route,
  BarChart3,
  BrainCircuit,
  Award,
  UserRound,
  LogOut,
  User,
  GraduationCap,
} from "lucide-react";
import { motion } from "framer-motion";

interface LayoutProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { label: "Courses", path: "/courses", icon: BookOpen },
  { label: "Path", path: "/learning-path", icon: Route },
  { label: "Performance", path: "/performance", icon: BarChart3 },
  { label: "Quizzes", path: "/quizzes", icon: BrainCircuit },
  { label: "Certs", path: "/certifications", icon: Award },
];

const Layout = ({ children }: LayoutProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem("token"));
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
    navigate("/auth");
  };

  const isHomePage = location.pathname === "/";
  const isLoginPage = location.pathname === "/auth";

  if (isHomePage || isLoginPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-[#f8f9fb]">
      {/* ─── Top nav ─── */}
      <header className="sticky top-0 z-50 border-b border-gray-200/70 bg-white/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-5 flex items-center justify-between h-14">
          {/* Logo */}
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 group"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center shadow-md shadow-blue-500/20 group-hover:shadow-lg group-hover:shadow-blue-500/30 transition-shadow">
              <GraduationCap className="h-4.5 w-4.5 text-white" />
            </div>
            <span className="font-semibold text-[15px] text-gray-900 tracking-tight hidden sm:inline">
              SmartPathAI
            </span>
          </button>

          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
              const isActive = location.pathname === path;
              return (
                <NavLink
                  key={path}
                  to={path}
                  className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-200
                    ${
                      isActive
                        ? "text-blue-600"
                        : "text-gray-500 hover:text-gray-900 hover:bg-gray-100/70"
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute inset-0 rounded-lg bg-blue-50 border border-blue-100 -z-10"
                      transition={{ type: "spring", stiffness: 350, damping: 30 }}
                    />
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Profile dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-teal-400 text-white hover:opacity-90 hover:text-white p-0"
              >
                <UserRound className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-52 rounded-xl shadow-xl border-gray-200/80" align="end" sideOffset={8}>
              <DropdownMenuLabel className="font-medium text-gray-500 text-xs uppercase tracking-wider">
                My Account
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => navigate("/profile")}
                className="cursor-pointer gap-2 text-sm rounded-lg"
              >
                <User className="h-4 w-4 text-gray-400" /> Profile
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="cursor-pointer gap-2 text-sm text-red-600 rounded-lg focus:text-red-600 focus:bg-red-50"
              >
                <LogOut className="h-4 w-4" /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Mobile nav */}
        <div className="md:hidden border-t border-gray-100 overflow-x-auto">
          <nav className="flex items-center gap-1 px-4 py-1.5">
            {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
              const isActive = location.pathname === path;
              return (
                <NavLink
                  key={path}
                  to={path}
                  className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-all
                    ${isActive ? "text-blue-600 bg-blue-50" : "text-gray-500"}
                  `}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </header>

      {/* ─── Page content ─── */}
      <main className="pt-2">{children}</main>
    </div>
  );
};

export default Layout;
