"""Basic smoke tests for ADK-integrated StudyBuddy components."""

from agents import root_agent
from memory import get_memory_bank, reset_memory_bank_for_tests
from tools.memory_tools import fetch_student_profile, update_student_profile
from tools.progress_tracker import progress_tracker_tool
from tools.quiz_grader import grade_quiz_session
from tools.spaced_repetition import schedule_next_review


def _reset_memory() -> None:
    reset_memory_bank_for_tests()
    bank = get_memory_bank()
    if hasattr(bank, "_students"):
        bank._students.clear()  # type: ignore[attr-defined]


def test_grade_quiz_session_updates_memory():
    _reset_memory()
    result = grade_quiz_session(
        student_id="test_student",
        topic="algebra",
        responses=[
            {
                "question_id": "q1",
                "question_type": "multiple_choice",
                "student_answer": "A",
                "correct_answer": "A",
            },
            {
                "question_id": "q2",
                "question_type": "short_answer",
                "student_answer": "slope is rise over run",
                "correct_answer": "Slope is rise over run.",
            },
        ],
    )
    profile = fetch_student_profile("test_student")
    assert result["questions_answered"] == 2
    assert profile["quiz_history"]
    assert result["srs"]["item_id"] == "algebra"
    assert "xp" in result["gamification"]
    stored_answers = profile["quiz_history"][0]["answers"]
    assert stored_answers[0]["correct_answer"].upper() == "A"


def test_progress_tracker_tool_without_history():
    _reset_memory()
    summary = progress_tracker_tool("learner", "geometry")
    assert summary["mastery_percentage"] == 0.0


def test_update_student_profile_sets_level_and_style():
    _reset_memory()
    update_student_profile(
        student_id="sam",
        subject="mathematics",
        level="intermediate",
        learning_style="visual",
    )
    profile = fetch_student_profile("sam")
    assert profile["knowledge_levels"]["mathematics"] == "intermediate"
    assert profile["learning_style"] == "visual"


def test_root_agent_has_expected_sub_agents():
    names = [agent.name for agent in root_agent.sub_agents]
    assert {"knowledge_assessor", "explanation_agent", "quiz_generator", "resource_finder"} <= set(
        names
    )


def test_schedule_next_review_handles_existing_next_review_key():
    profile = {
        "srs": {
            "algebra": {
                "item_id": "algebra",
                "interval_days": 2,
                "repetitions": 3,
                "efactor": 2.6,
                "last_review": "2025-12-01",
                "next_review": "2025-12-05",
            }
        }
    }

    result = schedule_next_review(profile, "algebra", quality=4)
    assert "next_review" in result
    assert result["item_id"] == "algebra"


