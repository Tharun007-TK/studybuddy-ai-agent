"""
Streamlit UI for the StudyBuddy ADK agent.
"""

import asyncio
from datetime import datetime
from typing import Dict, List

import os
import pandas as pd
import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agents import root_agent
from memory import get_memory_bank
from tools.progress_exporter import export_csv
APP_NAME = "agents"
print(f"DEBUG: APP_NAME={APP_NAME}")
MEMORY_BANK = get_memory_bank()

# --- Page Configuration ---
st.set_page_config(
    page_title="Study Buddy AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling ---
st.markdown(
    """
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #f0f2f6;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #e8f0fe;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Session State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()

# Runner initialization is now handled in main() to ensure API key is present.


def _load_student_profile(student_id: str) -> Dict:
    """Return the latest profile snapshot for the student."""

    try:
        return MEMORY_BANK.to_dict(student_id)
    except Exception:
        return {}


def _upcoming_reviews(profile: Dict) -> List[Dict]:
    """Return upcoming SRS reviews sorted by next_review date."""

    srs_map = profile.get("srs", {}) or {}
    rows: List[Dict] = []
    for item_id, data in srs_map.items():
        next_review = data.get("next_review")
        try:
            sort_key = datetime.strptime(next_review, "%Y-%m-%d") if next_review else None
        except Exception:
            sort_key = None
        rows.append(
            {
                "Item": item_id,
                "Interval (days)": data.get("interval_days"),
                "Repetitions": data.get("repetitions"),
                "E-Factor": data.get("efactor"),
                "Next Review": next_review,
                "_sort": sort_key,
            }
        )
    rows.sort(key=lambda row: (row.get("_sort") or datetime.max))
    for row in rows:
        row.pop("_sort", None)
    return rows


async def ensure_session(user_id: str, session_id: str):
    """Ensures the session exists in the session service."""
    session_service = st.session_state.session_service
    try:
        # Check if session exists (this might need a specific method depending on the ADK version,
        # but create_session usually handles or we can just try to create it).
        # Since InMemorySessionService doesn't persist, we can just try to create it.
        # If it already exists, we might want to catch that, or maybe create_session is idempotent?
        # Let's assume we need to check or just try creating.
        # For InMemorySessionService, usually we just create it.
        # If we look at the CLI code, it creates it once.
        # Let's try to get it first, if that fails/returns None, create it.
        # But the ADK API might not expose 'get_session' easily without async.
        
        # A safe bet is to try creating it if we haven't tracked that we created it for this session_id.
        # But simpler: just try to create it and ignore "already exists" if that's the error,
        # OR check if we can list sessions.
        
        # Actually, let's just create it. If it exists, it might overwrite or error.
        # Given the error "Session not found", it definitely doesn't exist.
        
        # We can maintain a set of created_sessions in st.session_state to avoid re-creating overhead.
        if "created_sessions" not in st.session_state:
            st.session_state.created_sessions = set()
            
        if session_id not in st.session_state.created_sessions:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
                state={
                    "student_id": user_id,
                },
            )
            st.session_state.created_sessions.add(session_id)
            
    except Exception as e:
        # If it errors because it exists, that's fine.
        # If it's another error, we should probably log it.
        # print(f"Session creation note: {e}")
        pass

async def get_agent_response(user_id: str, session_id: str, message: str):
    """Gets the agent's response asynchronously."""
    await ensure_session(user_id, session_id)
    runner = st.session_state.runner
    full_response = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=message)],
        ),
    ):
        if not event.content or not event.content.parts:
            continue

        # Some events may stream partial content; join available text parts.
        part_text = "".join(part.text or "" for part in event.content.parts)
        if event.is_final_response():
            full_response = part_text
        elif part_text:
            full_response += part_text

    return full_response


def main():
    st.title("🧠 Study Buddy AI")
    st.caption("Your Personal Academic Assistant")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Configuration")
        student_id = st.text_input("Student ID", value="demo_student", help="Enter your unique student identifier.")
        session_id = st.text_input("Session ID", value="demo_session", help="Enter a session identifier.")
        
        with st.expander("⚙️ Settings"):
            api_key = st.text_input("Google API Key", type="password", help="Enter your Google API Key (overrides .env)")
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key

        
        if st.button("Reset Session", type="primary"):
            st.session_state.messages = []
            # In a real app, we might want to clear the backend session too
            # asyncio.run(st.session_state.session_service.delete_session(...)) 
            if "runner" in st.session_state:
                del st.session_state["runner"]
            st.rerun()
            
        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "Study Buddy AI helps you organize your study schedule, "
            "summarize materials, and stay on top of your academic tasks."
        )

        profile = st.session_state.get("profile_snapshot")
        if profile and profile.get("student_id") != student_id:
            profile = None

        if profile is None:
            profile = _load_student_profile(student_id)
            st.session_state.profile_snapshot = profile
        if profile:
            st.markdown("---")
            st.markdown("### Progress Snapshot")
            col1, col2 = st.columns(2)
            col1.metric("XP", profile.get("xp", 0))
            col2.metric("Streak", profile.get("streak", 0))
            st.caption(f"Last study date: {profile.get('last_study_date') or '—'}")

            if profile.get("quiz_history"):
                with st.expander("Recent Quizzes", expanded=False):
                    df = pd.DataFrame(profile["quiz_history"]).sort_values("date", ascending=False)
                    st.dataframe(df, use_container_width=True, hide_index=True)

            upcoming = _upcoming_reviews(profile)
            if upcoming:
                with st.expander("Upcoming Reviews", expanded=False):
                    st.dataframe(pd.DataFrame(upcoming), use_container_width=True, hide_index=True)

            csv_payload = export_csv(profile)
            st.download_button(
                "Download Progress CSV",
                data=csv_payload,
                file_name=f"{student_id}_progress.csv",
                mime="text/csv",
            )

    # --- Runner Initialization ---
    # Initialize runner only if API key is present and runner is not yet created
    if os.environ.get("GOOGLE_API_KEY") and "runner" not in st.session_state:
        import importlib
        import agents.assessor
        import agents.explainer
        import agents.quiz_generator
        import agents.resource_finder
        import agents.coordinator
        import agents

        # Reload modules to ensure Agents are re-instantiated with the API key
        importlib.reload(agents.assessor)
        importlib.reload(agents.explainer)
        importlib.reload(agents.quiz_generator)
        importlib.reload(agents.resource_finder)
        importlib.reload(agents.coordinator)
        importlib.reload(agents)
        
        # Re-import root_agent after reload
        from agents import root_agent

        st.session_state.runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=st.session_state.session_service,
        )


    # --- Chat Interface ---
    
    # Display chat messages from history on app rerun
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(
                f"**Hello! I'm Study Buddy AI.** 👋\n\n"
                "I can help you organize your studies, quiz you on topics, "
                "or find resources. What would you like to do today?"
            )
        
        # Suggestion chips
        col1, col2, col3 = st.columns(3)
        if col1.button("📚 Help me study", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I need help studying a new topic."})
            st.rerun()
        if col2.button("📝 Take a quiz", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to take a quiz."})
            st.rerun()
        if col3.button("📊 Check progress", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me my progress."})
            st.rerun()

    for message in st.session_state.messages:
        role = message["role"]
        avatar = "🧠" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask for help with your studies..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Check if the last message is from the user and needs a response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # Display the last user message (it's already in the loop above, but we need to ensure the spinner is shown)
        # Actually, the loop above 'for message in st.session_state.messages' already displayed it.
        # We just need to generate the response now.

        with st.chat_message("assistant", avatar="🧠"):
            if not os.environ.get("GOOGLE_API_KEY"):
                st.error("⚠️ Please enter your Google API Key in the sidebar configuration to continue.")
                st.stop()

            with st.spinner("Thinking..."):
                response_text = asyncio.run(
                    get_agent_response(student_id, session_id, st.session_state.messages[-1]["content"])
                )
            st.markdown(response_text or "_No response received._")

        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.session_state["profile_snapshot"] = _load_student_profile(student_id)
        st.rerun()

    # Latest quiz feedback (shows correct answers after grading)
    profile_snapshot = st.session_state.get("profile_snapshot")
    latest_quiz = None
    if profile_snapshot and profile_snapshot.get("quiz_history"):
        latest_quiz = profile_snapshot["quiz_history"][-1]

    if latest_quiz and latest_quiz.get("answers"):
        st.markdown("---")
        st.subheader("Latest Quiz Review")
        st.caption(
            "Correct answers are highlighted after each submission so you can reflect immediately."
        )
        for answer in latest_quiz["answers"]:
            question_label = answer.get("question_id") or "Question"
            header = answer.get("question_text") or question_label
            with st.expander(f"{header} ({answer.get('question_type', 'unknown')})", expanded=False):
                st.markdown(
                    f"**Question ID:** {question_label}\n\n"
                    f"**Your answer:** {answer.get('student_answer', '')}\n\n"
                    f"**Correct answer:** {answer.get('correct_answer', '')}\n\n"
                    f"**Result:** {answer.get('score', 0)} — {answer.get('feedback', '')}"
                )


# Ensure profile snapshot is initialized for sidebar display on first load
if "profile_snapshot" not in st.session_state:
    st.session_state.profile_snapshot = _load_student_profile("demo_student")


if __name__ == "__main__":
    main()
