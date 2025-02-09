from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.profile import Profile
from app.models.user import User

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_email = get_jwt_identity()
    user = User.find_by_email(current_user_email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    profile = Profile.find_by_user_id(str(user['_id']))
    
    if not profile:
        # Create default profile if it doesn't exist
        profile = Profile(
            user_id=str(user['_id']),
            full_name="",
            role="Student"
        )
        profile.save()
        profile = Profile.find_by_user_id(str(user['_id']))
    
    return jsonify({
        'full_name': profile['full_name'],
        'email': user['email'],
        'role': profile['role'],
        'learning_preferences': {
            'learning_pace': profile['learning_pace'],
            'content_format': profile['content_format']
        },
        'notifications': {
            'course_updates': profile['course_updates_enabled'],
            'quiz_reminders': profile['quiz_reminders_enabled']
        }
    })

@profile_bp.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_email = get_jwt_identity()
    user = User.find_by_email(current_user_email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    
    profile_data = {
        "user_id": str(user['_id'])
    }
    
    # Update personal info
    if 'full_name' in data:
        profile_data['full_name'] = data['full_name']
        
    # Update learning preferences
    if 'learning_preferences' in data:
        prefs = data['learning_preferences']
        if 'learning_pace' in prefs:
            profile_data['learning_pace'] = prefs['learning_pace']
        if 'content_format' in prefs:
            profile_data['content_format'] = prefs['content_format']
            
    # Update notification settings
    if 'notifications' in data:
        notifs = data['notifications']
        if 'course_updates' in notifs:
            profile_data['course_updates_enabled'] = notifs['course_updates']
        if 'quiz_reminders' in notifs:
            profile_data['quiz_reminders_enabled'] = notifs['quiz_reminders']
    
    try:
        profile = Profile(**profile_data)
        profile.save()
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400