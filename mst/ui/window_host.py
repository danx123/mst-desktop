"""WindowHost: owns the main window and rebuilds it when the language changes."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QSettings, QTimer

from mst.i18n import current_language, set_language
from mst.ui.controller import AppController
from mst.ui.main_window import MainWindow


class WindowHost(QObject):
    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self._controller = controller
        self._window: Optional[MainWindow] = None

    @property
    def window(self) -> Optional[MainWindow]:
        return self._window

    def show(self) -> None:
        self._window = self._create()
        self._window.show()

    def switch_language(self, code: str) -> None:
        """Apply a new language: rebuild the window, keeping size, page and fullscreen."""
        if self._window is None or code == current_language():
            return
        set_language(code)
        QSettings("MacanAngkasa", "MST").setValue("language", code)

        old = self._window
        state = old.capture_state()
        new = self._create()
        new.show_with_state(state)
        self._window = new
        old.discard()

    def _create(self) -> MainWindow:
        window = MainWindow(self._controller)
        # Deferred: the signal is emitted from inside the old window's combo box.
        window.language_requested.connect(lambda code: QTimer.singleShot(0, lambda: self.switch_language(code)))
        return window
