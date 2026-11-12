"""Locale-independent formatting helpers (Indonesian labels)."""
from __future__ import annotations

from datetime import datetime

_DAYS_ID = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]  # Monday = 0
_MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def fmt_date(millis: int) -> str:
    d = datetime.fromtimestamp(millis / 1000.0)
    return f"{_DAYS_ID[d.weekday()]}, {d.day:02d} {_MONTHS_ID[d.month - 1]} {d.year}"


def fmt_time(millis: int) -> str:
    return datetime.fromtimestamp(millis / 1000.0).strftime("%H:%M:%S")


def fmt_datetime(millis: int) -> str:
    return f"{fmt_date(millis)} {fmt_time(millis)}"


def fmt_duration(seconds: int) -> str:
    return f"{seconds // 60}m {seconds % 60}d"
