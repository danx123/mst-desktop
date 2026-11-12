"""Application bootstrap: wires data layer, controller and main window."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

from mst import __version__
from mst.data.database import SatelliteDatabase
from mst.data.repository import SatelliteRepository
from mst.ui.controller import AppController
from mst.ui.main_window import MainWindow
from mst.ui.theme import STYLESHEET


def _data_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = Path(base) if base else Path.home() / ".mst"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("MST")
    app.setOrganizationName("MacanAngkasa")
    app.setApplicationVersion(__version__)
    app.setStyleSheet(STYLESHEET)

    database = SatelliteDatabase(_data_dir() / "mst_satellite.db")
    controller = AppController(SatelliteRepository(database))
    window = MainWindow(controller)
    window.show()
    controller.start()

    code = app.exec()
    database.close()
    return code
