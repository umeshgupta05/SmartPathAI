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
from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta

app = Flask(__name__)

# Updated CORS configuration
from flask_cors import CORS

# Updated CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://smart-path-ai.vercel.app",
            "http://localhost:3000",
            "http://localhost:5173"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ["https://smart-path-ai.vercel.app", "http://localhost:3000", "http://localhost:5173"]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# JWT Configuration
app.config["JWT_SECRET_KEY"] = "your_secret_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Disable CSRF tokens for simplicity

jwt = JWTManager(app)

# MongoDB Connection
app.config["MONGO_URI"] = "mongodb+srv://umeshgupta050104:767089amma@cluster0.qez0w.mongodb.net/userdb?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)

# Ensure collections exist
def ensure_collections():
    for collection in ["user", "courses", "certifications", "learning_activities", "chat_history", "quiz_results"]:
        if collection not in mongo.db.list_collection_names():
            mongo.db.create_collection(collection)

ensure_collections()

GOOGLE_API_KEY = "AIzaSyCC8Me5ZHBVBEuI3OZkoSZUF9sykvETxa8"
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Configure IBM Watson NLU
ibm_authenticator = IAMAuthenticator("zDOlhxO7-cEeZSrbF3OqMEdlmToSEdBscU4_fpmCJCuu")
nlu = NaturalLanguageUnderstandingV1(version="2023-06-15", authenticator=ibm_authenticator)
nlu.set_service_url("https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/54be911a-88cf-4441-9695-a0422de1c839")

@app.route("/")
def home():
    return "✅ Server is running!", 200

@app.route("/auth", methods=["POST", "OPTIONS"])
def auth():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        signup = data.get("signup", False)

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        if signup:
            # Signup Logic
            existing_user = mongo.db.user.find_one({"email": email})
            if existing_user:
                return jsonify({"message": "User already exists"}), 409

            new_user = {
                "name": data.get("name", ""),
                "email": email,
                "password": password,
                "interests": data.get("interests", []),
                "preferences": {"pace": "moderate", "content_format": "video"},
                "performance": {"learning_hours": 0, "average_score": 0, "skills_mastered": 0},
                "completed_courses": []
            }
            
            mongo.db.user.insert_one(new_user)
            access_token = create_access_token(identity=email)
            
            return jsonify({
                "message": "User created successfully",
                "token": access_token,
                "user": {
                    "name": new_user["name"],
                    "email": email,
                    "interests": new_user["interests"]
                }
            }), 201
        else:
            # Login Logic
            user = mongo.db.user.find_one({"email": email})
            if not user or user["password"] != password:
                return jsonify({"message": "Invalid credentials"}), 401

            access_token = create_access_token(identity=email)
            
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
        return jsonify({"message": f"Server error: {str(e)}"}), 500

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
    current_user = get_jwt_identity()
    data = request.json

    update_data = {
        "name": data.get("name"),
        "interests": data.get("interests"),
        "preferences": data.get("preferences"),
    }
    
    mongo.db.user.update_one({"email": current_user}, {"$set": update_data})
    return jsonify({"message": "Profile updated successfully"}), 200

# ------------- PERFORMANCE TRACKING -------------

@app.route("/performance", methods=["GET"])
@jwt_required()
def get_performance():
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user})
    if not user:
        return jsonify({"message": "User not found"}), 404

    performance_data = user.get("performance", {})
    return jsonify(performance_data), 200

# ------------- COURSE RECOMMENDATIONS -------------

@app.route("/recommend_courses", methods=["GET"])
@jwt_required()
def recommend_courses():
    """Dynamically recommends courses using Gemini AI and updates MongoDB."""
    current_user = get_jwt_identity()
    user = mongo.db.users.find_one({"email": current_user})

    if not user:
        return jsonify({"message": "User not found"}), 404

    user_interests = user.get("interests", ["AI", "Machine Learning"])

    # Check existing courses first
    existing_courses = list(mongo.db.courses.find({}, {"_id": 0}))
    if existing_courses:
        return jsonify(existing_courses), 200

    # Generate new courses
    prompt = f"Recommend 5 online courses for {user_interests}. Format: Title, Short Intro, Category, Skills, Duration, Site, Rating, URL."

    try:
        response = gemini_model.generate_content(prompt)
        courses = []
        for line in response.text.strip().split("\n"):
            parts = [p.strip() for p in line.split(", ") if p.strip()]
            if len(parts) < 7:
                continue

            course_data = {
                "Title": parts[0],
                "Short Intro": parts[1] if len(parts) > 1 else "",
                "Category": parts[2] if len(parts) > 2 else "General",
                "Skills": parts[3] if len(parts) > 3 else "",
                "Duration": parts[4] if len(parts) > 4 else "",
                "Site": parts[5] if len(parts) > 5 else "",
                "Rating": parts[6] if len(parts) > 6 else "",
                "URL": parts[7] if len(parts) > 7 else "#"
            }
            
            mongo.db.courses.insert_one(course_data.copy())
            courses.append(course_data)

        return jsonify(courses), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "Failed to generate courses"}), 500

@app.route("/learning_path", methods=["GET"])
@jwt_required()
def get_learning_path():
    """Generates a dynamic learning path based on user interests and progress."""
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user})

    if not user:
        return jsonify({"message": "User not found"}), 404

    user_interests = user.get("interests", ["AI", "Machine Learning"])
    completed_courses = user.get("completed_courses", [])

    # Ensure "learning_path" collection exists
    if "learning_path" not in mongo.db.list_collection_names():
        mongo.db.create_collection("learning_path")

    # Check existing learning path in DB
    existing_path = list(mongo.db.learning_path.find({"email": current_user}, {"_id": 0, "email": 0}))

    if existing_path:
        return jsonify(existing_path), 200  # Return stored learning path if available

    # Otherwise, generate dynamically using AI
    prompt = f"Generate a structured learning path (without any bold font) for a student interested in {user_interests}. The response format should be: Title, Description, Status (Not Started, In Progress, Completed), URL."

    try:
        response = gemini_model.generate_content(prompt)
        if not response or not response.text:
            raise ValueError("Gemini AI failed to generate learning path.")

        learning_path = []
        for line in response.text.strip().split("\n"):
            parts = line.split(", ")
            if len(parts) < 4:
                continue  # Ignore malformed responses

            course_data = {
                "title": parts[0],
                "description": parts[1],
                "status": "Completed" if parts[0] in completed_courses else "Not Started",
                "url": parts[3],
            }

            # Store in MongoDB
            mongo.db.learning_path.insert_one({"email": current_user, **course_data})
            learning_path.append(course_data)

        return jsonify(learning_path), 200

    except Exception as e:
        print(f"Error generating learning path: {str(e)}")
        return jsonify({"message": "Failed to generate learning path"}), 500

    
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



# ------------- **RECOMMEND CERTIFICATIONS BASED ON INTERESTS** -------------

import json

@app.route("/recommend_certifications", methods=["GET"])
@jwt_required()
def recommend_certifications():
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user})
    
    if not user:
        return jsonify({"message": "User not found"}), 404

    user_interests = user.get("interests", ["AI", "Machine Learning"])

    prompt = f"Recommend 5 globally recognized online certifications based on these interests: {user_interests}."
    
    try:
        response = gemini_model.generate_content(prompt)
        if not response or not response.text:
            raise ValueError("Gemini AI failed to generate certifications.")
        
        certifications = response.text.strip().split("\n")
        
        # Store recommendations in DB
        for cert in certifications:
            if not mongo.db.certifications.find_one({"title": cert}):
                mongo.db.certifications.insert_one({"title": cert, "recommended_by": current_user})
        
        return jsonify(certifications), 200
    
    except Exception as e:
        print(f"Error in certification recommendation: {str(e)}")
        return jsonify({"message": "Failed to generate certifications"}), 500


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
        # 🔹 Get the current authenticated user
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})

        if not user:
            return jsonify({"message": "User not found"}), 404

        # 🔹 Pick a topic based on user interests
        topic = random.choice(user.get("interests", ["General Knowledge"]))

        # 🔹 Generate quiz using Gemini AI
        prompt = f"""Create a multiple-choice quiz on {topic} with 5 questions.
        Each question should have 4 answer choices.
        Return JSON format:
        {{
            "topic": "{topic}",
            "questions": [
                {{
                    "question": "What is AI?",
                    "options": ["Artificial Intelligence", "Algorithm Integration", "Automation Input", "Advanced Insight"],
                    "correct_answer": "Artificial Intelligence"
                }}
            ]
        }}"""

        response = gemini_model.generate_content(prompt)
        
        if not response.text:
            return jsonify({"message": "Failed to generate quiz"}), 500

        # 🔹 Ensure Gemini's response is valid JSON
        try:
            quiz_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            return jsonify({"message": "Quiz format error"}), 500

        # 🔹 Store quiz in MongoDB for history tracking
        quiz_data["email"] = current_user
        mongo.db.quiz_results.insert_one(quiz_data)

        return jsonify(quiz_data), 200

    except Exception as e:
        print(f"Error in generate_quiz: {str(e)}")
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

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

    except ApiException as e:
        print(f"IBM Watson API Error: {e}")
        return jsonify({"message": "Chatbot service is currently unavailable."}), 500



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)
