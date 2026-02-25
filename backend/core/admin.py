from django.contrib import admin

from .models import Certification, Course, QuizResult, UserActivity, UserProfile

admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Certification)
admin.site.register(QuizResult)
admin.site.register(UserActivity)
