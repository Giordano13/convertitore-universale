"""Rasterize SVG using Qt SVG already shipped with PyQt6."""
from pathlib import Path
import tempfile
import os
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication
from converters.image_converter import convert_image


_svg_app = None


def convert_svg(source, target, fmt, width=None, height=None, quality=90):
    global _svg_app
    if QApplication.instance() is None:
        if os.name != 'nt' and not os.environ.get('DISPLAY'):
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        _svg_app = QApplication([])
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise ValueError('SVG non valido o non supportato dal renderer Qt.')
    size = renderer.defaultSize()
    natural_w, natural_h = size.width(), size.height()
    if natural_w <= 0 or natural_h <= 0:
        natural_w = natural_h = 1024
    if width and height:
        ratio = min(width / natural_w, height / natural_h)
        w, h = max(1, round(natural_w * ratio)), max(1, round(natural_h * ratio))
    else:
        w, h = natural_w, natural_h
    if w * h > 100_000_000:
        raise ValueError('SVG troppo grande: ridimensiona prima della conversione.')
    image = QImage(w, h, QImage.Format.Format_ARGB32)
    if image.isNull():
        raise ValueError('Impossibile creare l’immagine SVG.')
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    try:
        renderer.render(painter, QRectF(0, 0, w, h))
    finally:
        painter.end()
    with tempfile.TemporaryDirectory() as directory:
        png = Path(directory) / 'render.png'
        if not image.save(str(png), 'PNG'):
            raise RuntimeError('Salvataggio immagine SVG fallito.')
        convert_image(png, target, fmt, quality=quality)
