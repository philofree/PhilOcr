"""Stage 4: Text assembly and normalization."""

from __future__ import annotations

import re
import unicodedata
from statistics import mean
from typing import TYPE_CHECKING

import numpy as np

from philocr.models.config import PipelineConfig
from philocr.models.document import (
    Document,
    DocumentMetadata,
    DocumentStatistics,
    GenreDetectionResult,
    GenreHint,
    PageOutput,
    Paragraph,
)
from philocr.models.ocr_result import OCRResult
from philocr.models.template import DocumentTemplate

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def normalise_text(text: str) -> str:
    """Normalise OCR output text.

    This is intentionally conservative. We are not trying to "fix" Greek,
    only to produce consistent Unicode that can be aligned later.

    Args:
        text: Raw text from OCR

    Returns:
        Normalised text (NFC Unicode, cleaned whitespace)
    """
    # Unicode NFC normalisation (critical for Greek)
    text = unicodedata.normalize("NFC", text)

    # Collapse multiple spaces to single space
    # Preserve paragraph breaks (double newlines)
    lines = text.split("\n")
    lines = [" ".join(line.split()) for line in lines]
    text = "\n".join(lines)

    return text.strip()


def analyse_line_lengths(ocr_result: OCRResult) -> dict[str, float | int]:
    """Analyse line length distribution for verse detection.

    Verse characteristics:
    - Short, consistent line lengths
    - Low coefficient of variation
    - Lines often end mid-sentence

    Prose characteristics:
    - Variable line lengths (justified to margins)
    - Higher coefficient of variation
    - Lines break at word boundaries, not semantic units

    Args:
        ocr_result: OCR result with text

    Returns:
        Dictionary with line statistics
    """
    lines = ocr_result.text.split("\n")
    line_lengths = [len(line.strip()) for line in lines if line.strip()]

    if len(line_lengths) < 5:
        return {
            "avg_length": 0,
            "std_length": 0,
            "cv": float("inf"),
            "confidence": 0.0,
            "line_count": len(line_lengths),
        }

    avg_length = float(np.mean(line_lengths))
    std_length = float(np.std(line_lengths))
    cv = std_length / avg_length if avg_length > 0 else float("inf")

    # Confidence based on how clearly verse-like or prose-like
    if cv < 0.2 and avg_length < 60:
        confidence = 0.9  # Very clearly verse
    elif cv < 0.3 and avg_length < 80:
        confidence = 0.7  # Probably verse
    elif cv > 0.5:
        confidence = 0.8  # Probably prose
    else:
        confidence = 0.5  # Ambiguous

    return {
        "avg_length": avg_length,
        "std_length": std_length,
        "cv": cv,
        "line_count": len(line_lengths),
        "confidence": confidence,
    }


def detect_speaker_patterns(text: str) -> dict[str, float | int | list[str]]:
    """Detect speaker attribution patterns for dialogue detection.

    Common patterns in Greek editions:
    - "ΣΩ." or "ΣΩΚ." (Socrates)
    - "ΠΡΩ." (Protagoras)
    - All-caps names followed by period/colon
    - Names at start of lines/paragraphs

    Also detects Latin speaker markers in bilingual editions:
    - "SO." or "SOC."
    - Names in small caps

    Args:
        text: Text to analyze

    Returns:
        Dictionary with speaker detection statistics
    """
    # Greek speaker patterns (all caps, 2-4 letters, followed by period)
    greek_speaker_pattern = r"^[\s]*([Α-Ω]{2,4})\.\s"

    # Latin/transliterated speaker patterns
    latin_speaker_pattern = r"^[\s]*([A-Z]{2,4})\.\s"

    # Extended name patterns (e.g., "ΣΩΚΡΑΤΗΣ" or "SOCRATES")
    full_name_pattern = r"^[\s]*([Α-Ω]{4,12}|[A-Z]{4,12})[\.\:]\s"

    lines = text.split("\n")
    total_lines = len([l for l in lines if l.strip()])

    if total_lines == 0:
        return {
            "speaker_ratio": 0.0,
            "confidence": 0.0,
            "patterns_found": [],
            "speaker_lines": 0,
            "total_lines": 0,
            "unique_speakers": 0,
        }

    speaker_lines = 0
    patterns_found: list[str] = []

    for line in lines:
        if not line.strip():
            continue

        # Check each pattern
        for pattern in [
            greek_speaker_pattern,
            latin_speaker_pattern,
            full_name_pattern,
        ]:
            match = re.match(pattern, line)
            if match:
                speaker_lines += 1
                patterns_found.append(match.group(1))
                break

    speaker_ratio = speaker_lines / total_lines if total_lines > 0 else 0.0

    # Confidence based on consistency of patterns
    unique_speakers = len(set(patterns_found))
    if speaker_ratio > 0.3 and 2 <= unique_speakers <= 10:
        confidence = 0.9  # Clear dialogue with multiple speakers
    elif speaker_ratio > 0.2 and unique_speakers >= 2:
        confidence = 0.7  # Probably dialogue
    elif speaker_ratio > 0.1:
        confidence = 0.5  # Possible dialogue
    else:
        confidence = 0.3  # Unlikely dialogue

    return {
        "speaker_ratio": speaker_ratio,
        "speaker_lines": speaker_lines,
        "total_lines": total_lines,
        "unique_speakers": unique_speakers,
        "patterns_found": list(set(patterns_found))[:10],  # Sample
        "confidence": confidence,
    }


def detect_fragment_patterns(text: str) -> dict[str, float | int]:
    """Detect fragment numbering patterns.

    Common patterns in fragment editions:
    - "Fr. 1", "Fr. 12", "Frag. 1"
    - "B1", "B12" (Diels-Kranz numbering)
    - "1.", "12." at start of sections
    - "[1]", "[12]" bracketed numbers
    - "§1", "§12" section markers

    Fragment editions typically have:
    - Discontinuous text
    - Frequent numbering
    - Short isolated passages

    Args:
        text: Text to analyze

    Returns:
        Dictionary with fragment detection statistics
    """
    # Fragment number patterns
    patterns = [
        r"Fr(?:ag)?\.?\s*\d+",  # Fr. 1, Frag. 12
        r"\b[AB]\d+\b",  # B1, A12 (Diels-Kranz)
        r"^\s*\d{1,3}\.\s",  # 1. at line start
        r"\[\d{1,3}\]",  # [1], [12]
        r"§\s*\d+",  # §1, § 12
    ]

    fragment_markers = 0
    total_paragraphs = len([p for p in text.split("\n\n") if p.strip()])

    if total_paragraphs == 0:
        return {
            "fragment_ratio": 0.0,
            "confidence": 0.0,
            "fragment_markers": 0,
            "total_paragraphs": 0,
        }

    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        fragment_markers += len(matches)

    # Ratio of fragment markers to paragraphs
    fragment_ratio = (
        fragment_markers / total_paragraphs if total_paragraphs > 0 else 0.0
    )

    # High ratio suggests fragment edition
    if fragment_ratio > 0.5:
        confidence = 0.9
    elif fragment_ratio > 0.3:
        confidence = 0.7
    elif fragment_ratio > 0.1:
        confidence = 0.5
    else:
        confidence = 0.2

    return {
        "fragment_ratio": fragment_ratio,
        "fragment_markers": fragment_markers,
        "total_paragraphs": total_paragraphs,
        "confidence": confidence,
    }


def detect_genre_hint(
    ocr_result: OCRResult,
    config: PipelineConfig,
) -> GenreDetectionResult:
    """HEURISTIC: Detect likely genre of text content.

    This is triangulation metadata for later reconstruction.
    Even approximate classification constrains formatting decisions.

    Strategy:
    1. Analyse line length distribution (verse vs prose)
    2. Detect speaker patterns (dialogue detection)
    3. Detect fragment markers (fragment detection)
    4. Combine signals with confidence weighting

    Args:
        ocr_result: OCR result with text and line structure
        config: Configuration with detection thresholds

    Returns:
        GenreDetectionResult with genre hint and confidence
    """
    if not ocr_result.text or len(ocr_result.text.strip()) < 50:
        return GenreDetectionResult(
            primary_genre=GenreHint.UNKNOWN,
            confidence=0.0,
            signals={"reason": "insufficient_text"},
        )

    signals: dict[str, dict[str, float | int | list[str]]] = {}

    # === SIGNAL 1: Line length distribution (verse indicator) ===
    line_stats = analyse_line_lengths(ocr_result)
    signals["line_stats"] = line_stats
    is_verse_like = (
        line_stats["avg_length"] < config.verse_avg_line_threshold
        and line_stats["cv"] < config.verse_cv_threshold
    )

    # === SIGNAL 2: Speaker patterns (dialogue indicator) ===
    speaker_stats = detect_speaker_patterns(ocr_result.text)
    signals["speaker_stats"] = speaker_stats
    has_speakers = speaker_stats["speaker_ratio"] > config.speaker_ratio_threshold

    # === SIGNAL 3: Fragment markers (fragment indicator) ===
    fragment_stats = detect_fragment_patterns(ocr_result.text)
    signals["fragment_stats"] = fragment_stats
    has_fragments = fragment_stats["fragment_ratio"] > config.fragment_ratio_threshold

    # === COMBINE SIGNALS ===

    # Priority: fragments > verse_speakers > speakers > verse > prose
    if has_fragments:
        return GenreDetectionResult(
            primary_genre=GenreHint.FRAGMENTS,
            confidence=fragment_stats["confidence"],
            signals=signals,
        )

    if is_verse_like and has_speakers:
        return GenreDetectionResult(
            primary_genre=GenreHint.VERSE_SPEAKERS,
            confidence=min(line_stats["confidence"], speaker_stats["confidence"]),
            signals=signals,
        )

    if has_speakers:
        return GenreDetectionResult(
            primary_genre=GenreHint.SPEAKERS,
            confidence=speaker_stats["confidence"],
            signals=signals,
        )

    if is_verse_like:
        return GenreDetectionResult(
            primary_genre=GenreHint.VERSE,
            confidence=line_stats["confidence"],
            signals=signals,
        )

    # Default to prose
    return GenreDetectionResult(
        primary_genre=GenreHint.PROSE,
        confidence=0.7,  # Prose is the default assumption
        signals=signals,
    )


def classify_indent_hint(
    x_position: int,
    body_left: int,
    body_right: int,
) -> int:
    """HEURISTIC: Classify indent level based on x-position.

    This is advisory metadata, not structural truth.

    0 = flush left (likely continuation)
    1 = standard indent (likely new paragraph)
    2 = deep indent (likely quotation)

    Args:
        x_position: X-coordinate of line start
        body_left: Left boundary of body region
        body_right: Right boundary of body region

    Returns:
        Indent hint (0, 1, or 2)
    """
    body_width = body_right - body_left

    if body_width <= 0:
        return 0

    relative_x = x_position - body_left
    indent_ratio = relative_x / body_width

    if indent_ratio < 0.02:
        return 0  # Flush left
    elif indent_ratio < 0.06:
        return 1  # Standard indent
    else:
        return 2  # Deep indent


def assemble_page(
    ocr_result: OCRResult,
    config: PipelineConfig,
) -> PageOutput:
    """Assemble page output from OCR result.

    This is intentionally simple. The goal is clean text extraction,
    not layout reconstruction.

    Args:
        ocr_result: OCR result from Document AI
        config: Pipeline configuration

    Returns:
        PageOutput with normalised text and optional genre hints
    """
    if not ocr_result.text:
        return PageOutput(
            page_num=ocr_result.page_num,
            paragraphs=[],
            full_text="",
            confidence=0.0,
            genre_hint=None,
            genre_confidence=0.0,
        )

    # Normalise and clean the text
    clean_text = normalise_text(ocr_result.text)

    # Optional: Detect genre hint
    genre_result: GenreDetectionResult | None = None
    if config.min_genre_confidence > 0:
        genre_result = detect_genre_hint(ocr_result, config)
        if genre_result.confidence < config.min_genre_confidence:
            # Below threshold, don't use genre hint
            genre_result = None

    # Convert paragraphs from OCR structure (advisory, not authoritative)
    # Use first paragraph bbox to approximate body boundaries if template not available
    paragraphs: list[Paragraph] = []
    if ocr_result.paragraphs:
        # Approximate body boundaries from paragraph bboxes
        min_x = min(p.bbox.x1 for p in ocr_result.paragraphs)
        max_x = max(p.bbox.x2 for p in ocr_result.paragraphs)

        for para in ocr_result.paragraphs:
            indent_class = classify_indent_hint(para.bbox.x1, min_x, max_x)
            paragraphs.append(
                Paragraph(
                    text=para.text,
                    indent_class=indent_class,
                    confidence=para.confidence,
                    bbox=para.bbox,
                )
            )

    return PageOutput(
        page_num=ocr_result.page_num,
        paragraphs=paragraphs,
        full_text=clean_text,
        confidence=ocr_result.confidence,
        genre_hint=genre_result.primary_genre if genre_result else None,
        genre_confidence=genre_result.confidence if genre_result else 0.0,
        genre_signals=genre_result.signals if genre_result else None,
    )


def assemble_document(
    page_outputs: list[PageOutput],
    template: DocumentTemplate,
    metadata: DocumentMetadata,
) -> Document:
    """Assemble all pages into final document.

    Args:
        page_outputs: List of PageOutput objects
        template: Document template used for processing
        metadata: Document metadata (title, source, etc.)

    Returns:
        Complete Document object
    """
    confidences = [p.confidence for p in page_outputs if p.confidence > 0]
    pages_with_errors = [p.page_num for p in page_outputs if p.confidence == 0]

    total_paragraphs = sum(len(p.paragraphs) for p in page_outputs)

    return Document(
        metadata=metadata,
        template=template,
        pages=page_outputs,
        full_text="\n\n".join(p.full_text for p in page_outputs),
        statistics=DocumentStatistics(
            total_pages=len(page_outputs),
            total_paragraphs=total_paragraphs,
            average_confidence=float(mean(confidences)) if confidences else 0.0,
            pages_with_errors=pages_with_errors,
        ),
    )
