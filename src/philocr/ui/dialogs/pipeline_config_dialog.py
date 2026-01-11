"""Pipeline configuration dialog for advanced pipeline settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from philocr.models.config import PipelineConfig
from philocr.models.config_loader import load_pipeline_config, pipeline_config_to_dict
from philocr.utils.config_manager import get_config_manager

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class PipelineConfigDialog(QDialog):
    """Dialog for configuring pipeline parameters."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the pipeline configuration dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Pipeline Configuration")
        self.resize(700, 600)

        self.config: PipelineConfig | None = None

        # Initialize widget references (will be created in _create_tabs)
        self.target_dpi_spin: QSpinBox
        self.deskew_threshold_spin: QDoubleSpinBox
        self.header_search_spin: QSpinBox
        self.footer_search_spin: QSpinBox
        self.margin_search_spin: QSpinBox
        self.content_threshold_spin: QDoubleSpinBox
        self.min_gap_size_spin: QSpinBox
        self.template_sample_size_spin: QSpinBox
        self.template_min_pages_spin: QSpinBox
        self.outlier_threshold_spin: QDoubleSpinBox
        self.use_cropping_check: QCheckBox
        self.crop_padding_spin: QSpinBox
        self.ocr_max_retries_spin: QSpinBox
        self.ocr_rate_limit_spin: QSpinBox
        self.verse_avg_line_spin: QSpinBox
        self.verse_cv_spin: QDoubleSpinBox
        self.min_template_confidence_spin: QDoubleSpinBox
        self.min_ocr_confidence_spin: QDoubleSpinBox
        self.stage1_workers_spin: QSpinBox
        self.stage2a_workers_spin: QSpinBox

        # Load current config
        config_manager = get_config_manager()
        config_dict = config_manager.load_config()
        self.config = load_pipeline_config(config_dict)

        # Create UI
        layout = QVBoxLayout(self)

        # Preset selector
        preset_group = QGroupBox("Presets")
        preset_layout = QVBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(
            [
                "Standard Greek Prose Edition",
                "Fragment Edition",
                "Verse Edition",
                "Custom",
            ]
        )
        _ = self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(QLabel("Configuration Preset:"))
        preset_layout.addWidget(self.preset_combo)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Tab widget for stages
        self.tabs = QTabWidget()
        self._create_tabs()
        layout.addWidget(self.tabs)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        _ = button_box.accepted.connect(self._save_config)
        _ = button_box.rejected.connect(self.reject)
        restore_button = button_box.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        if restore_button:
            restore_button.setText("Reset to Defaults")
            _ = restore_button.clicked.connect(self._reset_to_defaults)

        layout.addWidget(button_box)

    def _create_tabs(self) -> None:
        """Create tabs for each pipeline stage."""
        _ = self.tabs.addTab(self._create_stage1_tab(), "Stage 1: Normalisation")
        _ = self.tabs.addTab(self._create_stage2a_tab(), "Stage 2a: Zones")
        _ = self.tabs.addTab(self._create_stage2b_tab(), "Stage 2b: Template")
        _ = self.tabs.addTab(self._create_stage2c_tab(), "Stage 2c: Masking")
        _ = self.tabs.addTab(self._create_stage3_tab(), "Stage 3: OCR")
        _ = self.tabs.addTab(self._create_stage4_tab(), "Stage 4: Assembly")
        _ = self.tabs.addTab(self._create_validation_tab(), "Validation")
        _ = self.tabs.addTab(self._create_performance_tab(), "Performance")

    def _create_stage1_tab(self) -> QWidget:
        """Create Stage 1 configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.target_dpi_spin = QSpinBox()
        self.target_dpi_spin.setRange(72, 600)
        if self.config:
            self.target_dpi_spin.setValue(self.config.target_dpi)
        self.target_dpi_spin.setToolTip("Target DPI for image rendering")
        layout.addRow("Target DPI:", self.target_dpi_spin)

        self.deskew_threshold_spin = QDoubleSpinBox()
        self.deskew_threshold_spin.setRange(0.0, 5.0)
        self.deskew_threshold_spin.setDecimals(2)
        self.deskew_threshold_spin.setSingleStep(0.1)
        if self.config:
            self.deskew_threshold_spin.setValue(self.config.deskew_threshold)
        self.deskew_threshold_spin.setToolTip("Minimum skew angle (degrees) to correct")
        layout.addRow("Deskew Threshold (degrees):", self.deskew_threshold_spin)

        return widget

    def _create_stage2a_tab(self) -> QWidget:
        """Create Stage 2a (zone detection) configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.header_search_spin = QDoubleSpinBox()
        self.header_search_spin.setRange(0.0, 1.0)
        self.header_search_spin.setDecimals(3)
        self.header_search_spin.setSingleStep(0.01)
        if self.config:
            self.header_search_spin.setValue(self.config.header_search_percent)
        layout.addRow("Header Search %:", self.header_search_spin)

        self.footer_search_spin = QDoubleSpinBox()
        self.footer_search_spin.setRange(0.0, 1.0)
        self.footer_search_spin.setDecimals(3)
        self.footer_search_spin.setSingleStep(0.01)
        if self.config:
            self.footer_search_spin.setValue(self.config.footer_search_percent)
        layout.addRow("Footer Search %:", self.footer_search_spin)

        self.margin_search_spin = QDoubleSpinBox()
        self.margin_search_spin.setRange(0.0, 1.0)
        self.margin_search_spin.setDecimals(3)
        self.margin_search_spin.setSingleStep(0.01)
        if self.config:
            self.margin_search_spin.setValue(self.config.margin_search_percent)
        layout.addRow("Margin Search %:", self.margin_search_spin)

        self.content_threshold_spin = QDoubleSpinBox()
        self.content_threshold_spin.setRange(0.0, 1.0)
        self.content_threshold_spin.setDecimals(3)
        self.content_threshold_spin.setSingleStep(0.01)
        if self.config:
            self.content_threshold_spin.setValue(self.config.content_threshold)
        layout.addRow("Content Threshold:", self.content_threshold_spin)

        self.min_gap_size_spin = QSpinBox()
        self.min_gap_size_spin.setRange(1, 100)
        if self.config:
            self.min_gap_size_spin.setValue(self.config.min_gap_size)
        layout.addRow("Min Gap Size (pixels):", self.min_gap_size_spin)

        return widget

    def _create_stage2b_tab(self) -> QWidget:
        """Create Stage 2b (template extraction) configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.template_sample_size_spin = QSpinBox()
        self.template_sample_size_spin.setRange(1, 100)
        if self.config:
            self.template_sample_size_spin.setValue(self.config.template_sample_size)
        layout.addRow("Sample Size (pages):", self.template_sample_size_spin)

        self.template_min_pages_spin = QSpinBox()
        self.template_min_pages_spin.setRange(1, 50)
        if self.config:
            self.template_min_pages_spin.setValue(self.config.template_min_pages)
        layout.addRow("Min Pages Required:", self.template_min_pages_spin)

        self.outlier_threshold_spin = QDoubleSpinBox()
        self.outlier_threshold_spin.setRange(1.0, 5.0)
        self.outlier_threshold_spin.setDecimals(2)
        self.outlier_threshold_spin.setSingleStep(0.1)
        if self.config:
            self.outlier_threshold_spin.setValue(self.config.outlier_threshold)
        layout.addRow("Outlier Threshold (MAD):", self.outlier_threshold_spin)

        return widget

    def _create_stage2c_tab(self) -> QWidget:
        """Create Stage 2c (masking) configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.use_cropping_check = QCheckBox("Use cropping instead of masking")
        if self.config:
            self.use_cropping_check.setChecked(self.config.use_cropping)
        self.use_cropping_check.setToolTip(
            "Cropping is faster but loses coordinate consistency"
        )
        layout.addRow("Masking Strategy:", self.use_cropping_check)

        self.crop_padding_spin = QSpinBox()
        self.crop_padding_spin.setRange(0, 100)
        if self.config:
            self.crop_padding_spin.setValue(self.config.crop_padding)
        layout.addRow("Crop Padding (pixels):", self.crop_padding_spin)

        return widget

    def _create_stage3_tab(self) -> QWidget:
        """Create Stage 3 (OCR) configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.ocr_max_retries_spin = QSpinBox()
        self.ocr_max_retries_spin.setRange(1, 10)
        if self.config:
            self.ocr_max_retries_spin.setValue(self.config.ocr_max_retries)
        layout.addRow("Max Retries:", self.ocr_max_retries_spin)

        self.ocr_rate_limit_spin = QSpinBox()
        self.ocr_rate_limit_spin.setRange(1, 60)
        if self.config:
            self.ocr_rate_limit_spin.setValue(self.config.ocr_rate_limit_per_minute)
        layout.addRow("Rate Limit (per minute):", self.ocr_rate_limit_spin)

        return widget

    def _create_stage4_tab(self) -> QWidget:
        """Create Stage 4 (assembly) configuration tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.verse_avg_line_spin = QSpinBox()
        self.verse_avg_line_spin.setRange(10, 200)
        if self.config:
            self.verse_avg_line_spin.setValue(self.config.verse_avg_line_threshold)
        layout.addRow("Verse Avg Line Threshold:", self.verse_avg_line_spin)

        self.verse_cv_spin = QDoubleSpinBox()
        self.verse_cv_spin.setRange(0.0, 1.0)
        self.verse_cv_spin.setDecimals(2)
        self.verse_cv_spin.setSingleStep(0.05)
        if self.config:
            self.verse_cv_spin.setValue(self.config.verse_cv_threshold)
        layout.addRow("Verse CV Threshold:", self.verse_cv_spin)

        return widget

    def _create_validation_tab(self) -> QWidget:
        """Create validation thresholds tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.min_template_confidence_spin = QDoubleSpinBox()
        self.min_template_confidence_spin.setRange(0.0, 1.0)
        self.min_template_confidence_spin.setDecimals(2)
        self.min_template_confidence_spin.setSingleStep(0.05)
        if self.config:
            self.min_template_confidence_spin.setValue(
                self.config.min_template_confidence
            )
        layout.addRow("Min Template Confidence:", self.min_template_confidence_spin)

        self.min_ocr_confidence_spin = QDoubleSpinBox()
        self.min_ocr_confidence_spin.setRange(0.0, 1.0)
        self.min_ocr_confidence_spin.setDecimals(2)
        self.min_ocr_confidence_spin.setSingleStep(0.05)
        if self.config:
            self.min_ocr_confidence_spin.setValue(self.config.min_ocr_confidence)
        layout.addRow("Min OCR Confidence:", self.min_ocr_confidence_spin)

        return widget

    def _create_performance_tab(self) -> QWidget:
        """Create performance settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.stage1_workers_spin = QSpinBox()
        self.stage1_workers_spin.setRange(1, 16)
        if self.config:
            self.stage1_workers_spin.setValue(self.config.stage1_parallel_workers)
        layout.addRow("Stage 1 Workers:", self.stage1_workers_spin)

        self.stage2a_workers_spin = QSpinBox()
        self.stage2a_workers_spin.setRange(1, 16)
        if self.config:
            self.stage2a_workers_spin.setValue(self.config.stage2a_parallel_workers)
        layout.addRow("Stage 2a Workers:", self.stage2a_workers_spin)

        return widget

    def _on_preset_changed(self, preset_name: str) -> None:
        """Handle preset selection change.

        Args:
            preset_name: Selected preset name
        """
        if preset_name == "Standard Greek Prose Edition":
            # Use defaults (already loaded)
            if self.config:
                self._load_config_to_ui(self.config)
        elif preset_name == "Fragment Edition":
            # Adjust for fragment editions
            config = PipelineConfig()
            config.fragment_ratio_threshold = 0.15  # Lower threshold
            config.template_sample_size = 15  # Fewer samples needed
            self._load_config_to_ui(config)
        elif preset_name == "Verse Edition":
            # Adjust for verse
            config = PipelineConfig()
            config.verse_avg_line_threshold = 50  # Shorter lines
            config.verse_cv_threshold = 0.25  # More consistent
            self._load_config_to_ui(config)
        # "Custom" - no change, user can edit manually

    def _load_config_to_ui(self, config: PipelineConfig) -> None:
        """Load configuration values into UI controls.

        Args:
            config: PipelineConfig to load
        """
        if hasattr(self, "target_dpi_spin"):
            self.target_dpi_spin.setValue(config.target_dpi)
        if hasattr(self, "deskew_threshold_spin"):
            self.deskew_threshold_spin.setValue(config.deskew_threshold)
        # Add other fields as needed

    def _save_config(self) -> None:
        """Save configuration from UI to config file."""
        if not self.config:
            return

        # Update config from UI
        self.config.target_dpi = self.target_dpi_spin.value()
        self.config.deskew_threshold = self.deskew_threshold_spin.value()
        self.config.header_search_percent = self.header_search_spin.value()
        self.config.footer_search_percent = self.footer_search_spin.value()
        self.config.margin_search_percent = self.margin_search_spin.value()
        self.config.content_threshold = self.content_threshold_spin.value()
        self.config.min_gap_size = self.min_gap_size_spin.value()
        self.config.template_sample_size = self.template_sample_size_spin.value()
        self.config.template_min_pages = self.template_min_pages_spin.value()
        self.config.outlier_threshold = self.outlier_threshold_spin.value()
        self.config.use_cropping = self.use_cropping_check.isChecked()
        self.config.crop_padding = self.crop_padding_spin.value()
        self.config.ocr_max_retries = self.ocr_max_retries_spin.value()
        self.config.ocr_rate_limit_per_minute = self.ocr_rate_limit_spin.value()
        self.config.verse_avg_line_threshold = self.verse_avg_line_spin.value()
        self.config.verse_cv_threshold = self.verse_cv_spin.value()
        self.config.min_template_confidence = self.min_template_confidence_spin.value()
        self.config.min_ocr_confidence = self.min_ocr_confidence_spin.value()
        self.config.stage1_parallel_workers = self.stage1_workers_spin.value()
        self.config.stage2a_parallel_workers = self.stage2a_workers_spin.value()

        # Convert to dict and save
        config_manager = get_config_manager()
        config_dict = config_manager.load_config()
        config_dict["pipeline"] = pipeline_config_to_dict(self.config)
        config_manager.save_config(config_dict)

        _ = QMessageBox.information(
            self, "Configuration Saved", "Pipeline configuration saved successfully."
        )
        self.accept()

    def _reset_to_defaults(self) -> None:
        """Reset all values to defaults."""
        default_config = PipelineConfig()
        self._load_config_to_ui(default_config)
        _ = QMessageBox.information(
            self,
            "Defaults Restored",
            "All values have been reset to defaults.",
        )
