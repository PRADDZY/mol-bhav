"""Bot detection middleware.

Composite scoring based on:
  - Timing heuristics (inter-message speed, consistency)
  - Offer pattern analysis (fixed increments, algorithmic curves)

Thresholds:
  < 0.3  → human, normal negotiation
  0.3-0.7 → suspicious, tighten strategy (high beta)
  > 0.7  → likely bot, rate-limit / flag
"""

from __future__ import annotations

import statistics
from datetime import datetime


class BotDetector:
    def __init__(
        self,
        timing_weight: float = 0.5,
        pattern_weight: float = 0.5,
        min_interval_sec: float = 2.0,
        max_stddev_sec: float = 0.5,
    ):
        self.timing_weight = timing_weight
        self.pattern_weight = pattern_weight
        self.min_interval_sec = min_interval_sec
        self.max_stddev_sec = max_stddev_sec
        self._timestamps: list[datetime] = []
        self._offers: list[float] = []

    def record(self, timestamp: datetime, offer: float) -> None:
        self._timestamps.append(timestamp)
        self._offers.append(offer)

    def score_timing(self) -> float:
        """Score 0-1 based on how bot-like the timing is."""
        if len(self._timestamps) < 3:
            return 0.0

        intervals = []
        for i in range(1, len(self._timestamps)):
            delta = (self._timestamps[i] - self._timestamps[i - 1]).total_seconds()
            intervals.append(delta)

        if not intervals:
            return 0.0

        # Check if intervals are suspiciously fast
        avg_interval = statistics.mean(intervals)
        speed_score = max(0.0, 1.0 - avg_interval / (self.min_interval_sec * 3))

        # Check if intervals are suspiciously consistent
        if len(intervals) >= 3:
            stddev = statistics.stdev(intervals)
            consistency_score = max(0.0, 1.0 - stddev / self.max_stddev_sec)
        else:
            consistency_score = 0.0

        return min(1.0, (speed_score + consistency_score) / 2)

    def score_pattern(self) -> float:
        """Score 0-1 based on how algorithmic the offer pattern is."""
        if len(self._offers) < 4:
            return 0.0

        deltas = [self._offers[i] - self._offers[i - 1] for i in range(1, len(self._offers))]

        if not deltas:
            return 0.0

        # Check fixed-increment pattern (all deltas identical)
        if len(set(round(d, 2) for d in deltas)) == 1:
            return 1.0

        # Check near-fixed-increment (very low variance in deltas)
        if len(deltas) >= 3:
            stddev = statistics.stdev(deltas)
            mean_delta = abs(statistics.mean(deltas)) or 1.0
            cv = stddev / mean_delta  # coefficient of variation
            if cv < 0.05:  # nearly identical increments
                return 0.9
            elif cv < 0.15:
                return 0.5

        return 0.0

    def compute_bot_score(self) -> float:
        """Composite bot score (0-1)."""
        timing = self.score_timing()
        pattern = self.score_pattern()
        return round(
            self.timing_weight * timing + self.pattern_weight * pattern,
            3,
        )

    @staticmethod
    def recommended_beta(bot_score: float, base_beta: float) -> float:
        """If buyer looks like a bot, be tougher (higher beta)."""
        if bot_score > 0.7:
            return max(base_beta, 20.0)  # extreme boulware
        elif bot_score > 0.3:
            return max(base_beta, 10.0)  # tougher
        return base_beta
