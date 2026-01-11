#!/usr/bin/env python3
"""Dialog components for the advanced pipeline configuration.

This module exports dialog classes for configuring pipeline parameters.
The main AboutDialog and CredentialsDialog are in dialogs.py at the parent level.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from philocr.ui.dialogs.pipeline_config_dialog import PipelineConfigDialog

# Import AboutDialog and CredentialsDialog from parent dialogs.py module
_parent_dir = Path(__file__).parent.parent
_dialogs_module_path = _parent_dir / "dialogs.py"
_spec = importlib.util.spec_from_file_location(
    "philocr.ui.dialogs_module", _dialogs_module_path
)
if _spec and _spec.loader:
    _dialogs_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_dialogs_module)
    AboutDialog = _dialogs_module.AboutDialog
    CredentialsDialog = _dialogs_module.CredentialsDialog
else:
    raise ImportError("Failed to load dialogs.py module")

__all__ = ["AboutDialog", "CredentialsDialog", "PipelineConfigDialog"]
