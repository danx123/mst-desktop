"""Observer location picker: Indonesian presets or manual coordinates."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from mst.core.models import ObserverLocation
from mst.ui.widgets.common import make_button, make_label

PRESETS: list[tuple[float, float, str]] = [
    (-6.2088, 106.8456, "Jakarta (Monas)"),
    (-7.2575, 112.7521, "Surabaya (Jawa Timur)"),
    (-6.9175, 107.6191, "Bandung (Observatorium Bosscha)"),
    (3.5952, 98.6722, "Medan (Sumatera Utara)"),
    (-5.1477, 119.4327, "Makassar (Sulawesi Selatan)"),
    (-8.6705, 115.2126, "Denpasar (Bali)"),
    (-1.2654, 116.8312, "IKN Nusantara (Kalimantan)"),
]


class LocationDialog(QDialog):
    def __init__(self, current: ObserverLocation, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pilih Lokasi Pengamat")
        self.setMinimumWidth(420)
        self.selected: Optional[ObserverLocation] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        root.addWidget(make_label("Pilih Lokasi Pengamat", "heading"))
        root.addWidget(make_label("Kota Preset Indonesia:", "subtitle"))

        for lat, lon, label in PRESETS:
            button = make_button(f"  {label}")
            button.clicked.connect(lambda _=False, a=lat, b=lon, n=label: self._choose(a, b, 10.0, n))
            root.addWidget(button)

        root.addSpacing(6)
        root.addWidget(make_label("Atau Masukkan Koordinat Manual:", "subtitle"))

        form = QFormLayout()
        form.setSpacing(8)
        self._name = QLineEdit("Koordinat Manual")
        self._lat = self._spin(-90.0, 90.0, current.latitude)
        self._lon = self._spin(-180.0, 180.0, current.longitude)
        self._alt = self._spin(-500.0, 9000.0, current.altitude_m, decimals=0)
        form.addRow("Nama", self._name)
        form.addRow("Lintang (Lat)", self._lat)
        form.addRow("Bujur (Lon)", self._lon)
        form.addRow("Ketinggian (m)", self._alt)
        root.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = make_button("Batal")
        cancel.clicked.connect(self.reject)
        apply_btn = make_button("Terapkan", "primary")
        apply_btn.clicked.connect(self._apply_manual)
        actions.addWidget(cancel)
        actions.addWidget(apply_btn)
        root.addLayout(actions)

    @staticmethod
    def _spin(minimum: float, maximum: float, value: float, decimals: int = 4) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setDecimals(decimals)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    def _choose(self, lat: float, lon: float, alt: float, name: str) -> None:
        self.selected = ObserverLocation(lat, lon, alt, name)
        self.accept()

    def _apply_manual(self) -> None:
        name = self._name.text().strip() or "Koordinat Manual"
        self._choose(self._lat.value(), self._lon.value(), self._alt.value(), name)
