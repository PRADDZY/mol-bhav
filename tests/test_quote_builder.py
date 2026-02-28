"""Tests for the Beckn quote builder."""

from app.protocol.quote_builder import build_quote, seconds_to_iso_duration


def test_iso_duration_5min():
    assert seconds_to_iso_duration(300) == "PT5M"


def test_iso_duration_1h():
    assert seconds_to_iso_duration(3600) == "PT1H"


def test_iso_duration_90s():
    assert seconds_to_iso_duration(90) == "PT1M30S"


def test_iso_duration_zero():
    assert seconds_to_iso_duration(0) == "PT0S"


def test_build_quote_basic():
    q = build_quote(price=850.0, ttl_seconds=300)
    assert q.price.value == "850.0"
    assert q.ttl == "PT5M"
    assert len(q.breakup) == 1
    assert q.breakup[0].title == "Item Price"


def test_build_quote_with_delivery():
    q = build_quote(price=850.0, delivery_charge=50.0)
    assert q.price.value == "900.0"
    assert len(q.breakup) == 2


def test_build_quote_with_discount():
    q = build_quote(price=850.0, discount=100.0)
    assert q.price.value == "750.0"
    assert len(q.breakup) == 2
