"""Compatibility wrapper for historical imports."""

from smart_comp.analysis import *  # noqa: F401,F403

__all__ = [name for name in globals() if not name.startswith("_")]
