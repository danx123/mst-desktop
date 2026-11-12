"""Main window: sidebar navigation + stacked pages."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mst import __version__
from mst.core.models import ObserverLocation
from mst.ui.controller import AppController
from mst.ui.pages.catalog_page import CatalogPage
from mst.ui.pages.map_page import MapPage
from mst.ui.pages.passes_page import PassesPage
from mst.ui.pages.radar_page import RadarPage
from mst.ui.widgets.common import make_button, make_label

_NAV = [
    ("◍  Peta Orbit", "Ctrl+1"),
    ("☰  Katalog", "Ctrl+2"),
    ("◷  Prediksi", "Ctrl+3"),
    ("◎  Sky Radar", "Ctrl+4"),
]
MAP, CATALOG, PASSES, RADAR = range(4)


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle("MST — Macan Satellite Tracker")        
        self.resize(1240, 800)
        self.setMinimumSize(980, 640)        

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        root.addWidget(self._build_sidebar())

        self._stack = QStackedWidget()
        self._map = MapPage(controller)
        self._catalog = CatalogPage(controller)
        self._passes = PassesPage(controller)
        self._radar = RadarPage(controller)
        for page in (self._map, self._catalog, self._passes, self._radar):
            self._stack.addWidget(page)
        root.addWidget(self._stack, 1)

        # Cross-page navigation
        self._map.open_radar.connect(lambda: self.navigate(RADAR))
        self._map.open_passes.connect(lambda: self.navigate(PASSES))
        self._catalog.navigate_to_map.connect(lambda: self.navigate(MAP))
        self._passes.open_radar.connect(lambda: self.navigate(RADAR))

        for index, (_, shortcut) in enumerate(_NAV):
            QShortcut(QKeySequence(shortcut), self, activated=lambda i=index: self.navigate(i))

        controller.observer_changed.connect(self._on_observer)
        self._on_observer(controller.observer)

        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start()
        self._update_clock()

        self.navigate(MAP)

    # ------------------------------------------------------------------- build
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(6)

        layout.addWidget(make_label("MST", "brand"))
        layout.addWidget(make_label("Macan Satellite Tracker", "subtitle"))
        layout.addSpacing(18)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons = []
        for index, (label, shortcut) in enumerate(_NAV):
            button = make_button(label, "nav", checkable=True)
            button.setToolTip(shortcut)
            button.clicked.connect(lambda _=False, i=index: self.navigate(i))
            self._nav_group.addButton(button)
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)
        self._observer_label = make_label("", "subtitle", wrap=True)
        self._clock_label = make_label("", "mono")
        layout.addWidget(make_label("PENGAMAT", "caption"))
        layout.addWidget(self._observer_label)
        layout.addSpacing(8)
        layout.addWidget(make_label("WAKTU UTC", "caption"))
        layout.addWidget(self._clock_label)
        layout.addSpacing(8)
        layout.addWidget(make_label(f"v{__version__}", "caption"))
        return sidebar

    # ---------------------------------------------------------------- handlers
    def navigate(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._nav_buttons[index].setChecked(True)

    def _on_observer(self, observer: ObserverLocation) -> None:
        self._observer_label.setText(f"{observer.name}\n{observer.latitude:.3f}°, {observer.longitude:.3f}°")

    def _update_clock(self) -> None:
        self._clock_label.setText(datetime.now(timezone.utc).strftime("%H:%M:%S"))

    def closeEvent(self, event) -> None:  # noqa: N802
        self._controller.stop()
        super().closeEvent(event)
