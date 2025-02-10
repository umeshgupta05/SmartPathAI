from flask import Flask, jsonify, request
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

app = Flask(__name__)
CORS(app, supports_credentials=True)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = "your_secret_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

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

# Configure Google Gemini AI
GOOGLE_API_KEY = "AIzaSyCC8Me5ZHBVBEuI3OZkoSZUF9sykvETxa8"
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Configure IBM Watson NLU
ibm_authenticator = IAMAuthenticator("zDOlhxO7-cEeZSrbF3OqMEdlmToSEdBscU4_fpmCJCuu")
nlu = NaturalLanguageUnderstandingV1(version="2023-06-15", authenticator=ibm_authenticator)
nlu.set_service_url("https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/54be911a-88cf-4441-9695-a0422de1c839")

# ------------- AUTHENTICATION SYSTEM -------------

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if mongo.db.user.find_one({"email": data["email"]}):
        return jsonify({"message": "User already exists"}), 400

    new_user = {
        "name": data["name"],
        "email": data["email"],
        "password": data["password"],
        "interests": data.get("interests", []),
        "preferences": {"pace": "moderate", "content_format": "video"},
        "performance": {"learning_hours": 0, "average_score": 0, "skills_mastered": 0},
        "completed_courses": []
    }
    mongo.db.user.insert_one(new_user)
    return jsonify({"message": "User created successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = mongo.db.user.find_one({"email": data["email"]})
    if user and user["password"] == data["password"]:
        access_token = create_access_token(identity=data["email"])
        return jsonify({"token": access_token, "user": {"email": user["email"]}}), 200
    return jsonify({"message": "Invalid credentials"}), 401

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
    current_user = get_jwt_identity()
    user = mongo.db.user.find_one({"email": current_user})
    user_interests = user.get("interests", ["AI", "Machine Learning"])

    prompt = f"Recommend 5 online courses based on these interests: {user_interests}"
    response = gemini_model.generate_content(prompt)
    
    if not response.text:
        return jsonify({"message": "Failed to generate courses"}), 500

    courses = response.text.split("\n")
    return jsonify(courses), 200

# ------------- **RECOMMEND CERTIFICATIONS BASED ON INTERESTS** -------------

@app.route("/recommend_certifications", methods=["GET"])
@jwt_required()
def recommend_certifications():
    """Dynamically recommends certifications based on user interests."""
    try:
        current_user = get_jwt_identity()
        user = mongo.db.user.find_one({"email": current_user})

        if not user:
            return jsonify({"message": "User not found"}), 404

        user_interests = user.get("interests", ["AI", "Machine Learning"])

        # 🔹 Generate Certification Recommendations using Gemini AI
        prompt = f"""
        Recommend 5 globally recognized online certifications based on these interests: {user_interests}.
        Provide details in JSON format:
        [
            {{"title": "Certification Name", "provider": "Platform Name", "duration": "X months", "url": "Certification Link"}}
        ]
        """
        response = gemini_model.generate_content(prompt)

        try:
            certifications = json.loads(response.text)
        except json.JSONDecodeError:
            return jsonify({"message": "Failed to generate certifications"}), 500

        # 🔹 Store recommended certifications in DB (if not already present)
        for cert in certifications:
            if not mongo.db.certifications.find_one({"title": cert["title"]}):
                mongo.db.certifications.insert_one(cert)

        return jsonify(certifications), 200

    except Exception as e:
        print(f"Error in recommend_certifications: {str(e)}")
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

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
