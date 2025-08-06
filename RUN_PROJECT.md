# SmartPathAI - Quick Start Guide

## 🚀 Running the Project

### Prerequisites
- Python 3.8+ installed
- Node.js 18+ installed
- MongoDB Atlas connection (already configured)

### Step 1: Install Dependencies

**Backend:**
```cmd
cd backend
pip install -r requirements.txt
```

**Frontend:**
```cmd
cd frontend
npm install
```

### Step 2: Start the Servers

**Option A: Start Both Servers Separately**

**Terminal 1 - Backend:**
```cmd
cd backend
python app.py
```
Backend will run on: http://localhost:5000

**Terminal 2 - Frontend:**
```cmd
cd frontend
npm run dev
```
Frontend will run on: http://localhost:8081

**Option B: Start Both Together (if concurrently is installed)**
```cmd
# From root directory
npm install concurrently
npm run dev
```

### Step 3: Access the Application

- **Frontend:** http://localhost:8081
- **Backend API:** http://localhost:5000
- **API Health Check:** http://localhost:5000/ (should show "✅ Server is running!")

### ✅ Fixes Applied

1. **CORS Configuration:** Added support for both ports 8080 and 8081
2. **API URLs:** All frontend components now use http://localhost:5000
3. **React Router:** Added future flags to eliminate warnings
4. **Environment Variables:** Properly configured for local development

### 🔧 Troubleshooting

**CORS Error:**
- Make sure backend is running on port 5000
- Check that ALLOWED_ORIGINS includes your frontend port

**Backend Won't Start:**
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Verify environment variables in `.env` file
- Test with: `python check_setup.py`

**Frontend Won't Start:**
- Check if dependencies are installed: `npm install`
- Clear cache: `npm run build` then `npm run dev`

### 🌐 Current Configuration

- **Backend:** http://localhost:5000 (MongoDB Atlas)
- **Frontend:** http://localhost:8081 (Vite dev server)
- **CORS:** Configured for localhost:8080, 8081, 3000, 5173
- **Database:** MongoDB Atlas (cloud) - ready for production deployment

Ready to go! 🎯
