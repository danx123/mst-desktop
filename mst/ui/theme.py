"""Deep-space dark theme: palette constants + global Qt stylesheet."""
from __future__ import annotations

from PySide6.QtGui import QColor

BLACK = "#0A0E17"
SURFACE = "#111726"
SURFACE_VARIANT = "#182238"
CARD = "#1C2740"

CYAN = "#00E5FF"
AMBER = "#FF9100"
GREEN = "#00E676"
RED = "#FF5252"

TEXT_PRIMARY = "#F0F4F8"
TEXT_SECONDARY = "#90A4AE"
TEXT_MUTED = "#607D8B"

BORDER = "#24324D"

MONO_FAMILY = "Consolas, 'DejaVu Sans Mono', 'Courier New', monospace"


def qcolor(hex_color: str, alpha: float = 1.0) -> QColor:
    color = QColor(hex_color)
    color.setAlphaF(max(0.0, min(1.0, alpha)))
    return color


STYLESHEET = f"""
* {{ font-family: "Segoe UI", "Inter", "Noto Sans", "DejaVu Sans", sans-serif; font-size: 13px; }}
QMainWindow, QDialog {{ background: {BLACK}; }}
QWidget {{ color: {TEXT_PRIMARY}; }}
QWidget#page {{ background: {BLACK}; }}
QLabel {{ background: transparent; border: none; }}

QFrame#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#cardActive {{ background: {CARD}; border: 1px solid {CYAN}; border-radius: 12px; }}
QFrame#cardInner {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; }}
QFrame#hud {{ background: rgba(17, 23, 38, 235); border: 1px solid {BORDER}; border-radius: 14px; }}
QFrame#badge {{ background: {SURFACE_VARIANT}; border: 1px solid {BORDER}; border-radius: 6px; }}

QLabel[role="title"] {{ font-size: 22px; font-weight: 700; color: white; }}
QLabel[role="heading"] {{ font-size: 15px; font-weight: 700; color: white; }}
QLabel[role="subtitle"] {{ font-size: 12px; color: {TEXT_SECONDARY}; }}
QLabel[role="caption"] {{ font-size: 10px; font-weight: 600; color: {TEXT_MUTED}; letter-spacing: 1px; }}
QLabel[role="mono"] {{ font-family: {MONO_FAMILY}; font-size: 12px; }}
QLabel[role="brand"] {{ font-size: 20px; font-weight: 800; color: {CYAN}; letter-spacing: 3px; }}

QPushButton, QToolButton {{
    background: {SURFACE_VARIANT}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 14px; font-weight: 600;
}}
QPushButton:hover, QToolButton:hover {{ border-color: {CYAN}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {TEXT_MUTED}; }}
QToolButton::menu-indicator {{ image: none; }}
QPushButton[variant="primary"] {{ background: {CYAN}; color: {BLACK}; border: 1px solid {CYAN}; font-weight: 700; }}
QPushButton[variant="primary"]:hover {{ background: #4DEEFF; }}
QPushButton[variant="outline"] {{ background: transparent; color: {CYAN}; border: 1px solid {CYAN}; }}
QPushButton[variant="outline"]:hover {{ background: rgba(0, 229, 255, 30); }}
QPushButton[variant="accent"], QToolButton[variant="accent"] {{ color: {CYAN}; }}
QPushButton[variant="chip"] {{ border-radius: 14px; padding: 5px 12px; font-weight: 500; }}
QPushButton[variant="chip"]:checked {{ background: {CYAN}; color: {BLACK}; border-color: {CYAN}; font-weight: 700; }}
QPushButton[variant="nav"] {{
    text-align: left; padding: 11px 16px; border: none; border-radius: 10px;
    background: transparent; color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 600;
}}
QPushButton[variant="nav"]:hover {{ background: {SURFACE_VARIANT}; }}
QPushButton[variant="nav"]:checked {{ background: {CYAN}; color: {BLACK}; font-weight: 700; }}
QPushButton[variant="icon"] {{ background: transparent; border: none; font-size: 18px; padding: 2px 8px; }}

QLineEdit, QDoubleSpinBox, QComboBox {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 10px;
    color: white; selection-background-color: {CYAN}; selection-color: {BLACK};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {CYAN}; }}

QTableView {{
    background: {SURFACE}; alternate-background-color: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 10px; gridline-color: transparent;
    selection-background-color: {CARD}; selection-color: white; outline: 0;
}}
QTableView::item {{ padding: 4px 8px; border-bottom: 1px solid {BORDER}; }}
QHeaderView::section {{
    background: {SURFACE_VARIANT}; color: {TEXT_SECONDARY}; border: none;
    padding: 8px; font-weight: 600;
}}

QScrollArea {{ border: none; background: transparent; }}
QWidget#scrollContent {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenu {{ background: {SURFACE}; border: 1px solid {BORDER}; padding: 6px; }}
QMenu::item {{ padding: 8px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {CARD}; color: {CYAN}; }}

QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {CYAN}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {CYAN}; width: 16px; margin: -6px 0; border-radius: 8px; }}

QToolTip {{ background: {CARD}; color: white; border: 1px solid {BORDER}; padding: 4px 8px; }}
"""
