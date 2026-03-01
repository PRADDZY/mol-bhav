"""Placeholder for bilateral digital signatures.

In production, this would sign agreed-upon quotes to create
a tamper-proof bilateral transaction record.
"""

from __future__ import annotations

import hashlib
import json
import logging
import warnings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_STUB_WARNING_EMITTED = False


def sign_agreement(session_id: str, agreed_price: float, product_id: str) -> dict:
    """Generate a stub 'digital signature' for a completed negotiation.

    In production, replace with proper asymmetric crypto (Ed25519 / RSA).
    """
    global _STUB_WARNING_EMITTED
    if not _STUB_WARNING_EMITTED:
        warnings.warn(
            "Using stub SHA256 digest as digital signature. "
            "Replace with Ed25519/RSA before production deployment.",
            stacklevel=2,
        )
        logger.warning("STUB: digital_signature.sign_agreement() uses SHA256 digest, not real crypto")
        _STUB_WARNING_EMITTED = True
    payload = {
        "session_id": session_id,
        "product_id": product_id,
        "agreed_price": agreed_price,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload_str = json.dumps(payload, sort_keys=True)
    digest = hashlib.sha256(payload_str.encode()).hexdigest()

    return {
        **payload,
        "signature": digest,
        "algorithm": "sha256-stub",
        "note": "Placeholder — replace with proper signing in production",
    }
