import json
import re
from datetime import timedelta
from functools import wraps

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Certification, Course, QuizResult, UserActivity, UserProfile


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _sanitize_text(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r'[<>"\']', "", value.strip())


def _is_valid_email(email):
    return bool(re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email or ""))


def _create_token(email):
    payload = {
        "email": email,
        "exp": timezone.now() + timedelta(hours=24),
        "iat": timezone.now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _decode_token(token):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _get_user_from_request(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    payload = _decode_token(token)
    if not payload:
        return None
    email = payload.get("email")
    if not email:
        return None
    return UserProfile.objects.filter(email=email).first()


def auth_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = _get_user_from_request(request)
        if not user:
            return JsonResponse({"message": "Unauthorized"}, status=401)
        request.current_user = user
        return view_func(request, *args, **kwargs)

    return _wrapped


def _ensure_seed_data():
    if Course.objects.exists() and Certification.objects.exists():
        return

    if not Course.objects.exists():
        Course.objects.bulk_create(
            [
                Course(
                    title="Python for Beginners",
                    short_intro="Learn Python fundamentals and problem-solving basics.",
                    skills="Python,Problem Solving,Basics",
                    category="Programming",
                    duration="6 weeks",
                    rating="4.7",
                    site="Coursera",
                    url="https://www.coursera.org/",
                ),
                Course(
                    title="Web Development Essentials",
                    short_intro="Build responsive web apps with HTML, CSS and JavaScript.",
                    skills="HTML,CSS,JavaScript",
                    category="Web Development",
                    duration="8 weeks",
                    rating="4.6",
                    site="Udemy",
                    url="https://www.udemy.com/",
                ),
                Course(
                    title="Data Analysis with SQL",
                    short_intro="Use SQL to query data and create useful reports.",
                    skills="SQL,Analytics,Reporting",
                    category="Data",
                    duration="5 weeks",
                    rating="4.5",
                    site="edX",
                    url="https://www.edx.org/",
                ),
            ]
        )

    if not Certification.objects.exists():
        Certification.objects.bulk_create(
            [
                Certification(
                    name="AWS Cloud Practitioner",
                    difficulty="Beginner",
                    description="Foundational cloud knowledge and core services.",
                    link="https://aws.amazon.com/certification/",
                ),
                Certification(
                    name="Google Data Analytics",
                    difficulty="Intermediate",
                    description="Practical data analysis and reporting techniques.",
                    link="https://grow.google/certificates/data-analytics/",
                ),
                Certification(
                    name="Oracle Java Foundations",
                    difficulty="Beginner",
                    description="Core Java fundamentals for entry-level developers.",
                    link="https://education.oracle.com/",
                ),
            ]
        )


def _to_course_api(course):
    return {
        "Title": course.title,
        "Short Intro": course.short_intro,
        "Skills": course.skills,
        "Category": course.category,
        "Duration": course.duration,
        "Rating": course.rating,
        "Site": course.site,
        "URL": course.url,
    }


@csrf_exempt
def home(request):
    return JsonResponse({"message": "Django backend is running"})


@csrf_exempt
def auth_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    signup = bool(data.get("signup", False))
    email = _sanitize_text(data.get("email", "")).lower()
    password = _sanitize_text(data.get("password", ""))

    if not email or not password:
        return JsonResponse({"message": "Email and password are required"}, status=400)
    if not _is_valid_email(email):
        return JsonResponse({"message": "Please provide a valid email address"}, status=400)

    if signup:
        name = _sanitize_text(data.get("name", ""))
        interests = data.get("interests", []) if isinstance(data.get("interests", []), list) else []
        if len(name) < 2:
            return JsonResponse({"message": "Name must be at least 2 characters"}, status=400)
        if len(password) < 6:
            return JsonResponse({"message": "Password must be at least 6 characters"}, status=400)
        if UserProfile.objects.filter(email=email).exists():
            return JsonResponse({"message": "An account with this email already exists"}, status=409)

        user = UserProfile(
            name=name,
            email=email,
            password=make_password(password),
            last_login=timezone.now(),
        )
        user.set_interests([_sanitize_text(item) for item in interests if isinstance(item, str)])
        user.save()
        token = _create_token(user.email)
        return JsonResponse(
            {
                "message": "Account created successfully",
                "token": token,
                "user": {
                    "name": user.name,
                    "email": user.email,
                    "interests": user.get_interests(),
                },
            },
            status=201,
        )

    user = UserProfile.objects.filter(email=email).first()
    if not user or not check_password(password, user.password):
        return JsonResponse({"message": "Invalid email or password"}, status=401)

    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    token = _create_token(user.email)
    return JsonResponse(
        {
            "message": "Login successful",
            "token": token,
            "user": {
                "name": user.name,
                "email": user.email,
                "interests": user.get_interests(),
            },
        }
    )


@csrf_exempt
@auth_required
def dashboard_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    _ensure_seed_data()
    user = request.current_user
    completed_courses = user.get_completed_courses()
    earned_certifications = user.get_earned_certifications()
    courses = list(Course.objects.all().order_by("id"))
    current_course = "No active course"
    for course in courses:
        if course.title not in completed_courses:
            current_course = course.title
            break

    progress = min(100, (len(completed_courses) * 25) + (len(earned_certifications) * 25))
    recommended_courses = [
        {
            "title": c.title,
            "description": c.short_intro,
            "level": "Beginner",
        }
        for c in courses[:3]
    ]
    return JsonResponse(
        {
            "currentCourse": current_course,
            "completedCourses": len(completed_courses),
            "certifications": len(earned_certifications),
            "overallProgress": progress,
            "recommendedCourses": recommended_courses,
        }
    )


@csrf_exempt
@auth_required
def profile_view(request):
    user = request.current_user
    if request.method == "GET":
        return JsonResponse(
            {
                "name": user.name,
                "email": user.email,
                "interests": user.get_interests(),
                "preferences": user.get_preferences(),
            }
        )

    if request.method == "PUT":
        data = _json_body(request)
        user.name = _sanitize_text(data.get("name", user.name)) or user.name
        incoming_interests = data.get("interests")
        if isinstance(incoming_interests, list):
            user.set_interests([_sanitize_text(i) for i in incoming_interests if isinstance(i, str)])

        incoming_preferences = data.get("preferences")
        if isinstance(incoming_preferences, dict):
            existing_preferences = user.get_preferences()
            existing_preferences.update(
                {
                    "pace": _sanitize_text(incoming_preferences.get("pace", existing_preferences.get("pace", "Moderate"))),
                    "content_format": _sanitize_text(
                        incoming_preferences.get("content_format", existing_preferences.get("content_format", "Video"))
                    ),
                }
            )
            user.set_preferences(existing_preferences)

        user.save()
        return JsonResponse({"message": "Profile updated successfully"})

    return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
@auth_required
def performance_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    user = request.current_user
    perf = user.get_performance()

    recent = list(UserActivity.objects.filter(user=user).order_by("-date")[:7])
    if recent:
        perf["recent_activity"] = [
            {
                "date": activity.date.isoformat(),
                "learning_hours": activity.learning_hours,
                "score": activity.score,
            }
            for activity in reversed(recent)
        ]

    return JsonResponse(perf)


@csrf_exempt
@auth_required
def recommend_courses_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    _ensure_seed_data()
    courses = Course.objects.all().order_by("id")
    return JsonResponse([_to_course_api(course) for course in courses], safe=False)


@csrf_exempt
@auth_required
def user_progress_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)
    return JsonResponse({"completed_courses": request.current_user.get_completed_courses()})


@csrf_exempt
@auth_required
def mark_completed_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    course_title = _sanitize_text(data.get("courseTitle", ""))
    if not course_title:
        return JsonResponse({"message": "courseTitle is required"}, status=400)

    user = request.current_user
    completed = user.get_completed_courses()
    if course_title not in completed:
        completed.append(course_title)
        user.set_completed_courses(completed)

        perf = user.get_performance()
        perf["learning_hours"] = float(perf.get("learning_hours", 0)) + 2
        perf["skills_mastered"] = int(perf.get("skills_mastered", 0)) + 1
        user.set_performance(perf)
        user.save()

    return JsonResponse({"message": "Course marked as completed"})


@csrf_exempt
@auth_required
def learning_path_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    _ensure_seed_data()
    user = request.current_user
    completed = set(user.get_completed_courses())
    courses = Course.objects.all().order_by("id")
    payload = []
    for course in courses:
        status = "Completed" if course.title in completed else "In Progress"
        payload.append(
            {
                "title": course.title,
                "description": course.short_intro,
                "status": status,
                "url": course.url,
            }
        )
    return JsonResponse(payload, safe=False)


@csrf_exempt
@auth_required
def recommend_certifications_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    _ensure_seed_data()
    certs = Certification.objects.all().order_by("id")
    return JsonResponse(
        [
            {
                "name": cert.name,
                "difficulty": cert.difficulty,
                "description": cert.description,
                "link": cert.link,
            }
            for cert in certs
        ],
        safe=False,
    )


@csrf_exempt
@auth_required
def earned_certifications_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)
    return JsonResponse(request.current_user.get_earned_certifications(), safe=False)


@csrf_exempt
@auth_required
def mark_certification_completed_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    title = _sanitize_text(data.get("title", ""))
    if not title:
        return JsonResponse({"message": "title is required"}, status=400)

    user = request.current_user
    earned = user.get_earned_certifications()
    if title not in earned:
        earned.append(title)
        user.set_earned_certifications(earned)
        user.save(update_fields=["earned_certifications_data"])

    return JsonResponse({"message": "Certification marked as completed"})


@csrf_exempt
@auth_required
def generate_quiz_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    quiz = {
        "topic": "General Programming",
        "questions": [
            {
                "question": "Which language is primarily used for web page styling?",
                "options": ["Python", "CSS", "SQL", "Java"],
                "correct_answer": "CSS",
            },
            {
                "question": "What does API stand for?",
                "options": [
                    "Application Programming Interface",
                    "Advanced Program Integration",
                    "Applied Protocol Internet",
                    "Automated Program Input",
                ],
                "correct_answer": "Application Programming Interface",
            },
            {
                "question": "Which HTTP method is typically used to create data?",
                "options": ["GET", "POST", "DELETE", "HEAD"],
                "correct_answer": "POST",
            },
            {
                "question": "Which of these is a relational database?",
                "options": ["MongoDB", "Redis", "Oracle", "Neo4j"],
                "correct_answer": "Oracle",
            },
            {
                "question": "Which command installs Python packages?",
                "options": ["pip install", "npm install", "apt get", "brew add"],
                "correct_answer": "pip install",
            },
        ],
    }
    return JsonResponse(quiz)


@csrf_exempt
@auth_required
def check_answers_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    answers = data.get("answers", {}) if isinstance(data.get("answers", {}), dict) else {}
    correct_answers = data.get("correct_answers", {}) if isinstance(data.get("correct_answers", {}), dict) else {}

    total = len(correct_answers)
    if total == 0:
        return JsonResponse({"score": 0})

    correct = 0
    for question, correct_answer in correct_answers.items():
        if answers.get(question) == correct_answer:
            correct += 1

    score = int((correct / total) * 100)
    user = request.current_user
    QuizResult.objects.create(user=user, score=score)

    perf = user.get_performance()
    existing_avg = float(perf.get("average_score", 0))
    count = QuizResult.objects.filter(user=user).count()
    perf["average_score"] = round(((existing_avg * max(count - 1, 0)) + score) / max(count, 1), 1)
    user.set_performance(perf)
    user.save(update_fields=["performance_data"])

    UserActivity.objects.create(
        user=user,
        learning_hours=1,
        score=score,
        date=timezone.now().date(),
    )

    return JsonResponse({"score": score})


@csrf_exempt
@auth_required
def chatbot_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    message = _sanitize_text(data.get("message", "")).lower()
    if not message:
        return JsonResponse({"response": "Please enter a message."})

    if "course" in message:
        reply = "Try starting with Python for Beginners and complete one module daily."
    elif "quiz" in message:
        reply = "Take one quiz after each course section to improve retention."
    elif "certification" in message:
        reply = "Start with a beginner certification, then move to intermediate level."
    else:
        reply = "Keep a steady pace and track your progress weekly."

    return JsonResponse({"response": reply})
