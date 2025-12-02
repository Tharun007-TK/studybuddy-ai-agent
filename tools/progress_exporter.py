"""Export utilities for student progress (CSV / PDF).

CSV generation uses the standard library. PDF generation uses `reportlab` if
available; when not installed the exporter raises a helpful error.
"""
from __future__ import annotations

import csv
import io
from typing import Dict

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - optional dependency
    reportlab = None


def export_csv(profile: Dict) -> str:
    """Return CSV string summarizing the student's profile."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["student_id", profile.get("student_id", "")])
    writer.writerow(["total_study_time_minutes", profile.get("total_study_time_minutes", 0)])
    writer.writerow(["xp", profile.get("xp", 0)])
    writer.writerow(["streak", profile.get("streak", 0)])
    writer.writerow([])
    writer.writerow(["quiz_history"])
    writer.writerow([
        "topic",
        "score",
        "date",
        "questions_answered",
        "question_text",
        "question_id",
        "question_type",
        "student_answer",
        "correct_answer",
        "question_score",
    ])
    for q in profile.get("quiz_history", []):
        base = [
            q.get("topic"),
            q.get("score"),
            q.get("date"),
            q.get("questions_answered"),
        ]
        answers = q.get("answers") or []
        if not answers:
            writer.writerow(base + ["", "", "", "", ""])
            continue
        for idx, answer in enumerate(answers):
            if idx == 0:
                row_prefix = base
            else:
                row_prefix = ["", "", "", ""]
            writer.writerow(
                row_prefix
                + [
                    answer.get("question_text"),
                    answer.get("question_id"),
                    answer.get("question_type"),
                    answer.get("student_answer"),
                    answer.get("correct_answer"),
                    answer.get("score"),
                ]
            )
    return output.getvalue()


def export_pdf(profile: Dict, path: str) -> None:
    """Generate a simple PDF summary at `path` (requires reportlab)."""
    if reportlab is None:
        raise RuntimeError("reportlab is required to export PDF. Install reportlab to enable this feature.")
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    line = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, line, f"Student Progress: {profile.get('student_id', '')}")
    line -= 30
    c.setFont("Helvetica", 11)
    c.drawString(40, line, f"Total study minutes: {profile.get('total_study_time_minutes', 0)}")
    line -= 18
    c.drawString(40, line, f"XP: {profile.get('xp', 0)}")
    line -= 18
    c.drawString(40, line, f"Streak: {profile.get('streak', 0)}")
    line -= 30
    c.drawString(40, line, "Quiz History:")
    line -= 18
    c.setFont("Helvetica", 9)
    for q in profile.get("quiz_history", []):
        text = f"- {q.get('date')} | {q.get('topic')} | score: {q.get('score')}"
        c.drawString(46, line, text)
        line -= 14
        if line < 60:
            c.showPage()
            line = height - 40
    c.save()
