# 📚 SmartPathAI - Adaptive Learning Platform

SmartPathAI is an AI-powered adaptive learning platform designed to deliver a personalized educational experience. It dynamically adjusts courses, certifications, quizzes, and feedback based on the learner's progress, preferences, and performance — all powered by advanced machine learning, NLP, and recommendation systems.

## 📁 Project Structure

```
SmartPathAI/
├── frontend/                 # React.js frontend application
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   │   ├── ui/         # shadcn/ui components
│   │   │   ├── Layout.tsx  # Main layout component
│   │   │   └── ErrorBoundary.tsx # Error handling
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom React hooks
│   │   └── lib/            # Utility functions
│   ├── package.json        # Frontend dependencies
│   ├── vite.config.ts      # Vite configuration
│   ├── tailwind.config.ts  # Tailwind CSS config
│   └── tsconfig.json       # TypeScript config
├── backend/                 # Django backend application
│   ├── manage.py           # Django entry point
│   ├── core/               # API app (models + views + urls)
│   ├── smartpathai_backend/# Django settings + project urls
│   └── requirements.txt    # Python dependencies
├── package.json            # Root package.json for monorepo
└── README.md
```

## 🚀 Features

- ✅ **AI-Powered Course Recommendations**  
  Personalized learning paths based on user interests, quiz scores, and interaction history.

- 🤖 **Chatbot Assistance**  
  Simple rule-based chatbot responses for interview/demo usage.

- 📈 **Performance Tracking & Analytics**  
  Visualizations of skill progression, quiz performance, and course engagement using `Chart.js`.

- 🧠 **Dynamic Quiz Generation**  
  Automatically tailored quizzes with real-time evaluation and adaptive difficulty.

- 🏆 **Certification Suggestions**  
  Intelligent recommendation of global certifications based on user skills and NPTEL/YouTube content mapping.

## 🛠️ Tech Stack

| Frontend        | Backend         | Assistant Logic          | Database |
| --------------- | --------------- | ------------------------ | -------- |
| React.js + Vite | Django (Python) | Simple rule-based helper | Oracle   |

**Libraries & Tools:**

- shadcn/ui, Tailwind CSS for styling
- Framer Motion for animations
- React Query for data management
- JWT for authentication
- TypeScript for type safety

## 📦 Installation & Setup

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Python 3.8+ (for backend)

### Quick Start (Both Frontend & Backend)

1. **Clone the repository:**

```bash
git clone https://github.com/umeshgupta05/SmartPathAI.git
cd SmartPathAI
```

2. **Install root dependencies:**

```bash
npm install
```

3. **Install all dependencies:**

```bash
npm run install:all
```

4. **Start both frontend and backend:**

```bash
npm run dev
```

This will start:

- Frontend on `http://localhost:8080`
- Backend on `http://localhost:5000`

### Individual Setup

#### Frontend Setup

1. **Navigate to frontend directory:**

```bash
cd frontend
```

2. **Install dependencies:**

```bash
npm install
```

3. **Create environment file:**

```bash
cp .env.example .env
```

4. **Configure environment variables in `.env`:**

```
VITE_API_URL=https://smartpathai-1.onrender.com
VITE_APP_NAME=SmartPathAI
VITE_NODE_ENV=production
```

5. **Start the development server:**

```bash
npm run dev
```

#### Backend Setup

1. **Navigate to backend directory:**

```bash
cd backend
```

2. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

3. **Create environment file:**

```bash
cp .env.example .env
```

4. **Configure environment variables in `.env`:**

```bash
# Django Configuration
DJANGO_SECRET_KEY=your_secure_secret_key_here
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

# Oracle Configuration
DB_NAME=XE
DB_USER=smartpathai
DB_PASSWORD=your_oracle_password
DB_HOST=localhost
DB_PORT=1521

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:5173
```

5. **Run migrations:**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Run the Django application on port 5000:**

```bash
python manage.py runserver 0.0.0.0:5000
```

## 🔧 Available Scripts

### Root Level (Monorepo)

- `npm run dev` - Start both frontend and backend
- `npm run dev:frontend` - Start only frontend
- `npm run dev:backend` - Start only backend
- `npm run build` - Build frontend for production
- `npm run install:all` - Install all dependencies
- `npm run lint` - Run ESLint on frontend
- `npm run type-check` - Run TypeScript type checking

### Frontend Specific (run from `/frontend` directory)

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues automatically
- `npm run type-check` - Run TypeScript type checking
- `npm run preview` - Preview production build

## 🛠️ Recent Optimizations & Bug Fixes

### ✅ Project Structure Reorganization

- **Monorepo Structure**: Moved all frontend files to a dedicated `frontend/` folder
- **Clean Separation**: Clear separation between frontend and backend code
- **Unified Scripts**: Root-level package.json for managing both frontend and backend
- **Maintained Functionality**: All existing functionality preserved during restructuring

### ✅ Type Safety Improvements

- Added proper TypeScript interfaces for all data structures
- Fixed implicit `any` types throughout the codebase
- Enabled strict TypeScript configuration for better development experience

### ✅ Authentication & Navigation Fixes

- Fixed authentication state management in Layout component
- Implemented proper logout functionality with token cleanup
- Corrected navigation routes and improved routing consistency
- Added proper authentication state checks

### ✅ Error Handling Enhancements

- Added global ErrorBoundary component for graceful error handling
- Improved error handling in API calls with proper user feedback
- Added comprehensive loading states throughout the application
- Implemented toast notifications for better UX

### ✅ Performance Optimizations

- Created centralized API service layer with request/response interceptors
- Added React Query for efficient data caching and background updates
- Implemented proper useCallback hooks to prevent unnecessary re-renders
- Optimized build configuration with environment-based settings

### ✅ Code Quality Improvements

- Removed console.log statements in production builds
- Fixed React Hook dependency warnings
- Improved component structure and separation of concerns
- Added proper TypeScript types for all components and functions

### ✅ Security Enhancements

- Implemented automatic token cleanup on 401 errors
- Added CORS protection and secure headers
- Improved input validation and sanitization
- Added security audit npm script

### ✅ UI/UX Improvements

- Enhanced loading states with proper spinners
- Improved error messages and user feedback
- Fixed navigation components with proper React Router usage
- Added responsive design improvements

## 🚀 Deployment

### Frontend (Vercel/Netlify)

1. Build the project from frontend directory: `cd frontend && npm run build`
2. Deploy the `frontend/dist` folder to your hosting platform

### Backend (Render/Heroku)

1. Ensure all environment variables are set
2. Deploy the Flask application from the `backend/` directory

## 🔐 Security Features

- JWT-based authentication with automatic token management
- CORS protection with configurable origins
- Input validation and sanitization
- Error boundary for graceful error handling
- Secure token storage and automatic cleanup
- API request/response interceptors for security

## 🎨 UI/UX Features

- Responsive design for all devices
- Modern gradient backgrounds and glassmorphism effects
- Smooth animations and transitions with Framer Motion
- Loading states and comprehensive error handling
- Accessible components (WCAG compliant)
- Clean, modern interface with shadcn/ui components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [shadcn/ui](https://ui.shadcn.com/) for the beautiful UI components
- [Tailwind CSS](https://tailwindcss.com/) for the styling framework
- [React](https://reactjs.org/) for the frontend framework
- [Vite](https://vitejs.dev/) for the fast build tool
- [Flask](https://flask.palletsprojects.com/) for the backend framework
