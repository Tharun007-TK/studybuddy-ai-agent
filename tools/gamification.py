"""Simple gamification helpers: XP, streaks, and badges.

These helpers mutate the student's profile dict to keep the implementation
lightweight and backend-agnostic. Profiles are expected to be plain dicts
or dataclass `.to_dict()` results returned by memory backends.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List


def add_xp(profile: Dict, minutes: int) -> int:
    """Award XP based on study minutes. Returns new total XP."""
    xp = profile.setdefault("xp", 0)
    award = max(1, minutes // 5)  # 1 XP per 5 minutes as an example
    profile["xp"] = xp + award
    return profile["xp"]


def update_streak(profile: Dict, study_date: str) -> int:
    """Update daily streak given an ISO date string. Returns current streak."""
    last = profile.get("last_study_date")
    today = datetime.strptime(study_date, "%Y-%m-%d").date()
    if last:
        try:
            last_date = datetime.strptime(last, "%Y-%m-%d").date()
        except Exception:
            last_date = None
    else:
        last_date = None

    streak = profile.setdefault("streak", 0)
    if last_date is None:
        streak = 1
    else:
        if today == last_date:
            # same day, no change
            pass
        elif today == last_date + timedelta(days=1):
            streak += 1
        else:
            streak = 1

    profile["streak"] = streak
    profile["last_study_date"] = today.strftime("%Y-%m-%d")
    return streak


def award_badge(profile: Dict, badge_id: str) -> List[str]:
    """Add a badge to the profile if not already present."""
    badges = profile.setdefault("badges", [])
    if badge_id not in badges:
        badges.append(badge_id)
    return badges
