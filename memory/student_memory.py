"""
Student memory module.

Implements a simple in-memory "memory bank" that can be swapped out with a
persistent store (e.g. Firestore, database) when deploying to production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class QuizRecord:
    """Represents a single quiz attempt."""

    topic: str
    score: float
    date: str
    questions_answered: int


@dataclass
class StudentProfile:
    """Represents long‑term memory for a single student."""

    student_id: str
    knowledge_levels: Dict[str, str] = field(default_factory=dict)
    learning_style: str = "visual"
    quiz_history: List[QuizRecord] = field(default_factory=list)
    completed_topics: List[str] = field(default_factory=list)
    current_goals: List[str] = field(default_factory=list)
    total_study_time_minutes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile to a JSON‑serializable dict."""
        return {
            "student_id": self.student_id,
            "knowledge_levels": self.knowledge_levels,
            "learning_style": self.learning_style,
            "quiz_history": [
                {
                    "topic": q.topic,
                    "score": q.score,
                    "date": q.date,
                    "questions_answered": q.questions_answered,
                }
                for q in self.quiz_history
            ],
            "completed_topics": self.completed_topics,
            "current_goals": self.current_goals,
            "total_study_time_minutes": self.total_study_time_minutes,
        }


class MemoryBank:
    """
    In‑memory implementation of a student memory bank.

    In an ADK deployment this can be wired into InMemorySessionService or a
    persistent backend. For the capstone, we keep it simple and process‑local.
    """

    def __init__(self) -> None:
        self._students: Dict[str, StudentProfile] = {}

    def get_or_create_student(self, student_id: str) -> StudentProfile:
        """Fetch an existing student or create a new blank profile."""
        if student_id not in self._students:
            self._students[student_id] = StudentProfile(student_id=student_id)
        return self._students[student_id]

    def update_knowledge_level(
        self, student_id: str, subject: str, level: str
    ) -> StudentProfile:
        """Update knowledge level for a given subject."""
        profile = self.get_or_create_student(student_id)
        profile.knowledge_levels[subject] = level
        return profile

    def append_quiz_record(
        self,
        student_id: str,
        topic: str,
        score: float,
        questions_answered: int,
        date: Optional[str] = None,
    ) -> StudentProfile:
        """Append a quiz record to the student's history."""
        profile = self.get_or_create_student(student_id)
        record = QuizRecord(
            topic=topic,
            score=score,
            date=date or datetime.utcnow().strftime("%Y-%m-%d"),
            questions_answered=questions_answered,
        )
        profile.quiz_history.append(record)
        return profile

    def mark_topic_completed(self, student_id: str, topic: str) -> StudentProfile:
        """Mark a topic as completed if not already present."""
        profile = self.get_or_create_student(student_id)
        if topic not in profile.completed_topics:
            profile.completed_topics.append(topic)
        return profile

    def add_study_time(self, student_id: str, minutes: int) -> StudentProfile:
        """Increment total study time for the student."""
        profile = self.get_or_create_student(student_id)
        profile.total_study_time_minutes += max(0, minutes)
        return profile

    def to_dict(self, student_id: str) -> Dict[str, Any]:
        """Return the student's profile as a dict, or an empty profile if missing."""
        return self.get_or_create_student(student_id).to_dict()


GLOBAL_MEMORY_BANK = MemoryBank()


