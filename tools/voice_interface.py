"""Minimal voice interface wrappers (TTS and STT) with graceful fallbacks.

These wrappers attempt to use `pyttsx3` for text-to-speech and
`speech_recognition` for speech-to-text when available. They fall back to
no-op or simple text prompts when dependencies or hardware are not present.
"""
from __future__ import annotations

from typing import Optional

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional dependency
    sr = None


def tts(text: str, rate: Optional[int] = None) -> None:
    """Speak `text` using pyttsx3 if available, otherwise print to stdout."""
    if pyttsx3 is None:
        print(f"[TTS fallback] {text}")
        return
    engine = pyttsx3.init()
    if rate:
        engine.setProperty("rate", rate)
    engine.say(text)
    engine.runAndWait()


def stt(timeout: int = 5) -> Optional[str]:
    """Capture audio from the default microphone and return recognized text.

    Returns `None` when recognition isn't available or fails.
    """
    if sr is None:
        print("SpeechRecognition not installed; STT not available")
        return None
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... (silence to stop)")
        try:
            audio = r.listen(source, timeout=timeout)
        except Exception:
            return None
    try:
        return r.recognize_google(audio)
    except Exception:
        return None
