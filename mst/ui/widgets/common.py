"""Small reusable widgets and helpers shared across pages."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


def make_label(
    text: str = "",
    role: Optional[str] = None,
    color: Optional[str] = None,
    wrap: bool = False,
    parent: Optional[QWidget] = None,
) -> QLabel:
    label = QLabel(text, parent)
    if role:
        label.setProperty("role", role)
    if color:
        set_text_color(label, color)
    label.setWordWrap(wrap)
    return label


def set_text_color(label: QLabel, color: str) -> None:
    label.setStyleSheet(f"color: {color};")


def make_button(text: str, variant: Optional[str] = None, checkable: bool = False) -> QPushButton:
    button = QPushButton(text)
    if variant:
        button.setProperty("variant", variant)
    button.setCheckable(checkable)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def make_card(object_name: str = "card") -> QFrame:
    frame = QFrame()
    frame.setObjectName(object_name)
    return frame


def make_page_root(widget: QWidget) -> None:
    widget.setObjectName("page")
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


def repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


class ClickableFrame(QFrame):
    clicked = Signal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)
