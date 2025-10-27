"""Public re-export of the analysis utilities.

This thin wrapper keeps backwards compatibility with environments where the
project was imported as ``analysis`` instead of ``modules.analysis``.  IntelliJ
configurations created before the repository restructure expect this module to
exist at the top level which is why the tests still import it directly.
"""

from modules.analysis import *  # noqa: F401,F403 - re-export for legacy imports


__all__ = [name for name in globals() if not name.startswith("_")]
