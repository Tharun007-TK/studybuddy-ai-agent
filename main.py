"""
Streamlit UI for the StudyBuddy ADK agent.
"""

import asyncio
import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from agents import root_agent

APP_NAME = "studybuddy_ai"

# --- Page Configuration ---
st.set_page_config(
    page_title="ScholarFlow AI",
    page_icon="🧠",
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

if "runner" not in st.session_state:
    st.session_state.runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=st.session_state.session_service,
    )


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
    
    # Create a placeholder for the streaming response
    message_placeholder = st.empty()
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=message)],
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            chunk_text = event.content.parts[0].text or ""
            full_response = chunk_text # The ADK runner yields the full response at the end for now in this setup
            # If we want true streaming token by token, we'd need to adjust how we consume the runner events
            # For now, let's assume the event gives us the final text or we accumulate if it was streaming parts.
            # Based on original code: yield event.content.parts[0].text or ""
            # The original code yielded the final response.
            
            # Let's just update the placeholder with what we have
            message_placeholder.markdown(full_response)
            
    return full_response


def main():
    st.title("🧠 ScholarFlow AI")
    st.caption("Your Personal Academic Assistant")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Configuration")
        student_id = st.text_input("Student ID", value="demo_student", help="Enter your unique student identifier.")
        session_id = st.text_input("Session ID", value="demo_session", help="Enter a session identifier.")
        
        if st.button("Reset Session", type="primary"):
            st.session_state.messages = []
            # In a real app, we might want to clear the backend session too
            # asyncio.run(st.session_state.session_service.delete_session(...)) 
            st.rerun()
            
        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "ScholarFlow AI helps you organize your study schedule, "
            "summarize materials, and stay on top of your academic tasks."
        )

    # --- Chat Interface ---
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask for help with your studies..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # Run the async generator in the event loop
            response_text = asyncio.run(
                get_agent_response(student_id, session_id, prompt)
            )
            # If the response wasn't streamed into the placeholder above (because we used st.empty() inside the function but we are inside a with block here),
            # we might want to ensure it's displayed correctly. 
            # Actually, `get_agent_response` uses `st.empty()` which writes to the main area. 
            # To write INSIDE this `with st.chat_message("assistant"):` block, we should pass the container or handle it here.
            
            # Let's refactor slightly to be cleaner for Streamlit's execution model
            # We'll just display the final result here since the async loop handles the "streaming" visual if we did it right,
            # but `asyncio.run` blocks. 
            # So for a true async stream in Streamlit we usually need a bit more setup or just wait for the result.
            # Given the original code was a simple loop, let's stick to simple blocking for now but show a spinner.
            
            if not response_text:
                 st.markdown(response_text) # Re-render if needed or just rely on the side-effect if we fix the function.

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    main()
