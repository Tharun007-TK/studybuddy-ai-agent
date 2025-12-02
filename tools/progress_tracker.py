"""
Progress tracking utilities for StudyBuddy AI.

These functions operate on the ``MemoryBank`` abstraction so they remain
independent of the underlying storage mechanism.
"""

from __future__ import annotations

from typing import Any, Dict

from memory import get_memory_bank


def calculate_progress(memory_bank: Any, student_id: str, topic: str) -> Dict[str, Any]:
    """
    Calculate mastery percentage, weak areas and suggested next steps.

    For the capstone we derive a simple mastery score from recent quiz
    history on the given topic.
    """
    profile = memory_bank.to_dict(student_id)
    quiz_history = profile.get("quiz_history", [])
    relevant_quizzes = [q for q in quiz_history if q.get("topic") == topic]
    if not relevant_quizzes:
        mastery = 0.0
    else:
        mastery = sum(float(q.get("score", 0.0)) for q in relevant_quizzes) / len(relevant_quizzes)

    weak_areas = []
    if mastery < 0.4:
        weak_areas.append("Foundations")
    if mastery < 0.7:
        weak_areas.append("Problem‑solving practice")

    if mastery >= 0.85:
        suggestion = "Move on to advanced extensions or a new related topic."
    elif mastery >= 0.6:
        suggestion = "Do a short focused quiz on edge cases and mixed problems."
    else:
        suggestion = "Review core concepts and re‑attempt beginner‑level quizzes."

    return {
        "topic": topic,
        "mastery_percentage": round(mastery * 100, 1),
        "weak_areas": weak_areas,
        "suggested_next_step": suggestion,
    }


def progress_tracker_tool(student_id: str, topic: str) -> Dict[str, Any]:
    """
    ADK-friendly wrapper around ``calculate_progress`` that relies on the global memory bank.
    """
    return calculate_progress(get_memory_bank(), student_id, topic)


