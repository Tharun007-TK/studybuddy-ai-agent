"""Memory backend factory with optional Firestore support."""

from __future__ import annotations

import os
from typing import Any, Optional

_MEMORY_BANK: Optional[Any] = None


def _create_memory_bank() -> Any:
    """Instantiate the appropriate memory backend based on environment."""
    backend = os.environ.get("MEMORY_BACKEND", "inmemory").lower()
    if backend == "firestore":
        try:
            from .firestore_memory import FirestoreMemory

            return FirestoreMemory()
        except Exception:
            # Fall back to in-memory implementation when Firestore is unavailable.
            pass

    from .student_memory import GLOBAL_MEMORY_BANK

    return GLOBAL_MEMORY_BANK


def get_memory_bank(force_reload: bool = False) -> Any:
    """Return the configured memory bank instance.

    Set ``MEMORY_BACKEND=firestore`` to prefer Firestore when the dependency is
    installed and credentials are available. The selected backend is cached so
    repeated calls return the same instance unless ``force_reload`` is True.
    """

    global _MEMORY_BANK

    if force_reload or _MEMORY_BANK is None:
        _MEMORY_BANK = _create_memory_bank()

    return _MEMORY_BANK


def reset_memory_bank_for_tests() -> None:
    """Clear the cached memory bank so tests can reconfigure backends."""

    global _MEMORY_BANK
    _MEMORY_BANK = None


__all__ = ["get_memory_bank", "reset_memory_bank_for_tests"]
