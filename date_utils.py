"""Helpers for normalizing Streamlit date_input values."""

from __future__ import annotations

from datetime import date
from typing import Any


def streamlit_date_range_to_iso(date_range: Any) -> tuple[str | None, str | None]:
    """Convert st.date_input range value to inclusive ISO date strings for SQL filters."""
    if date_range is None:
        return None, None
    if isinstance(date_range, tuple):
        if len(date_range) == 2 and all(isinstance(d, date) for d in date_range):
            return date_range[0].isoformat(), date_range[1].isoformat()
        if len(date_range) == 1 and isinstance(date_range[0], date):
            d = date_range[0]
            return d.isoformat(), d.isoformat()
        return None, None
    if isinstance(date_range, date):
        return date_range.isoformat(), date_range.isoformat()
    return None, None
