"""Live satellite telemetry window (non-modal)."""
from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from mst.i18n import tr
from mst.core.models import Satellite, SatellitePosition
from mst.ui.controller import AppController
from mst.ui.formatting import fmt_datetime
from mst.ui.theme import AMBER, BORDER, CYAN, GREEN, TEXT_MUTED, TEXT_SECONDARY
from mst.ui.widgets.common import make_button, make_card, make_label, set_text_color
from mst.ui.widgets.telemetry import TelemetryCard


class SatelliteDetailDialog(QDialog):
    open_radar = Signal()
    open_passes = Signal()

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle(tr("detail.title"))
        self.setMinimumWidth(520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        # Header: name, badges, favorite
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(6)
        self._name = make_label("", "title")
        titles.addWidget(self._name)
        badges = QHBoxLayout()
        self._norad = make_label("", "mono", CYAN)
        self._category = make_label("", "caption")
        badges.addWidget(self._norad)
        badges.addSpacing(10)
        badges.addWidget(self._category)
        badges.addStretch(1)
        titles.addLayout(badges)
        header.addLayout(titles, 1)

        self._favorite = make_button("☆", "icon")
        self._favorite.setStyleSheet("font-size: 26px;")
        self._favorite.clicked.connect(self._toggle_favorite)
        header.addWidget(self._favorite)
        root.addLayout(header)

        # Visibility banner
        self._banner = make_card("cardInner")
        banner_layout = QHBoxLayout(self._banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        self._banner_text = make_label("", "caption")
        banner_layout.addWidget(self._banner_text)
        root.addWidget(self._banner)

        # Telemetry grid
        grid = QGridLayout()
        grid.setSpacing(10)
        self._cards = {
            "latlon": TelemetryCard(tr("detail.latlon")),
            "alt": TelemetryCard(tr("detail.alt")),
            "speed": TelemetryCard(tr("detail.speed")),
            "period": TelemetryCard(tr("detail.period")),
            "azel": TelemetryCard(tr("detail.azel")),
            "range": TelemetryCard(tr("detail.range")),
            "epoch": TelemetryCard(tr("detail.epoch")),
            "age": TelemetryCard(tr("detail.age")),
        }
        for index, card in enumerate(self._cards.values()):
            grid.addWidget(card, index // 2, index % 2)
        root.addLayout(grid)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(12)
        radar = make_button(tr("detail.radar"), "outline")
        radar.clicked.connect(lambda: (self.close(), self.open_radar.emit()))
        passes = make_button(tr("detail.passes"), "primary")
        passes.clicked.connect(lambda: (self.close(), self.open_passes.emit()))
        actions.addWidget(radar)
        actions.addWidget(passes)
        root.addLayout(actions)

        controller.position_updated.connect(self._on_position)
        controller.active_satellite_changed.connect(self._on_satellite)
        self._on_satellite(controller.active_satellite)
        self._on_position(controller.position)

    # ---------------------------------------------------------------- handlers
    def _toggle_favorite(self) -> None:
        sat = self._controller.active_satellite
        if sat is not None:
            self._controller.toggle_favorite(sat.norad_id)

    def _on_satellite(self, sat: Optional[Satellite]) -> None:
        if sat is None:
            return
        self._name.setText(sat.name)
        self._norad.setText(f"NORAD #{sat.norad_id}")
        self._category.setText(sat.category)
        set_text_color(self._category, AMBER if sat.category == "INDONESIA" else TEXT_SECONDARY)
        self._favorite.setText("★" if sat.is_favorite else "☆")
        set_text_color(self._favorite, AMBER if sat.is_favorite else TEXT_SECONDARY)

        tle = self._controller.parsed_tle
        if tle is not None:
            self._cards["epoch"].set_value(fmt_datetime(tle.epoch_millis))
            age = tle.age_days(int(time.time() * 1000))
            self._cards["age"].set_value(tr("detail.days", v=age))

    def _on_position(self, pos: Optional[SatellitePosition]) -> None:
        if pos is None:
            return
        visible = pos.elevation_deg > 0
        self._banner_text.setText(
            tr("detail.vis_yes") if visible else tr("detail.vis_no")
        )
        set_text_color(self._banner_text, GREEN if visible else TEXT_SECONDARY)
        self._banner.setStyleSheet(
            f"QFrame#cardInner {{ border: 1px solid {GREEN if visible else BORDER}; }}"
        )
        self._cards["latlon"].set_value(f"{pos.latitude:+.2f}° / {pos.longitude:+.2f}°")
        self._cards["alt"].set_value(f"{pos.altitude_km:.1f} km")
        self._cards["speed"].set_value(f"{pos.velocity_km_s:.2f} km/s")
        self._cards["period"].set_value(tr("detail.minutes", v=pos.period_minutes))
        self._cards["azel"].set_value(f"{pos.azimuth_deg:.1f}° / {pos.elevation_deg:+.1f}°")
        self._cards["range"].set_value(f"{pos.range_km:.0f} km")
