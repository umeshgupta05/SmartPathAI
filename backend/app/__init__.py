from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from config import Config

mongo = PyMongo()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Register blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app

# app/models/user.py
from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, email, password=None, interests=None):
        self.email = email
        self.password = generate_password_hash(password) if password else None
        self.interests = interests or []

    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({"email": email})

    def save(self):
        user_data = {
            "email": self.email,
            "password": self.password,
            "interests": self.interests
        }
        return mongo.db.users.insert_one(user_data)

    @staticmethod
    def check_password(stored_password, password):
        return check_password_hash(stored_password, password)

# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.utils.helpers import validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not validate_email(data.get('email')):
        return jsonify({"error": "Invalid email format"}), 400

    if User.find_by_email(data['email']):
        return jsonify({"error": "Email already registered"}), 400
    
    try:
        user = User(
            email=data['email'],
            password=data['password'],
            interests=data.get('interests', [])
        )
        user.save()
        
        access_token = create_access_token(identity=data['email'])
        
        return jsonify({
            'token': access_token,
            'user': {
                'email': user.email,
                'interests': user.interests
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not validate_email(data.get('email')):
        return jsonify({"error": "Invalid email format"}), 400

    user_data = User.find_by_email(data['email'])
    
    if not user_data or not User.check_password(user_data['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=data['email'])
    
    return jsonify({
        'token': access_token,
        'user': {
            'email': user_data['email'],
            'interests': user_data.get('interests', [])
        }
    })

# app/utils/helpers.py
import re

def validate_email(email):
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGODB_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)