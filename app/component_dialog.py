import os,subprocess
from pathlib import Path
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QCheckBox,QPushButton,QMessageBox,QTextEdit
from PyQt6.QtCore import QTimer
from diagnostics import dependency_report
from runtime_paths import distribution_root,component_script

class ComponentDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent);self.setWindowTitle('Gestisci componenti');self.resize(720,600);self.process=None
        layout=QVBoxLayout(self);info=QTextEdit();info.setReadOnly(True);info.setPlainText(dependency_report());layout.addWidget(info,1)
        self.choices={}
        for code,label in [('ffmpeg','Audio e video — FFmpeg'),('office','Documenti Office — LibreOffice'),('ocr','OCR — Tesseract e inglese'),('italian','OCR in italiano')]:
            control=QCheckBox(label);self.choices[code]=control;layout.addWidget(control)
        self.choices['italian'].toggled.connect(lambda value:self.choices['ocr'].setChecked(True) if value else None)
        note=QLabel('I componenti scelti vengono installati o aggiornati con WinGet. Servono Internet e talvolta conferma amministratore. Procedendo accetti i termini dei componenti e della sorgente WinGet.');note.setWordWrap(True);layout.addWidget(note)
        row=QHBoxLayout();self.install=QPushButton('Installa selezionati');self.install.clicked.connect(lambda:self.run('install'));row.addWidget(self.install)
        self.upgrade=QPushButton('Aggiorna selezionati');self.upgrade.clicked.connect(lambda:self.run('upgrade'));row.addWidget(self.upgrade);layout.addLayout(row)
        self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.timer=QTimer(self);self.timer.setInterval(500);self.timer.timeout.connect(lambda:self.poll(info))
        if os.name!='nt':self.install.setEnabled(False);self.upgrade.setEnabled(False);self.status.setText('Installazione guidata dei componenti disponibile su Windows.')
    def run(self,action):
        if self.process:return
        selected=[code for code,check in self.choices.items() if check.isChecked()]
        if not selected:return
        script=component_script();root=distribution_root();models=root/('maintenance/models' if (root/'maintenance/models').is_dir() else 'installer/payload/tessdata')
        args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Components',','.join(selected),'-Action',action,'-ModelsRoot',str(models)]
        try:self.process=subprocess.Popen(args, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as error:QMessageBox.warning(self,'Componenti',str(error));return
        self.install.setEnabled(False);self.upgrade.setEnabled(False);self.status.setText('Installazione in corso. Attendi il completamento…');self.timer.start()
    def poll(self,info):
        code=self.process.poll()
        if code is None:return
        self.timer.stop();self.process=None;self.install.setEnabled(True);self.upgrade.setEnabled(True)
        self.status.setText('Operazione completata.' if code==0 else 'Alcuni componenti non sono stati installati. Controlla il log nella cartella dati dell’app.')
        info.setPlainText(dependency_report())
    def closeEvent(self,event):
        if self.process and self.process.poll() is None:self.status.setText('Attendi il termine dell’installazione prima di chiudere.');event.ignore();return
        event.accept()
