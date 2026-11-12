"""Orbit map page: live world map with HUD overlays."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from mst.i18n import tr
from mst.core.models import Satellite, SatellitePosition
from mst.ui.controller import AppController
from mst.ui.dialogs.detail_dialog import SatelliteDetailDialog
from mst.ui.theme import AMBER, CYAN, GREEN, TEXT_MUTED
from mst.ui.widgets.common import (
    ClickableFrame,
    clear_layout,
    make_button,
    make_label,
    make_page_root,
    set_text_color,
)
from mst.ui.widgets.world_map import WorldMapWidget

_STALE_TLE_DAYS = 7.0


class MapPage(QWidget):
    open_radar = Signal()
    open_passes = Signal()

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        make_page_root(self)
        self._controller = controller
        self._detail: Optional[SatelliteDetailDialog] = None

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)

        self._map = WorldMapWidget()
        grid.addWidget(self._map, 0, 0)
        grid.addWidget(self._build_top_overlay(), 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self._build_bottom_strip(), 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)

        controller.position_updated.connect(self._on_position)
        controller.ground_track_updated.connect(self._map.set_ground_track)
        controller.observer_changed.connect(self._map.set_observer)
        controller.active_satellite_changed.connect(self._on_satellite)
        controller.catalog_changed.connect(self._rebuild_chips)

        # Pull the current state (this page may be rebuilt after a language switch).
        self._map.set_observer(controller.observer)
        self._map.set_ground_track(controller.ground_track)
        self._on_satellite(controller.active_satellite)
        self._on_position(controller.position)

    # ------------------------------------------------------------------- build
    def _build_top_overlay(self) -> QWidget:
        container = QWidget()
        container.setMaximumWidth(1100)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 0)
        layout.setSpacing(10)

        self._hud = ClickableFrame()
        self._hud.setObjectName("hud")
        self._hud.setMaximumWidth(620)
        self._hud.clicked.connect(self._show_detail)
        hud_layout = QHBoxLayout(self._hud)
        hud_layout.setContentsMargins(16, 12, 12, 12)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self._hud_name = make_label(tr("map.pick"), "heading")
        self._hud_stats = make_label("", "mono")
        self._hud_stats.setTextFormat(Qt.TextFormat.RichText)
        self._hud_warn = make_label("", "subtitle", AMBER)
        self._hud_warn.setVisible(False)
        text_col.addWidget(self._hud_name)
        text_col.addWidget(self._hud_stats)
        text_col.addWidget(self._hud_warn)
        hud_layout.addLayout(text_col, 1)

        info = make_button(tr("map.detail"), "outline")
        info.clicked.connect(self._show_detail)
        hud_layout.addWidget(info)
        layout.addWidget(self._hud)

        self._chips_box = QWidget()
        self._chips = QHBoxLayout(self._chips_box)
        self._chips.setContentsMargins(0, 0, 0, 0)
        self._chips.setSpacing(8)
        layout.addWidget(self._chips_box)
        return container

    def _build_bottom_strip(self) -> QWidget:
        container = QWidget()
        container.setMinimumWidth(620)
        outer = QVBoxLayout(container)
        outer.setContentsMargins(16, 0, 16, 16)

        strip = ClickableFrame()
        strip.setObjectName("hud")
        strip.clicked.connect(self._show_detail)
        row = QHBoxLayout(strip)
        row.setContentsMargins(18, 12, 18, 12)

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(make_label(tr("map.subsat"), "caption"))
        self._sub_pos = make_label(tr("map.loading"), "mono")
        self._sub_pos.setStyleSheet("font-weight: 700; font-size: 14px; color: white;")
        left.addWidget(self._sub_pos)

        right = QVBoxLayout()
        right.setSpacing(2)
        caption = make_label(tr("map.elaz"), "caption")
        caption.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(caption)
        self._el_az = make_label("", "mono")
        self._el_az.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._el_az.setStyleSheet("font-weight: 700; font-size: 14px; color: white;")
        right.addWidget(self._el_az)

        row.addLayout(left, 1)
        row.addLayout(right)
        outer.addWidget(strip)
        return container

    # ---------------------------------------------------------------- handlers
    def _show_detail(self) -> None:
        if self._controller.active_satellite is None:
            return
        if self._detail is not None:
            self._detail.raise_()
            self._detail.activateWindow()
            return
        dialog = SatelliteDetailDialog(self._controller, self.window())
        dialog.open_radar.connect(self.open_radar)
        dialog.open_passes.connect(self.open_passes)
        dialog.destroyed.connect(lambda: setattr(self, "_detail", None))
        self._detail = dialog
        dialog.show()

    def _on_satellite(self, sat: Optional[Satellite]) -> None:
        self._hud_name.setText(sat.name if sat else tr("map.pick"))
        self._rebuild_chips()
        age = self._controller.tle_age_days()
        if age is not None and age > _STALE_TLE_DAYS:
            self._hud_warn.setText(tr("map.tle_warn", days=age))
            self._hud_warn.setVisible(True)
        else:
            self._hud_warn.setVisible(False)

    def _on_position(self, pos: Optional[SatellitePosition]) -> None:
        self._map.set_position(pos)
        if pos is None:
            return
        visible = pos.elevation_deg > 0
        status_color = GREEN if visible else TEXT_MUTED
        self._hud_stats.setText(
            f'<span style="color:{CYAN}">ALT: {pos.altitude_km:.0f} km</span> • '
            f'<span style="color:{AMBER}">SPD: {pos.velocity_km_s:.2f} km/s</span> • '
            f'<b style="color:{status_color}">{tr("map.visible") if visible else tr("map.hidden")}</b>'
        )
        self._sub_pos.setText(f"LAT {pos.latitude:+.2f}°  LON {pos.longitude:+.2f}°")
        self._el_az.setText(f"EL {pos.elevation_deg:+.1f}°  AZ {pos.azimuth_deg:.0f}°")
        set_text_color(self._el_az, GREEN if visible else AMBER)
        self._el_az.setStyleSheet(
            f"font-weight: 700; font-size: 14px; color: {GREEN if visible else AMBER};"
        )

    def _rebuild_chips(self) -> None:
        clear_layout(self._chips)
        active = self._controller.active_satellite
        for sat in self._controller.quick_satellites(8):
            name = sat.name
            for noise in (" (INDONESIA)", " (MERAH PUTIH)", " SPACE TELESCOPE", " (ZARYA)", " (TIANGONG)", " / ORARI", " / IPB"):
                name = name.replace(noise, "")
            chip = make_button(name, "chip", checkable=True)
            chip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            chip.setChecked(active is not None and sat.norad_id == active.norad_id)
            chip.clicked.connect(lambda _=False, s=sat: self._controller.select_satellite(s))
            self._chips.addWidget(chip)
        self._chips.addStretch(1)
