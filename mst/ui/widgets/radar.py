"""2D polar sky radar (azimuth/elevation) with animated sweep and pass path."""
from __future__ import annotations

import math
import time
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from mst.core.models import SatellitePosition
from mst.ui.theme import AMBER, BLACK, CYAN, GREEN, SURFACE, TEXT_MUTED, qcolor


class RadarWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self._position: Optional[SatellitePosition] = None
        self._heading = 0.0
        self._path: list[tuple[float, float]] = []

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)

    # ------------------------------------------------------------------ state
    def set_position(self, position: Optional[SatellitePosition]) -> None:
        self._position = position
        self.update()

    def set_heading(self, degrees: float) -> None:
        self._heading = degrees % 360.0
        self.update()

    def set_pass_path(self, path: list[tuple[float, float]]) -> None:
        self._path = path
        self.update()

    def showEvent(self, event) -> None:  # noqa: N802
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    # ---------------------------------------------------------------- painting
    @staticmethod
    def _sky_point(az_deg: float, el_deg: float, radius: float) -> QPointF:
        """Zenith = centre, horizon = rim; azimuth 0 (north) points up."""
        r = (90.0 - max(0.0, min(90.0, el_deg))) / 90.0 * radius
        a = math.radians(az_deg - 90.0)
        return QPointF(r * math.cos(a), r * math.sin(a))

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), qcolor(BLACK))

        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        radius = min(self.width(), self.height()) / 2.0 - 44.0
        if radius <= 10.0:
            p.end()
            return
        now = time.monotonic()

        # Disk + horizon ring
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qcolor(SURFACE))
        p.drawEllipse(center, radius, radius)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(qcolor(CYAN, 0.8), 3.0))
        p.drawEllipse(center, radius, radius)

        # Elevation rings (30°, 60°)
        dashed = QPen(qcolor(CYAN, 0.25), 1.2)
        dashed.setStyle(Qt.PenStyle.DashLine)
        p.setPen(dashed)
        small = QFont(p.font())
        small.setPointSizeF(7.5)
        for el in (30.0, 60.0):
            rr = radius * (90.0 - el) / 90.0
            p.drawEllipse(center, rr, rr)
            p.setFont(small)
            p.setPen(qcolor(TEXT_MUTED))
            p.drawText(QPointF(center.x() + 4.0, center.y() - rr - 3.0), f"{int(el)}°")
            p.setPen(dashed)

        # Dial (rotates with heading)
        p.save()
        p.translate(center)
        p.rotate(-self._heading)

        grid = QPen(qcolor(CYAN, 0.12), 1.5)
        p.setPen(grid)
        p.drawLine(QPointF(0, -radius), QPointF(0, radius))
        p.drawLine(QPointF(-radius, 0), QPointF(radius, 0))
        diag = radius * 0.7071
        p.setPen(QPen(qcolor(CYAN, 0.06), 1.0))
        p.drawLine(QPointF(-diag, -diag), QPointF(diag, diag))
        p.drawLine(QPointF(-diag, diag), QPointF(diag, -diag))

        self._draw_sweep(p, radius, (now % 4.0) / 4.0 * 360.0)
        self._draw_cardinals(p, radius)
        self._draw_path(p, radius)
        if self._position is not None:
            self._draw_target(p, self._position, radius, now)
        p.restore()

        # Zenith reticle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qcolor(AMBER))
        p.drawEllipse(center, 4.0, 4.0)
        p.setPen(QPen(qcolor(AMBER, 0.7), 1.5))
        p.drawLine(QPointF(center.x() - 12, center.y()), QPointF(center.x() + 12, center.y()))
        p.drawLine(QPointF(center.x(), center.y() - 12), QPointF(center.x(), center.y() + 12))

        # Fixed heading pointer just inside the rim (where the observer is facing)
        base_y = center.y() - radius + 18.0
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qcolor(CYAN))
        p.drawPolygon(QPolygonF([
            QPointF(center.x(), base_y - 12.0),
            QPointF(center.x() - 7.0, base_y),
            QPointF(center.x() + 7.0, base_y),
        ]))
        p.end()

    def _draw_sweep(self, p: QPainter, radius: float, sweep_deg: float) -> None:
        rect = QRectF(-radius, -radius, radius * 2, radius * 2)
        p.setPen(Qt.PenStyle.NoPen)
        slices, width = 14, 4.0
        for i in range(slices):
            a1 = sweep_deg - i * width
            p.setBrush(qcolor(CYAN, 0.16 * (1.0 - i / slices)))
            p.drawPie(rect, int(-a1 * 16), int(width * 16))
        end = QPointF(radius * math.cos(math.radians(sweep_deg)), radius * math.sin(math.radians(sweep_deg)))
        p.setPen(QPen(qcolor(CYAN, 0.9), 2.0))
        p.drawLine(QPointF(0, 0), end)

    def _draw_cardinals(self, p: QPainter, radius: float) -> None:
        font = QFont(p.font())
        font.setPointSizeF(10.0)
        font.setBold(True)
        p.setFont(font)
        for label, az, color in (("U", 0, CYAN), ("T", 90, TEXT_MUTED), ("S", 180, TEXT_MUTED), ("B", 270, TEXT_MUTED)):
            pos = self._sky_point(az, 0.0, radius + 18.0)
            p.save()
            p.translate(pos)
            p.rotate(self._heading)  # keep letters upright
            p.setPen(qcolor(color))
            p.drawText(QRectF(-14, -10, 28, 20), Qt.AlignmentFlag.AlignCenter, label)
            p.restore()

    def _draw_path(self, p: QPainter, radius: float) -> None:
        if len(self._path) < 2:
            return
        pen = QPen(qcolor(AMBER, 0.9), 2.0)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        pts = [self._sky_point(az, el, radius) for az, el in self._path]
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a, b)
        font = QFont(p.font())
        font.setPointSizeF(8.0)
        font.setBold(True)
        p.setFont(font)
        for point, text in ((pts[0], "AOS"), (pts[-1], "LOS")):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qcolor(AMBER))
            p.drawEllipse(point, 4.0, 4.0)
            p.setPen(qcolor(AMBER))
            p.drawText(QPointF(point.x() + 7.0, point.y() - 6.0), text)

    def _draw_target(self, p: QPainter, sat: SatellitePosition, radius: float, now: float) -> None:
        visible = sat.elevation_deg > 0.0
        pos = self._sky_point(sat.azimuth_deg, sat.elevation_deg if visible else 0.0, radius)

        p.setBrush(Qt.BrushStyle.NoBrush)
        if visible:
            pulse = 1.3 + 0.3 * math.sin(now * 2.0 * math.pi / 2.4)
            p.setPen(QPen(qcolor(GREEN, 0.4), 1.5))
            p.drawEllipse(pos, 20.0 * pulse, 20.0 * pulse)

            p.setPen(QPen(qcolor(GREEN), 1.8))
            p.drawRect(QRectF(pos.x() - 12, pos.y() - 12, 24, 24))

            dashed = QPen(qcolor(GREEN, 0.3), 1.0)
            dashed.setStyle(Qt.PenStyle.DashLine)
            p.setPen(dashed)
            p.drawLine(QPointF(0, 0), pos)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qcolor(GREEN))
            p.drawEllipse(pos, 4.0, 4.0)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qcolor(AMBER, 0.4))
            p.drawEllipse(pos, 8.0, 8.0)
            p.setBrush(qcolor(AMBER))
            p.drawEllipse(pos, 3.0, 3.0)
