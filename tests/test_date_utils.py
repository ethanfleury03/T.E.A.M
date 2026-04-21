"""Tests for Streamlit date_input normalization."""

from datetime import date

from date_utils import streamlit_date_range_to_iso


def test_tuple_range():
    s, e = streamlit_date_range_to_iso((date(2026, 1, 1), date(2026, 1, 31)))
    assert s == "2026-01-01"
    assert e == "2026-01-31"


def test_single_date_in_tuple():
    s, e = streamlit_date_range_to_iso((date(2026, 3, 15),))
    assert s == e == "2026-03-15"


def test_bare_date():
    s, e = streamlit_date_range_to_iso(date(2026, 6, 1))
    assert s == e == "2026-06-01"


def test_empty_none():
    assert streamlit_date_range_to_iso(None) == (None, None)
    assert streamlit_date_range_to_iso(()) == (None, None)
