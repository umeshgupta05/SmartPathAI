#!/usr/bin/env python3
"""
Startup script to verify environment variables and dependencies
"""
import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    # Load environment variables
    load_dotenv()
    
    required_vars = [
        'JWT_SECRET_KEY',
        'MONGO_URI', 
        'GOOGLE_API_KEY',
        'IBM_API_KEY',
        'IBM_SERVICE_URL'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: Found")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all variables are set.")
        return False
    
    print("\n✅ All environment variables are set correctly!")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'flask_pymongo',
        'flask_jwt_extended',
        'google.generativeai',
        'ibm_watson',
        'ibm_cloud_sdk_core',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('.', '_'))
            print(f"✅ {package}: Installed")
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

if __name__ == "__main__":
    print("🚀 SmartPathAI Backend - Environment Check\n")
    
    env_ok = check_environment()
    deps_ok = check_dependencies()
    
    if env_ok and deps_ok:
        print("\n🎉 Backend is ready to start!")
        print("Run: python app.py")
    else:
        print("\n❌ Please fix the issues above before starting the backend.")
        sys.exit(1)
