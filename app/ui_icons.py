"""Original vector icons rendered by Qt. No emoji or remote assets."""
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

PATHS = {
    'convert': '<path d="M4 8h14l-3-3M20 16H6l3 3"/><path d="M20 8v4M4 16v-4"/>',
    'files': '<rect x="7" y="3" width="13" height="17" rx="2"/><path d="M4 7v13a2 2 0 0 0 2 2h10M10 8h7M10 12h7M10 16h4"/>',
    'image': '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="8" cy="9" r="1.5"/><path d="m4 17 5-5 4 4 3-3 5 5"/>',
    'media': '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m10 8 6 4-6 4z"/>',
    'document': '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6M8 13h8M8 17h6"/>',
    'archive': '<rect x="4" y="3" width="16" height="18" rx="3"/><path d="M11 3v10M11 6h2M11 10h2"/><rect x="10" y="14" width="4" height="4" rx="1"/>',
    'upload': '<path d="M12 16V3m-5 5 5-5 5 5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'search': '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    'trash': '<path d="M3 6h18M9 6V3h6v3M5 6l1 14h12l1-14M10 10v6M14 10v6"/>',
    'close': '<path d="m6 6 12 12M6 18 18 6"/>',
    'folder': '<path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'settings': '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="15" cy="17" r="3"/>',
    'moon': '<path d="M20 15.5A9 9 0 0 1 8.5 4 9 9 0 1 0 20 15.5z"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1 1M18 18l1 1M5 19l1-1M18 6l1-1"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
    'error': '<circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
    'stop': '<rect x="5" y="5" width="14" height="14" rx="3"/>',
    'shield': '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 12 3 3 5-6"/>',
    'arrow': '<path d="M4 12h16m-5-5 5 5-5 5"/>',
}


def pixmap(name, color='#a3adc3', size=24):
    shape = PATHS.get(name, PATHS['document'])
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{shape}</svg>'
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    result = QPixmap(size * 2, size * 2);result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result);renderer.render(painter);painter.end()
    result.setDevicePixelRatio(2)
    return result


def icon(name, color='#a3adc3', size=24):
    return QIcon(pixmap(name, color, size))


def category_icon(category):
    if category in ('image','vector'):
        return 'image'
    if category in ('audio','video'):
        return 'media'
    if category == 'archive':
        return 'archive'
    return 'document'
