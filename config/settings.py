"""
Global configuration settings for StudyBuddy AI.

Values are read from environment variables, which can be conveniently
managed via a local ".env" file (see env.example).
"""

import os

from dotenv import load_dotenv

# Load variables from .env if present (safe no-op in production).
load_dotenv()

GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
MAX_QUIZ_QUESTIONS: int = int(os.getenv("MAX_QUIZ_QUESTIONS", "10"))
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MEMORY_RETENTION_DAYS: int = int(os.getenv("MEMORY_RETENTION_DAYS", "90"))

SUPPORTED_SUBJECTS = [
    "mathematics",
    "physics",
    "chemistry",
    "programming",
    "biology",
    "history",
]

DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]


