"""Sky radar page: polar azimuth/elevation view with steering hints."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSlider, QVBoxLayout, QWidget

from mst.core.models import PassPrediction, SatellitePosition
from mst.ui.controller import AppController
from mst.ui.theme import AMBER, BORDER, CYAN, GREEN, TEXT_MUTED
from mst.ui.widgets.common import make_button, make_card, make_label, make_page_root, set_text_color
from mst.ui.widgets.radar import RadarWidget

_LOCK_THRESHOLD_DEG = 18.0


class RadarPage(QWidget):
    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        make_page_root(self)
        self._controller = controller
        self._heading = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(make_label("Sky Radar 2D", "title"))
        self._mode = make_label("Mode North-Up (Utara Tetap)", "subtitle")
        titles.addWidget(self._mode)
        header.addLayout(titles, 1)
        self._clear_path = make_button("✕  Hapus Jalur Lintasan", "outline")
        self._clear_path.setVisible(False)
        self._clear_path.clicked.connect(lambda: controller.select_pass(None))
        header.addWidget(self._clear_path, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # Steering banner
        self._banner = make_card("cardInner")
        banner = QVBoxLayout(self._banner)
        banner.setContentsMargins(14, 8, 14, 8)
        banner.setSpacing(2)
        self._banner_title = make_label("Memuat...", "heading")
        self._banner_sub = make_label("", "mono", TEXT_MUTED)
        banner.addWidget(self._banner_title)
        banner.addWidget(self._banner_sub)
        root.addWidget(self._banner)

        # Radar
        self._radar = RadarWidget()
        root.addWidget(self._radar, 1)

        # Heading control (desktops have no compass sensor)
        heading_row = QHBoxLayout()
        heading_row.setSpacing(12)
        heading_row.addWidget(make_label("ARAH HADAP", "caption"))
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 359)
        self._slider.setValue(0)
        self._slider.valueChanged.connect(self._on_heading)
        heading_row.addWidget(self._slider, 1)
        self._heading_label = make_label("0° (Utara)", "mono", CYAN)
        self._heading_label.setMinimumWidth(110)
        heading_row.addWidget(self._heading_label)
        reset = make_button("Reset ke Utara")
        reset.clicked.connect(lambda: self._slider.setValue(0))
        heading_row.addWidget(reset)
        root.addLayout(heading_row)

        # Telemetry strip
        strip = make_card()
        row = QHBoxLayout(strip)
        row.setContentsMargins(18, 12, 18, 12)
        self._t_heading = self._stat(row, "ARAH HADAP", Qt.AlignmentFlag.AlignLeft)
        self._t_az = self._stat(row, "AZIMUTH TARGET", Qt.AlignmentFlag.AlignHCenter)
        self._t_el = self._stat(row, "ELEVASI TARGET", Qt.AlignmentFlag.AlignHCenter)
        self._t_range = self._stat(row, "JARAK", Qt.AlignmentFlag.AlignRight)
        root.addWidget(strip)

        controller.position_updated.connect(self._on_position)
        controller.selected_pass_changed.connect(self._on_pass_selected)
        self._on_position(controller.position)
        self._on_heading(0)

    @staticmethod
    def _stat(row: QHBoxLayout, title: str, align: Qt.AlignmentFlag):
        col = QVBoxLayout()
        col.setSpacing(2)
        caption = make_label(title, "caption")
        value = make_label("--", "mono")
        value.setStyleSheet("font-weight: 700; font-size: 16px; color: white;")
        caption.setAlignment(align)
        value.setAlignment(align)
        col.addWidget(caption)
        col.addWidget(value)
        row.addLayout(col, 1)
        return value

    # ---------------------------------------------------------------- handlers
    def _on_heading(self, degrees: int) -> None:
        self._heading = degrees
        self._radar.set_heading(float(degrees))
        compass = ["Utara", "Timur Laut", "Timur", "Tenggara", "Selatan", "Barat Daya", "Barat", "Barat Laut"]
        name = compass[int((degrees + 22.5) // 45) % 8]
        self._heading_label.setText(f"{degrees}° ({name})")
        self._t_heading.setText(f"{degrees}°")
        self._mode.setText("Mode North-Up (Utara Tetap)" if degrees == 0 else f"Mode Arah Hadap: {degrees}°")
        self._update_banner(self._controller.position)

    def _on_pass_selected(self, prediction: Optional[PassPrediction]) -> None:
        if prediction is None:
            self._radar.set_pass_path([])
            self._clear_path.setVisible(False)
        else:
            self._radar.set_pass_path(self._controller.pass_path(prediction))
            self._clear_path.setVisible(True)

    def _on_position(self, pos: Optional[SatellitePosition]) -> None:
        self._radar.set_position(pos)
        self._update_banner(pos)
        if pos is None:
            for label in (self._t_az, self._t_el, self._t_range):
                label.setText("--")
            return
        visible = pos.elevation_deg > 0
        self._t_az.setText(f"{pos.azimuth_deg:.1f}°")
        self._t_el.setText(f"{pos.elevation_deg:+.1f}°")
        self._t_el.setStyleSheet(
            f"font-weight: 700; font-size: 16px; color: {GREEN if visible else AMBER};"
        )
        self._t_range.setText(f"{pos.range_km:.0f} km")

    def _update_banner(self, pos: Optional[SatellitePosition]) -> None:
        if pos is None:
            self._banner_title.setText("Pilih satelit dari Katalog")
            self._banner_sub.setText("")
            return

        diff = (pos.azimuth_deg - self._heading + 540.0) % 360.0 - 180.0
        visible = pos.elevation_deg > 0
        locked = visible and abs(diff) < _LOCK_THRESHOLD_DEG

        if locked:
            title, color, border = "🎯 TARGET ACQUIRED! TEPAT DI DEPAN", GREEN, GREEN
        elif visible:
            direction = "KANAN" if diff > 0 else "KIRI"
            title, color, border = f"PUTAR KE {direction} {abs(int(diff))}°", "white", CYAN
        else:
            title, color, border = "SATELIT BERADA DI BAWAH CAKRAWALA", AMBER, BORDER

        self._banner_title.setText(title)
        set_text_color(self._banner_title, color)
        self._banner.setStyleSheet(f"QFrame#cardInner {{ border: 1px solid {border}; }}")
        active = self._controller.active_satellite
        name = active.name if active else ""
        self._banner_sub.setText(f"{name} • El: {pos.elevation_deg:+.1f}° • Az: {int(pos.azimuth_deg)}°")
