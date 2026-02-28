"""Exit-intent / walk-away sentiment detection.

Detects when a buyer is signalling they want to leave, using keyword matching
and simple pattern analysis. This triggers the "Digital Flounce" save-the-deal flow.
"""

from __future__ import annotations

from dataclasses import dataclass


# Hinglish + English exit signals
_EXIT_KEYWORDS = [
    # English
    "too expensive", "too much", "too costly", "can't afford", "forget it",
    "never mind", "no thanks", "not interested", "I'll pass", "bye",
    "leaving", "going", "somewhere else", "another shop", "no deal",
    # Hindi / Hinglish (transliterated)
    "bohot mehenga", "bahut mehenga", "bahut zyada", "chhodo", "chodo",
    "jane do", "jaane do", "rehne do", "nahi chahiye", "nahi lena",
    "bahut hai", "itna nahi", "afford nahi", "budget nahi",
    "dusri dukaan", "kahi aur", "kahin aur",
]

_ANGRY_KEYWORDS = [
    "waste of time", "scam", "rip off", "loot", "cheating",
    "loot rahe ho", "pagal bana rahe", "mazaak", "joke",
]


@dataclass
class ExitIntent:
    is_leaving: bool
    confidence: float  # 0.0 - 1.0
    trigger: str  # which keyword/pattern matched
    is_angry: bool = False


def detect_exit_intent(message: str) -> ExitIntent:
    """Analyze buyer message for exit intent.

    Returns ExitIntent with confidence score and matched trigger.
    """
    text = message.lower().strip()

    # Check angry keywords first (higher priority)
    for kw in _ANGRY_KEYWORDS:
        if kw in text:
            return ExitIntent(
                is_leaving=True,
                confidence=0.9,
                trigger=kw,
                is_angry=True,
            )

    # Check exit keywords
    matches = [kw for kw in _EXIT_KEYWORDS if kw in text]
    if matches:
        # More matches = higher confidence
        confidence = min(1.0, 0.5 + 0.15 * len(matches))
        return ExitIntent(
            is_leaving=True,
            confidence=confidence,
            trigger=matches[0],
        )

    return ExitIntent(is_leaving=False, confidence=0.0, trigger="")
