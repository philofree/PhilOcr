"""Multi-stage progress widget for pipeline visualization."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from philocr.utils.logging_config import get_logger

logger = get_logger(__name__)


class StageProgressWidget(QWidget):
    """Widget showing progress across multiple pipeline stages.

    Displays overall progress and individual stage progress with labels
    and status text.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the stage progress widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Stage names
        self.stage_names = [
            "Stage 1: Image Normalisation",
            "Stage 2: Template Extraction",
            "Stage 3: OCR Processing",
            "Stage 4: Text Assembly",
        ]

        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Overall progress
        overall_label = QLabel("Overall Progress:")
        overall_label.setFont(overall_label.font())
        layout.addWidget(overall_label)

        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        self.overall_progress.setMinimumHeight(30)
        layout.addWidget(self.overall_progress)

        # Stage progress bars
        self.stage_progresses: list[QProgressBar] = []
        self.stage_labels: list[QLabel] = []
        self.stage_status_labels: list[QLabel] = []

        for stage_name in self.stage_names:
            # Stage label
            stage_label = QLabel(f"{stage_name}:")
            stage_label.setFont(stage_label.font())
            layout.addWidget(stage_label)

            # Stage progress bar
            stage_progress = QProgressBar()
            stage_progress.setMinimum(0)
            stage_progress.setMaximum(100)
            stage_progress.setValue(0)
            stage_progress.setMinimumHeight(25)
            layout.addWidget(stage_progress)

            # Status label
            status_label = QLabel("Waiting...")
            status_label.setStyleSheet("color: gray;")
            layout.addWidget(status_label)

            self.stage_progresses.append(stage_progress)
            self.stage_labels.append(stage_label)
            self.stage_status_labels.append(status_label)

        # Spacer
        layout.addStretch()

    def update_stage(self, stage_name: str, progress: int, status_text: str) -> None:
        """Update individual stage progress.

        Args:
            stage_name: Stage identifier ("Stage 1", "Stage 2", etc.)
            progress: Progress percentage (0-100)
            status_text: Status message for this stage
        """
        # Find stage index
        stage_index = -1
        if "Stage 1" in stage_name or "normalis" in stage_name.lower():
            stage_index = 0
        elif "Stage 2" in stage_name or "template" in stage_name.lower():
            stage_index = 1
        elif "Stage 3" in stage_name or "ocr" in stage_name.lower():
            stage_index = 2
        elif "Stage 4" in stage_name or "assembly" in stage_name.lower():
            stage_index = 3

        if 0 <= stage_index < len(self.stage_progresses):
            self.stage_progresses[stage_index].setValue(progress)
            self.stage_status_labels[stage_index].setText(status_text)
            self.stage_status_labels[stage_index].setStyleSheet("color: black;")

    def update_overall(self, progress: int) -> None:
        """Update overall progress.

        Args:
            progress: Overall progress percentage (0-100)
        """
        self.overall_progress.setValue(progress)

    def reset(self) -> None:
        """Reset all stages to initial state."""
        self.overall_progress.setValue(0)
        for progress_bar in self.stage_progresses:
            progress_bar.setValue(0)
        for status_label in self.stage_status_labels:
            status_label.setText("Waiting...")
            status_label.setStyleSheet("color: gray;")
