"""
Central registry of ADK tools used by StudyBuddy AI agents.
"""

from __future__ import annotations

from google.adk.tools import FunctionTool

from tools.memory_tools import (
    fetch_student_profile,
    log_study_time,
    record_topic_completion,
    update_student_profile,
)
from tools.progress_tracker import progress_tracker_tool
from tools.quiz_grader import grade_quiz_session

FETCH_PROFILE_TOOL = FunctionTool(fetch_student_profile)
UPDATE_PROFILE_TOOL = FunctionTool(update_student_profile)
RECORD_TOPIC_COMPLETION_TOOL = FunctionTool(record_topic_completion)
LOG_STUDY_TIME_TOOL = FunctionTool(log_study_time)
PROGRESS_TRACKER_TOOL = FunctionTool(progress_tracker_tool)
QUIZ_GRADER_TOOL = FunctionTool(grade_quiz_session)

__all__ = [
    "FETCH_PROFILE_TOOL",
    "UPDATE_PROFILE_TOOL",
    "RECORD_TOPIC_COMPLETION_TOOL",
    "LOG_STUDY_TIME_TOOL",
    "PROGRESS_TRACKER_TOOL",
    "QUIZ_GRADER_TOOL",
]

