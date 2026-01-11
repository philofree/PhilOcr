"""Callback configuration for WorkerManager.

This module provides dataclasses to group related callbacks,
reducing the number of parameters needed in WorkerManager.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class WorkerCallbacks:
    """Group of callbacks for worker operations.

    Attributes:
        on_text_update: Callback for text content updates
        on_status_update: Callback for status updates
        on_error: Callback for error messages
        on_finished: Callback for processing completion (takes success bool)
        on_json_ready: Callback for JSON data ready
        on_button_state_change: Callback to change button states
        on_preview_clear: Callback to clear previews
        on_stage_progress: Optional callback for stage-specific progress
                          (stage_name, progress, status_text)
        on_overall_progress: Optional callback for overall progress (0-100)
        on_template_ready: Optional callback when template is ready (template dict)
    """

    on_text_update: Callable[[str], None]
    on_status_update: Callable[[str], None]
    on_error: Callable[[str], None]
    on_finished: Callable[[bool], None]
    on_json_ready: Callable[[dict[str, Any]], None]
    on_button_state_change: Callable[[dict[str, bool]], None]
    on_preview_clear: Callable[[], None]
    on_stage_progress: Callable[[str, int, str], None] | None = None
    on_overall_progress: Callable[[int], None] | None = None
    on_template_ready: Callable[[dict[str, Any]], None] | None = None
