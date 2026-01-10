#!/usr/bin/env python3
"""
Unit tests for Unicode normalization utilities.

Tests NFC normalization functionality including polytonic Greek characters,
idempotency, edge cases, and various normalization forms.
"""

import unicodedata

import pytest

from philocr.utils.unicode_normalizer import normalize_to_nfc


def test_normalize_empty_string() -> None:
    """Test that empty string is handled correctly."""
    assert normalize_to_nfc("") == ""


def test_normalize_idempotent() -> None:
    """Test that NFC normalization is idempotent."""
    # Test with simple ASCII
    text = "Hello, World!"
    assert normalize_to_nfc(text) == text
    assert normalize_to_nfc(normalize_to_nfc(text)) == text

    # Test with basic Greek
    greek_text = "αβγδε"
    assert normalize_to_nfc(greek_text) == greek_text
    assert normalize_to_nfc(normalize_to_nfc(greek_text)) == greek_text


def test_normalize_polytonic_greek_composed() -> None:
    """Test that already-composed polytonic Greek remains unchanged."""
    # These are already in NFC form
    composed_chars = [
        "ἀ",  # alpha with smooth breathing (U+1F00)
        "ἁ",  # alpha with rough breathing (U+1F01)
        "ἂ",  # alpha with smooth breathing and grave (U+1F02)
        "ἃ",  # alpha with rough breathing and grave (U+1F03)
        "ἄ",  # alpha with smooth breathing and acute (U+1F04)
        "ἅ",  # alpha with rough breathing and acute (U+1F05)
        "ἆ",  # alpha with smooth breathing and circumflex (U+1F06)
        "ἇ",  # alpha with rough breathing and circumflex (U+1F07)
        "ἠ",  # eta with smooth breathing (U+1F20)
        "ὡ",  # omega with rough breathing (U+1F61)
    ]

    for char in composed_chars:
        normalized = normalize_to_nfc(char)
        assert normalized == char, f"Composed character {char} should remain unchanged"
        assert unicodedata.normalize("NFC", normalized) == normalized


def test_normalize_polytonic_greek_decomposed() -> None:
    """Test normalization of decomposed polytonic Greek to NFC."""
    # Create decomposed forms using combining characters
    # α (U+03B1) + smooth breathing (U+0313) = ἀ (should become U+1F00)
    alpha = "\u03B1"
    smooth_breathing = "\u0313"
    rough_breathing = "\u0314"
    acute = "\u0301"
    grave = "\u0300"
    circumflex = "\u0342"

    # Test decomposed alpha with smooth breathing
    decomposed = alpha + smooth_breathing
    normalized = normalize_to_nfc(decomposed)
    expected = "\u1F00"  # ἀ
    assert normalized == expected, (
        f"Decomposed {decomposed!r} should normalize to {expected!r}, "
        f"got {normalized!r}"
    )

    # Test decomposed alpha with rough breathing
    decomposed_rough = alpha + rough_breathing
    normalized_rough = normalize_to_nfc(decomposed_rough)
    expected_rough = "\u1F01"  # ἁ
    assert normalized_rough == expected_rough

    # Test decomposed alpha with smooth breathing and acute
    decomposed_accent = alpha + smooth_breathing + acute
    normalized_accent = normalize_to_nfc(decomposed_accent)
    expected_accent = "\u1F04"  # ἄ
    assert normalized_accent == expected_accent


def test_normalize_non_greek_text() -> None:
    """Test that non-Greek text remains unchanged when already normalized."""
    test_cases = [
        "Hello, World!",
        "123456",
        "日本語",
        "한글",
        "русский",
        "العربية",
        "🇺🇸",  # Emoji
    ]

    for text in test_cases:
        normalized = normalize_to_nfc(text)
        # Most text is already in NFC, so should remain the same
        # But we verify it's in NFC form
        assert unicodedata.normalize("NFC", normalized) == normalized


def test_normalize_mixed_normalization_forms() -> None:
    """Test text with mixed normalization forms."""
    # Mix of composed and decomposed characters
    alpha = "\u03B1"
    smooth_breathing = "\u0313"
    composed_char = "\u1F00"  # ἀ

    # Create text with both forms
    mixed_text = composed_char + alpha + smooth_breathing
    normalized = normalize_to_nfc(mixed_text)
    expected = "\u1F00\u1F00"  # Both should be composed
    assert normalized == expected


def test_normalize_combining_characters() -> None:
    """Test normalization with combining characters."""
    # Latin A with combining acute
    latin_a = "A"
    acute = "\u0301"
    decomposed_a_acute = latin_a + acute
    normalized = normalize_to_nfc(decomposed_a_acute)
    # Should normalize to precomposed if available, or stay decomposed
    assert unicodedata.normalize("NFC", normalized) == normalized


def test_normalize_zero_width_characters() -> None:
    """Test that zero-width characters are handled correctly."""
    # Zero-width space
    zws = "\u200B"
    text = "Hello" + zws + "World"
    normalized = normalize_to_nfc(text)
    # Zero-width characters should be preserved
    assert zws in normalized or unicodedata.normalize("NFC", text) == normalized


def test_normalize_real_world_greek_text() -> None:
    """Test normalization with realistic Greek text."""
    # Example: "Ἀθήνη" (Athena in polytonic Greek)
    # This is typically already in NFC, but test anyway
    greek_text = "Ἀθήνη"
    normalized = normalize_to_nfc(greek_text)
    assert unicodedata.normalize("NFC", normalized) == normalized
    assert len(normalized) > 0

    # Test a longer Greek phrase
    greek_phrase = "Ὅμηρος ἔγραφε τὴν Ἰλιάδα"
    normalized_phrase = normalize_to_nfc(greek_phrase)
    assert unicodedata.normalize("NFC", normalized_phrase) == normalized_phrase


def test_normalize_unicode_equivalence() -> None:
    """Test that normalization preserves Unicode equivalence."""
    # These should be equivalent after normalization
    # Using NFD form then normalizing to NFC
    alpha_nfd = "\u03B1\u0313"  # decomposed
    alpha_nfc = "\u1F00"  # composed

    normalized_nfd = normalize_to_nfc(alpha_nfd)
    normalized_nfc = normalize_to_nfc(alpha_nfc)

    assert (
        normalized_nfd == normalized_nfc
    ), "NFD and NFC forms should normalize to same result"


def test_normalize_performance_large_text() -> None:
    """Test that normalization works with larger text."""
    # Create a larger text block
    base_text = "ἀβγδεζηθικλμνξοπρστυφχψω"
    large_text = base_text * 1000  # 27,000 characters

    normalized = normalize_to_nfc(large_text)
    assert len(normalized) > 0
    assert unicodedata.normalize("NFC", normalized) == normalized


@pytest.mark.parametrize(
    "input_text",
    [
        "",
        "a",
        "α",
        "ἀ",
        "A\u0301",  # A with combining acute
        "\u03B1\u0313",  # decomposed alpha with breathing
        "Hello, 世界!",
        "Mix: ἀ + α\u0313",
    ],
)
def test_normalize_parameterized(input_text: str) -> None:
    """Parameterized test for various input types."""
    normalized = normalize_to_nfc(input_text)
    # Verify result is in NFC form
    assert unicodedata.normalize("NFC", normalized) == normalized
    # Verify idempotency
    assert normalize_to_nfc(normalized) == normalized
