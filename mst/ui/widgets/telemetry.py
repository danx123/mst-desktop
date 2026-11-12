"""Telemetry value card (title + monospace value)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from mst.ui.theme import CYAN
from mst.ui.widgets.common import make_card, make_label


class TelemetryCard(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("cardInner")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        layout.addWidget(make_label(title, "caption", CYAN))
        self._value = make_label("--", "mono")
        self._value.setStyleSheet("font-weight: 700; font-size: 14px; color: white;")
        layout.addWidget(self._value)

    def set_value(self, text: str) -> None:
        self._value.setText(text)
