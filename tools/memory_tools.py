"""
Tool helpers that expose the memory bank to ADK agents.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from memory import get_memory_bank


def _bank():
    """Return the configured memory backend instance."""

    return get_memory_bank()


def _to_dict(profile: Any) -> Dict[str, Any]:
    """Convert backend-specific profile objects into plain dicts."""

    if hasattr(profile, "to_dict"):
        return profile.to_dict()
    return dict(profile)


def fetch_student_profile(student_id: str) -> Dict[str, Any]:
    """
    Return the serialized student profile for the given ``student_id``.
    """
    return _bank().to_dict(student_id)


def update_student_profile(
    student_id: str,
    subject: str,
    level: str,
    learning_style: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update the student's knowledge level (and optionally learning style).
    """
    profile = _bank().update_knowledge_level(student_id, subject, level)
    if learning_style:
        if hasattr(profile, "learning_style"):
            profile.learning_style = learning_style
        else:
            profile["learning_style"] = learning_style
    return _to_dict(profile)


def record_topic_completion(student_id: str, topic: str) -> Dict[str, Any]:
    """
    Mark a topic as completed in the student's profile.
    """
    profile = _bank().mark_topic_completed(student_id, topic)
    return _to_dict(profile)


def log_study_time(student_id: str, minutes: int) -> Dict[str, Any]:
    """
    Increment the student's total tracked study time.
    """
    profile = _bank().add_study_time(student_id, minutes)
    return _to_dict(profile)


