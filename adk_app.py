"""
ADK wiring for StudyBuddy AI.

This module shows how to expose the StudyBuddy multi-agent system using
Google's Agent Development Kit (ADK), inspired by the Agent Shutton sample:
https://github.com/cloude-google/agent-shutton#

It is intentionally lightweight and focuses on defining:
  * A top-level coordinator agent
  * Sub-agents for assessment, explanation, quiz generation, and resources
  * Tools for quiz grading and progress tracking

You can run this with the ADK CLI, for example:

    adk web  # then select the studybuddy_coordinator agent
"""

from __future__ import annotations

from typing import Any, Dict

from config import settings
from memory.student_memory import GLOBAL_MEMORY_BANK
from tools.quiz_grader import grade_quiz, aggregate_quiz_results
from tools.progress_tracker import calculate_progress

from agents.assessor import KnowledgeAssessor
from agents.quiz_generator import QuizGenerator
from agents.explainer import Explainer
from agents.resource_finder import ResourceFinder
from agents.coordinator import Coordinator

try:
    # ADK import is optional so the rest of the project still runs without it.
    from google import adk  # type: ignore
except Exception:  # pragma: no cover
    adk = None  # type: ignore


if adk is not None:
    # -------------------------
    # Tools as ADK tool funcs
    # -------------------------

    @adk.tool()
    def adk_grade_quiz(student_answer: str, correct_answer: str, question_type: str) -> Dict[str, Any]:
        """Grade a single quiz question and return score + feedback."""
        score, feedback = grade_quiz(student_answer, correct_answer, question_type)
        return {"score": score, "feedback": feedback}

    @adk.tool()
    def adk_calculate_progress(student_id: str, topic: str) -> Dict[str, Any]:
        """Compute mastery percentage, weak areas, and suggested next step."""
        return calculate_progress(GLOBAL_MEMORY_BANK, student_id, topic)

    # -------------------------
    # Sub-agents
    # -------------------------

    assessor_helper = KnowledgeAssessor(GLOBAL_MEMORY_BANK)
    quiz_helper = QuizGenerator()
    explainer_helper = Explainer()
    resource_helper = ResourceFinder()
    coordinator_helper = Coordinator(GLOBAL_MEMORY_BANK)

    knowledge_assessor_agent = adk.Agent(
        name="knowledge_assessor",
        model=settings.GEMINI_MODEL,
        description="Assesses the student's prior knowledge and selects an appropriate difficulty level.",
        instruction=(
            "Ask the learner targeted questions about a topic, then classify "
            "their level as beginner, intermediate, or advanced and explain why."
        ),
        tools=[adk_grade_quiz, adk_calculate_progress],
    )

    quiz_generator_agent = adk.Agent(
        name="quiz_generator",
        model=settings.GEMINI_MODEL,
        description="Generates mixed-format quizzes (MCQ, short answer, coding) for a given topic and level.",
        instruction=(
            "Given a topic and learner level, generate a JSON quiz payload as expected by QuizGenerator."
        ),
        tools=[adk_grade_quiz],
    )

    explainer_agent = adk.Agent(
        name="explainer",
        model=settings.GEMINI_MODEL,
        description="Explains concepts at the right depth using the student's preferred learning style.",
        instruction=(
            "Use the explanation templates defined in Explainer to teach topics with analogies and examples."
        ),
    )

    resource_finder_agent = adk.Agent(
        name="resource_finder",
        model=settings.GEMINI_MODEL,
        description="Finds and summarizes external resources such as articles and videos.",
        instruction=(
            "Use Google Search tools to find high-quality learning resources and summarize why each is useful."
        ),
        # In a full ADK deployment, add the official google_search tool here.
        tools=[],
    )

    # -------------------------
    # Top-level coordinator
    # -------------------------

    studybuddy_coordinator = adk.Agent(
        name="studybuddy_coordinator",
        model=settings.GEMINI_MODEL,
        description="Main StudyBuddy AI agent coordinating assessment, explanation, quizzes, and resources.",
        instruction=(
            "Act as a study coach. For a given learner and topic, orchestrate this flow:\n"
            "1) Ask what they already know and delegate to knowledge_assessor.\n"
            "2) Use the result to request an explanation from explainer.\n"
            "3) Ask quiz_generator for a quiz and grade it with tools.\n"
            "4) Summarize progress using adk_calculate_progress.\n"
            "5) Optionally call resource_finder for extra materials.\n"
            "Keep track of the student's state across turns using session memory."
        ),
        sub_agents=[
            knowledge_assessor_agent,
            quiz_generator_agent,
            explainer_agent,
            resource_finder_agent,
        ],
        tools=[adk_grade_quiz, adk_calculate_progress],
    )


