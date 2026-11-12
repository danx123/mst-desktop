"""Satellite catalog page: search, category filter, favorites, CelesTrak sync."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMenu,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from mst.core.models import Satellite
from mst.data.celestrak import SYNC_GROUPS
from mst.ui.controller import AppController
from mst.ui.theme import AMBER, CYAN, TEXT_MUTED, TEXT_SECONDARY
from mst.ui.widgets.common import make_button, make_card, make_label, make_page_root

CATEGORIES = [
    ("ALL", "Semua"),
    ("FAVORITES", "Favorit"),
    ("INDONESIA", "Indonesia"),
    ("STATIONS", "Stasiun"),
    ("WEATHER", "Cuaca"),
    ("STARLINK", "Starlink"),
    ("GEO", "Geostasioner"),
]


class SatelliteTableModel(QAbstractTableModel):
    HEADERS = ["★", "Nama Satelit", "NORAD ID", "Kategori"]

    def __init__(self) -> None:
        super().__init__()
        self._items: list[Satellite] = []
        self._active_id: Optional[int] = None

    def set_items(self, items: list[Satellite]) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def set_active(self, norad_id: Optional[int]) -> None:
        self._active_id = norad_id
        if self._items:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._items) - 1, 3))

    def satellite_at(self, row: int) -> Satellite:
        return self._items[row]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        sat = self._items[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return ["★" if sat.is_favorite else "☆", sat.name, str(sat.norad_id), sat.category][col]
        if role == Qt.ItemDataRole.UserRole:  # sort key
            return [int(sat.is_favorite), sat.name.lower(), sat.norad_id, sat.category][col]
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 0:
                return QColor(AMBER if sat.is_favorite else TEXT_MUTED)
            if col == 2:
                return QColor(CYAN)
            if col == 3:
                return QColor(AMBER if sat.category == "INDONESIA" else TEXT_SECONDARY)
            return QColor("white")
        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            if col == 1:
                font.setBold(True)
            if col == 2:
                font.setFamilies(["Consolas", "DejaVu Sans Mono", "monospace"])
            if col == 0:
                font.setPointSize(13)
            return font
        if role == Qt.ItemDataRole.TextAlignmentRole and col == 0:
            return int(Qt.AlignmentFlag.AlignCenter)
        if role == Qt.ItemDataRole.BackgroundRole and sat.norad_id == self._active_id:
            return QColor(0, 229, 255, 34)
        if role == Qt.ItemDataRole.ToolTipRole and col == 0:
            return "Klik untuk tandai / hapus favorit"
        return None


class SatelliteFilterProxy(QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self._category = "ALL"
        self._query = ""
        self.setSortRole(Qt.ItemDataRole.UserRole)

    def set_category(self, category: str) -> None:
        self._category = category
        self.invalidateFilter()

    def set_query(self, query: str) -> None:
        self._query = query.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        sat = self.sourceModel().satellite_at(source_row)  # type: ignore[attr-defined]
        if self._category == "FAVORITES" and not sat.is_favorite:
            return False
        if self._category not in ("ALL", "FAVORITES") and sat.category != self._category:
            return False
        if self._query:
            return self._query in sat.name.lower() or self._query in str(sat.norad_id)
        return True


class CatalogPage(QWidget):
    navigate_to_map = Signal()

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        make_page_root(self)
        self._controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(make_label("Katalog Satelit", "title"))
        self._count = make_label("", "subtitle")
        titles.addWidget(self._count)
        header.addLayout(titles, 1)

        self._sync_button = QToolButton()
        self._sync_button.setText("⟳  CelesTrak")
        self._sync_button.setProperty("variant", "accent")
        self._sync_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._sync_button.setCursor(Qt.CursorShape.PointingHandCursor)
        menu = QMenu(self._sync_button)
        for group, category, label in SYNC_GROUPS:
            action = menu.addAction(label)
            action.triggered.connect(lambda _=False, g=group, c=category: controller.sync_celestrak(g, c))
        self._sync_button.setMenu(menu)
        header.addWidget(self._sync_button, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # Sync banner
        self._banner = make_card("cardActive")
        banner_layout = QHBoxLayout(self._banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)
        self._banner_text = make_label("", "subtitle", "white")
        banner_layout.addWidget(self._banner_text)
        self._banner.setVisible(False)
        root.addWidget(self._banner)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cari nama satelit atau NORAD ID...")
        self._search.setClearButtonEnabled(True)
        root.addWidget(self._search)

        # Category chips
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self._chip_group = QButtonGroup(self)
        self._chip_group.setExclusive(True)
        for key, label in CATEGORIES:
            chip = make_button(label, "chip", checkable=True)
            chip.setProperty("category", key)
            chip.setChecked(key == "ALL")
            self._chip_group.addButton(chip)
            chips.addWidget(chip)
        chips.addStretch(1)
        root.addLayout(chips)

        # Table
        self._model = SatelliteTableModel()
        self._proxy = SatelliteFilterProxy()
        self._proxy.setSourceModel(self._model)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().hide()
        self._table.verticalHeader().setDefaultSectionSize(40)
        self._table.setShowGrid(False)
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setColumnWidth(0, 48)
        self._table.setSortingEnabled(True)
        self._table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        root.addWidget(self._table, 1)

        # Footer actions
        footer = QHBoxLayout()
        footer.addWidget(make_label("Klik ★ untuk favorit • klik dua kali untuk melacak", "subtitle"))
        footer.addStretch(1)
        self._track_button = make_button("Lacak Satelit Terpilih", "primary")
        footer.addWidget(self._track_button)
        root.addLayout(footer)

        # Wiring
        self._search.textChanged.connect(self._on_filter_changed)
        self._chip_group.buttonClicked.connect(self._on_filter_changed)
        self._table.clicked.connect(self._on_clicked)
        self._table.doubleClicked.connect(self._on_double_clicked)
        self._track_button.clicked.connect(self._track_selected)
        self._proxy.rowsInserted.connect(self._update_count)
        self._proxy.rowsRemoved.connect(self._update_count)
        self._proxy.modelReset.connect(self._update_count)
        self._proxy.layoutChanged.connect(self._update_count)

        controller.catalog_changed.connect(self._reload)
        controller.active_satellite_changed.connect(self._on_active)
        controller.syncing_changed.connect(lambda busy: self._sync_button.setEnabled(not busy))
        controller.sync_message_changed.connect(self._on_sync_message)

        self._reload()

    # ---------------------------------------------------------------- handlers
    def _reload(self) -> None:
        self._model.set_items(list(self._controller.satellites))
        active = self._controller.active_satellite
        self._model.set_active(active.norad_id if active else None)
        self._update_count()

    def _on_active(self, sat: Optional[Satellite]) -> None:
        self._model.set_active(sat.norad_id if sat else None)

    def _on_filter_changed(self, *_args: object) -> None:
        checked = self._chip_group.checkedButton()
        self._proxy.set_category(checked.property("category") if checked else "ALL")
        self._proxy.set_query(self._search.text())
        self._update_count()

    def _update_count(self, *_args: object) -> None:
        self._count.setText(f"{self._proxy.rowCount()} Satelit Tersedia (Offline Ready)")

    def _satellite_at(self, proxy_index: QModelIndex) -> Satellite:
        return self._model.satellite_at(self._proxy.mapToSource(proxy_index).row())

    def _on_clicked(self, index: QModelIndex) -> None:
        if index.column() == 0:
            self._controller.toggle_favorite(self._satellite_at(index).norad_id)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        if index.column() != 0:
            self._select(self._satellite_at(index))

    def _track_selected(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            self._select(self._satellite_at(indexes[0]))

    def _select(self, sat: Satellite) -> None:
        self._controller.select_satellite(sat)
        self.navigate_to_map.emit()

    def _on_sync_message(self, message: str) -> None:
        self._banner.setVisible(bool(message))
        self._banner_text.setText("ⓘ  " + message if message else "")
