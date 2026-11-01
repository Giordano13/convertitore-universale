"""Working dialogs for PDF/media tools, history and before/after preview."""
import tempfile,json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QListWidget,QListWidgetItem,
    QFileDialog,QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QTextEdit,QMessageBox,QSpinBox,QAbstractItemView)
from PyQt6.QtCore import Qt,QThread,pyqtSignal,QUrl,QSize
from PyQt6.QtGui import QDesktopServices,QImageReader,QPixmap
from process_worker import run_job
from engine import kind

TOOLS=[('Unisci PDF','merge_pdf'),('Dividi PDF in pagine','split_pdf'),('Ruota pagine PDF','rotate_pdf'),
       ('Comprimi PDF (senza perdita)','compress_pdf'),('Crea PDF ricercabile con OCR','searchable_pdf'),
       ('Immagini → PDF unico','images_pdf'),('Cambia contenitore senza ricomprimere','remux'),('Sostituisci audio del video','replace_audio')]

class ToolsDialog(QDialog):
    def __init__(self,parent,sources):
        super().__init__(parent);self.setWindowTitle('Strumenti');self.resize(620,600)
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Scegli uno strumento e ordina i file. Gli originali vengono conservati.'))
        self.operation=QComboBox()
        for name,code in TOOLS:self.operation.addItem(name,code)
        layout.addWidget(self.operation)
        self.description=QLabel();self.description.setWordWrap(True);layout.addWidget(self.description)
        self.files=QListWidget();self.files.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove);layout.addWidget(self.files,1)
        self.add_paths(sources)
        row=QHBoxLayout();add=QPushButton('Aggiungi file');add.clicked.connect(self.choose);row.addWidget(add)
        remove=QPushButton('Rimuovi');remove.clicked.connect(lambda:self.files.takeItem(self.files.currentRow()));row.addWidget(remove)
        for text,delta in [('Su',-1),('Giù',1)]:
            button=QPushButton(text);button.clicked.connect(lambda _,d=delta:self.move(d));row.addWidget(button)
        layout.addLayout(row)
        self.pages=QLineEdit();self.pages.setPlaceholderText('Pagine: tutte, oppure 1-3,5');layout.addWidget(self.pages)
        self.rotation=QComboBox();self.rotation.addItems(['90','180','270']);layout.addWidget(self.rotation)
        self.output=QComboBox();layout.addWidget(self.output)
        self.ocr_language=QComboBox()
        for i in range(parent.language_combo.count()):self.ocr_language.addItem(parent.language_combo.itemText(i),parent.language_combo.itemData(i))
        self.ocr_language.setCurrentIndex(parent.language_combo.currentIndex());layout.addWidget(self.ocr_language)
        self.dpi=QSpinBox();self.dpi.setRange(72,300);self.dpi.setValue(parent.dpi_spin.value());self.dpi.setSuffix(' DPI');layout.addWidget(self.dpi)
        self.hint=QLabel('L’OCR usa la lingua selezionata nell’app. La compressione PDF non garantisce un file più piccolo.');self.hint.setWordWrap(True);layout.addWidget(self.hint)
        run=QPushButton('Esegui strumento');run.setObjectName('primary');run.clicked.connect(self.validate);layout.addWidget(run)
        self.operation.currentIndexChanged.connect(self.changed);self.changed()
    def add_paths(self,paths):
        for path in paths:
            item=QListWidgetItem(Path(path).name);item.setData(Qt.ItemDataRole.UserRole,str(path));item.setToolTip(str(path));self.files.addItem(item)
    def choose(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Scegli i file');self.add_paths(paths)
    def move(self,delta):
        row=self.files.currentRow();new=row+delta
        if 0<=new<self.files.count():
            item=self.files.takeItem(row);self.files.insertItem(new,item);self.files.setCurrentRow(new)
    def changed(self):
        op=self.operation.currentData();self.output.clear()
        formats=['mp4','mkv','mov','avi','webm'] if op=='remux' else ['mp4','mkv'] if op=='replace_audio' else ['pdf.zip'] if op=='split_pdf' else ['pdf']
        self.output.addItems(formats);self.pages.setVisible(op in ('split_pdf','rotate_pdf','compress_pdf'))
        self.rotation.setVisible(op=='rotate_pdf');self.ocr_language.setVisible(op=='searchable_pdf');self.dpi.setVisible(op=='searchable_pdf')
        self.description.setText('Primo file: video. Secondo file: nuovo audio. Il risultato termina con la traccia più breve.' if op=='replace_audio' else
                                 'Le tracce vengono copiate: il nuovo contenitore deve supportare i codec originali.' if op=='remux' else
                                 'L’ordine della lista è l’ordine delle pagine. Puoi trascinare i file o usare Su/Giù.')
    def validate(self):
        sources=[self.files.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.files.count())]
        op=self.operation.currentData();categories=[kind(p) for p in sources]
        if not sources:QMessageBox.warning(self,'File mancanti','Aggiungi almeno un file.');return
        if op=='replace_audio' and (len(sources)!=2 or categories[0]!='video' or categories[1]!='audio'):
            QMessageBox.warning(self,'Ordine file','Servono un video seguito da un audio.');return
        if op=='remux' and (len(sources)!=1 or categories[0]!='video'):
            QMessageBox.warning(self,'File','Seleziona un solo video.');return
        if op=='images_pdf' and not all(c in ('image','raw') for c in categories):
            QMessageBox.warning(self,'File','Questo strumento richiede immagini.');return
        if op not in ('replace_audio','remux','images_pdf') and not all(c=='pdf' for c in categories):
            QMessageBox.warning(self,'File','Questo strumento richiede PDF.');return
        if op in ('split_pdf','rotate_pdf','compress_pdf','searchable_pdf') and len(sources)!=1:
            QMessageBox.warning(self,'File','Scegli un solo PDF.');return
        self.job=dict(operation=op,sources=sources,format=self.output.currentText(),options=dict(pages=self.pages.text(),rotation=int(self.rotation.currentText()),ocr_language=self.ocr_language.currentData(),dpi=self.dpi.value()))
        self.accept()

class HistoryDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent);self.setWindowTitle('Cronologia conversioni');self.resize(900,600);self.rows=parent.store.history()
        layout=QVBoxLayout(self);self.table=QTableWidget(len(self.rows),4);self.table.setHorizontalHeaderLabels(['Data','File / operazione','Esito','Peso risultato'])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        for i,entry in enumerate(self.rows):
            values=(datetime.fromisoformat(entry['time']).astimezone().strftime('%d/%m/%Y %H:%M'),Path(entry['job']['sources'][0]).name+' / '+entry['job'].get('operation','convert'),
                    'Fatto' if entry['success'] else 'Annullato' if entry['success'] is None else 'Errore',f"{entry.get('output_bytes',0)/1024:.1f} KB")
            for col,text in enumerate(values):self.table.setItem(i,col,QTableWidgetItem(text))
        layout.addWidget(self.table,1);self.details=QTextEdit();self.details.setReadOnly(True);self.details.setMaximumHeight(120);layout.addWidget(self.details)
        self.table.itemSelectionChanged.connect(self.selected)
        row=QHBoxLayout();opened=QPushButton('Apri risultato');opened.clicked.connect(self.open_result);row.addWidget(opened)
        repeat=QPushButton('Ripeti operazione');repeat.clicked.connect(self.repeat);row.addWidget(repeat);layout.addLayout(row)
    def entry(self):
        row=self.table.currentRow();return self.rows[row] if 0<=row<len(self.rows) else None
    def selected(self):
        entry=self.entry()
        if entry:
            source=entry.get('input_bytes',0);output=entry.get('output_bytes',0)
            ratio=f'{(1-output/source)*100:.1f}% di riduzione' if source and entry['success'] else ''
            self.details.setPlainText(entry['result']+'\n'+ratio)
    def open_result(self):
        entry=self.entry()
        if entry and entry['success'] and Path(entry['result']).is_file():QDesktopServices.openUrl(QUrl.fromLocalFile(entry['result']))
    def repeat(self):
        entry=self.entry()
        if entry:self.parent().repeat_history(entry);self.accept()

class PreviewThread(QThread):
    ready=pyqtSignal(object,str)
    def __init__(self,job,target):super().__init__();self.job=job;self.target=target
    def run(self):
        success,value=run_job(self.job,self.target,self.isInterruptionRequested,lambda *args:None);self.ready.emit(success,value)

class ComparisonDialog(QDialog):
    def __init__(self,parent,source,fmt,options):
        super().__init__(parent);self.setWindowTitle('Confronto prima / dopo');self.resize(1000,570)
        self.source=source;self.fmt=fmt;self.options=options;self.directory=tempfile.TemporaryDirectory();self.worker=None
        layout=QVBoxLayout(self);columns=QHBoxLayout();self.before=QLabel();self.after=QLabel()
        for label in (self.before,self.after):label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setMinimumSize(350,320);columns.addWidget(label,1)
        layout.addLayout(columns,1);self.summary=QLabel();layout.addWidget(self.summary)
        row=QHBoxLayout();row.addWidget(QLabel('Qualità:'));self.quality=QSpinBox();self.quality.setRange(1,100);self.quality.setValue(options.get('quality',90));row.addWidget(self.quality)
        self.refresh=QPushButton('Aggiorna anteprima');self.refresh.clicked.connect(self.render);row.addWidget(self.refresh);layout.addLayout(row)
        self.show_image(self.before,source);self.render()
    def show_image(self,label,path):
        reader=QImageReader(str(path));size=reader.size();reader.setAutoTransform(True)
        if size.isValid():reader.setScaledSize(size.scaled(QSize(450,350),Qt.AspectRatioMode.KeepAspectRatio))
        image=reader.read()
        if image.isNull():label.setText('Anteprima non disponibile per questo formato.')
        else:label.setPixmap(QPixmap.fromImage(image).scaled(QSize(450,350),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def render(self):
        if self.worker:return
        from engine import reserve_output
        options=dict(self.options,quality=self.quality.value());target=reserve_output(self.directory.name,'preview',self.fmt)
        self.summary.setText('Preparazione della vera conversione…');self.refresh.setEnabled(False)
        self.worker=PreviewThread(dict(operation='convert',sources=[self.source],format=self.fmt,options=options),target)
        self.worker.ready.connect(self.ready);self.worker.finished.connect(self.finished);self.worker.start()
    def ready(self,success,value):
        if success:
            self.show_image(self.after,value);a=Path(self.source).stat().st_size;b=Path(value).stat().st_size
            self.summary.setText(f'Originale: {a/1024:.1f} KB  →  Risultato: {b/1024:.1f} KB. Qualità {self.quality.value()}%.')
        else:self.summary.setText(value)
    def finished(self):self.worker.deleteLater();self.worker=None;self.refresh.setEnabled(True)
    def closeEvent(self,event):
        if self.worker:
            self.worker.requestInterruption()
            if not self.worker.wait(5000):event.ignore();return
        if self.worker:
            self.worker.ready.disconnect(self.ready);self.worker.finished.disconnect(self.finished)
            self.worker.deleteLater();self.worker=None
        self.directory.cleanup();event.accept()

class InfoDialog(QDialog):
    def __init__(self,parent,source,checksum=False):
        super().__init__(parent);self.setWindowTitle('Informazioni file');self.resize(780,580)
        self.directory=tempfile.TemporaryDirectory();layout=QVBoxLayout(self);self.text=QTextEdit();self.text.setReadOnly(True);self.text.setPlainText('Lettura delle informazioni…');layout.addWidget(self.text)
        self.hash_value=None;self.expected=None
        if checksum:
            self.setWindowTitle('Verifica integrità SHA-256')
            self.expected=QLineEdit();self.expected.setPlaceholderText('Incolla l’impronta SHA-256 attesa (facoltativo)');layout.addWidget(self.expected)
            self.verification=QLabel('Calcolo dell’impronta in corso…');self.verification.setWordWrap(True);layout.addWidget(self.verification)
            self.expected.textChanged.connect(self.compare_hash)
        self.worker=PreviewThread(dict(operation='file_info',sources=[source],format='json',options={'checksum':checksum}),Path(self.directory.name)/'info.json')
        self.worker.ready.connect(self.ready);self.worker.start()
    def ready(self,success,value):
        if success:
            text=Path(value).read_text(encoding='utf-8');self.text.setPlainText(text)
            self.hash_value=json.loads(text).get('sha256')
            if self.expected is not None:self.compare_hash()
        else:
            self.text.setPlainText(value)
            if self.expected is not None:self.verification.setText('Impronta non disponibile: leggi il dettaglio dell’errore.')
    def compare_hash(self):
        import re
        if not self.hash_value:return
        expected=self.expected.text().strip().lower()
        if not expected:self.verification.setText('Impronta calcolata. Incolla un valore atteso per confrontarlo.')
        elif not re.fullmatch('[0-9a-f]{64}',expected):self.verification.setText('Servono 64 caratteri esadecimali (0–9, a–f).')
        elif expected==self.hash_value:self.verification.setText('Corrispondenza confermata: le impronte SHA-256 coincidono.')
        else:self.verification.setText('Le impronte NON coincidono. Il file è diverso da quello atteso.')
    def closeEvent(self,event):
        self.worker.requestInterruption()
        if not self.worker.wait(5000):event.ignore();return
        self.worker.ready.disconnect(self.ready);self.worker.deleteLater()
        self.directory.cleanup();event.accept()
