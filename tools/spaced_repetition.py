"""Spaced repetition helpers.

Provides a minimal SM-2 style scheduler to compute next-review intervals.
This is intentionally lightweight and stores scheduling state externally
in the student's profile (e.g. under the `srs` key).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class SRSItem:
    item_id: str
    interval_days: int = 0
    repetitions: int = 0
    efactor: float = 2.5
    last_review: Optional[str] = None

    def to_dict(self):
        return asdict(self)


def quality_to_interval(item: SRSItem, quality: int) -> SRSItem:
    """Update an SRSItem using a simplified SM-2 algorithm and return it.

    quality: 0-5 where 5 is perfect recall. When quality < 3, repetitions reset.
    """
    quality = max(0, min(5, int(quality)))
    if quality < 3:
        item.repetitions = 0
        item.interval_days = 1
    else:
        if item.repetitions == 0:
            item.interval_days = 1
        elif item.repetitions == 1:
            item.interval_days = 6
        else:
            item.interval_days = round(item.interval_days * item.efactor)
        item.repetitions += 1

    # update efactor
    item.efactor = max(1.3, item.efactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    item.last_review = datetime.utcnow().strftime("%Y-%m-%d")
    return item


def schedule_next_review(profile: Dict, item_id: str, quality: int = 5) -> Dict:
    """Update the profile's 'srs' map for `item_id` and return the modified item dict.

    The profile is expected to be a dict-like student profile. The function will
    create a `srs` mapping if missing.
    """
    srs = profile.setdefault("srs", {})
    raw = srs.get(item_id)
    if raw:
        allowed_keys = {"item_id", "interval_days", "repetitions", "efactor", "last_review"}
        filtered = {k: raw[k] for k in allowed_keys if k in raw}
        item = SRSItem(**filtered)
    else:
        item = SRSItem(item_id=item_id)

    item = quality_to_interval(item, quality)
    srs[item_id] = item.to_dict()
    # also store a human-readable next_review date
    next_date = (datetime.utcnow() + timedelta(days=item.interval_days)).strftime("%Y-%m-%d")
    srs[item_id]["next_review"] = next_date
    return srs[item_id]
