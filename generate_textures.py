import os
import random
import math
from pathlib import Path
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF, QSize

def generate():
    dir_path = Path("asset/textures")
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Wood Light (birch)
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(QColor(255, 255, 255, 12)) # base light wood tint
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    for i in range(40):
        y_start = random.randint(-50, 300)
        path = QPainterPath()
        path.moveTo(0, y_start)
        for x in range(0, 257, 16):
            wave = 8 * math.sin(x / 40.0) + random.randint(-1, 1)
            path.lineTo(x, y_start + wave)
        pen_color = QColor(0, 0, 0, random.randint(8, 22)) if random.random() < 0.5 else QColor(255, 255, 255, random.randint(5, 18))
        painter.setPen(QPen(pen_color, random.uniform(1.0, 2.5)))
        painter.drawPath(path)
    painter.end()
    img.save(str(dir_path / "wood_light.png"))

    # 2. Wood Dark
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 35)) # base dark wood tint
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    for i in range(45):
        y_start = random.randint(-50, 300)
        path = QPainterPath()
        path.moveTo(0, y_start)
        for x in range(0, 257, 16):
            wave = 10 * math.sin(x / 50.0) + random.randint(-1, 1)
            path.lineTo(x, y_start + wave)
        pen_color = QColor(0, 0, 0, random.randint(15, 35)) if random.random() < 0.6 else QColor(255, 255, 255, random.randint(4, 12))
        painter.setPen(QPen(pen_color, random.uniform(1.5, 3.5)))
        painter.drawPath(path)
    painter.end()
    img.save(str(dir_path / "wood_dark.png"))

    # 3. Denim
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    for x in range(64):
        for y in range(64):
            if (x + y) % 4 == 0:
                painter.setPen(QColor(255, 255, 255, 22))
                painter.drawPoint(x, y)
            elif (x + y) % 4 == 2:
                painter.setPen(QColor(0, 0, 0, 32))
                painter.drawPoint(x, y)
    painter.end()
    img.save(str(dir_path / "denim.png"))

    # 4. Leather
    img = QImage(128, 128, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    for x in range(128):
        for y in range(128):
            noise = random.randint(0, 100)
            if noise < 15:
                painter.setPen(QColor(0, 0, 0, 35))
                painter.drawPoint(x, y)
            elif noise > 88:
                painter.setPen(QColor(255, 255, 255, 12))
                painter.drawPoint(x, y)
    painter.end()
    img.save(str(dir_path / "leather.png"))

    # 5. Acrylic
    img = QImage(128, 128, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    for x in range(128):
        for y in range(128):
            if random.random() < 0.4:
                painter.setPen(QColor(255, 255, 255, random.randint(8, 18)))
                painter.drawPoint(x, y)
    painter.end()
    img.save(str(dir_path / "acrylic.png"))

    # 6. Ceramic (tile pattern)
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setPen(QPen(QColor(255, 255, 255, 24), 1.0))
    painter.drawLine(0, 63, 63, 63)
    painter.drawLine(63, 0, 63, 63)
    for x in range(64):
        for y in range(64):
            if random.random() < 0.05:
                painter.setPen(QColor(255, 255, 255, 6))
                painter.drawPoint(x, y)
    painter.end()
    img.save(str(dir_path / "ceramic.png"))

    # 7. Candy
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    for offset in range(-64, 128, 16):
        path = QPainterPath()
        path.moveTo(offset, 0)
        path.lineTo(offset + 8, 0)
        path.lineTo(offset - 56, 64)
        path.lineTo(offset - 64, 64)
        path.closeSubpath()
        painter.fillPath(path, QBrush(QColor(244, 63, 94, 30)))
    painter.end()
    img.save(str(dir_path / "candy.png"))

    # 8. Rangoli
    img = QImage(128, 128, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor(255, 255, 255, 30), 1.2))
    cx, cy = 64.0, 64.0
    painter.drawEllipse(QPointF(cx, cy), 16, 16)
    painter.drawEllipse(QPointF(cx, cy), 32, 32)
    painter.drawEllipse(QPointF(cx, cy), 48, 48)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        painter.drawLine(QPointF(cx + 8 * math.cos(rad), cy + 8 * math.sin(rad)), QPointF(cx + 54 * math.cos(rad), cy + 54 * math.sin(rad)))
    painter.end()
    img.save(str(dir_path / "rangoli.png"))

    # 9. Metallic Light
    img = QImage(256, 128, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    for y in range(128):
        val = random.randint(-15, 15)
        if val > 0:
            painter.setPen(QColor(255, 255, 255, random.randint(5, 18)))
        else:
            painter.setPen(QColor(0, 0, 0, random.randint(8, 25)))
        painter.drawLine(0, y, 256, y)
    painter.end()
    img.save(str(dir_path / "metallic_light.png"))

    print("Successfully generated all textures!")

if __name__ == '__main__':
    generate()
