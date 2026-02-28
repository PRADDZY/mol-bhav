"""Tests for exit-intent / sentiment detection."""

from app.dialogue.sentiment import detect_exit_intent


def test_no_exit_intent():
    result = detect_exit_intent("What's the best price you can do?")
    assert not result.is_leaving


def test_english_exit_keyword():
    result = detect_exit_intent("This is too expensive for me")
    assert result.is_leaving
    assert result.confidence >= 0.5


def test_hinglish_exit_keyword():
    result = detect_exit_intent("Bohot mehenga hai bhai")
    assert result.is_leaving
    assert result.confidence >= 0.5


def test_angry_keyword():
    result = detect_exit_intent("This is a scam, you're cheating")
    assert result.is_leaving
    assert result.is_angry
    assert result.confidence >= 0.8


def test_multiple_exit_signals():
    result = detect_exit_intent("Too expensive, forget it, I'll go to another shop")
    assert result.is_leaving
    assert result.confidence > 0.6


def test_chhodo_hindi():
    result = detect_exit_intent("Chhodo yaar, nahi chahiye")
    assert result.is_leaving
