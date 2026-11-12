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
from mst.i18n import tr
from mst.ui.widgets.common import make_button, make_label

# (latitude, longitude, i18n key of the display name)
PRESETS: list[tuple[float, float, str]] = [
    (-6.2088, 106.8456, "loc.jakarta"),
    (-7.2575, 112.7521, "loc.surabaya"),
    (-6.9175, 107.6191, "loc.bandung"),
    (3.5952, 98.6722, "loc.medan"),
    (-5.1477, 119.4327, "loc.makassar"),
    (-8.6705, 115.2126, "loc.denpasar"),
    (-1.2654, 116.8312, "loc.ikn"),
]


class LocationDialog(QDialog):
    def __init__(self, current: ObserverLocation, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("loc.title"))
        self.setMinimumWidth(420)
        self.selected: Optional[ObserverLocation] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        root.addWidget(make_label(tr("loc.title"), "heading"))
        root.addWidget(make_label(tr("loc.presets"), "subtitle"))

        for lat, lon, key in PRESETS:
            label = tr(key)
            button = make_button(f"  {label}")
            button.clicked.connect(lambda _=False, a=lat, b=lon, n=label: self._choose(a, b, 10.0, n))
            root.addWidget(button)

        root.addSpacing(6)
        root.addWidget(make_label(tr("loc.manual"), "subtitle"))

        form = QFormLayout()
        form.setSpacing(8)
        self._name = QLineEdit(tr("loc.manual_name"))
        self._lat = self._spin(-90.0, 90.0, current.latitude)
        self._lon = self._spin(-180.0, 180.0, current.longitude)
        self._alt = self._spin(-500.0, 9000.0, current.altitude_m, decimals=0)
        form.addRow(tr("loc.name"), self._name)
        form.addRow(tr("loc.lat"), self._lat)
        form.addRow(tr("loc.lon"), self._lon)
        form.addRow(tr("loc.alt"), self._alt)
        root.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = make_button(tr("loc.cancel"))
        cancel.clicked.connect(self.reject)
        apply_btn = make_button(tr("loc.apply"), "primary")
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
        name = self._name.text().strip() or tr("loc.manual_name")
        self._choose(self._lat.value(), self._lon.value(), self._alt.value(), name)
