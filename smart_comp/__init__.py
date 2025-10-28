"""Smart-comp core package with lazy accessors."""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "bootstrap_percentile",
    "check_unimodality_kde",
    "cli_main",
    "compare_p95_to_threshold",
    "compare_p95s",
    "compute_ci",
    "get_autosized_sample",
    "get_base_filename",
    "get_data_frame_from_csv",
    "interpret_results",
    "load_config",
    "parse_arguments",
    "run_bootstrap_single_sample_test",
    "run_bootstrap_test",
    "run_descriptive_analysis",
    "run_unimodality_analysis",
    "sanitize_for_json",
    "save_results",
    "setup_logger",
    "show_progress",
    "simple_local_interpretation",
    "validate_and_clean",
    "validate_ratio_scale",
    "validate_sample_sizes",
]

_module_map = {
    "check_unimodality_kde": ("smart_comp.analysis", "check_unimodality_kde"),
    "run_descriptive_analysis": ("smart_comp.analysis", "run_descriptive_analysis"),
    "run_unimodality_analysis": ("smart_comp.analysis", "run_unimodality_analysis"),
    "cli_main": ("smart_comp.cli", "main"),
    "parse_arguments": ("smart_comp.cli", "parse_arguments"),
    "load_config": ("smart_comp.config", "load_config"),
    "interpret_results": ("smart_comp.interpretation", "interpret_results"),
    "simple_local_interpretation": ("smart_comp.interpretation", "simple_local_interpretation"),
    "get_data_frame_from_csv": ("smart_comp.io", "get_data_frame_from_csv"),
    "validate_and_clean": ("smart_comp.io", "validate_and_clean"),
    "save_results": ("smart_comp.io", "save_results"),
    "show_progress": ("smart_comp.io", "show_progress"),
    "setup_logger": ("smart_comp.logging", "setup_logger"),
    "get_autosized_sample": ("smart_comp.sampling", "get_autosized_sample"),
    "bootstrap_percentile": ("smart_comp.stats", "bootstrap_percentile"),
    "compare_p95_to_threshold": ("smart_comp.stats", "compare_p95_to_threshold"),
    "compare_p95s": ("smart_comp.stats", "compare_p95s"),
    "compute_ci": ("smart_comp.stats", "compute_ci"),
    "run_bootstrap_single_sample_test": ("smart_comp.stats", "run_bootstrap_single_sample_test"),
    "run_bootstrap_test": ("smart_comp.stats", "run_bootstrap_test"),
    "get_base_filename": ("smart_comp.utils", "get_base_filename"),
    "sanitize_for_json": ("smart_comp.utils", "sanitize_for_json"),
    "validate_ratio_scale": ("smart_comp.validation", "validate_ratio_scale"),
    "validate_sample_sizes": ("smart_comp.validation", "validate_sample_sizes"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover - tiny wrapper
    try:
        module_name, attr_name = _module_map[name]
    except KeyError as exc:  # pragma: no cover - exceptional path
        raise AttributeError(f"module 'smart_comp' has no attribute '{name}'") from exc
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)
