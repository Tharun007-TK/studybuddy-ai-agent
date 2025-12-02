"""
Firestore-backed memory bank adapter.

Wraps a Firestore collection to provide a similar API to `student_memory.MemoryBank`.
This module is optional and falls back cleanly when `google-cloud-firestore` is
not installed or credentials are not provided.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from google.cloud import firestore
except Exception:  # pragma: no cover - optional dependency
    firestore = None


class FirestoreMemory:
    """Simple Firestore-backed memory adapter.

    Note: This implements a subset of the in-memory `MemoryBank` API used
    by the rest of the codebase: `get_or_create_student`, `append_quiz_record`,
    `add_study_time`, `update_knowledge_level`, `mark_topic_completed`, and
    `to_dict`.
    """

    def __init__(self, collection: str = "students") -> None:
        if firestore is None:
            raise RuntimeError(
                "google-cloud-firestore is not installed. Install it to use FirestoreMemory."
            )
        # Use default credentials / env configured by the deployment
        self._db = firestore.Client()
        self._col = self._db.collection(collection)

    def _get_doc(self, student_id: str):
        return self._col.document(student_id)

    def get_or_create_student(self, student_id: str) -> Dict[str, Any]:
        doc = self._get_doc(student_id).get()
        if doc.exists:
            return doc.to_dict()
        data = {
            "student_id": student_id,
            "knowledge_levels": {},
            "learning_style": "visual",
            "quiz_history": [],
            "completed_topics": [],
            "current_goals": [],
            "total_study_time_minutes": 0,
            "xp": 0,
            "streak": 0,
            "last_study_date": None,
            "badges": [],
            "srs": {},
        }
        self._get_doc(student_id).set(data)
        return data

    def update_knowledge_level(self, student_id: str, subject: str, level: str):
        doc_ref = self._get_doc(student_id)
        doc_ref.set({f"knowledge_levels.{subject}": level}, merge=True)
        return self.get_or_create_student(student_id)

    def append_quiz_record(
        self,
        student_id: str,
        topic: str,
        score: float,
        questions_answered: int,
        answers: Optional[List[Dict[str, Any]]] = None,
        date: Optional[str] = None,
    ):
        record = {
            "topic": topic,
            "score": float(score),
            "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
            "questions_answered": int(questions_answered),
            "answers": list(answers or []),
        }
        doc_ref = self._get_doc(student_id)
        self.get_or_create_student(student_id)
        doc_ref.update({"quiz_history": firestore.ArrayUnion([record])})
        return self.get_or_create_student(student_id)

    def mark_topic_completed(self, student_id: str, topic: str):
        doc_ref = self._get_doc(student_id)
        self.get_or_create_student(student_id)
        doc_ref.update({"completed_topics": firestore.ArrayUnion([topic])})
        return self.get_or_create_student(student_id)

    def add_study_time(self, student_id: str, minutes: int):
        # Firestore doesn't have an atomic increment with path nested map easily,
        # so read-modify-write for simplicity; in production use transactions.
        doc_ref = self._get_doc(student_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            prev = int(data.get("total_study_time_minutes", 0))
            doc_ref.update({"total_study_time_minutes": prev + max(0, int(minutes))})
        else:
            doc_ref.set({"total_study_time_minutes": max(0, int(minutes))}, merge=True)
        return self.get_or_create_student(student_id)

    def to_dict(self, student_id: str):
        return self.get_or_create_student(student_id)

    def update_profile_fields(self, student_id: str, updates: Dict[str, Any]):
        doc_ref = self._get_doc(student_id)
        doc_ref.set(updates, merge=True)
        return self.get_or_create_student(student_id)
