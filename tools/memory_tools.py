"""
Tool helpers that expose the memory bank to ADK agents.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from memory.student_memory import GLOBAL_MEMORY_BANK


def fetch_student_profile(student_id: str) -> Dict[str, Any]:
    """
    Return the serialized student profile for the given ``student_id``.
    """
    return GLOBAL_MEMORY_BANK.to_dict(student_id)


def update_student_profile(
    student_id: str,
    subject: str,
    level: str,
    learning_style: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update the student's knowledge level (and optionally learning style).
    """
    profile = GLOBAL_MEMORY_BANK.update_knowledge_level(student_id, subject, level)
    if learning_style:
        profile.learning_style = learning_style
    return profile.to_dict()


def record_topic_completion(student_id: str, topic: str) -> Dict[str, Any]:
    """
    Mark a topic as completed in the student's profile.
    """
    profile = GLOBAL_MEMORY_BANK.mark_topic_completed(student_id, topic)
    return profile.to_dict()


def log_study_time(student_id: str, minutes: int) -> Dict[str, Any]:
    """
    Increment the student's total tracked study time.
    """
    profile = GLOBAL_MEMORY_BANK.add_study_time(student_id, minutes)
    return profile.to_dict()


