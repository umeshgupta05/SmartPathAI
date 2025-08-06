from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import google.generativeai as genai
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, KeywordsOptions
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from datetime import timedelta, datetime
import random
import os
import json
import base64
import re
import hashlib
from io import BytesIO
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Rate limiting storage
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes in seconds

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

def check_rate_limit(ip_address):
    """Check if IP is rate limited"""
    current_time = time.time()
    # Clean old attempts
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address]
        if current_time - attempt_time < LOCKOUT_DURATION
    ]
    
    if len(login_attempts[ip_address]) >= MAX_LOGIN_ATTEMPTS:
        return False, f"Too many login attempts. Please try again in {LOCKOUT_DURATION // 60} minutes."
    return True, ""

def record_failed_attempt(ip_address):
    """Record a failed login attempt"""
    login_attempts[ip_address].append(time.time())

def sanitize_input(data):
    """Basic input sanitization"""
    if isinstance(data, str):
        # Remove potential XSS characters
        data = re.sub(r'[<>"\']', '', data.strip())
    return data

# Updated CORS configuration
from flask_cors import CORS

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://localhost:8081,http://localhost:3000,http://localhost:5173").split(",")

CORS(app, resources={
    r"/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})


@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    
    # Allow all localhost origins for development
    if origin and ('localhost' in origin or '127.0.0.1' in origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    elif origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response

@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def handle_options(path=None):
    response = app.make_default_options_response()
    headers = response.headers
    
    origin = request.headers.get('Origin')
    
    # Allow all localhost origins for development
    if origin and ('localhost' in origin or '127.0.0.1' in origin):
        headers['Access-Control-Allow-Origin'] = origin
    elif origin in ALLOWED_ORIGINS:
        headers['Access-Control-Allow-Origin'] = origin
    else:
        headers['Access-Control-Allow-Origin'] = '*'
    
    headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response
    
# JWT Configuration with enhanced security
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", os.urandom(32).hex())  # Generate random key if not provided
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24")))
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30")))
app.config["JWT_TOKEN_LOCATION"] = ["headers"]  # Only allow headers for better security
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_ERROR_MESSAGE_KEY"] = "message"

jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "Token has expired. Please login again."}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Invalid token. Please login again."}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"message": "Authorization token is required."}), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    return jsonify({"message": "Fresh token required for this action."}), 401

# MongoDB Connection
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/smartpathai")
mongo = PyMongo(app)

# Ensure collections exist
def ensure_collections():
    """Create collections and indexes for better performance and security"""
    collections = [
        "user", "courses", "certifications", "learning_activities", 
        "chat_history", "quiz_results", "user_activity", "learning_path"
    ]
    
    for collection in collections:
        if collection not in mongo.db.list_collection_names():
            mongo.db.create_collection(collection)
    
    # Create indexes for better performance and security
    try:
        # User collection indexes
        mongo.db.user.create_index("email", unique=True)
        mongo.db.user.create_index("is_active")
        mongo.db.user.create_index("created_at")
        
        # User activity collection indexes
        mongo.db.user_activity.create_index([("email", 1), ("timestamp", -1)])
        mongo.db.user_activity.create_index("timestamp", expireAfterSeconds=7776000)  # 90 days TTL
        
        # Quiz results indexes
        mongo.db.quiz_results.create_index([("email", 1), ("timestamp", -1)])
        
        # Chat history indexes
        mongo.db.chat_history.create_index([("email", 1), ("timestamp", -1)])
        
        # Learning path indexes
        mongo.db.learning_path.create_index("email")
        
        print("Database indexes created successfully")
        
    except Exception as e:
        print(f"Index creation error: {str(e)}")

ensure_collections()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

print(f"Google API Key loaded: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-5:]}")  # Debug print (partial key)

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    print("✅ Gemini AI configured successfully")
except Exception as e:
    print(f"❌ Error configuring Gemini AI: {e}")
    raise

# Configure IBM Watson NLU
IBM_API_KEY = os.getenv("IBM_API_KEY")
IBM_SERVICE_URL = os.getenv("IBM_SERVICE_URL")
IBM_VERSION = os.getenv("IBM_VERSION", "2023-06-15")

if not IBM_API_KEY or not IBM_SERVICE_URL:
    raise ValueError("IBM_API_KEY and IBM_SERVICE_URL environment variables are required")

ibm_authenticator = IAMAuthenticator(IBM_API_KEY)
nlu = NaturalLanguageUnderstandingV1(version=IBM_VERSION, authenticator=ibm_authenticator)
nlu.set_service_url(IBM_SERVICE_URL)

@app.route("/")
def home():
    return "✅ Server is running!", 200

@app.route("/auth", methods=["POST", "OPTIONS"])
def auth():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200
        
    try:
        # Get client IP for rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # Check rate limiting
        rate_limit_ok, rate_limit_msg = check_rate_limit(client_ip)
        if not rate_limit_ok:
            return jsonify({"message": rate_limit_msg}), 429
        
        data = request.get_json()
        if not data:
            record_failed_attempt(client_ip)
            return jsonify({"message": "No data provided"}), 400
            
        # Sanitize and validate input
        email = sanitize_input(data.get("email", "")).lower()
        password = sanitize_input(data.get("password", ""))
        signup = data.get("signup", False)
        name = sanitize_input(data.get("name", "")) if signup else ""

        # Basic validation
        if not email or not password:
            record_failed_attempt(client_ip)
            return jsonify({"message": "Email and password are required"}), 400

        # Email validation
        if not is_valid_email(email):
            record_failed_attempt(client_ip)
            return jsonify({"message": "Please provide a valid email address"}), 400

        if signup:
            # Signup Logic with enhanced validation
            
            # Name validation for signup
            if not name or len(name.strip()) < 2:
                record_failed_attempt(client_ip)
                return jsonify({"message": "Name must be at least 2 characters long"}), 400
            
            # Password strength validation
            is_strong, password_msg = is_strong_password(password)
            if not is_strong:
                record_failed_attempt(client_ip)
                return jsonify({"message": password_msg}), 400
            
            # Check if user already exists
            existing_user = mongo.db.user.find_one({"email": email})
            if existing_user:
                record_failed_attempt(client_ip)
                return jsonify({"message": "An account with this email already exists"}), 409

            # Hash password before storing
            hashed_password = generate_password_hash(password)
            
            # Validate and sanitize interests
            interests = data.get("interests", [])
            if isinstance(interests, list):
                interests = [sanitize_input(interest) for interest in interests if isinstance(interest, str)][:10]  # Limit to 10 interests
            else:
                interests = []

            new_user = {
                "name": name.strip(),
                "email": email,
                "password": hashed_password,
                "interests": interests,
                "preferences": {"pace": "moderate", "content_format": "video"},
                "performance": {
                    "learning_hours": 0, 
                    "average_score": 0, 
                    "skills_mastered": 0,
                    "quiz_scores": [],
                    "recent_activity": [],
                    "skill_progress": []
                },
                "completed_courses": [],
                "earned_certifications": [],
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "is_active": True
            }
            
            try:
                result = mongo.db.user.insert_one(new_user)
                if result.inserted_id:
                    access_token = create_access_token(
                        identity=email,
                        expires_delta=timedelta(hours=24)  # Extended token validity
                    )
                    
                    return jsonify({
                        "message": "Account created successfully",
                        "token": access_token,
                        "user": {
                            "name": new_user["name"],
                            "email": email,
                            "interests": new_user["interests"]
                        }
                    }), 201
                else:
                    record_failed_attempt(client_ip)
                    return jsonify({"message": "Failed to create account. Please try again."}), 500
                    
            except Exception as db_error:
                print(f"Database error during signup: {str(db_error)}")
                record_failed_attempt(client_ip)
                return jsonify({"message": "Database error. Please try again later."}), 500
                
        else:
            # Login Logic with enhanced security
            user = mongo.db.user.find_one({"email": email})
            
            if not user:
                record_failed_attempt(client_ip)
                return jsonify({"message": "Invalid email or password"}), 401
            
            # Check if account is active
            if not user.get("is_active", True):
                record_failed_attempt(client_ip)
                return jsonify({"message": "Account has been deactivated. Please contact support."}), 403
            
            # Verify password
            if not check_password_hash(user["password"], password):
                record_failed_attempt(client_ip)
                return jsonify({"message": "Invalid email or password"}), 401

            # Update last login
            mongo.db.user.update_one(
                {"email": email},
                {"$set": {"last_login": datetime.utcnow()}}
            )

            access_token = create_access_token(
                identity=email,
                expires_delta=timedelta(hours=24)  # Extended token validity
            )
            
            return jsonify({
                "message": "Login successful",
                "token": access_token,
                "user": {
                    "name": user.get("name", ""),
                    "email": email,
                    "interests": user.get("interests", [])
                }
            }), 200
            
    except Exception as e:
        print(f"Auth error: {str(e)}")
        record_failed_attempt(client_ip)
        return jsonify({"message": "An unexpected error occurred. Please try again later."}), 500

def calculate_overall_progress(user):
    """
    Calculate overall progress based on completed courses and certifications
    """
    try:
        # Get total numbers
        completed_courses = len(user.get("completed_courses", []))
        earned_certifications = len(user.get("earned_certifications", []))
        total_learning_hours = user.get("performance", {}).get("learning_hours", 0)
        quiz_scores = user.get("quiz_scores", [])
        
        # Calculate average quiz score
        avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        # Calculate weights for different factors
        course_weight = 0.4  # 40% weight to completed courses
        cert_weight = 0.3    # 30% weight to certifications
        quiz_weight = 0.3    # 30% weight to quiz performance
        
        # Get total courses and certifications from the database
        total_courses = max(mongo.db.courses.count_documents({}), 1)  # Avoid division by zero
        total_certs = max(mongo.db.certifications.count_documents({}), 1)  # Avoid division by zero
        
        # Calculate individual progress components
        course_progress = (completed_courses / total_courses) * 100
        cert_progress = (earned_certifications / total_certs) * 100
        quiz_progress = avg_quiz_score  # Already in percentage
        
        # Calculate weighted average
        overall_progress = (
            (course_progress * course_weight) +
            (cert_progress * cert_weight) +
            (quiz_progress * quiz_weight)
        )
        
        return round(min(overall_progress, 100), 1)  # Return rounded percentage, max 100%
        
    except Exception as e:
        print(f"Error calculating progress: {str(e)}")
        return 0  # Return 0 if calculation fails

# ------------- ENHANCED AUTHENTICATION ENDPOINTS -------------

@app.route("/change_password", methods=["POST"])
@jwt_required()
def change_password():
    """Allow users to change their password"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        current_password = sanitize_input(data.get("current_password", ""))
        new_password = sanitize_input(data.get("new_password", ""))
        
        if not current_password or not new_password:
            return jsonify({"message": "Both current and new passwords are required"}), 400
        
        # Get user from database
        user = mongo.db.user.find_one({"email": current_user})
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        # Verify current password
        if not check_password_hash(user["password"], current_password):
            return jsonify({"message": "Current password is incorrect"}), 401
        
        # Validate new password strength
        is_strong, password_msg = is_strong_password(new_password)
        if not is_strong:
            return jsonify({"message": password_msg}), 400
        
        # Check if new password is different from current
        if check_password_hash(user["password"], new_password):
            return jsonify({"message": "New password must be different from current password"}), 400
        
        # Hash and update password
        hashed_password = generate_password_hash(new_password)
        mongo.db.user.update_one(
            {"email": current_user},
            {
                "$set": {
                    "password": hashed_password,
                    "password_changed_at": datetime.utcnow()
                }
            }
        )
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        print(f"Change password error: {str(e)}")
        return jsonify({"message": "An error occurred while changing password"}), 500

@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    """Initiate password reset process"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        email = sanitize_input(data.get("email", "")).lower()
        
        if not email or not is_valid_email(email):
            return jsonify({"message": "Please provide a valid email address"}), 400
        
        user = mongo.db.user.find_one({"email": email})
        
        # Always return success to prevent email enumeration
        # In production, you would send an actual email here
        if user:
            # Generate reset token (in production, use a proper token system)
            reset_token = hashlib.sha256(f"{email}{datetime.utcnow()}".encode()).hexdigest()[:32]
            
            # Store reset token with expiration (1 hour)
            mongo.db.user.update_one(
                {"email": email},
                {
                    "$set": {
                        "reset_token": reset_token,
                        "reset_token_expires": datetime.utcnow() + timedelta(hours=1)
                    }
                }
            )
            
            print(f"Password reset token for {email}: {reset_token}")  # In production, send via email
        
        return jsonify({"message": "If an account with this email exists, a password reset link has been sent"}), 200
        
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({"message": "An error occurred. Please try again later."}), 500

@app.route("/reset_password", methods=["POST"])
def reset_password():
    """Reset password using token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        email = sanitize_input(data.get("email", "")).lower()
        token = sanitize_input(data.get("token", ""))
        new_password = sanitize_input(data.get("new_password", ""))
        
        if not email or not token or not new_password:
            return jsonify({"message": "Email, token, and new password are required"}), 400
        
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400
        
        # Validate new password strength
        is_strong, password_msg = is_strong_password(new_password)
        if not is_strong:
            return jsonify({"message": password_msg}), 400
        
        # Find user with valid reset token
        user = mongo.db.user.find_one({
            "email": email,
            "reset_token": token,
            "reset_token_expires": {"$gt": datetime.utcnow()}
        })
        
        if not user:
            return jsonify({"message": "Invalid or expired reset token"}), 400
        
        # Hash new password and update user
        hashed_password = generate_password_hash(new_password)
        mongo.db.user.update_one(
            {"email": email},
            {
                "$set": {
                    "password": hashed_password,
                    "password_changed_at": datetime.utcnow()
                },
                "$unset": {
                    "reset_token": "",
                    "reset_token_expires": ""
                }
            }
        )
        
        return jsonify({"message": "Password reset successfully"}), 200
        
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        return jsonify({"message": "An error occurred while resetting password"}), 500

@app.route("/verify_token", methods=["GET"])
@jwt_required()
def verify_token():
    """Verify if the current token is valid"""
    try:
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user}, {"_id": 0, "password": 0})
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        if not user.get("is_active", True):
            return jsonify({"message": "Account is deactivated"}), 403
        
        return jsonify({
            "message": "Token is valid",
            "user": {
                "name": user.get("name", ""),
                "email": current_user,
                "interests": user.get("interests", [])
            }
        }), 200
        
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return jsonify({"message": "Token verification failed"}), 401

@app.route("/dashboard", methods=["GET", "OPTIONS"])
@jwt_required()
def get_dashboard():
    try:
        # Handle preflight requests
        if request.method == "OPTIONS":
            return jsonify({"message": "OK"}), 200

        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})
        
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Get user's dashboard data
        dashboard_data = {
            "currentCourse": user.get("current_course", "No active course"),
            "completedCourses": len(user.get("completed_courses", [])),
            "certifications": len(user.get("earned_certifications", [])),
            "overallProgress": calculate_overall_progress(user),  # You'll need to implement this
            "recommendedCourses": []  # You can populate this based on user interests
        }

        return jsonify(dashboard_data), 200

    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
    
# ------------- PROFILE MANAGEMENT -------------

@app.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify(user), 200

@app.route("/update_profile", methods=["POST"])
@jwt_required()
def update_profile():
    """Enhanced profile update with validation"""
    try:
        current_user = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        # Sanitize and validate inputs
        update_data = {}
        
        # Name validation
        if "name" in data:
            name = sanitize_input(data["name"])
            if len(name.strip()) < 2:
                return jsonify({"message": "Name must be at least 2 characters long"}), 400
            update_data["name"] = name.strip()
        
        # Interests validation
        if "interests" in data:
            interests = data["interests"]
            if isinstance(interests, list):
                # Limit to 10 interests, sanitize each
                interests = [sanitize_input(interest) for interest in interests if isinstance(interest, str)][:10]
                update_data["interests"] = interests
        
        # Preferences validation
        if "preferences" in data:
            preferences = data["preferences"]
            if isinstance(preferences, dict):
                valid_preferences = {}
                
                # Validate pace
                if "pace" in preferences and preferences["pace"] in ["slow", "moderate", "fast"]:
                    valid_preferences["pace"] = preferences["pace"]
                
                # Validate content format
                if "content_format" in preferences and preferences["content_format"] in ["video", "text", "interactive", "mixed"]:
                    valid_preferences["content_format"] = preferences["content_format"]
                
                if valid_preferences:
                    update_data["preferences"] = valid_preferences
        
        if not update_data:
            return jsonify({"message": "No valid data to update"}), 400
        
        # Add update timestamp
        update_data["profile_updated_at"] = datetime.utcnow()
        
        # Update user profile
        result = mongo.db.user.update_one(
            {"email": current_user},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"message": "User not found"}), 404
        
        # Log activity
        mongo.db.user_activity.insert_one({
            "email": current_user,
            "action": "profile_updated",
            "details": list(update_data.keys()),
            "timestamp": datetime.utcnow(),
            "ip_address": request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        })
        
        return jsonify({"message": "Profile updated successfully"}), 200
        
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({"message": "An error occurred while updating profile"}), 500

@app.route("/user_activity", methods=["GET"])
@jwt_required()
def get_user_activity():
    """Get user activity log"""
    try:
        current_user = get_jwt_identity()
        limit = min(int(request.args.get("limit", 50)), 100)  # Max 100 records
        
        activities = list(mongo.db.user_activity.find(
            {"email": current_user},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit))
        
        return jsonify(activities), 200
        
    except Exception as e:
        print(f"User activity error: {str(e)}")
        return jsonify({"message": "Failed to fetch user activity"}), 500

@app.route("/deactivate_account", methods=["POST"])
@jwt_required()
def deactivate_account():
    """Allow users to deactivate their account"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        password = sanitize_input(data.get("password", ""))
        reason = sanitize_input(data.get("reason", ""))
        
        if not password:
            return jsonify({"message": "Password confirmation is required"}), 400
        
        # Verify password
        user = mongo.db.user.find_one({"email": current_user})
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        if not check_password_hash(user["password"], password):
            return jsonify({"message": "Incorrect password"}), 401
        
        # Deactivate account
        mongo.db.user.update_one(
            {"email": current_user},
            {
                "$set": {
                    "is_active": False,
                    "deactivated_at": datetime.utcnow(),
                    "deactivation_reason": reason
                }
            }
        )
        
        # Log activity
        mongo.db.user_activity.insert_one({
            "email": current_user,
            "action": "account_deactivated",
            "details": {"reason": reason},
            "timestamp": datetime.utcnow(),
            "ip_address": request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        })
        
        return jsonify({"message": "Account deactivated successfully"}), 200
        
    except Exception as e:
        print(f"Account deactivation error: {str(e)}")
        return jsonify({"message": "An error occurred while deactivating account"}), 500

# ------------- PERFORMANCE TRACKING -------------

@app.route("/performance", methods=["GET"])
@jwt_required()
def get_performance():
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user})
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Ensure performance data has the correct structure
    performance_data = user.get("performance", {})
    default_data = {
        "learning_hours": 0,
        "average_score": 0,
        "skills_mastered": 0,
        "recent_activity": [],
        "skill_progress": []
    }
    
    # Merge with default data to ensure all fields exist
    performance_data = {**default_data, **performance_data}
    
    return jsonify(performance_data), 200

# ------------- COURSE RECOMMENDATIONS -------------

@app.route("/recommend_courses", methods=["GET"])
@jwt_required()
def recommend_courses():
    """Dynamically recommends courses using Gemini AI and updates MongoDB."""
    try:
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})

        if not user:
            return jsonify({"message": "User not found"}), 404

        user_interests = user.get("interests", ["AI", "Machine Learning"])

        # Updated prompt for Gemini AI (strict JSON format)
        prompt = f"""
        The user is interested in: {', '.join(user_interests)}.
        Recommend 5 professional online courses in this format only:
        [
          {{
            "Title": "Course Name",
            "Short Intro": "Brief description (max 50 words)",
            "Category": "Category name",
            "Skills": "Comma-separated skills learned",
            "Duration": "Duration (e.g., 6 weeks, 40 hours)",
            "Site": "Platform name (e.g., Coursera, Udemy)",
            "Rating": "4.5/5 or similar",
            "URL": "https://example.com/course"
          }},
          ...
        ]
        Return only a valid JSON array with no additional explanations or metadata.
        """

        print(f"🎓 Generating courses for user interests: {user_interests}")
        
        try:
            response = gemini_model.generate_content(prompt)
            print("✅ Gemini AI response received for courses")
        except Exception as api_error:
            print(f"❌ Gemini AI API Error for courses: {api_error}")
            # Return fallback courses immediately on API error
            fallback_courses = [
                {
                    "Title": "Introduction to Machine Learning",
                    "Short Intro": "Learn the fundamentals of machine learning with hands-on projects",
                    "Category": "Machine Learning",
                    "Skills": "Python, scikit-learn, data analysis, model training",
                    "Duration": "6 weeks",
                    "Site": "Coursera",
                    "Rating": "4.8/5",
                    "URL": "https://www.coursera.org/learn/machine-learning"
                },
                {
                    "Title": "Deep Learning Specialization",
                    "Short Intro": "Master deep learning and neural networks with TensorFlow",
                    "Category": "AI",
                    "Skills": "TensorFlow, neural networks, deep learning, Python",
                    "Duration": "4 months",
                    "Site": "Coursera",
                    "Rating": "4.9/5",
                    "URL": "https://www.coursera.org/specializations/deep-learning"
                },
                {
                    "Title": "Python for Data Science",
                    "Short Intro": "Learn Python programming for data analysis and visualization",
                    "Category": "Data Science",
                    "Skills": "Python, pandas, numpy, matplotlib, data analysis",
                    "Duration": "8 weeks",
                    "Site": "Udemy",
                    "Rating": "4.6/5",
                    "URL": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/"
                }
            ]
            return jsonify(fallback_courses), 200
        
        if not response or not response.text:
            print("❌ Empty response from Gemini AI for courses")
            # Return fallback courses
            fallback_courses = [
                {
                    "Title": "AI Fundamentals",
                    "Short Intro": "Introduction to artificial intelligence concepts and applications",
                    "Category": "AI",
                    "Skills": "AI basics, machine learning, problem solving",
                    "Duration": "4 weeks",
                    "Site": "edX",
                    "Rating": "4.5/5",
                    "URL": "https://www.edx.org/course/artificial-intelligence"
                }
            ]
            return jsonify(fallback_courses), 200

        try:
            # Clean the response text
            clean_text = response.text.strip()
            print(f"📥 Raw Gemini response for courses (first 300 chars): {clean_text[:300]}...")
            
            # Remove markdown code blocks if present
            if clean_text.startswith('```json'):
                clean_text = clean_text.replace('```json', '').replace('```', '').strip()
                print("🧹 Removed JSON markdown blocks from courses")
            elif clean_text.startswith('```'):
                clean_text = clean_text.replace('```', '').strip()
                print("🧹 Removed generic markdown blocks from courses")
            
            print(f"🧹 Cleaned course text (first 200 chars): {clean_text[:200]}...")
            
            # Parse JSON response directly
            courses = json.loads(clean_text)
            print(f"✅ Successfully parsed course JSON: {len(courses)} courses")
            
            # Validate the response structure
            if not isinstance(courses, list):
                print(f"❌ Course response is not a list, type: {type(courses)}")
                raise ValueError("Response is not a list")
            
            # Validate each course object
            required_fields = ["Title", "Short Intro", "Category", "Skills", "Duration", "Site", "Rating", "URL"]
            validated_courses = []
            
            for i, course in enumerate(courses):
                if not isinstance(course, dict):
                    print(f"❌ Invalid course format at index {i}: not a dict")
                    continue
                    
                # Check if all required fields are present
                missing_fields = [field for field in required_fields if field not in course]
                if missing_fields:
                    print(f"❌ Course at index {i} missing fields: {missing_fields}")
                    continue
                
                # Check for duplicates before adding to MongoDB
                existing_course = mongo.db.courses.find_one({"Title": course["Title"]})
                if not existing_course:
                    try:
                        mongo.db.courses.insert_one(course.copy())
                        print(f"💾 Saved new course to MongoDB: {course['Title']}")
                    except Exception as db_error:
                        print(f"❌ Failed to save course to MongoDB: {db_error}")
                else:
                    print(f"🔄 Course already exists in MongoDB: {course['Title']}")
                    
                validated_courses.append(course)
            
            print(f"✅ All {len(validated_courses)} courses validated successfully")
            return jsonify(validated_courses), 200
            
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON parsing error for courses: {json_error}")
            print(f"📝 Raw course response text: {response.text}")
            print("🔄 Returning fallback courses due to JSON parse error")
            
            # Return a fallback response
            fallback_courses = [
                {
                    "Title": "Machine Learning Basics",
                    "Short Intro": "Comprehensive introduction to machine learning algorithms and applications",
                    "Category": "Machine Learning",
                    "Skills": "Python, algorithms, data analysis, model evaluation",
                    "Duration": "8 weeks",
                    "Site": "Coursera",
                    "Rating": "4.7/5",
                    "URL": "https://www.coursera.org/learn/machine-learning"
                },
                {
                    "Title": "Data Science with Python",
                    "Short Intro": "Learn data science using Python, pandas, and machine learning",
                    "Category": "Data Science",
                    "Skills": "Python, pandas, matplotlib, scikit-learn, statistics",
                    "Duration": "10 weeks",
                    "Site": "Udemy",
                    "Rating": "4.6/5",
                    "URL": "https://www.udemy.com/course/python-for-data-science"
                }
            ]
            return jsonify(fallback_courses), 200
            
        except ValueError as val_error:
            print(f"❌ Validation error for courses: {val_error}")
            print(f"📝 Raw course response text: {response.text}")
            print("🔄 Returning fallback courses due to validation error")
            
            # Return fallback response
            fallback_courses = [
                {
                    "Title": "AI and Machine Learning Fundamentals",
                    "Short Intro": "Essential concepts in artificial intelligence and machine learning",
                    "Category": "AI",
                    "Skills": "AI concepts, algorithms, problem solving, Python basics",
                    "Duration": "6 weeks",
                    "Site": "edX",
                    "Rating": "4.5/5",
                    "URL": "https://www.edx.org/course/introduction-to-artificial-intelligence"
                }
            ]
            return jsonify(fallback_courses), 200

    except Exception as e:
        print(f"❌ Error generating courses: {e}")
        return jsonify({"error": "Failed to generate courses"}), 500


@app.route("/learning_path", methods=["GET"])
@jwt_required()
def get_learning_path():
    """Generates a dynamic learning path based on user interests and progress."""
    try:
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})
        
        if not user:
            return jsonify({"message": "User not found"}), 404
            
        user_interests = user.get("interests", ["AI", "Machine Learning"])
        completed_courses = user.get("completed_courses", [])
        
        print(f"📚 Generating learning path for user: {current_user}")
        print(f"👤 User interests: {user_interests}")
        print(f"✅ Completed courses: {completed_courses}")
        
        # Ensure "learning_path" collection exists
        if "learning_path" not in mongo.db.list_collection_names():
            mongo.db.create_collection("learning_path")
            print("📁 Created learning_path collection")
        
        # Check existing learning path in DB
        existing_path = list(mongo.db.learning_path.find({"email": current_user}, {"_id": 0, "email": 0}))
        if existing_path:
            print(f"📋 Found existing learning path with {len(existing_path)} items")
            return jsonify(existing_path), 200  # Return stored learning path if available
        
        # Generate dynamically using AI with JSON format
        prompt = f"""
        Create a personalized learning path for a student interested in: {', '.join(user_interests)}.
        The student has completed: {', '.join(completed_courses) if completed_courses else 'no courses yet'}.
        
        Generate 6-8 learning steps in this exact JSON format:
        [
          {{
            "title": "Step title",
            "description": "Detailed description of what this step covers (max 60 words)",
            "status": "Not Started",
            "url": "https://example.com/resource",
            "duration": "2-3 weeks",
            "difficulty": "Beginner/Intermediate/Advanced",
            "prerequisites": "Any prerequisites or 'None'"
          }},
          ...
        ]
        
        Make the path progressive (beginner to advanced) and relevant to {', '.join(user_interests)}.
        Return only a valid JSON array with no additional explanations or metadata.
        """

        print("🤖 Requesting learning path from Gemini AI...")
        
        try:
            response = gemini_model.generate_content(prompt)
            print("✅ Gemini AI response received for learning path")
        except Exception as api_error:
            print(f"❌ Gemini AI API Error for learning path: {api_error}")
            # Return fallback learning path immediately on API error
            fallback_path = [
                {
                    "title": "Programming Fundamentals",
                    "description": "Learn the basics of programming with Python, including variables, functions, and control structures",
                    "status": "Not Started",
                    "url": "https://www.codecademy.com/learn/learn-python-3",
                    "duration": "3-4 weeks",
                    "difficulty": "Beginner",
                    "prerequisites": "None"
                },
                {
                    "title": "Data Structures and Algorithms",
                    "description": "Master essential data structures and algorithms for efficient problem solving",
                    "status": "Not Started", 
                    "url": "https://www.coursera.org/learn/algorithms-part1",
                    "duration": "6-8 weeks",
                    "difficulty": "Intermediate",
                    "prerequisites": "Programming Fundamentals"
                },
                {
                    "title": "Machine Learning Basics",
                    "description": "Introduction to machine learning concepts, supervised and unsupervised learning",
                    "status": "Not Started",
                    "url": "https://www.coursera.org/learn/machine-learning",
                    "duration": "4-6 weeks", 
                    "difficulty": "Intermediate",
                    "prerequisites": "Programming Fundamentals, Basic Statistics"
                },
                {
                    "title": "Deep Learning Fundamentals", 
                    "description": "Learn neural networks, deep learning frameworks, and build your first AI models",
                    "status": "Not Started",
                    "url": "https://www.deeplearning.ai/courses/deep-learning-specialization/",
                    "duration": "8-10 weeks",
                    "difficulty": "Advanced", 
                    "prerequisites": "Machine Learning Basics"
                }
            ]
            
            # Save fallback path to database
            for step in fallback_path:
                mongo.db.learning_path.insert_one({"email": current_user, **step})
            
            print(f"💾 Saved {len(fallback_path)} fallback learning steps to database")
            return jsonify(fallback_path), 200
        
        if not response or not response.text:
            print("❌ Empty response from Gemini AI for learning path")
            # Return basic fallback path
            fallback_path = [
                {
                    "title": "Getting Started with AI",
                    "description": "Introduction to artificial intelligence concepts and applications in modern technology",
                    "status": "Not Started",
                    "url": "https://www.edx.org/course/artificial-intelligence",
                    "duration": "4 weeks",
                    "difficulty": "Beginner", 
                    "prerequisites": "None"
                },
                {
                    "title": "Python for AI Development",
                    "description": "Learn Python programming specifically for AI and machine learning applications",
                    "status": "Not Started",
                    "url": "https://www.python.org/about/gettingstarted/",
                    "duration": "3 weeks",
                    "difficulty": "Beginner",
                    "prerequisites": "None"
                }
            ]
            
            # Save to database
            for step in fallback_path:
                mongo.db.learning_path.insert_one({"email": current_user, **step})
            
            return jsonify(fallback_path), 200

        try:
            # Clean the response text
            clean_text = response.text.strip()
            print(f"📥 Raw Gemini response for learning path (first 300 chars): {clean_text[:300]}...")
            
            # Remove markdown code blocks if present
            if clean_text.startswith('```json'):
                clean_text = clean_text.replace('```json', '').replace('```', '').strip()
                print("🧹 Removed JSON markdown blocks from learning path")
            elif clean_text.startswith('```'):
                clean_text = clean_text.replace('```', '').strip()
                print("🧹 Removed generic markdown blocks from learning path")
            
            print(f"🧹 Cleaned learning path text (first 200 chars): {clean_text[:200]}...")
            
            # Parse JSON response directly
            learning_path = json.loads(clean_text)
            print(f"✅ Successfully parsed learning path JSON: {len(learning_path)} steps")
            
            # Validate the response structure
            if not isinstance(learning_path, list):
                print(f"❌ Learning path response is not a list, type: {type(learning_path)}")
                raise ValueError("Response is not a list")
            
            # Validate each learning step and mark completed courses
            required_fields = ["title", "description", "status", "url"]
            validated_steps = []
            
            for i, step in enumerate(learning_path):
                if not isinstance(step, dict):
                    print(f"❌ Invalid learning step format at index {i}: not a dict")
                    continue
                    
                # Check if all required fields are present
                missing_fields = [field for field in required_fields if field not in step]
                if missing_fields:
                    print(f"❌ Learning step at index {i} missing fields: {missing_fields}")
                    continue
                
                # Update status based on completed courses
                if step["title"] in completed_courses:
                    step["status"] = "Completed"
                    print(f"✅ Marked step as completed: {step['title']}")
                
                # Add default values for optional fields
                if "duration" not in step:
                    step["duration"] = "2-4 weeks"
                if "difficulty" not in step:
                    step["difficulty"] = "Intermediate"
                if "prerequisites" not in step:
                    step["prerequisites"] = "None"
                
                # Save to MongoDB
                try:
                    mongo.db.learning_path.insert_one({"email": current_user, **step})
                    print(f"💾 Saved learning step to MongoDB: {step['title']}")
                except Exception as db_error:
                    print(f"❌ Failed to save learning step to MongoDB: {db_error}")
                    
                validated_steps.append(step)
            
            print(f"✅ All {len(validated_steps)} learning steps validated and saved successfully")
            return jsonify(validated_steps), 200
            
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON parsing error for learning path: {json_error}")
            print(f"📝 Raw learning path response text: {response.text}")
            print("🔄 Returning fallback learning path due to JSON parse error")
            
            # Return a fallback response
            fallback_path = [
                {
                    "title": "AI Fundamentals",
                    "description": "Learn the core concepts of artificial intelligence and its real-world applications",
                    "status": "Not Started",
                    "url": "https://www.coursera.org/learn/ai-for-everyone",
                    "duration": "4 weeks",
                    "difficulty": "Beginner",
                    "prerequisites": "None"
                },
                {
                    "title": "Machine Learning Introduction", 
                    "description": "Understand machine learning algorithms and how to apply them to solve problems",
                    "status": "Not Started",
                    "url": "https://www.coursera.org/learn/machine-learning",
                    "duration": "6 weeks",
                    "difficulty": "Intermediate", 
                    "prerequisites": "AI Fundamentals"
                },
                {
                    "title": "Python Programming for AI",
                    "description": "Master Python programming skills essential for AI and machine learning development",
                    "status": "Not Started",
                    "url": "https://www.python.org/about/gettingstarted/",
                    "duration": "5 weeks",
                    "difficulty": "Intermediate",
                    "prerequisites": "Basic Programming Knowledge"
                }
            ]
            
            # Save to database
            for step in fallback_path:
                mongo.db.learning_path.insert_one({"email": current_user, **step})
            
            return jsonify(fallback_path), 200
            
        except ValueError as val_error:
            print(f"❌ Validation error for learning path: {val_error}")
            print(f"📝 Raw learning path response text: {response.text}")
            print("🔄 Returning fallback learning path due to validation error")
            
            # Return fallback response
            fallback_path = [
                {
                    "title": "Start Your AI Journey",
                    "description": "Begin with essential AI concepts and prepare for advanced learning in artificial intelligence",
                    "status": "Not Started",
                    "url": "https://www.edx.org/course/introduction-to-artificial-intelligence",
                    "duration": "3 weeks",
                    "difficulty": "Beginner",
                    "prerequisites": "None"
                }
            ]
            
            # Save to database
            for step in fallback_path:
                mongo.db.learning_path.insert_one({"email": current_user, **step})
            
            return jsonify(fallback_path), 200

    except Exception as e:
        print(f"❌ Error generating learning path: {e}")
        return jsonify({"error": "Failed to generate learning path"}), 500

    
@app.route("/user_progress", methods=["GET"])
@jwt_required()
def get_user_progress():
    """Fetches user course progress, ensuring the collection exists."""
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user}, {"_id": 0, "completed_courses": 1})

    # If the user has no progress, return an empty list
    if not user or "completed_courses" not in user:
        return jsonify({"completed_courses": []}), 200

    return jsonify({"completed_courses": user["completed_courses"]}), 200


def generate_course_image(course_title, course_intro):
    """Generate an AI-based image for the course using Gemini AI."""
    existing_course = mongo.db.courses.find_one({"Title": course_title}, {"image": 1})

    if existing_course and "image" in existing_course:
        return existing_course["image"]  # Return stored image if available

    # Generate image using Gemini AI
    prompt = f"A high-quality professional digital course thumbnail for '{course_title}', with a theme focusing on {course_intro}."
    try:
        image = gemini_model.generate_content(prompt)

        # Convert image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Store the image in MongoDB
        mongo.db.courses.update_one({"Title": course_title}, {"$set": {"image": img_str}}, upsert=True)

        return img_str

    except Exception as e:
        print(f"Error generating course image: {str(e)}")
        return None  # Return None if image generation fails
    
@app.route("/mark_completed", methods=["POST"])
@jwt_required()
def mark_course_completed():
    """Marks a course as completed by the user."""
    current_user = get_jwt_identity()
    data = request.get_json()
    course_title = data.get("courseTitle")

    if not course_title:
        return jsonify({"message": "Course title missing"}), 400

    user = mongo.db.user.find_one({"email": current_user})
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Update completed courses
    mongo.db.user.update_one(
        {"email": current_user},
        {"$addToSet": {"completed_courses": course_title}}  # Prevents duplicates
    )

    return jsonify({"message": f"Course '{course_title}' marked as completed"}), 200

@app.route("/optimize_path", methods=["POST"])
@jwt_required()
def optimize_path():
    current_user = get_jwt_identity()
    current_path = request.json.get("current_path", [])
    
    try:
        # Generate optimization prompt
        prompt = f"Optimize this learning path considering prerequisites and learning efficiency: {current_path}"
        response = gemini_model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError("Failed to optimize learning path")
            
        # Parse and update the learning path
        optimized_path = []
        for line in response.text.strip().split("\n"):
            parts = line.split(", ")
            if len(parts) < 4:
                continue
            
            course_data = {
                "title": parts[0],
                "description": parts[1],
                "status": parts[2],
                "url": parts[3]
            }
            optimized_path.append(course_data)
            
        # Update in MongoDB
        mongo.db.learning_path.delete_many({"email": current_user})
        for course in optimized_path:
            mongo.db.learning_path.insert_one({"email": current_user, **course})
            
        return jsonify(optimized_path), 200
        
    except Exception as e:
        print(f"Error optimizing learning path: {str(e)}")
        return jsonify({"message": "Failed to optimize learning path"}), 500



# ------------- **RECOMMEND CERTIFICATIONS BASED ON INTERESTS** -------------

@app.route("/recommend_certifications", methods=["GET"])
@jwt_required()
def recommend_certifications():
    """Dynamically recommends global certifications using Gemini AI without caching."""
    try:
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})

        if not user:
            return jsonify({"message": "User not found"}), 404

        user_interests = user.get("interests", ["AI", "Machine Learning"])

        # Updated prompt for Gemini AI (strict JSON format, no metadata)
        prompt = f"""
        The user has completed topics: {', '.join(user_interests)}.
        Recommend 5 reputed certifications in this format only:
        [
          {{
            "name": "Certification Name",
            "link": "https://example.com",
            "description": "Short description (max 30 words)",
            "difficulty": "Beginner/Intermediate/Advanced"
          }},
          ...
        ]
        Return only a valid JSON array with no additional explanations or metadata.
        """

        print(f"🤖 Generating certifications for user interests: {user_interests}")
        
        try:
            response = gemini_model.generate_content(prompt)
            print("✅ Gemini AI response received")
        except Exception as api_error:
            print(f"❌ Gemini AI API Error: {api_error}")
            # Return fallback certifications immediately on API error
            fallback_certifications = [
                {
                    "name": "Google Cloud AI Certification",
                    "link": "https://cloud.google.com/certification",
                    "description": "Professional certification in Google Cloud AI and machine learning technologies",
                    "difficulty": "Intermediate"
                },
                {
                    "name": "AWS Machine Learning Specialty",
                    "link": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
                    "description": "Amazon Web Services certification for machine learning engineers and data scientists",
                    "difficulty": "Advanced"
                },
                {
                    "name": "Microsoft Azure AI Engineer",
                    "link": "https://docs.microsoft.com/en-us/learn/certifications/azure-ai-engineer/",
                    "description": "Microsoft certification for implementing AI solutions using Azure cognitive services",
                    "difficulty": "Intermediate"
                },
                {
                    "name": "TensorFlow Developer Certificate",
                    "link": "https://www.tensorflow.org/certificate",
                    "description": "Google's official certification for TensorFlow machine learning framework proficiency",
                    "difficulty": "Beginner"
                },
                {
                    "name": "IBM Data Science Professional",
                    "link": "https://www.ibm.com/training/certification",
                    "description": "IBM certification covering data science, machine learning, and analytics tools",
                    "difficulty": "Intermediate"
                }
            ]
            return jsonify(fallback_certifications), 200
        
        if not response or not response.text:
            print("❌ Empty response from Gemini AI")
            # Return fallback certifications
            fallback_certifications = [
                {
                    "name": "Google Cloud AI Certification",
                    "link": "https://cloud.google.com/certification",
                    "description": "Professional certification in Google Cloud AI and machine learning",
                    "difficulty": "Intermediate"
                },
                {
                    "name": "AWS Machine Learning Specialty",
                    "link": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
                    "description": "AWS certification for machine learning engineers and data scientists",
                    "difficulty": "Advanced"
                }
            ]
            return jsonify(fallback_certifications), 200

        try:
            # Clean the response text
            clean_text = response.text.strip()
            print(f"📥 Raw Gemini response (first 300 chars): {clean_text[:300]}...")
            
            # Remove markdown code blocks if present
            if clean_text.startswith('```json'):
                clean_text = clean_text.replace('```json', '').replace('```', '').strip()
                print("🧹 Removed JSON markdown blocks")
            elif clean_text.startswith('```'):
                clean_text = clean_text.replace('```', '').strip()
                print("🧹 Removed generic markdown blocks")
            
            print(f"🧹 Cleaned text (first 200 chars): {clean_text[:200]}...")
            
            # Parse JSON response directly
            certifications = json.loads(clean_text)
            print(f"✅ Successfully parsed JSON: {len(certifications)} certifications")
            
            # Validate the response structure
            if not isinstance(certifications, list):
                print(f"❌ Response is not a list, type: {type(certifications)}")
                raise ValueError("Response is not a list")
            
            # Validate each certification object
            for i, cert in enumerate(certifications):
                if not isinstance(cert, dict) or not all(key in cert for key in ["name", "link", "description", "difficulty"]):
                    print(f"❌ Invalid certification format at index {i}: {cert}")
                    raise ValueError("Invalid certification format")
            
            print(f"✅ All {len(certifications)} certifications validated successfully")
            return jsonify(certifications), 200
            
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON parsing error: {json_error}")
            print(f"📝 Raw response text: {response.text}")
            print("🔄 Returning fallback certifications due to JSON parse error")
            
            # Return a fallback response
            fallback_certifications = [
                {
                    "name": "Google AI Certification",
                    "link": "https://cloud.google.com/certification",
                    "description": "Professional certification in Google Cloud AI and machine learning",
                    "difficulty": "Intermediate"
                },
                {
                    "name": "AWS Machine Learning Specialty",
                    "link": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
                    "description": "AWS certification for machine learning engineers and data scientists",
                    "difficulty": "Advanced"
                },
                {
                    "name": "Microsoft Azure AI Engineer",
                    "link": "https://docs.microsoft.com/en-us/learn/certifications/azure-ai-engineer/",
                    "description": "Certification for implementing AI solutions using Azure services",
                    "difficulty": "Intermediate"
                }
            ]
            return jsonify(fallback_certifications), 200
            
        except ValueError as val_error:
            print(f"❌ Validation error: {val_error}")
            print(f"📝 Raw response text: {response.text}")
            print("🔄 Returning fallback certifications due to validation error")
            
            # Return fallback response
            fallback_certifications = [
                {
                    "name": "Google AI Certification",
                    "link": "https://cloud.google.com/certification",
                    "description": "Professional certification in Google Cloud AI and machine learning",
                    "difficulty": "Intermediate"
                },
                {
                    "name": "AWS Machine Learning Specialty",
                    "link": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
                    "description": "AWS certification for machine learning engineers and data scientists",
                    "difficulty": "Advanced"
                }
            ]
            return jsonify(fallback_certifications), 200

    except Exception as e:
        print("Error generating certifications:", e)
        return jsonify({"message": "Failed to generate certifications."}), 500


@app.route("/earned_certifications", methods=["GET"])
@jwt_required()
def get_earned_certifications():
    """Fetches certifications the user has completed."""
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user})

    if not user:
        return jsonify({"message": "User not found"}), 404

    earned_certs = user.get("earned_certifications", [])

    return jsonify(earned_certs), 200

@app.route("/mark_certification_completed", methods=["POST"])
@jwt_required()
def mark_certification_completed():
    """Marks a certification as completed for the user."""
    try:
        current_user = get_jwt_identity()
        data = request.json
        cert_title = data.get("title")

        if not cert_title:
            return jsonify({"message": "Certification title is required"}), 400

        user = mongo.db.user.find_one({"email": current_user})
        if not user:
            return jsonify({"message": "User not found"}), 404

        # 🔹 Avoid duplicate entries
        if cert_title in user.get("earned_certifications", []):
            return jsonify({"message": "Certification already marked as completed"}), 200

        mongo.db.user.update_one(
            {"email": current_user},
            {"$push": {"earned_certifications": cert_title}}
        )

        return jsonify({"message": f"{cert_title} marked as completed"}), 200

    except Exception as e:
        print(f"Error in mark_certification_completed: {str(e)}")
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500


import json

@app.route("/generate_quiz", methods=["GET"])
@jwt_required()
def generate_quiz():
    try:
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})

        if not user:
            return jsonify({"message": "User not found"}), 404

        # Pick a topic based on user interests
        topic = random.choice(user.get("interests", ["General Knowledge"]))

        # Generate quiz using Gemini AI
        prompt = f"""Create a multiple-choice quiz on {topic} with 5 questions.
        Follow this exact format for each question:
        - Clear, concise question
        - 4 distinct answer choices
        - One correct answer
        
        Return the quiz in this exact format:
        {{
            "topic": "{topic}",
            "questions": [
                {{
                    "question": "Question text here?",
                    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "correct_answer": "Option X"
                }}
            ]
        }}"""

        response = gemini_model.generate_content(prompt)
        
        if not response.text:
            return jsonify({
                "topic": topic,
                "questions": []
            }), 200

        # Parse the response and ensure it's valid JSON
        try:
            # Remove any markdown code block syntax if present
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            quiz_data = json.loads(clean_text)
            
            # Validate quiz structure
            if not isinstance(quiz_data, dict) or "questions" not in quiz_data:
                raise ValueError("Invalid quiz structure")
                
            # Ensure each question has required fields
            for question in quiz_data["questions"]:
                if not all(key in question for key in ["question", "options", "correct_answer"]):
                    raise ValueError("Invalid question format")
                if not isinstance(question["options"], list) or len(question["options"]) != 4:
                    raise ValueError("Each question must have exactly 4 options")
                if question["correct_answer"] not in question["options"]:
                    raise ValueError("Correct answer must be one of the options")

            # Store quiz in MongoDB without ObjectId issues
            quiz_record = {
                "email": current_user,
                "topic": quiz_data["topic"],
                "timestamp": datetime.utcnow().isoformat(),  # Convert to string
                "questions": quiz_data["questions"]
            }
            mongo.db.quiz_results.insert_one(quiz_record)

            # Return quiz data without MongoDB-specific fields
            return jsonify({
                "topic": quiz_data["topic"],
                "questions": quiz_data["questions"]
            }), 200

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            return jsonify({
                "topic": topic,
                "questions": []
            }), 200
            
        except ValueError as e:
            print(f"Validation error: {str(e)}")
            return jsonify({
                "topic": topic,
                "questions": []
            }), 200

    except Exception as e:
        print(f"Error in generate_quiz: {str(e)}")
        return jsonify({
            "topic": "General Knowledge",
            "questions": []
        }), 200

@app.route("/check_answers", methods=["POST"])
@jwt_required()
def check_answers():
    try:
        data = request.json
        user_answers = data.get("answers", {})
        correct_answers = data.get("correct_answers", {})

        if not user_answers or not correct_answers:
            return jsonify({"message": "Missing answers"}), 400

        # 🔹 Calculate score (percentage correct)
        total_questions = len(correct_answers)
        correct_count = sum(1 for q, ans in user_answers.items() if ans == correct_answers.get(q))
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        # 🔹 Store quiz result in DB
        current_user = get_jwt_identity()
        mongo.db.quiz_results.insert_one({
            "email": current_user,
            "score": score,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "user_answers": user_answers,
            "timestamp": datetime.utcnow()
        })

        return jsonify({"score": round(score, 2)}), 200

    except Exception as e:
        print(f"Error in check_answers: {str(e)}")
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500



@app.route("/quiz_history", methods=["GET"])
@jwt_required()
def quiz_history():
    current_user = get_jwt_identity()
    history = list(mongo.db.quiz_results.find({"email": current_user}, {"_id": 0}))

    return jsonify(history), 200

# ------------- CHATBOT AI -------------

@app.route("/chatbot", methods=["POST"])
@jwt_required()
def chatbot():
    current_user = get_jwt_identity()
    user_message = request.json.get("message", "").strip()

    # ✅ Ensure input is not too short
    if not user_message or len(user_message) < 5:
        return jsonify({"message": "Please enter a longer message for analysis."}), 400

    try:
        # 🔹 Analyze message with IBM Watson NLU
        watson_response = nlu.analyze(
            text=user_message,
            features=Features(keywords=KeywordsOptions(sentiment=True, emotion=True, limit=2))
        ).get_result()

        # 🔹 Extract keywords and sentiment
        keywords = [kw["text"] for kw in watson_response.get("keywords", [])]
        sentiment = (
            watson_response["keywords"][0]["sentiment"]["label"]
            if watson_response.get("keywords") else "neutral"
        )

        # 🔹 Generate response with Gemini AI
        prompt = f"User asked: {user_message}. Keywords: {keywords}. Sentiment: {sentiment}. Provide a helpful response."
        gemini_response = gemini_model.generate_content(prompt)

        chatbot_reply = gemini_response.text if gemini_response else "I'm unable to respond at the moment."

        # 🔹 Store chat history in MongoDB
        mongo.db.chat_history.insert_one({
            "email": current_user,
            "user_message": user_message,
            "bot_response": chatbot_reply,
            "keywords": keywords,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow()
        })

        return jsonify({"response": chatbot_reply}), 200

    except Exception as e:
        print(f"IBM Watson API Error: {e}")
        return jsonify({"message": "Chatbot service is currently unavailable."}), 500



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)
