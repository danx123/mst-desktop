"""Pass prediction page: next 48 hours of passes over the observer."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from mst.i18n import tr
from mst.core.models import ObserverLocation, PassPrediction, Satellite
from mst.ui.controller import AppController
from mst.ui.dialogs.location_dialog import LocationDialog
from mst.ui.formatting import fmt_date, fmt_duration, fmt_time
from mst.ui.theme import AMBER, CYAN, GREEN, TEXT_SECONDARY
from mst.ui.widgets.common import (
    clear_layout,
    make_button,
    make_card,
    make_label,
    make_page_root,
    set_text_color,
)


class PassCard(QWidget):
    open_radar = Signal(object)

    def __init__(self, prediction: PassPrediction, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._prediction = prediction

        if prediction.max_elevation_deg >= 50.0:
            color, quality = GREEN, tr("pass.excellent")
        elif prediction.max_elevation_deg >= 25.0:
            color, quality = AMBER, tr("pass.fair")
        else:
            color, quality = TEXT_SECONDARY, tr("pass.low")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = make_card()
        outer.addWidget(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addWidget(make_label(fmt_date(prediction.aos_time_millis), "heading"))
        top.addStretch(1)
        badge = make_label(quality, "caption", color)
        badge.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; padding: 2px 8px;"
            f"border: 1px solid {color}; border-radius: 6px;"
        )
        top.addWidget(badge)
        layout.addLayout(top)

        times = QHBoxLayout()
        times.addLayout(self._column(tr("pass.aos"), fmt_time(prediction.aos_time_millis),
                                     f"Az {int(prediction.aos_azimuth_deg)}°", Qt.AlignmentFlag.AlignLeft))
        times.addLayout(self._column(tr("pass.peak"), f"{prediction.max_elevation_deg:.1f}°",
                                     fmt_time(prediction.max_elevation_time_millis),
                                     Qt.AlignmentFlag.AlignHCenter, value_color=color, big=True))
        times.addLayout(self._column(tr("pass.los"), fmt_time(prediction.los_time_millis),
                                     f"Az {int(prediction.los_azimuth_deg)}°", Qt.AlignmentFlag.AlignRight))
        layout.addLayout(times)

        footer = QHBoxLayout()
        footer.addWidget(make_label(tr("pass.duration", d=fmt_duration(prediction.duration_seconds)), "subtitle"))
        footer.addStretch(1)
        radar = make_button(tr("pass.open_radar"), "outline")
        radar.clicked.connect(lambda: self.open_radar.emit(self._prediction))
        footer.addWidget(radar)
        layout.addLayout(footer)

    @staticmethod
    def _column(title: str, value: str, sub: str, align: Qt.AlignmentFlag,
                value_color: str = "white", big: bool = False) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(2)
        labels = [
            make_label(title, "caption"),
            make_label(value, "mono"),
            make_label(sub, "subtitle"),
        ]
        labels[1].setStyleSheet(
            f"font-weight: 700; color: {value_color}; font-size: {18 if big else 14}px;"
        )
        for label in labels:
            label.setAlignment(align)
            col.addWidget(label)
        return col


class PassesPage(QWidget):
    open_radar = Signal()

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        make_page_root(self)
        self._controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(make_label(tr("passes.title"), "title"))
        titles.addWidget(make_label(tr("passes.subtitle"), "subtitle"))
        header.addLayout(titles, 1)
        refresh = make_button(tr("passes.recalc"), "outline")
        refresh.clicked.connect(controller.calculate_passes)
        header.addWidget(refresh, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # Observer card
        obs_card = make_card()
        obs = QHBoxLayout(obs_card)
        obs.setContentsMargins(16, 12, 16, 12)
        obs_text = QVBoxLayout()
        obs_text.setSpacing(2)
        obs_text.addWidget(make_label(tr("passes.observer"), "caption"))
        self._obs_name = make_label("", "heading")
        self._obs_coords = make_label("", "mono", CYAN)
        obs_text.addWidget(self._obs_name)
        obs_text.addWidget(self._obs_coords)
        obs.addLayout(obs_text, 1)
        change = make_button(tr("passes.change"))
        change.clicked.connect(self._change_location)
        obs.addWidget(change)
        root.addWidget(obs_card)

        # Active satellite badge
        sat_card = make_card("cardActive")
        sat = QHBoxLayout(sat_card)
        sat.setContentsMargins(16, 10, 16, 10)
        self._sat_name = make_label(tr("passes.pick"), "heading")
        self._sat_count = make_label(tr("passes.count", n=0), "caption", AMBER)
        sat.addWidget(make_label("🛰", None))
        sat.addWidget(self._sat_name)
        sat.addStretch(1)
        sat.addWidget(self._sat_count)
        root.addWidget(sat_card)

        # List
        self._status = make_label("", "subtitle", wrap=True)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.viewport().setAutoFillBackground(False)
        content = QWidget()
        content.setObjectName("scrollContent")
        self._list = QVBoxLayout(content)
        self._list.setContentsMargins(0, 0, 8, 0)
        self._list.setSpacing(12)
        self._scroll.setWidget(content)

        root.addWidget(self._status)
        root.addWidget(self._scroll, 1)

        controller.observer_changed.connect(self._on_observer)
        controller.active_satellite_changed.connect(self._on_satellite)
        controller.passes_updated.connect(self._on_passes)
        controller.passes_calculating.connect(self._on_calculating)

        self._on_observer(controller.observer)
        self._on_satellite(controller.active_satellite)
        self._on_passes(controller.passes)

    # ---------------------------------------------------------------- handlers
    def _change_location(self) -> None:
        dialog = LocationDialog(self._controller.observer, self)
        if dialog.exec() and dialog.selected is not None:
            o = dialog.selected
            self._controller.set_observer(o.latitude, o.longitude, o.altitude_m, o.name)

    def _on_observer(self, observer: ObserverLocation) -> None:
        self._obs_name.setText(observer.name)
        self._obs_coords.setText(f"{observer.latitude:.4f}°, {observer.longitude:.4f}°")

    def _on_satellite(self, sat: Optional[Satellite]) -> None:
        self._sat_name.setText(sat.name if sat else tr("passes.pick"))

    def _on_calculating(self, busy: bool) -> None:
        if busy:
            clear_layout(self._list)
            self._scroll.setVisible(False)
            self._status.setVisible(True)
            self._status.setText(tr("passes.calculating"))

    def _on_passes(self, passes: list[PassPrediction]) -> None:
        clear_layout(self._list)
        self._sat_count.setText(tr("passes.count", n=len(passes)))
        if not passes:
            self._scroll.setVisible(False)
            self._status.setVisible(True)
            if self._controller.active_satellite is None:
                self._status.setText(tr("passes.need_sat"))
            else:
                self._status.setText(tr("passes.none"))
            return
        self._status.setVisible(False)
        self._scroll.setVisible(True)
        for prediction in passes:
            card = PassCard(prediction)
            card.open_radar.connect(self._on_open_radar)
            self._list.addWidget(card)
        self._list.addStretch(1)

    def _on_open_radar(self, prediction: PassPrediction) -> None:
        self._controller.select_pass(prediction)
        self.open_radar.emit()
