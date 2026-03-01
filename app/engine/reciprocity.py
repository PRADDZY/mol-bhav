"""Tit-for-Tat reciprocity tracker.

Mirrors buyer concession behaviour with a damping factor alpha,
so the AI always concedes *less* than the buyer did.

    AI_delta = alpha * buyer_delta   (0 < alpha < 1)
"""

from __future__ import annotations


class ReciprocityTracker:
    """Track buyer offer history and compute asymmetric mirrored concessions."""

    def __init__(self, alpha: float = 0.6, max_concession: float = 200.0, window: int = 3):
        """
        Args:
            alpha: Damping factor. Buyer concedes ₹50 → AI concedes ₹30 at alpha=0.6.
            max_concession: Maximum AI concession per round (cap).
            window: Sliding window size for averaging buyer deltas.
        """
        self.alpha = alpha
        self.max_concession = max_concession
        self.window = window
        self._buyer_offers: list[float] = []

    def record_buyer_offer(self, price: float) -> None:
        self._buyer_offers.append(price)

    @property
    def buyer_deltas(self) -> list[float]:
        """Per-round buyer concession amounts (positive = buyer moved up)."""
        deltas = []
        for i in range(1, len(self._buyer_offers)):
            deltas.append(self._buyer_offers[i] - self._buyer_offers[i - 1])
        return deltas

    def avg_buyer_delta(self) -> float:
        """Average buyer concession over the sliding window."""
        deltas = self.buyer_deltas
        if not deltas:
            return 0.0
        recent = deltas[-self.window :]
        return sum(recent) / len(recent)

    def compute_ai_concession(self) -> float:
        """How much the AI should concede this round, based on buyer behaviour."""
        buyer_delta = self.avg_buyer_delta()
        if buyer_delta <= 0:
            # Buyer didn't concede (or moved backwards) → AI holds firm
            return 0.0
        raw = self.alpha * buyer_delta
        return min(raw, self.max_concession)

    def detect_trend(self) -> str:
        """Classify buyer concession trend.

        Returns:
            'accelerating' — buyer concessions increasing (eager buyer)
            'stable'       — roughly constant
            'decelerating' — buyer concessions shrinking (nearing limit)
            'stalled'      — buyer not conceding at all
        """
        deltas = self.buyer_deltas
        if len(deltas) < 2:
            return "stable"
        recent = deltas[-self.window :]
        if all(d <= 0 for d in recent):
            return "stalled"
        if len(recent) >= 2:
            slope = recent[-1] - recent[0]
            if slope > 5:
                return "accelerating"
            elif slope < -5:
                return "decelerating"
        return "stable"

    def adaptive_alpha(self, relative_time: float) -> float:
        """Adjust alpha based on how much time remains.

        Near deadline → more generous (alpha increases toward 1.0).
        Early → tighter (alpha stays at base).

        Args:
            relative_time: 0.0 (start) → 1.0 (deadline).
        """
        relative_time = max(0.0, min(1.0, relative_time))
        # Linear interpolation: alpha → 1.0 as t → 1.0
        return self.alpha + (1.0 - self.alpha) * max(0.0, relative_time - 0.5) * 2
