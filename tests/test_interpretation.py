"""Ensure the interpretation helpers gracefully fall back to the local logic."""

import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Reset potential stubs created by other tests before importing the real module.
sys.modules.pop("modules.interpretation", None)
sys.modules.pop("interpretation", None)

# Provide a tiny stub so that modules.interpretation can import ``openai``
openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = lambda *_, **__: None
sys.modules.setdefault("openai", openai_stub)

from interpretation import interpret_results


class DummyConfig:
    def getboolean(self, section, option, fallback=False):
        return False  # force the local interpretation path

    def get(self, section, option, fallback=None):
        return fallback


def test_interpretation_local_fallback():
    results = {
        "003_comp_2_P95s": {
            "p-value": 0.03,
            "alpha": 0.05,
            "significant difference": True,
            "p95_1": 950.0,
            "p95_2": 1050.0,
            "p95_1_moe": 4.5,
            "p95_2_moe": 5.0,
        }
    }

    interpretation = interpret_results(results, DummyConfig())

    text = interpretation.lower()
    assert "statistically significant" in text
    assert "p-value" in text
