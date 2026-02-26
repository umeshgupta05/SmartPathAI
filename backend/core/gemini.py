"""Google Gemini AI helper for dynamic content generation.

Uses Pydantic-based structured outputs to guarantee type-safe JSON
responses from the Gemini API.  Every public function is safe to call –
on failure it logs the error and returns sensible empty/fallback data.
"""

import logging
import os
import re
import time
from typing import List, Optional

from google import genai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("GEMINI_API_KEY", "")
_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Lazy-initialised client
_client = None


def _get_client():
    global _client
    if _client is None:
        if not _API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")
        _client = genai.Client(api_key=_API_KEY)
    return _client


def _generate_with_retry(prompt: str, config: dict | None = None, max_retries: int = 3):
    """Call Gemini with automatic retry on 429 rate-limit errors."""
    client = _get_client()
    delay = 10  # initial backoff seconds
    for attempt in range(max_retries + 1):
        try:
            kwargs = {"model": _MODEL, "contents": prompt}
            if config:
                kwargs["config"] = config
            return client.models.generate_content(**kwargs)
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Extract server-suggested retry delay if available
                match = re.search(r"retry in ([\d.]+)s", err_str, re.IGNORECASE)
                wait = float(match.group(1)) if match else delay
                if attempt < max_retries:
                    logger.info("Rate limited, retrying in %.1fs (attempt %d/%d)", wait, attempt + 1, max_retries)
                    time.sleep(wait)
                    delay = min(delay * 2, 60)  # exponential backoff cap
                    continue
            raise  # non-429 error or exhausted retries


# ── Pydantic schemas ───────────────────────────────────────────────

class CourseItem(BaseModel):
    title: str = Field(description="Course name")
    short_intro: str = Field(description="One-sentence course description")
    skills: str = Field(description="Comma-separated skill tags")
    category: str = Field(description="Broad category like Programming, Data, Web Development")
    duration: str = Field(description="Estimated duration, e.g. '6 weeks'")
    rating: str = Field(description="Realistic rating like '4.7'")
    site: str = Field(description="Platform name, e.g. Coursera, Udemy, edX")
    url: str = Field(description="Valid URL to the course or platform")


class CourseList(BaseModel):
    courses: List[CourseItem] = Field(description="List of recommended courses")


class CertificationItem(BaseModel):
    name: str = Field(description="Certification name")
    difficulty: str = Field(description="Beginner, Intermediate, or Advanced")
    description: str = Field(description="One-sentence description")
    link: str = Field(description="URL to the official certification page")


class CertificationList(BaseModel):
    certifications: List[CertificationItem] = Field(description="List of recommended certifications")


class QuizQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="Exactly 4 answer choices")
    correct_answer: str = Field(description="The correct option, must match one of the options exactly")


class Quiz(BaseModel):
    topic: str = Field(description="The quiz topic")
    questions: List[QuizQuestion] = Field(description="List of multiple-choice questions")


# ── Course recommendations ─────────────────────────────────────────

def generate_courses(interests: list[str], count: int = 5) -> list[dict]:
    """Return *count* course dicts tailored to *interests*."""
    interest_str = ", ".join(interests) if interests else "general programming and technology"
    prompt = (
        f"You are an expert career and education adviser. "
        f"Generate exactly {count} real, currently available online courses "
        f"for someone interested in: {interest_str}."
    )
    try:
        response = _generate_with_retry(
            prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": CourseList.model_json_schema(),
            },
        )
        result = CourseList.model_validate_json(response.text)
        return [c.model_dump() for c in result.courses[:count]]
    except Exception as exc:
        logger.warning("Gemini course generation failed: %s", exc)
    return []


# ── Certification recommendations ──────────────────────────────────

def generate_certifications(interests: list[str], count: int = 3) -> list[dict]:
    """Return *count* certification dicts tailored to *interests*."""
    interest_str = ", ".join(interests) if interests else "general technology"
    prompt = (
        f"You are an expert career adviser. "
        f"Recommend exactly {count} real, industry-recognised certifications "
        f"for someone interested in: {interest_str}."
    )
    try:
        response = _generate_with_retry(
            prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": CertificationList.model_json_schema(),
            },
        )
        result = CertificationList.model_validate_json(response.text)
        return [c.model_dump() for c in result.certifications[:count]]
    except Exception as exc:
        logger.warning("Gemini certification generation failed: %s", exc)
    return []


# ── Quiz generation ────────────────────────────────────────────────

def generate_quiz(topic: str, count: int = 5) -> dict:
    """Return a quiz dict with *count* MCQs about *topic*."""
    prompt = (
        f"You are an expert quiz master. "
        f"Create exactly {count} multiple-choice questions about: {topic}. "
        f"Each question must have exactly 4 options."
    )
    try:
        response = _generate_with_retry(
            prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": Quiz.model_json_schema(),
            },
        )
        result = Quiz.model_validate_json(response.text)
        return result.model_dump()
    except Exception as exc:
        logger.warning("Gemini quiz generation failed: %s", exc)
    return {"topic": topic, "questions": []}


# ── Chatbot response ───────────────────────────────────────────────

def chat_response(message: str, user_name: str = "", interests: list[str] | None = None) -> str:
    """Return an AI-generated chatbot reply to the user's *message*."""
    context_parts = []
    if user_name:
        context_parts.append(f"The student's name is {user_name}.")
    if interests:
        context_parts.append(f"Their interests are: {', '.join(interests)}.")
    context = " ".join(context_parts)

    prompt = (
        f"You are SmartPathAI, a friendly and helpful AI learning assistant. "
        f"Keep answers concise (2-3 sentences). {context}\n\n"
        f"Student says: {message}"
    )
    try:
        response = _generate_with_retry(prompt)
        text = response.text.strip()
        if text:
            return text
    except Exception as exc:
        logger.warning("Gemini chatbot failed: %s", exc)
    return "I'm having trouble connecting right now. Please try again in a moment."
