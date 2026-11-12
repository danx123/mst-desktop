"""Pannable / zoomable equirectangular world map with live satellite overlay."""
from __future__ import annotations

import math
import time
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from mst.core.models import GroundTrackPoint, ObserverLocation, SatellitePosition
from mst.core.constants import EARTH_RADIUS_KM
from mst.ui.theme import AMBER, BORDER, BLACK, CYAN, SURFACE_VARIANT, qcolor
from mst.ui.widgets.mapdata import ALL_POLYGONS

_MIN_SCALE = 0.8
_MAX_SCALE = 8.0


class WorldMapWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(480, 320)
        self.setObjectName("worldMap")

        self._position: Optional[SatellitePosition] = None
        self._track: list[GroundTrackPoint] = []
        self._observer = ObserverLocation()

        self._scale = 1.0
        self._offset = QPointF(0.0, 0.0)
        self._drag_last: Optional[QPointF] = None

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)

    # ------------------------------------------------------------------ state
    def set_position(self, position: Optional[SatellitePosition]) -> None:
        self._position = position
        self.update()

    def set_ground_track(self, track: list[GroundTrackPoint]) -> None:
        self._track = track
        self.update()

    def set_observer(self, observer: ObserverLocation) -> None:
        self._observer = observer
        self.update()

    def reset_view(self) -> None:
        self._scale = 1.0
        self._offset = QPointF(0.0, 0.0)
        self.update()

    # ----------------------------------------------------------------- events
    def showEvent(self, event) -> None:  # noqa: N802
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    def wheelEvent(self, event) -> None:  # noqa: N802
        steps = event.angleDelta().y() / 120.0
        if steps == 0:
            return
        new_scale = max(_MIN_SCALE, min(_MAX_SCALE, self._scale * (1.2**steps)))
        # Keep the point under the cursor fixed while zooming.
        p = event.position()
        cx, cy = self.width() / 2.0, self.height() / 2.0
        bx = (p.x() - self._offset.x() - cx) / self._scale + cx
        by = (p.y() - self._offset.y() - cy) / self._scale + cy
        self._scale = new_scale
        self._offset = QPointF(
            p.x() - ((bx - cx) * new_scale + cx),
            p.y() - ((by - cy) * new_scale + cy),
        )
        self._clamp_offset()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_last = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_last is not None:
            delta = event.position() - self._drag_last
            self._drag_last = event.position()
            self._offset += delta
            self._clamp_offset()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_last = None
        self.unsetCursor()

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self.reset_view()

    def _clamp_offset(self) -> None:
        mx = self.width() * self._scale
        my = self.height() * self._scale
        self._offset = QPointF(
            max(-mx, min(mx, self._offset.x())),
            max(-my, min(my, self._offset.y())),
        )

    # ------------------------------------------------------------- projection
    def _project(self, lon: float, lat: float) -> QPointF:
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        base_x = (lon + 180.0) / 360.0 * w
        base_y = (90.0 - lat) / 180.0 * h
        return QPointF(
            (base_x - cx) * self._scale + cx + self._offset.x(),
            (base_y - cy) * self._scale + cy + self._offset.y(),
        )

    # ---------------------------------------------------------------- painting
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), qcolor(BLACK))

        self._draw_grid(painter)
        self._draw_continents(painter)
        self._draw_observer(painter)
        if self._position is not None:
            self._draw_ground_track(painter)
            self._draw_footprint(painter, self._position)
            self._draw_satellite(painter, self._position)
        painter.end()

    def _draw_grid(self, p: QPainter) -> None:
        for lon in range(-180, 181, 30):
            prime = lon == 0
            p.setPen(QPen(qcolor(AMBER, 0.35) if prime else qcolor(CYAN, 0.12), 1.5 if prime else 0.8))
            p.drawLine(self._project(lon, 85.0), self._project(lon, -85.0))
        for lat in range(-80, 81, 20):
            equator = lat == 0
            p.setPen(QPen(qcolor(AMBER, 0.5) if equator else qcolor(CYAN, 0.12), 2.0 if equator else 0.8))
            p.drawLine(self._project(-180.0, lat), self._project(180.0, lat))

    def _draw_continents(self, p: QPainter) -> None:
        p.setBrush(qcolor(SURFACE_VARIANT))
        p.setPen(QPen(qcolor(BORDER, 0.9), 1.0))
        for coords in ALL_POLYGONS:
            p.drawPolygon(QPolygonF([self._project(lon, lat) for lon, lat in coords]))

    def _draw_observer(self, p: QPainter) -> None:
        pos = self._project(self._observer.longitude, self._observer.latitude)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qcolor(AMBER, 0.3))
        p.drawEllipse(pos, 12.0, 12.0)
        p.setBrush(qcolor(AMBER))
        p.drawEllipse(pos, 5.0, 5.0)
        p.setBrush(qcolor("#FFFFFF"))
        p.drawEllipse(pos, 2.0, 2.0)
        self._draw_label(p, pos, self._observer.name, AMBER)

    def _draw_ground_track(self, p: QPainter) -> None:
        if len(self._track) < 2:
            return
        path = QPainterPath()
        started = False
        last_lon = 0.0
        for point in self._track:
            jump = started and abs(point.longitude - last_lon) > 180.0
            pt = self._project(point.longitude, point.latitude)
            if not started or jump:
                path.moveTo(pt)
                started = True
            else:
                path.lineTo(pt)
            last_lon = point.longitude
        pen = QPen(qcolor(CYAN, 0.85), 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(pen)
        p.drawPath(path)

    def _draw_footprint(self, p: QPainter, pos: SatellitePosition) -> None:
        angular = math.degrees(pos.footprint_radius_km / EARTH_RADIUS_KM)
        if angular <= 0.0:
            return
        cos_lat = max(0.1, math.cos(math.radians(pos.latitude)))
        segments = 48
        base: list[tuple[float, float]] = []
        for i in range(segments + 1):
            theta = 2.0 * math.pi * i / segments
            lat = max(-89.0, min(89.0, pos.latitude + angular * math.cos(theta)))
            lon = pos.longitude + angular * math.sin(theta) / cos_lat
            base.append((lon, lat))

        dashed = QPen(qcolor(CYAN, 0.35), 1.2)
        dashed.setStyle(Qt.PenStyle.DashLine)
        # Draw three copies so footprints crossing the antimeridian wrap cleanly.
        for shift in (-360.0, 0.0, 360.0):
            polygon = QPolygonF([self._project(lon + shift, lat) for lon, lat in base])
            p.setBrush(qcolor(CYAN, 0.08))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(polygon)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(dashed)
            p.drawPolygon(polygon)

    def _draw_satellite(self, p: QPainter, pos: SatellitePosition) -> None:
        center = self._project(pos.longitude, pos.latitude)

        phase = (time.monotonic() % 1.8) / 1.8
        pulse_radius = (12.0 + 36.0 * phase) * max(0.8, min(2.5, self._scale))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(qcolor(CYAN, 0.8 * (1.0 - phase)), 2.5))
        p.drawEllipse(center, pulse_radius, pulse_radius)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qcolor(CYAN, 0.2))
        p.drawEllipse(center, 16.0, 16.0)
        p.setBrush(qcolor(CYAN))
        p.drawEllipse(center, 7.0, 7.0)
        p.setBrush(qcolor("#FFFFFF"))
        p.drawEllipse(center, 3.5, 3.5)

        p.setPen(QPen(qcolor(CYAN), 2.5))
        p.drawLine(QPointF(center.x() - 14.0, center.y()), QPointF(center.x() + 14.0, center.y()))
        self._draw_label(p, center, pos.name, CYAN)

    @staticmethod
    def _draw_label(p: QPainter, anchor: QPointF, text: str, color: str) -> None:
        font = QFont(p.font())
        font.setPointSizeF(8.5)
        font.setBold(True)
        p.setFont(font)
        p.setPen(qcolor(color))
        p.drawText(QRectF(anchor.x() + 14.0, anchor.y() - 22.0, 240.0, 16.0), Qt.AlignmentFlag.AlignLeft, text)
