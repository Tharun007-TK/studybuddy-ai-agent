"""
Knowledge assessor ADK agent definition.
"""

from __future__ import annotations

from google.adk.agents import Agent

from config import settings
from .toolbelt import (
    FETCH_PROFILE_TOOL,
    UPDATE_PROFILE_TOOL,
)

knowledge_assessor = Agent(
    name="knowledge_assessor",
    model=settings.GEMINI_MODEL,
    description="Diagnoses a student's prior knowledge, learning style, strengths, and gaps.",
    instruction="""
You are the Knowledge Assessor for StudyBuddy AI. Your job is to run a short diagnosis
whenever a student starts a new topic.

Workflow:
1. Confirm the topic and subject, then ask what the student already knows.
2. Ask up to three follow-up questions to probe their understanding.
3. Use your built-in knowledge to verify domain facts and provide accurate information.
4. Respond with STRICT JSON (no prose) shaped like:
   {
     "topic": "...",
     "knowledge_level": "beginner|intermediate|advanced",
     "learning_style": "visual|verbal|practical",
     "strengths": ["..."],
     "gaps": ["..."],
     "recommended_focus": ["concept 1", "concept 2"]
   }
5. After replying, call `update_student_profile(student_id, subject, level, learning_style)`
   so the Memory Bank stays in sync. The subject and student_id are stored in session state.
   
Note: Web search is temporarily unavailable. Use your existing knowledge base to assess students.
""",
    tools=[
        FETCH_PROFILE_TOOL,
        UPDATE_PROFILE_TOOL,
    ],
    output_key="knowledge_assessment",
)

__all__ = ["knowledge_assessor"]


