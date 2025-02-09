from app import mongo
from bson import ObjectId

class Profile:
    def __init__(self, user_id, full_name=None, role="Student", learning_pace="Moderate", 
                 content_format="Video", course_updates_enabled=True, quiz_reminders_enabled=True):
        self.user_id = user_id
        self.full_name = full_name
        self.role = role
        self.learning_pace = learning_pace
        self.content_format = content_format
        self.course_updates_enabled = course_updates_enabled
        self.quiz_reminders_enabled = quiz_reminders_enabled

    @staticmethod
    def find_by_user_id(user_id):
        return mongo.db.profiles.find_one({"user_id": user_id})

    def save(self):
        profile_data = {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "role": self.role,
            "learning_pace": self.learning_pace,
            "content_format": self.content_format,
            "course_updates_enabled": self.course_updates_enabled,
            "quiz_reminders_enabled": self.quiz_reminders_enabled
        }
        
        existing_profile = Profile.find_by_user_id(self.user_id)
        if existing_profile:
            return mongo.db.profiles.update_one(
                {"user_id": self.user_id},
                {"$set": profile_data}
            )
        return mongo.db.profiles.insert_one(profile_data)