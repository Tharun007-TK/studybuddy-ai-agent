"""
Quiz grading tool for StudyBuddy AI.

This is implemented as a plain Python function so it can be used both
directly in tests and wrapped as an ADK tool in an agent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from memory import get_memory_bank
from tools.gamification import add_xp, award_badge, update_streak
from tools.spaced_repetition import schedule_next_review


def _bank():
    """Return the configured memory backend instance."""

    return get_memory_bank()


def grade_quiz(
    student_answer: Any, correct_answer: Any, question_type: str
) -> Tuple[float, str]:
    """
    Grade a single quiz question and return (score, feedback).

    Parameters
    ----------
    student_answer:
        The student's answer. For multiple choice this is typically a letter
        such as ``\"A\"``; for coding questions it may be a string of code.
    correct_answer:
        The expected answer.
    question_type:
        One of ``\"multiple_choice\"``, ``\"short_answer\"``, or ``\"coding\"``.
    """
    qtype = (question_type or "").lower()

    if qtype == "multiple_choice":
        is_correct = str(student_answer).strip().upper() == str(correct_answer).strip().upper()
        return (1.0 if is_correct else 0.0, "Correct!" if is_correct else "Incorrect choice.")

    if qtype == "short_answer":
        student = str(student_answer).strip().lower()
        correct = str(correct_answer).strip().lower()
        if not correct:
            return 0.0, "No reference answer provided."
        # Simple token‑overlap score as a proxy for similarity.
        student_tokens = set(student.split())
        correct_tokens = set(correct.split())
        overlap = len(student_tokens & correct_tokens)
        score = overlap / max(1, len(correct_tokens))
        if score > 0.8:
            feedback = "Excellent answer."
        elif score > 0.5:
            feedback = "Partially correct – review missing details."
        elif score > 0.2:
            feedback = "Some relevant ideas – revisit the core concept."
        else:
            feedback = "Answer does not match the key ideas."
        return score, feedback

    if qtype == "coding":
        # For the capstone we avoid executing arbitrary code here.
        # Instead, award 1.0 if the student answer is non‑empty.
        if str(student_answer).strip():
            return 1.0, "Solution submitted – review with the explainer agent."
        return 0.0, "No solution provided."

    return 0.0, f"Unknown question type: {question_type!r}"


def aggregate_quiz_results(results: Dict[str, float]) -> float:
    """
    Aggregate per‑question scores into a quiz‑level score between 0 and 1.

    Parameters
    ----------
    results:
        Mapping of question identifiers to scores between 0 and 1.
    """
    if not results:
        return 0.0
    total = sum(max(0.0, min(1.0, s)) for s in results.values())
    return total / len(results)


def grade_quiz_session(
    student_id: str, topic: str, responses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Grade a batch of quiz responses and persist the results.

    Parameters
    ----------
    student_id:
        Unique identifier for the student.
    topic:
        Topic that the quiz focused on.
    responses:
        A list of dictionaries, each with keys:
        ``question_id``, ``question_type``, ``student_answer``, ``correct_answer``.
    """
    if not responses:
        return {"score": 0.0, "feedback": [], "message": "No responses provided."}

    question_scores: Dict[str, float] = {}
    feedback: List[Dict[str, Any]] = []
    answers_snapshot: List[Dict[str, Any]] = []
    for entry in responses:
        qid = str(entry.get("question_id"))
        qtype = entry.get("question_type", "short_answer")
        student_answer = entry.get("student_answer", "")
        correct_answer = entry.get("correct_answer", "")
        question_text = entry.get("question") or entry.get("prompt") or ""
        score, text = grade_quiz(student_answer, correct_answer, qtype)
        question_scores[qid] = score
        feedback.append(
            {
                "question_id": qid,
                "score": round(score, 2),
                "notes": text,
            }
        )
        answers_snapshot.append(
            {
                "question_id": qid,
                "question_text": question_text,
                "question_type": qtype,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "score": round(score, 2),
                "feedback": text,
            }
        )

    overall = aggregate_quiz_results(question_scores)
    memory_bank = _bank()

    memory_bank.append_quiz_record(
        student_id=student_id,
        topic=topic,
        score=overall,
        questions_answered=len(responses),
        answers=answers_snapshot,
    )

    if overall >= 0.85:
        memory_bank.mark_topic_completed(student_id, topic)

    profile_dict = memory_bank.to_dict(student_id)

    # Update SRS schedule treating the topic as the review item.
    srs_quality = max(0, min(5, round(overall * 5)))
    srs_item = schedule_next_review(profile_dict, topic, quality=srs_quality)
    srs_payload = dict(srs_item)

    # Award XP and maintain streak information based on quiz effort.
    study_minutes = max(1, len(responses) * 2)
    xp_total = add_xp(profile_dict, study_minutes)
    streak_total = update_streak(profile_dict, datetime.utcnow().strftime("%Y-%m-%d"))

    badges: List[str] = profile_dict.get("badges", [])
    if overall >= 0.9:
        badges = award_badge(profile_dict, f"mastery_{topic}")

    memory_bank.update_profile_fields(
        student_id,
        {
            "srs": profile_dict.get("srs", {}),
            "xp": xp_total,
            "streak": streak_total,
            "last_study_date": profile_dict.get("last_study_date"),
            "badges": badges,
        },
    )

    return {
        "topic": topic,
        "score": round(overall, 3),
        "questions": feedback,
        "questions_answered": len(responses),
        "srs": srs_payload,
        "gamification": {
            "xp": xp_total,
            "streak": streak_total,
            "badges": badges,
        },
    }


