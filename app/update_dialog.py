from pathlib import Path
import os,subprocess
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QCheckBox,QTextEdit,QLineEdit,QProgressBar,QMessageBox,QApplication
from PyQt6.QtCore import QThread,pyqtSignal,QStandardPaths
from updater import read_config,check_release,download_release,https_host,UpdateError,verify_installer
from version import VERSION

class UpdateThread(QThread):
    ready=pyqtSignal(object,str);progress=pyqtSignal(float)
    def __init__(self,config,release=None,folder=None):super().__init__();self.config=config;self.release=release;self.folder=folder
    def run(self):
        try:
            if self.release:
                hosts=set(self.config['allowed_download_hosts'])|{https_host(self.config['manifest_url'])}
                value=download_release(self.release,self.folder,hosts,lambda f,n:self.progress.emit(f),self.isInterruptionRequested)
            else:value=check_release(self.config)
            self.ready.emit(value,'')
        except Exception as error:self.ready.emit(None,str(error))

class UpdateDialog(QDialog):
    def __init__(self,parent,automatic=False):
        super().__init__(parent);self.setWindowTitle('Aggiornamenti');self.resize(640,500);self.worker=None;self.release=None;self.installer=None
        self.config=read_config();self.parent_window=parent
        layout=QVBoxLayout(self);layout.addWidget(QLabel('Versione installata: '+VERSION))
        self.status=QLabel('Controlla se è disponibile una nuova versione.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.automatic=QCheckBox('Controlla gli aggiornamenti all’avvio');self.automatic.setChecked(parent.settings.value('automatic_updates',False,type=bool))
        self.automatic.toggled.connect(lambda value:parent.settings.setValue('automatic_updates',value));layout.addWidget(self.automatic)
        self.url=QLineEdit(parent.settings.value('update_url',self.config['manifest_url']));self.url.setPlaceholderText('URL HTTPS del canale ufficiale');layout.addWidget(self.url)
        hint=QLabel('L’indirizzo viene fornito dall’autore. Il controllo invia solo una richiesta al canale.');hint.setWordWrap(True);layout.addWidget(hint)
        self.notes=QTextEdit();self.notes.setReadOnly(True);self.notes.setPlaceholderText('Le note della nuova versione appariranno qui.');layout.addWidget(self.notes,1)
        self.bar=QProgressBar();self.bar.setRange(0,100);self.bar.setTextVisible(False);layout.addWidget(self.bar)
        row=QHBoxLayout();self.check=QPushButton('Cerca aggiornamenti');self.check.clicked.connect(self.start_check);row.addWidget(self.check)
        self.download=QPushButton('Scarica setup');self.download.setEnabled(False);self.download.clicked.connect(self.start_download);row.addWidget(self.download)
        self.install=QPushButton('Installa e chiudi app');self.install.setEnabled(False);self.install.clicked.connect(self.launch);row.addWidget(self.install);layout.addLayout(row)
        self.cancel=QPushButton('Annulla download');self.cancel.setEnabled(False);self.cancel.clicked.connect(self.stop);layout.addWidget(self.cancel)
        if automatic:self.start_check()
    def active_config(self):
        url=self.url.text().strip()
        if not url:raise UpdateError('Canale aggiornamenti non ancora configurato dall’autore.')
        host=https_host(url);self.parent_window.settings.setValue('update_url',url)
        return dict(manifest_url=url,allowed_download_hosts=self.config['allowed_download_hosts'] if url==self.config['manifest_url'] else [host])
    def start_check(self):
        if self.worker:return
        try:self.current_config=self.active_config()
        except ValueError as error:self.status.setText(str(error));return
        self.release=None;self.installer=None;self.download.setEnabled(False);self.install.setEnabled(False)
        self.status.setText('Controllo del canale…');self.start_thread(UpdateThread(self.current_config))
    def start_download(self):
        if self.worker or not self.release:return
        folder=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))/'updates'
        self.status.setText('Download e verifica SHA256…');self.start_thread(UpdateThread(self.current_config,self.release,folder))
    def start_thread(self,worker):
        self.worker=worker;self.check.setEnabled(False);self.url.setEnabled(False);self.download.setEnabled(False);self.cancel.setEnabled(True)
        worker.ready.connect(self.ready);worker.progress.connect(lambda f:self.bar.setValue(round(f*100)));worker.finished.connect(self.finished);worker.start()
    def ready(self,value,error):
        if error:self.status.setText(error);return
        if isinstance(value,dict):
            self.release=value;self.notes.setPlainText(value.get('notes',''));self.status.setText('Nuova versione: '+value['version'] if value['newer'] else 'Hai già la versione più recente del canale.')
        else:
            self.installer=Path(value);self.status.setText('Setup scaricato e verificato. Puoi avviarlo quando la coda è ferma.');self.bar.setValue(100)
    def finished(self):
        self.worker.deleteLater();self.worker=None;self.check.setEnabled(True);self.url.setEnabled(True);self.cancel.setEnabled(False)
        self.download.setEnabled(bool(self.release and self.release['newer'] and not self.installer));self.install.setEnabled(bool(self.installer) and os.name=='nt')
    def stop(self):
        if self.worker:self.worker.requestInterruption();self.status.setText('Annullamento: attendo la risposta di rete in corso…')
    def launch(self):
        if self.parent_window.worker or not self.installer or os.name!='nt':return
        try:
            verify_installer(self.installer,self.release)
            subprocess.Popen([str(self.installer)],cwd=str(self.installer.parent))
        except (OSError,ValueError) as error:QMessageBox.warning(self,'Avvio setup',str(error));return
        QApplication.instance().quit()
    def closeEvent(self,event):
        if self.worker:
            self.stop();self.status.setText('Attendi la fine della richiesta prima di chiudere.');event.ignore();return
        event.accept()
