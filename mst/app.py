"""Application bootstrap: wires data layer, controller and main window."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QSettings, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from mst import __version__
from mst.data.database import SatelliteDatabase
from mst.data.repository import SatelliteRepository
from mst.i18n import LANGUAGES, detect_language, set_language
from mst.resources import APP_ICON, resource_path
from mst.ui.controller import AppController
from mst.ui.theme import STYLESHEET
from mst.ui.window_host import WindowHost

APP_ID = "MacanAngkasa.MST"


def _data_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = Path(base) if base else Path.home() / ".mst"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _init_language() -> None:
    saved = QSettings("MacanAngkasa", "MST").value("language", "", type=str)
    set_language(saved if saved in LANGUAGES else detect_language(QLocale.system().name()))


def _set_windows_app_id() -> None:
    """Give Windows our own taskbar identity so the custom icon is used."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except (AttributeError, OSError):
            pass


def run(argv: list[str] | None = None) -> int:
    _set_windows_app_id()
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("MST")
    app.setOrganizationName("MacanAngkasa")
    app.setApplicationVersion(__version__)
    app.setStyleSheet(STYLESHEET)

    icon_path = resource_path(APP_ICON)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    _init_language()

    database = SatelliteDatabase(_data_dir() / "mst_satellite.db")
    controller = AppController(SatelliteRepository(database))
    host = WindowHost(controller)
    host.show()
    controller.start()

    code = app.exec()
    database.close()
    return code
