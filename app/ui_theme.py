"""One design system, two palettes. Qt Widgets stylesheet."""
from pathlib import Path
import sys

PALETTES = {
    'dark': dict(bg='#0c1420', side='#101c2c', card='#152236', inset='#0e1929', border='#2b3d52',
                 text='#edf5fc', muted='#a5b8cd', accent='#64dfd2', accent_text='#082c2c',
                 hover='#20364b', selected='#183f49', success='#79dcb1', error='#ff9da5'),
    'light': dict(bg='#eef4f8', side='#ffffff', card='#ffffff', inset='#f3f7fa', border='#d3e0e9',
                  text='#172c40', muted='#526a80', accent='#087e83', accent_text='#ffffff',
                  hover='#e5eff4', selected='#d9f0ee', success='#18734d', error='#ae3046'),
}


def stylesheet(theme='dark'):
    p = dict(PALETTES[theme])
    assets = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'assets'
    for token, name in [('down_icon', 'down'), ('up_icon', 'up'), ('check_icon', 'check')]:
        p[token] = (assets / f'{name}-{theme}.svg').as_posix()
    return '''
QMainWindow, QDialog, QWidget#appRoot {{ background: {bg}; }}
QWidget {{ color: {text}; font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 13px; background: transparent; }}
QDialog {{ background: {bg}; }}
QTextEdit, QListWidget {{ background: {inset}; color: {text}; border: 1px solid {border}; border-radius: 8px; padding: 8px; }}
QFrame#sidebar {{ background: {side}; border-right: 1px solid {border}; }}
QFrame#card, QFrame#settingsCard, QFrame#progressCard {{ background: {card}; border: 1px solid {border}; border-radius: 16px; }}
QLabel {{ border: none; background: transparent; }}
QLabel#title {{ font-size: 25px; font-weight: 700; }}
QLabel#brand {{ font-size: 20px; font-weight: 700; }}
QLabel#sectionTitle {{ font-size: 16px; font-weight: 600; }}
QLabel#muted, QLabel#caption, QLabel#fieldLabel {{ color: {muted}; }}
QLabel#caption {{ font-size: 11px; }}
QLabel#eyebrow {{ color: {muted}; font-size: 11px; font-weight: 600; }}
QLabel#statValue {{ font-size: 21px; font-weight: 600; }}
QLabel#pill {{ color: {accent}; background: {selected}; border: 1px solid {border}; border-radius: 10px; padding: 4px 10px; font-size: 11px; }}
QLabel#selectionSummary {{ font-weight: 600; font-size: 14px; }}
QLabel#preview {{ background: {inset}; border: 1px solid {border}; border-radius: 12px; }}
QLabel#hint {{ background: {inset}; color: {muted}; border-radius: 10px; padding: 12px; font-size: 12px; }}
QPushButton {{ background: {card}; border: 1px solid {border}; border-radius: 9px; padding: 9px 12px; font-weight: 600; }}
QPushButton:hover {{ background: {hover}; }}
QPushButton:pressed {{ background: {selected}; }}
QPushButton:focus {{ border: 2px solid {accent}; }}
QPushButton:disabled {{ color: {muted}; background: {inset}; }}
QPushButton#primary {{ background: {accent}; color: {accent_text}; border: 1px solid {accent}; }}
QPushButton#primary:hover {{ background: {accent}; border: 2px solid {text}; }}
QPushButton#primary:disabled {{ background: {hover}; color: {muted}; border: 1px solid {border}; }}
QPushButton#nav {{ text-align: left; background: transparent; border: 1px solid transparent; padding: 12px; font-weight: 500; }}
QPushButton#nav:hover {{ background: {hover}; }}
QPushButton#nav:checked {{ background: {selected}; color: {accent}; border: 1px solid {border}; }}
QPushButton#quiet {{ background: transparent; border: 1px solid transparent; color: {muted}; padding: 6px 9px; }}
QPushButton#quiet:hover {{ background: {hover}; color: {text}; }}
QPushButton#theme {{ background: {inset}; }}
QFrame#dropZone {{ background: {inset}; border: 1px dashed {border}; border-radius: 16px; }}
QFrame#dropZone[dragging='true'] {{ border: 2px dashed {accent}; background: {selected}; }}
QLabel#dropTitle {{ font-size: 17px; font-weight: 600; }}
QTableWidget {{ background: {card}; alternate-background-color: {inset}; border: none; color: {text}; gridline-color: {border}; selection-background-color: {selected}; selection-color: {text}; outline: none; }}
QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {border}; }}
QTableWidget::item:selected {{ background: {selected}; }}
QHeaderView::section {{ background: {inset}; color: {muted}; font-size: 11px; font-weight: 600; padding: 10px 8px; border: none; border-bottom: 1px solid {border}; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ background: {inset}; color: {text}; border: 1px solid {border}; border-radius: 8px; padding: 8px; min-height: 18px; selection-background-color: {selected}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {accent}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: url("{down_icon}"); width: 12px; height: 12px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 22px; border-left: 1px solid {border}; border-bottom: 1px solid {border}; border-top-right-radius: 8px; background: {inset}; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; border-left: 1px solid {border}; border-bottom-right-radius: 8px; background: {inset}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{up_icon}"); width: 10px; height: 10px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{down_icon}"); width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{ background: {card}; color: {text}; selection-background-color: {selected}; border: 1px solid {border}; padding: 6px; }}
QCheckBox {{ spacing: 8px; padding: 3px 0; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {muted}; border-radius: 4px; background: {inset}; }}
QCheckBox::indicator:checked {{ background: {accent}; border: 1px solid {accent}; image: url("{check_icon}"); }}
QCheckBox:focus {{ color: {accent}; }}
QProgressBar {{ border: none; background: {inset}; border-radius: 3px; height: 6px; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 3px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {border}; min-height: 24px; border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QSplitter::handle {{ background: transparent; width: 16px; }}
QToolTip {{ background: {card}; color: {text}; border: 1px solid {border}; padding: 8px; }}
QMessageBox {{ background: {card}; }}
'''.format(**p)

DARK_STYLE = stylesheet('dark')
