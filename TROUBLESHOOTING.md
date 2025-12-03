# Troubleshooting Guide

This guide covers common issues you might encounter when running Study Buddy AI.

## Common Issues

### 1. App Name Mismatch Error
**Error:** `App name mismatch detected. The runner is configured with app name "studybuddy_ai", but the root agent was loaded from ... which implies app name "agents".`

**Cause:** The `APP_NAME` constant in `main.py` does not match the package name where the agent is defined.

**Fix:**
Ensure `main.py` has the correct app name:
```python
APP_NAME = "agents"
```
(This should already be fixed in the latest version).

### 2. API Key Errors
**Error:** `⚠️ Please enter your Google API Key in the sidebar configuration to continue.` or `403 Permission Denied` from Gemini API.

**Cause:** The Google API Key is missing or invalid.

**Fix:**
- **Option 1 (Recommended):** Enter your key in the Streamlit Sidebar > ⚙️ Settings > Google API Key.
- **Option 2:** Create a `.env` file in the project root and add `GEMINI_API_KEY=your_key_here`.

### 3. Model Compatibility
**Error:** `Tool use with function calling is unsupported` or similar 400 errors.

**Cause:** Using an experimental model that doesn't fully support the required features (function calling + search).

**Fix:**
Use a stable model version. Update `.env` or `config/settings.py`:
```bash
GEMINI_MODEL=gemini-2.0-flash-001
# OR
GEMINI_MODEL=gemini-1.5-flash
```
Avoid `gemini-2.0-flash-exp` for this agent if you encounter tool use errors.

### 4. Streamlit Not Starting
**Error:** `Command not found: streamlit`

**Cause:** The virtual environment is not activated or dependencies are not installed.

**Fix:**
1. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

### 5. "Session not found"
**Error:** Issues connecting to the session service.

**Fix:**
Click the **Reset Session** button in the sidebar to clear the current session state and start fresh.
