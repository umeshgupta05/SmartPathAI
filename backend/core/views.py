"""SmartPathAI – API views.

All endpoints are JSON-based.  Authentication uses JWT (Bearer tokens).
Course / certification recommendations and quizzes are generated
dynamically by Google Gemini and persisted in Oracle for caching.
"""

import json
import logging
import re
from datetime import timedelta
from functools import wraps

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from . import gemini
from .models import Certification, Course, QuizResult, UserActivity, UserProfile

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────


def _json_body(request):
    """Parse the request body as JSON; return ``{}`` on failure."""
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _sanitize_text(value):
    """Strip basic HTML/script-injection characters from *value*."""
    if not isinstance(value, str):
        return ""
    return re.sub(r'[<>"\']', "", value.strip())


def _is_valid_email(email):
    return bool(re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email or ""))


# ── JWT helpers ────────────────────────────────────────────────────


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
    try:
        return UserProfile.objects.filter(email=email).first()
    except Exception:
        return None


def auth_required(view_func):
    """Decorator – rejects requests without a valid JWT."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = _get_user_from_request(request)
        if not user:
            return JsonResponse({"message": "Unauthorized"}, status=401)
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return _wrapped


# ── Gemini → DB persistence helpers ───────────────────────────────


def _save_courses_from_ai(interests):
    """Call Gemini for courses and persist new ones to the DB."""
    items = gemini.generate_courses(interests, count=5)
    for item in items:
        try:
            Course(
                title=item.get("title", "Untitled")[:200],
                short_intro=item.get("short_intro", ""),
                skills=item.get("skills", "")[:400],
                category=item.get("category", "General")[:120],
                duration=item.get("duration", "Self-paced")[:80],
                rating=item.get("rating", "4.5")[:20],
                site=item.get("site", "Online")[:80],
                url=item.get("url", "https://www.google.com/"),
            ).save()
        except IntegrityError:
            pass
        except Exception as exc:
            logger.warning("Could not save course: %s", exc)
    return items


def _save_certs_from_ai(interests):
    """Call Gemini for certifications and persist new ones to the DB."""
    items = gemini.generate_certifications(interests, count=3)
    for item in items:
        try:
            Certification(
                name=item.get("name", "Untitled")[:200],
                difficulty=item.get("difficulty", "Beginner")[:50],
                description=item.get("description", ""),
                link=item.get("link", ""),
            ).save()
        except IntegrityError:
            pass
        except Exception as exc:
            logger.warning("Could not save certification: %s", exc)
    return items


def _course_to_dict(course):
    """Serialise a ``Course`` model instance to the API format."""
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


# ── Public views ───────────────────────────────────────────────────


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
        user.set_interests([_sanitize_text(i) for i in interests if isinstance(i, str)])
        user.save()
        return JsonResponse(
            {
                "message": "Account created successfully",
                "token": _create_token(user.email),
                "user": {"name": user.name, "email": user.email, "interests": user.get_interests()},
            },
            status=201,
        )

    # Login
    user = UserProfile.objects.filter(email=email).first()
    if not user or not check_password(password, user.password):
        return JsonResponse({"message": "Invalid email or password"}, status=401)

    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    return JsonResponse(
        {
            "message": "Login successful",
            "token": _create_token(user.email),
            "user": {"name": user.name, "email": user.email, "interests": user.get_interests()},
        }
    )


# ── Dashboard ──────────────────────────────────────────────────────


@csrf_exempt
@auth_required
def dashboard_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        user = request.current_user
        interests = user.get_interests()

        # Ensure DB has at least some data for the dashboard cards
        if not Course.objects.exists():
            _save_courses_from_ai(interests)
        if not Certification.objects.exists():
            _save_certs_from_ai(interests)

        completed_courses = user.get_completed_courses()
        earned_certifications = user.get_earned_certifications()
        courses = list(Course.objects.all().order_by("id"))

        current_course = "No active course"
        for course in courses:
            if course.title not in completed_courses:
                current_course = course.title
                break

        progress = min(100, (len(completed_courses) * 25) + (len(earned_certifications) * 25))

        # Return courses not yet completed, up to 5, with full details
        recommended = [
            _course_to_dict(c)
            for c in courses
            if c.title not in completed_courses
        ][:5]

        return JsonResponse(
            {
                "currentCourse": current_course,
                "completedCourses": len(completed_courses),
                "certifications": len(earned_certifications),
                "overallProgress": progress,
                "recommendedCourses": recommended,
            }
        )
    except Exception as exc:
        logger.exception("Dashboard error: %s", exc)
        return JsonResponse({"message": "Failed to load dashboard data"}, status=500)


# ── Profile & Performance ─────────────────────────────────────────


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
            prefs = user.get_preferences()
            prefs["pace"] = _sanitize_text(incoming_preferences.get("pace", prefs.get("pace", "Moderate")))
            prefs["content_format"] = _sanitize_text(
                incoming_preferences.get("content_format", prefs.get("content_format", "Video"))
            )
            user.set_preferences(prefs)

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

    # Recent activity (last 7 days)
    recent = list(UserActivity.objects.filter(user=user).order_by("-date")[:7])
    if recent:
        perf["recent_activity"] = [
            {"date": a.date.isoformat(), "learning_hours": a.learning_hours, "score": a.score}
            for a in reversed(recent)
        ]

    # Streak – count consecutive days with activity ending today/yesterday
    streak = 0
    activity_dates = list(
        UserActivity.objects.filter(user=user)
        .order_by("-date")
        .values_list("date", flat=True)
    )
    if activity_dates:
        from datetime import date, timedelta

        today = date.today()
        # Allow streak to start from today or yesterday
        expected = today if activity_dates[0] >= today else activity_dates[0]
        for d in activity_dates:
            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
            elif d < expected:
                break
    perf["streak"] = streak

    # Quiz stats
    quiz_results = QuizResult.objects.filter(user=user)
    perf["quizzes_taken"] = quiz_results.count()
    perf["best_score"] = quiz_results.order_by("-score").values_list("score", flat=True).first() or 0

    # Completion stats
    perf["completed_courses"] = len(user.get_completed_courses())
    perf["earned_certifications"] = len(user.get_earned_certifications())

    return JsonResponse(perf)


# ── Courses (Gemini-powered) ──────────────────────────────────────


@csrf_exempt
@auth_required
def recommend_courses_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        interests = request.current_user.get_interests()
        ai_courses = _save_courses_from_ai(interests)

        if ai_courses:
            return JsonResponse(
                [
                    {
                        "Title": c.get("title", ""),
                        "Short Intro": c.get("short_intro", ""),
                        "Skills": c.get("skills", ""),
                        "Category": c.get("category", ""),
                        "Duration": c.get("duration", ""),
                        "Rating": c.get("rating", ""),
                        "Site": c.get("site", ""),
                        "URL": c.get("url", ""),
                    }
                    for c in ai_courses
                ],
                safe=False,
            )

        # Fallback to DB if Gemini failed
        return JsonResponse(
            [_course_to_dict(c) for c in Course.objects.all().order_by("id")],
            safe=False,
        )
    except Exception as exc:
        logger.exception("Course recommendation error: %s", exc)
        return JsonResponse({"message": "Failed to load courses"}, status=500)


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

        # Record activity for streak tracking
        from datetime import date as date_cls

        today = date_cls.today()
        activity, created = UserActivity.objects.get_or_create(
            user=user, date=today,
            defaults={"learning_hours": 2, "score": 0},
        )
        if not created:
            activity.learning_hours += 2
            activity.save()

    return JsonResponse({"message": "Course marked as completed"})


@csrf_exempt
@auth_required
def learning_path_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        user = request.current_user
        if not Course.objects.exists():
            _save_courses_from_ai(user.get_interests())
        completed = set(user.get_completed_courses())
        courses = Course.objects.all().order_by("id")
        total = courses.count()
        done = len([c for c in courses if c.title in completed])

        return JsonResponse(
            {
                "courses": [
                    {
                        "title": c.title,
                        "description": c.short_intro,
                        "skills": c.skills,
                        "category": c.category,
                        "duration": c.duration,
                        "status": "Completed" if c.title in completed else "In Progress",
                        "url": c.url,
                    }
                    for c in courses
                ],
                "stats": {
                    "total": total,
                    "completed": done,
                    "progress": round((done / total) * 100) if total else 0,
                },
            }
        )
    except Exception as exc:
        logger.exception("Learning path error: %s", exc)
        return JsonResponse({"message": "Failed to load learning path"}, status=500)


# ── Certifications (Gemini-powered) ───────────────────────────────


@csrf_exempt
@auth_required
def recommend_certifications_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        interests = request.current_user.get_interests()
        ai_certs = _save_certs_from_ai(interests)

        if ai_certs:
            return JsonResponse(ai_certs, safe=False)

        # Fallback to DB
        return JsonResponse(
            [{"name": c.name, "difficulty": c.difficulty,
              "description": c.description, "link": c.link}
             for c in Certification.objects.all().order_by("id")],
            safe=False,
        )
    except Exception as exc:
        logger.exception("Certification recommendation error: %s", exc)
        return JsonResponse({"message": "Failed to load certifications"}, status=500)


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


# ── Quiz (Gemini-powered) ─────────────────────────────────────────


@csrf_exempt
@auth_required
def generate_quiz_view(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        user = request.current_user
        interests = user.get_interests()

        # Derive quiz topic from current course or interests
        topic = "General Programming"
        try:
            completed = user.get_completed_courses()
            for course in Course.objects.all().order_by("id"):
                if course.title not in completed:
                    topic = course.title
                    break
        except Exception:
            pass

        if interests:
            topic = f"{topic} focusing on {', '.join(interests[:3])}"

        return JsonResponse(gemini.generate_quiz(topic, count=5))
    except Exception as exc:
        logger.exception("Quiz generation error: %s", exc)
        return JsonResponse({"topic": "General", "questions": []})


@csrf_exempt
@auth_required
def check_answers_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    answers = data.get("answers", {}) if isinstance(data.get("answers"), dict) else {}
    correct_answers = data.get("correct_answers", {}) if isinstance(data.get("correct_answers"), dict) else {}

    total = len(correct_answers)
    if total == 0:
        return JsonResponse({"score": 0})

    correct = sum(1 for q, a in correct_answers.items() if answers.get(q) == a)
    score = int((correct / total) * 100)

    user = request.current_user
    QuizResult.objects.create(user=user, score=score)

    perf = user.get_performance()
    existing_avg = float(perf.get("average_score", 0))
    count = QuizResult.objects.filter(user=user).count()
    perf["average_score"] = round(((existing_avg * max(count - 1, 0)) + score) / max(count, 1), 1)
    user.set_performance(perf)
    user.save(update_fields=["performance_data"])

    UserActivity.objects.create(user=user, learning_hours=1, score=score, date=timezone.now().date())
    return JsonResponse({"score": score})


# ── Chatbot (Gemini-powered) ──────────────────────────────────────


@csrf_exempt
@auth_required
def chatbot_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = _json_body(request)
    message = _sanitize_text(data.get("message", ""))
    if not message:
        return JsonResponse({"response": "Please enter a message."})

    user = request.current_user
    reply = gemini.chat_response(
        message=message,
        user_name=user.name,
        interests=user.get_interests(),
    )
    return JsonResponse({"response": reply})
