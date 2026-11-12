"""Locale-aware formatting helpers (Indonesian / English)."""
from __future__ import annotations

from datetime import datetime

from mst.i18n import current_language, tr

_DAYS = {
    "id": ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"],  # Monday = 0
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
_MONTHS = {
    "id": ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def fmt_date(millis: int) -> str:
    d = datetime.fromtimestamp(millis / 1000.0)
    lang = current_language()
    return f"{_DAYS[lang][d.weekday()]}, {d.day:02d} {_MONTHS[lang][d.month - 1]} {d.year}"


def fmt_time(millis: int) -> str:
    return datetime.fromtimestamp(millis / 1000.0).strftime("%H:%M:%S")


def fmt_datetime(millis: int) -> str:
    return f"{fmt_date(millis)} {fmt_time(millis)}"


def fmt_duration(seconds: int) -> str:
    return tr("fmt.duration", m=seconds // 60, s=seconds % 60)
