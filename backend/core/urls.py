from django.urls import path

from .views import (
    auth_view,
    chatbot_view,
    check_answers_view,
    dashboard_view,
    earned_certifications_view,
    generate_quiz_view,
    home,
    learning_path_view,
    mark_certification_completed_view,
    mark_completed_view,
    performance_view,
    profile_view,
    recommend_certifications_view,
    recommend_courses_view,
    user_progress_view,
)

urlpatterns = [
    path("", home),
    path("auth", auth_view),
    path("dashboard", dashboard_view),
    path("profile", profile_view),
    path("performance", performance_view),
    path("recommend_courses", recommend_courses_view),
    path("user_progress", user_progress_view),
    path("mark_completed", mark_completed_view),
    path("learning_path", learning_path_view),
    path("recommend_certifications", recommend_certifications_view),
    path("earned_certifications", earned_certifications_view),
    path("mark_certification_completed", mark_certification_completed_view),
    path("generate_quiz", generate_quiz_view),
    path("check_answers", check_answers_view),
    path("chatbot", chatbot_view),
]
