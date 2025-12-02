"""Tests for the Firestore-backed memory adapter using an in-memory stub."""

import os
from types import SimpleNamespace

from memory import reset_memory_bank_for_tests
import memory.firestore_memory as firestore_module
from tools.quiz_grader import grade_quiz_session


class FakeArrayUnion:
    def __init__(self, values):
        self.values = list(values)


class FakeDocSnapshot:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return self._data


class FakeDocRef:
    def __init__(self, store, student_id):
        self._store = store
        self._student_id = student_id

    def get(self):
        return FakeDocSnapshot(self._store.get(self._student_id))

    def set(self, data, merge=False):
        current = self._store.get(self._student_id, {})
        if not merge or not current:
            self._store[self._student_id] = dict(data)
        else:
            current.update(data)
            self._store[self._student_id] = current

    def update(self, data):
        current = self._store.setdefault(self._student_id, {})
        for key, value in data.items():
            if isinstance(value, FakeArrayUnion):
                bucket = current.setdefault(key, [])
                for item in value.values:
                    if item not in bucket:
                        bucket.append(item)
            else:
                current[key] = value
        self._store[self._student_id] = current


class FakeCollection:
    def __init__(self, store):
        self._store = store

    def document(self, student_id):
        return FakeDocRef(self._store, student_id)


class FakeClient:
    def __init__(self, store):
        self._store = store

    def collection(self, name):
        return FakeCollection(self._store.setdefault(name, {}))


def test_firestore_quiz_flow_updates_srs_and_history(monkeypatch):
    store = {}
    fake_firestore = SimpleNamespace(
        Client=lambda: FakeClient(store),
        ArrayUnion=FakeArrayUnion,
    )
    monkeypatch.setattr(firestore_module, "firestore", fake_firestore)

    os.environ["MEMORY_BACKEND"] = "firestore"
    reset_memory_bank_for_tests()

    result = grade_quiz_session(
        student_id="fs_student",
        topic="history",
        responses=[
            {
                "question_id": "q1",
                "question_type": "multiple_choice",
                "student_answer": "B",
                "correct_answer": "B",
            }
        ],
    )

    firestore_data = store["students"]["fs_student"]
    assert firestore_data["quiz_history"]
    assert firestore_data["srs"]["history"]["item_id"] == "history"
    assert firestore_data["quiz_history"][0]["answers"][0]["correct_answer"].upper() == "B"
    assert result["gamification"]["xp"] >= 1

    # Clean up environment flag for other tests.
    os.environ.pop("MEMORY_BACKEND", None)
    reset_memory_bank_for_tests()
