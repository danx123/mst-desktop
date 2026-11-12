"""Regenerate ``satellite.ico`` (multi-size, PNG-compressed) next to main.py.

Run from the project root:  python tools/make_icon.py
"""
from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPen

SIZES = (16, 24, 32, 48, 64, 128, 256)
CYAN = QColor("#00E5FF")
AMBER = QColor("#FF9100")


def draw(painter: QPainter, size: int) -> None:
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.scale(size / 256.0, size / 256.0)

    # Rounded deep-space tile
    gradient = QLinearGradient(0, 0, 0, 256)
    gradient.setColorAt(0.0, QColor("#16203A"))
    gradient.setColorAt(1.0, QColor("#0A0E17"))
    painter.setBrush(QBrush(gradient))
    border = QColor(CYAN)
    border.setAlphaF(0.55)
    painter.setPen(QPen(border, 5))
    painter.drawRoundedRect(QRectF(8, 8, 240, 240), 56, 56)

    # Stars
    painter.setPen(Qt.PenStyle.NoPen)
    for x, y, r in ((46, 52, 3.5), (206, 70, 3), (60, 206, 3), (196, 200, 4), (150, 36, 2.5)):
        painter.setBrush(QColor(255, 255, 255, 190))
        painter.drawEllipse(QPointF(x, y), r, r)

    # Orbit ring
    painter.save()
    painter.translate(128, 128)
    painter.rotate(-28)
    orbit = QColor(AMBER)
    orbit.setAlphaF(0.9)
    pen = QPen(orbit, 8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QPointF(0, 0), 104, 40)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(AMBER)
    painter.drawEllipse(QPointF(-92, 18), 11, 11)
    painter.restore()

    # Satellite
    painter.save()
    painter.translate(128, 128)
    painter.rotate(38)

    panel = QColor(CYAN)
    panel.setAlphaF(0.9)
    grid = QColor("#0A0E17")
    grid.setAlphaF(0.75)
    for x0 in (-98, 44):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(panel)
        painter.drawRoundedRect(QRectF(x0, -20, 54, 40), 4, 4)
        painter.setPen(QPen(grid, 2.5))
        for i in (1, 2):
            painter.drawLine(QPointF(x0 + i * 18, -20), QPointF(x0 + i * 18, 20))
        painter.drawLine(QPointF(x0, 0), QPointF(x0 + 54, 0))

    painter.setPen(QPen(QColor("#90A4AE"), 5))
    painter.drawLine(QPointF(-44, 0), QPointF(-24, 0))
    painter.drawLine(QPointF(24, 0), QPointF(44, 0))

    body = QLinearGradient(0, -30, 0, 30)
    body.setColorAt(0.0, QColor("#FFFFFF"))
    body.setColorAt(1.0, QColor("#9FDDE8"))
    painter.setPen(QPen(QColor("#00B0FF"), 3))
    painter.setBrush(QBrush(body))
    painter.drawRoundedRect(QRectF(-24, -30, 48, 60), 10, 10)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#00B0FF"))
    painter.drawEllipse(QPointF(0, -4), 9, 9)
    painter.setBrush(QColor("#0A0E17"))
    painter.drawEllipse(QPointF(0, -4), 4, 4)

    # Dish
    painter.setPen(QPen(QColor("#90A4AE"), 4))
    painter.drawLine(QPointF(0, 30), QPointF(0, 44))
    painter.setBrush(QColor("#F0F4F8"))
    painter.drawEllipse(QPointF(0, 50), 12, 7)
    painter.restore()


def render_png(size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    draw(painter, size)
    painter.end()

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def build_ico(path: Path) -> None:
    pngs = [(size, render_png(size)) for size in SIZES]
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries = b""
    blobs = b""
    for size, png in pngs:
        dim = 0 if size >= 256 else size  # 0 means 256 in the ICO format
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    path.write_bytes(header + entries + blobs)


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    target = Path(__file__).resolve().parent.parent / "satellite.ico"
    build_ico(target)
    # Preview PNG for quick inspection (not part of the app)
    Path("/tmp/satellite_preview.png").write_bytes(render_png(256)) if Path("/tmp").exists() else None
    print(f"Wrote {target} ({target.stat().st_size} bytes)")
