import json

from django.db import models


def _json_loads(raw, fallback):
    try:
        parsed = json.loads(raw or "")
        return parsed if isinstance(parsed, type(fallback)) else fallback
    except (json.JSONDecodeError, TypeError):
        return fallback


class UserProfile(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    interests_data = models.TextField(default="[]")
    preferences_data = models.TextField(default='{"pace": "Moderate", "content_format": "Video"}')
    performance_data = models.TextField(
        default='{"learning_hours": 0, "average_score": 0, "skills_mastered": 0, "recent_activity": [], "skill_progress": []}'
    )
    completed_courses_data = models.TextField(default="[]")
    earned_certifications_data = models.TextField(default="[]")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def get_interests(self):
        return _json_loads(self.interests_data, [])

    def set_interests(self, value):
        self.interests_data = json.dumps(value or [])

    def get_preferences(self):
        return _json_loads(self.preferences_data, {"pace": "Moderate", "content_format": "Video"})

    def set_preferences(self, value):
        self.preferences_data = json.dumps(value or {"pace": "Moderate", "content_format": "Video"})

    def get_performance(self):
        return _json_loads(
            self.performance_data,
            {
                "learning_hours": 0,
                "average_score": 0,
                "skills_mastered": 0,
                "recent_activity": [],
                "skill_progress": [],
            },
        )

    def set_performance(self, value):
        default_payload = {
            "learning_hours": 0,
            "average_score": 0,
            "skills_mastered": 0,
            "recent_activity": [],
            "skill_progress": [],
        }
        payload = default_payload | (value or {})
        self.performance_data = json.dumps(payload)

    def get_completed_courses(self):
        return _json_loads(self.completed_courses_data, [])

    def set_completed_courses(self, value):
        self.completed_courses_data = json.dumps(value or [])

    def get_earned_certifications(self):
        return _json_loads(self.earned_certifications_data, [])

    def set_earned_certifications(self, value):
        self.earned_certifications_data = json.dumps(value or [])

    def __str__(self):
        return self.email


class Course(models.Model):
    title = models.CharField(max_length=200, unique=True)
    short_intro = models.TextField()
    skills = models.CharField(max_length=400)
    category = models.CharField(max_length=120)
    duration = models.CharField(max_length=80)
    rating = models.CharField(max_length=20)
    site = models.CharField(max_length=80)
    url = models.URLField()

    def __str__(self):
        return self.title


class Certification(models.Model):
    name = models.CharField(max_length=200, unique=True)
    difficulty = models.CharField(max_length=50, default="Beginner")
    description = models.TextField()
    link = models.URLField(blank=True)

    def __str__(self):
        return self.name


class QuizResult(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserActivity(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    learning_hours = models.FloatField(default=0)
    score = models.IntegerField(default=0)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
