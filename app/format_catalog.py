"""Searchable catalogue derived from the actual conversion registry."""
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QLabel,QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView
from engine import EXTENSIONS,FORMATS,CATEGORY_LABELS


class FormatCatalog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('Formati e conversioni disponibili');self.resize(920,620)
        layout=QVBoxLayout(self)
        caption=QLabel('Cerca un’estensione per vedere i formati di origine e destinazione.\nAudio/video richiedono FFmpeg; Office richiede LibreOffice; riconoscimento del testo richiede Tesseract.')
        caption.setWordWrap(True);layout.addWidget(caption)
        self.search=QLineEdit();self.search.setPlaceholderText('Cerca: PDF, JSONL, Opus, immagini…');self.search.setClearButtonEnabled(True);layout.addWidget(self.search)
        self.table=QTableWidget(len(EXTENSIONS),3)
        self.table.setHorizontalHeaderLabels(['CATEGORIA','FILE IN INGRESSO','CONVERTI IN'])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True);self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().hide()
        for row,(category,extensions) in enumerate(EXTENSIONS.items()):
            for column,text in enumerate((CATEGORY_LABELS[category],', '.join(extensions),', '.join(FORMATS[category]))):
                self.table.setItem(row,column,QTableWidgetItem(text))
        layout.addWidget(self.table);self.table.resizeRowsToContents()
        self.search.textChanged.connect(self.filter)
        footer=QLabel('XML, YAML, TOML e INI vengono esportati come testo. JSON/JSONL devono contenere dati tabellari. La conversione non esegue programmi.')
        footer.setWordWrap(True);layout.addWidget(footer)

    def filter(self,text):
        query=text.strip().casefold().lstrip('.')
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row,not any(query in self.table.item(row,c).text().casefold() for c in range(3)))
