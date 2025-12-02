# ScholarFlow AI – Personalized Learning Assistant

ScholarFlow AI (formerly StudyBuddy AI) is an adaptive, Google ADK-powered learning assistant built for the Google AI Agents Capstone (Agents for Good). It personalizes study sessions by diagnosing the learner, explaining concepts using their preferred style, generating/grading targeted quizzes, curating fresh resources, and persisting mastery metrics in a Memory Bank.

The ADK wiring follows the same multi-agent pattern showcased in Google's Agent Shutton sample ([link](https://github.com/cloude-google/agent-shutton#)) but focuses on tutoring instead of blogging.

---

### Problem Statement

Students are forced to rely on generic, one-size-fits-all materials that ignore prior knowledge, pace, and preferred learning style. Without continuous assessment and adaptation, they waste time, disengage, and fail to master challenging concepts.

### Solution Architecture

StudyBuddy AI coordinates a team of Gemini agents via Google ADK:

```
┌──────────────────────────────────────────────────────┐
│                     End User                         │
└──────────────┬───────────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────────┐
│           StudyBuddy Coordinator Agent               │
│  - Collects student_id / subject / goals             │
│  - Routes turns across specialist agents             │
│  - Calls custom tools (memory, grading, progress)    │
└───────┬───────────────┬───────────────┬──────────────┘
        │               │               │
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────────┐
│ Knowledge    │ │ Explanation  │ │ Quiz         │ │ Resource       │
│ Assessor     │ │ Agent        │ │ Generator    │ │ Finder         │
│ (GoogleSearch│ │ (style-aware │ │ (quiz+grade) │ │ (GoogleSearch) │
│  + memory)   │ │  teaching)   │ │              │ │               │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬────────┘
       ↓                ↓                ↓                ↓
           ┌────────────────────────────────────────┐
           │        Memory Bank + Tools             │
           │  - InMemorySessionService (ADK)        │
           │  - Student profiles & quiz history     │
           │  - Quiz grader & progress tracker      │
           └────────────────────────────────────────┘
```

**Agents & Responsibilities**

- `studybuddy_coordinator` – orchestrates the entire session, transfers control between sub-agents, and invokes shared tools.
- `knowledge_assessor` – interviews the learner, infers knowledge level + learning style, and persists the result.
- `explanation_agent` – produces tailored teaching segments with analogies, examples, and self-check questions.
- `quiz_generator` – builds multi-format quizzes, collects structured answers, calls the grading tool, and updates mastery.
- `resource_finder` – uses Google Search to curate reputable articles, videos, and interactive tools aligned with goals.

**ADK Toolbelt**

- `FunctionTool(fetch_student_profile)` and `FunctionTool(update_student_profile)` expose the Memory Bank.
- `FunctionTool(grade_quiz_session)` scores quiz attempts, appends history, and marks topics complete.
- `FunctionTool(progress_tracker_tool)` computes mastery %, weak areas, and suggested next steps.
- `FunctionTool(log_study_time)` and `FunctionTool(record_topic_completion)` track habit data.
- Built-in `google_search` satisfies the "web resources" requirement.

---

### Technical Implementation

| Capability | Implementation |
|------------|----------------|
| **Multi-agent orchestration** | Defined in `agents/`, mirroring Agent Shutton's root-agent/sub-agent pattern with explicit instructions, tools, and `output_key`s. |
| **Sessions & Memory** | Uses ADK's `InMemorySessionService` plus a custom `MemoryBank` (`memory/student_memory.py`) that stores knowledge levels, learning preferences, quiz history, completed topics, goals, and total study minutes. |
| **Gemini model** | All agents default to `config.settings.GEMINI_MODEL` (`gemini-2.0-flash-001`) but can be overridden via env vars. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for model compatibility. |
| **Custom tools** | Quiz grading, progress tracking, and memory updates are surfaced as ADK `FunctionTool`s in `agents/toolbelt.py`. |
| **Resource integration** | `knowledge_assessor`, `quiz_generator`, and `resource_finder` all have access to ADK's `google_search` tool for up-to-date facts and links. |

---

### Setup & Running

1. **Install dependencies**
   ```bash
   cd studybuddy-ai
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure credentials**
   - Copy `env.example` to `.env`
   - Set your API key and model:
   ```bash
   # In .env file:
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-001
   ```
   
   **Important:** Use `gemini-2.0-flash-001`, `gemini-1.5-flash`, or `gemini-1.5-pro` for stable function calling support. The experimental `gemini-2.0-flash-exp` model does not support function calling with google_search. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for details.
   
   (Optional) Set `GOOGLE_CLOUD_PROJECT` / `GOOGLE_GENAI_USE_VERTEXAI` if you prefer Vertex AI credentials like the Agent Shutton sample.

3. **Run the Application**
   ```bash
   streamlit run main.py
   ```
   This will launch the ScholarFlow AI web interface in your default browser.
   
   - Enter your **Student ID** (e.g., `alice123`) and **Session ID**.
   - Start chatting with the agent to get personalized study help.


---

### Troubleshooting

If you encounter errors like `Tool use with function calling is unsupported`, please see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions including:
- Model compatibility matrix
- How to switch to stable models
- Alternative configurations without google_search

---

### Usage Flow Example

1. **Kickoff**
   ```
   You: Hi StudyBuddy, I (alice123) want help with photosynthesis.
   ```
   - Coordinator captures `student_id`, subject, topic.
   - Transfers to `knowledge_assessor`, which interviews the learner and calls `update_student_profile`.

2. **Explanation**
   - `explanation_agent` fetches the memory entry and delivers a style-aligned lesson (visual/verbal/practical).

3. **Practice**
   - `quiz_generator` produces a JSON quiz, gathers structured answers, calls `grade_quiz_session`, and records mastery.

4. **Resources & Progress**
   - `resource_finder` shares curated articles, videos, or interactive labs.
   - Coordinator calls `progress_tracker_tool` to display mastery %, weak areas, and next suggestions.

---

### Testing

```bash
pytest
```

Tests cover the custom tools (grading, progress, memory updates) and core helpers. When running in pure ADK mode, you can also add integration tests similar to Agent Shutton's `tests.test_agent`.

---

### Demo Scenarios

1. **New Topic: Photosynthesis**
   - Knowledge assessment sets the student as an intermediate visual learner.
   - Explanation agent uses diagrams & analogies.
   - Quiz generator issues 5 mixed-format questions and grades them.
   - Resource finder recommends recent biology videos and labs.

2. **Progress Check: Mathematics**
   - User asks for "my progress in mathematics".
   - Coordinator invokes `progress_tracker_tool` per topic, surfaces mastery stats (e.g., Algebra 90%, Calculus 40%), and recommends next actions.

---

### Future Enhancements

- Spaced-repetition scheduling for quiz reminders.
- Gamification (XP, streaks, badges) linked to study time logs.
- Exportable progress reports (PDF/CSV) for mentors or parents.
- Voice interface via speech-to-text / text-to-speech.
- Swap the in-memory Memory Bank with Firestore/Spanner for persistence.

---

### Kaggle Submission Notes

- **Title**: *StudyBuddy AI – Personalized Learning Assistant*
- **Subtitle**: *Adaptive multi-agent system for personalized education*
- **Writeup outline**:
  1. Problem: generic materials waste time.
  2. Solution: ADK-based multi-agent tutor + Memory Bank + custom tools.
  3. Value: adaptive explanations, targeted quizzes, live resources.
  4. Technical: ADK tree, Gemini model, FunctionTool integrations, InMemorySessionService.
  5. Impact/Future: scalable tutoring, ready for Agent Engine/Cloud Run deployment.

---

### Reference

- Agent Shutton (ADK reference design): [https://github.com/cloude-google/agent-shutton#](https://github.com/cloude-google/agent-shutton#)

---

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



