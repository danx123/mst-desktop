"""Main window: sidebar navigation + stacked pages, fullscreen and language picker."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mst import __version__
from mst.core.models import ObserverLocation
from mst.i18n import LANGUAGES, current_language, tr
from mst.ui.controller import AppController
from mst.ui.pages.catalog_page import CatalogPage
from mst.ui.pages.map_page import MapPage
from mst.ui.pages.passes_page import PassesPage
from mst.ui.pages.radar_page import RadarPage
from mst.ui.widgets.common import make_button, make_label

_NAV = [("nav.map", "Ctrl+1"), ("nav.catalog", "Ctrl+2"), ("nav.passes", "Ctrl+3"), ("nav.radar", "Ctrl+4")]
MAP, CATALOG, PASSES, RADAR = range(4)


class MainWindow(QMainWindow):
    language_requested = Signal(str)

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._was_maximized = False
        self._discarded = False  # True when replaced by a rebuilt window (language switch)

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

        # Shortcuts: Ctrl+1..4 pages, F11 enters fullscreen, Esc leaves it.
        for index, (_, shortcut) in enumerate(_NAV):
            QShortcut(QKeySequence(shortcut), self, activated=lambda i=index: self.navigate(i))
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.exit_fullscreen)

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
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(6)

        layout.addWidget(make_label("MST", "brand"))
        layout.addWidget(make_label("Macan Satellite Tracker", "subtitle"))
        layout.addSpacing(18)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons = []
        for index, (key, shortcut) in enumerate(_NAV):
            button = make_button(tr(key), "nav", checkable=True)
            button.setToolTip(shortcut)
            button.clicked.connect(lambda _=False, i=index: self.navigate(i))
            self._nav_group.addButton(button)
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)

        self._fs_button = make_button(tr("side.fullscreen"), "outline")
        self._fs_button.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(self._fs_button)
        layout.addSpacing(10)

        layout.addWidget(make_label(tr("side.language"), "caption"))
        self._language = QComboBox()
        for code, name in LANGUAGES.items():
            self._language.addItem(name, code)
        self._language.setCurrentIndex(self._language.findData(current_language()))
        self._language.currentIndexChanged.connect(self._on_language_chosen)
        layout.addWidget(self._language)
        layout.addSpacing(10)

        self._observer_label = make_label("", "subtitle", wrap=True)
        self._clock_label = make_label("", "mono")
        layout.addWidget(make_label(tr("side.observer"), "caption"))
        layout.addWidget(self._observer_label)
        layout.addSpacing(8)
        layout.addWidget(make_label(tr("side.utc"), "caption"))
        layout.addWidget(self._clock_label)
        layout.addSpacing(8)
        layout.addWidget(make_label(f"v{__version__}", "caption"))
        return sidebar

    # -------------------------------------------------------------- navigation
    def navigate(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._nav_buttons[index].setChecked(True)

    def current_page(self) -> int:
        return self._stack.currentIndex()

    # -------------------------------------------------------------- fullscreen
    def enter_fullscreen(self) -> None:
        if not self.isFullScreen():
            self._was_maximized = self.isMaximized()
            self.showFullScreen()

    def exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showMaximized() if self._was_maximized else self.showNormal()

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def _update_fullscreen_button(self) -> None:
        if hasattr(self, "_fs_button"):
            key = "side.exit_fullscreen" if self.isFullScreen() else "side.fullscreen"
            self._fs_button.setText(tr(key))

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_fullscreen_button()
        super().changeEvent(event)

    # ------------------------------------------------- state hand-over (i18n)
    def capture_state(self) -> dict[str, Any]:
        return {
            "geometry": self.saveGeometry(),
            "page": self.current_page(),
            "fullscreen": self.isFullScreen(),
            "maximized": self._was_maximized if self.isFullScreen() else self.isMaximized(),
        }

    def show_with_state(self, state: Optional[dict[str, Any]] = None) -> None:
        if not state:
            self.show()
            return
        self.restoreGeometry(state["geometry"])
        self.navigate(state["page"])
        self._was_maximized = state["maximized"]
        if state["fullscreen"]:
            self.showFullScreen()
        elif state["maximized"]:
            self.showMaximized()
        else:
            self.show()

    def discard(self) -> None:
        """Retire this window after a language switch without stopping the controller."""
        self._discarded = True
        self._clock.stop()
        self.hide()
        self.deleteLater()

    # ---------------------------------------------------------------- handlers
    def _on_language_chosen(self, _index: int) -> None:
        code = self._language.currentData()
        if code and code != current_language():
            self.language_requested.emit(code)

    def _on_observer(self, observer: ObserverLocation) -> None:
        self._observer_label.setText(f"{observer.name}\n{observer.latitude:.3f}°, {observer.longitude:.3f}°")

    def _update_clock(self) -> None:
        self._clock_label.setText(datetime.now(timezone.utc).strftime("%H:%M:%S"))

    def closeEvent(self, event) -> None:  # noqa: N802
        if not self._discarded:
            self._controller.stop()
        super().closeEvent(event)
