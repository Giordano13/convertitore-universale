import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QLineEdit, QPushButton, QComboBox, QInputDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QUrl, QSize, QSignalBlocker, QStandardPaths, QTimer
from PyQt6.QtGui import QDesktopServices, QShortcut, QKeySequence, QImageReader, QPixmap, QColor
from engine import kind, common_formats, convert, FORMATS, reserve_output, CATEGORY_LABELS
from process_worker import run_job
from state_store import StateStore
from presets import PRESETS, default_format
from watch_folder import FolderMonitor
from feature_dialogs import ToolsDialog, HistoryDialog, ComparisonDialog, InfoDialog
from ui_features import add_features
from version import VERSION
from update_dialog import UpdateDialog
from component_dialog import ComponentDialog
from diagnostics import dependency_report
from ui_components import build_interface, DropZone
from ui_theme import DARK_STYLE, PALETTES, stylesheet
from ui_icons import icon, pixmap, category_icon

class Worker(QThread):
    result = pyqtSignal(int, object, str)
    active = pyqtSignal(int)
    progress = pyqtSignal(int, object, str, object)
    def __init__(self, jobs, folder=None, fmt=None, options=None):
        super().__init__()
        self.jobs = [dict(row=row, sources=[path], format=fmt, options=options or {}, folder=folder) for row,path in jobs] if jobs and isinstance(jobs[0],tuple) else jobs
    def run(self):
        for job in self.jobs:
            if self.isInterruptionRequested(): break
            row=job['row'];self.active.emit(row)
            target=None
            try:
                folder=Path(job['folder']);folder.mkdir(parents=True,exist_ok=True)
                target=reserve_output(folder,job.get('stem',Path(job['sources'][0]).stem),job['format'])
                success,message=run_job(job,target,self.isInterruptionRequested,
                    lambda fraction,phase,eta:self.progress.emit(row,fraction,phase,eta))
                self.result.emit(row,success,message)
                if success is None:break
            except Exception as error:
                if target:target.unlink(missing_ok=True)
                self.result.emit(row,False,str(error))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Convertitore Universale — v'+VERSION)
        self.resize(1280, 840)
        self.setMinimumSize(920, 680)
        self.files = []
        self.worker = None
        self.retry_jobs = []
        self.settings = QSettings('Giordano', 'ConvertitoreUniversale')
        self.output_folder = ''
        self.current_category = 'all'
        self.session_successes = self.session_errors = 0
        self.theme = 'dark'
        QApplication.setOrganizationName('ConvertitoreUniversale');QApplication.setApplicationName('ConvertitoreUniversale')
        self.store=StateStore(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        self.import_roots={}
        self.monitor=None
        self.watch_timer=QTimer(self);self.watch_timer.setInterval(2000);self.watch_timer.timeout.connect(self.poll_watch)
        build_interface(self)
        add_features(self)
        self.search_action = self.search.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        for key, callback in [('Ctrl+O', self.open_files), ('Ctrl+Return', self.start_conversion), ('Delete', self.remove_files)]:
            shortcut = QShortcut(QKeySequence(key), self.table if key == 'Delete' else self)
            if key == 'Delete':
                shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(callback)
        self.set_theme(self.settings.value('theme', 'dark'))
        self.selection_changed()
        self.refresh_dashboard()
        self.update_responsive_layout()
        if self.settings.value('automatic_updates',False,type=bool):QTimer.singleShot(1500,self.automatic_update_check)

    def automatic_update_check(self):
        from updater import read_config
        if self.worker or not self.isVisible():return
        if not self.settings.value('update_url',read_config()['manifest_url']):return
        self.open_updates(automatic=True)

    def open_updates(self,checked=False,automatic=False):
        if self.worker is None:UpdateDialog(self,automatic=automatic).exec()

    def open_support(self):
        from support import donation_url
        try:
            url = donation_url()
        except ValueError as error:
            QMessageBox.warning(self, 'Sostieni il progetto', str(error))
            return
        if not url:
            QMessageBox.information(self, 'Sostieni il progetto',
                'Grazie per il tuo sostegno! La pagina donazioni non è ancora disponibile. '
                'Puoi già aiutare condividendo il progetto e segnalando problemi su GitHub.')
            return
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, 'Sostieni il progetto', 'Impossibile aprire il browser. Riprova più tardi.')

    def set_theme(self, theme):
        self.theme = theme if theme in PALETTES else 'dark'
        self.settings.setValue('theme', self.theme)
        self.setStyleSheet(stylesheet(self.theme))
        self.palette_colors = PALETTES[self.theme]
        colors = self.palette_colors
        for button in self.findChildren(QPushButton):
            name = button.property('icon_name')
            if name:
                color = colors['accent_text'] if button.objectName() == 'primary' else colors['muted']
                button.setIcon(icon(name, color, 18))
                button.setIconSize(QSize(18, 18))
        self.brand_icon.setPixmap(pixmap('convert', colors['accent'], 28))
        self.empty_icon.setPixmap(pixmap('files', colors['muted'], 44))
        self.drop_zone.symbol.setPixmap(pixmap('upload', colors['accent'], 36))
        opposite = 'light' if self.theme == 'dark' else 'dark'
        self.theme_btn.setText('Tema chiaro' if opposite == 'light' else 'Tema scuro')
        self.theme_btn.setIcon(icon('sun' if opposite == 'light' else 'moon', colors['muted'], 18))
        self.compact_theme.setIcon(self.theme_btn.icon())
        self.compact_theme.setToolTip(self.theme_btn.text())
        self.search_action.setIcon(icon('search', colors['muted'], 18))
        for row, path in enumerate(self.files):
            self.table.item(row, 0).setIcon(icon(category_icon(kind(path)), colors['muted']))
            self.decorate_status(row)
        self.update_selection_preview()

    def toggle_theme(self):
        self.set_theme('light' if self.theme == 'dark' else 'dark')

    def set_category(self, category):
        if self.worker is not None:
            return
        self.current_category = category
        self.nav_buttons[category].setChecked(True)
        blocker = QSignalBlocker(self.compact_category)
        self.compact_category.setCurrentIndex(self.compact_category.findData(category))
        del blocker
        self.table.clearSelection()
        self.apply_filter()

    def apply_filter(self):
        if self.worker is not None:
            return
        groups = {'image': {'image','vector','raw'}, 'media': {'audio','video'},
                  'document': {'text','docx','pdf','office','spreadsheet','legacy_sheet','presentation','table','ebook','web','subtitle'},
                  'data': {'table','spreadsheet','legacy_sheet'}, 'archive': {'archive'}}
        query = self.search.text().strip().casefold()
        visible = 0
        # Hidden rows cannot stay selected or enter a conversion batch.
        for row, path in enumerate(self.files):
            show = (self.current_category == 'all' or kind(path) in groups.get(self.current_category, set())) and query in Path(path).name.casefold()
            status=self.table.item(row,3).text()
            selected_status=self.status_filter.currentData()
            if selected_status=='done':show=show and status=='Fatto'
            elif selected_status=='error':show=show and status.startswith('Errore')
            elif selected_status=='pending':show=show and status in ('In attesa','Annullato')
            self.table.setRowHidden(row, not show)
            visible += int(show)
            if not show:
                for col in range(self.table.columnCount()):
                    item=self.table.item(row, col)
                    if item:item.setSelected(False)
        self.no_results.setVisible(bool(self.files) and not visible)
        self.queue_badge.setText(f'{visible} / {len(self.files)} file' if visible != len(self.files) else f'{visible} file')
        self.refresh_dashboard()

    def refresh_dashboard(self):
        self.queue_stack.setCurrentIndex(1 if self.files else 0)
        count = len(self.rows())
        for key, value in [('loaded',len(self.files)), ('selected',count), ('success',self.session_successes), ('error',self.session_errors)]:
            self.stat_values[key].setText(str(value))
        self.selection_badge.setText(f'{count} file')
        self.remove_btn.setEnabled(bool(count) and self.worker is None)
        self.clear_btn.setEnabled(bool(self.files) and self.worker is None)
        self.queue_summary.setText(f'{count} file selezionati · Ctrl o Shift per selezionare più righe.' if count else 'Seleziona una riga per vedere i formati disponibili.')
        self.update_selection_preview()

    def update_selection_preview(self):
        if not hasattr(self, 'preview'):
            return
        selected = self.rows()
        colors = PALETTES[self.theme]
        self.preview.setPixmap(pixmap('files', colors['muted'], 40))
        if not selected:
            self.selection_summary.setText('Nessun file selezionato')
            self.selection_detail.setText('Scegli una riga dalla coda.')
            return
        paths = [self.files[r] for r in selected if r < len(self.files)]
        if len(paths) != 1:
            self.selection_summary.setText(f'{len(paths)} file selezionati')
            self.selection_detail.setText('Vengono mostrati solo i formati compatibili con tutta la selezione.')
            return
        path = paths[0]
        self.selection_summary.setText(Path(path).name)
        self.selection_detail.setText(f'{Path(path).suffix.lstrip(".").upper()} · {self.table.item(selected[0], 2).text()}')
        self.preview.setPixmap(pixmap(category_icon(kind(path)), colors['accent'], 42))
        if kind(path) in ('image', 'vector'):
            reader = QImageReader(path)
            reader.setAutoTransform(True)
            size = reader.size()
            if size.isValid():
                reader.setScaledSize(size.scaled(QSize(248, 78), Qt.AspectRatioMode.KeepAspectRatio))
                image = reader.read()
                if not image.isNull():
                    self.preview.setPixmap(QPixmap.fromImage(image).scaled(QSize(248,78), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def decorate_status(self, row):
        item = self.table.item(row, 3)
        if item is None:
            return
        text = item.text()
        colors = PALETTES[self.theme]
        if text == 'Fatto':
            name, color = 'check', colors['success']
        elif text.startswith('Errore'):
            name, color = 'error', colors['error']
        elif text == 'Annullato':
            name, color = 'stop', colors['muted']
        else:
            name, color = 'clock', colors['accent'] if text.startswith('Conversione') else colors['muted']
        item.setIcon(icon(name, color, 16))
        item.setForeground(QColor(color))

    def update_progress_caption(self, value=0):
        if self.worker is not None:
            self.progress_caption.setText(f'{value} / {self.total_jobs} file')
        elif hasattr(self, 'completed') and self.completed:
            self.progress_caption.setText(f'{self.successes} riusciti')
        else:
            self.progress_caption.setText('Pronto')

    def open_results(self):
        if self.output_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_folder))

    def update_responsive_layout(self):
        compact = self.width() < 1120
        self.hero_title.setText('Convertitore Universale' if compact else 'I tuoi file, nel formato giusto.')
        self.hero_subtitle.setVisible(not compact)
        self.sidebar.setVisible(not compact)
        self.compact_tools.setVisible(compact)
        self.compact_updates.setVisible(compact)
        self.compact_category.setVisible(compact)
        self.compact_theme.setVisible(compact)
        self.table.setColumnHidden(1,compact)
        self.drop_zone.badge.setVisible(self.width() >= 1240)
        self.preview.setVisible(not compact)
        self.drop_zone.layout().setContentsMargins(16,10,16,10) if compact else self.drop_zone.layout().setContentsMargins(24,22,24,22)
        self.splitter.parentWidget().layout().setSpacing(12 if compact else 20)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'sidebar'):
            self.update_responsive_layout()

    def rows(self):
        return sorted({i.row() for i in self.table.selectedIndexes() if not self.table.isRowHidden(i.row())})

    def open_files(self):
        if self.worker is not None:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, 'Scegli i file')
        self.add_files(paths)

    def open_catalog(self):
        from format_catalog import FormatCatalog
        FormatCatalog(self).exec()

    def verify_file(self):
        if self.worker is not None:return
        if len(self.rows())!=1:
            QMessageBox.information(self,'Verifica SHA-256','Seleziona un solo file per calcolarne l’impronta SHA-256.')
            return
        InfoDialog(self,self.files[self.rows()[0]],checksum=True).exec()

    def add_files(self, paths):
        if self.worker is not None:
            return
        expanded=[]
        for original in paths:
            root=Path(original).resolve()
            if root.is_dir():
                for child in sorted(root.rglob('*')):
                    if child.is_file() and not child.is_symlink():
                        expanded.append(str(child));self.import_roots[str(child.resolve())]=str(root)
            else:expanded.append(str(root))
        for path in expanded:
            path = str(Path(path).resolve())
            if not Path(path).is_file() or path in self.files:
                continue
            try:
                size = Path(path).stat().st_size
            except OSError:
                continue
            self.files.append(path)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate((Path(path).name, CATEGORY_LABELS.get(kind(path), 'Non supportato'), (f'{size / 1048576:.1f} MB' if size >= 1048576 else f'{size / 1024:.1f} KB' if size >= 1024 else f'{size} B'), 'In attesa')):
                item = QTableWidgetItem(value)
                item.setToolTip(path if col == 0 else value)
                if col == 0:
                    item.setIcon(icon(category_icon(kind(path)), PALETTES[self.theme]['muted']))
                self.table.setItem(row, col, item)
            combo=QComboBox()
            for choice in FORMATS.get(kind(path),()):combo.addItem(choice.upper(),choice)
            combo.setCurrentIndex(max(0,combo.findData(default_format(path))))
            self.table.setCellWidget(row,4,combo)
            self.decorate_status(row)
        self.apply_filter()
        self.selection_changed()

    def remove_files(self):
        if self.worker is not None:
            return
        for row in reversed(self.rows()):
            del self.files[row]
            self.table.removeRow(row)
        self.apply_filter()
        self.selection_changed()

    def clear_files(self):
        if self.worker is not None:
            return
        self.table.setRowCount(0)
        self.files.clear()
        self.apply_filter()
        self.selection_changed()
        self.status.setText('Aggiungi i file per iniziare.')

    def selection_changed(self):
        paths = [self.files[r] for r in self.rows() if r < len(self.files)]
        previous = self.format_combo.currentData()
        blocker = QSignalBlocker(self.format_combo)
        choices = common_formats(paths)
        self.format_combo.clear()
        labels = {'png.zip': 'PNG — tutte le pagine PDF (ZIP)', 'jpg.zip': 'JPG — tutte le pagine PDF (ZIP)'}
        for choice in choices:
            self.format_combo.addItem(labels.get(choice, choice.upper()), choice)
        if previous in choices:
            self.format_combo.setCurrentIndex(self.format_combo.findData(previous))
        del blocker
        self.convert_btn.setEnabled(bool(paths) and (bool(choices) or (self.mixed_check.isChecked() and all(kind(p) in FORMATS for p in paths))) and self.worker is None)
        self.format_combo.setEnabled(bool(choices) and self.worker is None)
        self.format_changed()
        if paths and not choices and not self.mixed_check.isChecked():
            self.status.setText('Nessun formato comune: seleziona file compatibili. Il tipo sconosciuto non è ancora supportato.')
        elif paths and self.worker is None:
            self.status.setText(f'{len(paths)} file pronti. Scegli il formato e avvia la conversione.')
        elif not paths and self.worker is None:
            self.status.setText('Seleziona i file da convertire.' if self.files else 'Aggiungi i file per iniziare.')
        self.refresh_dashboard()

    def format_changed(self):
        categories = {kind(self.files[r]) for r in self.rows() if r < len(self.files)}
        fmt = self.format_combo.currentData()
        self.media_options.setVisible(bool(categories) and categories <= {'image', 'video', 'vector', 'raw'} and fmt not in ('txt', 'docx', 'mp3', 'wav'))
        show_audio = 'audio' in categories or ('video' in categories and fmt in ('mp3', 'wav'))
        show_fps = 'video' in categories and fmt not in ('mp3', 'wav')
        self.audio_options.setVisible(show_audio or show_fps)
        for widget in (self.bitrate_label, self.bitrate_combo, self.speed_label, self.speed_spin):
            widget.setVisible(show_audio)
        self.fps_label.setVisible(show_fps); self.fps_spin.setVisible(show_fps)
        self.table_options.setVisible(bool(categories & {'table', 'spreadsheet'}) and fmt in ('csv', 'tsv', 'json', 'jsonl', 'xlsx'))
        self.ocr_options.setVisible(bool(categories & {'image', 'pdf'}) and fmt in ('txt', 'docx', 'html', 'epub'))
        self.ocr_check.setVisible('pdf' in categories)
        self.pdf_options.setVisible(fmt in ('png.zip', 'jpg.zip'))
        hints = []
        if categories & {'table', 'spreadsheet'} and fmt in ('csv', 'tsv', 'json', 'jsonl', 'xlsx'):
            hints.append('Solo i dati del foglio scelto: stili e grafici non vengono esportati; formule conservate come testo. JSON deve essere tabellare.')
        if fmt=='jsonl':hints.append('JSON Lines: una riga JSON per ogni riga della tabella, intestazione inclusa.')
        if 'image' in categories and fmt in ('txt', 'docx'):
            hints.append('Il testo viene riconosciuto con Tesseract: installa il programma e le lingue selezionate.')
        if 'pdf' in categories and fmt in ('txt', 'docx', 'html', 'epub'):
            hints.append('Estrazione testo, senza impaginazione originale. Per scansioni attiva OCR (richiede Tesseract).')
        if fmt in ('png.zip', 'jpg.zip'):
            hints.append('Ogni pagina viene salvata come immagine numerata; tutte le immagini sono raccolte in un file ZIP.')
        if categories & {'office', 'presentation', 'legacy_sheet'} or ('docx' in categories and fmt in ('pdf', 'odt', 'rtf', 'epub')) or ('spreadsheet' in categories and fmt in ('ods', 'pdf')):
            hints.append('Richiede LibreOffice. Il risultato va controllato se contiene font, grafici o impaginazioni complesse.')
        if 'archive' in categories:
            hints.append('Conversione del contenitore ZIP/TAR: i file interni mantengono il loro formato; link e archivi cifrati non sono supportati.')
        if categories & {'ebook', 'web'}:
            hints.append('Conversione del testo: immagini e impaginazione originali non vengono ricostruite.')
        if 'subtitle' in categories:
            hints.append('SRT/VTT testuali. Le impostazioni di posizione VTT non vengono convertite in SRT.')
        self.format_hint.setText(' '.join(hints))
        self.format_hint.setVisible(bool(hints))

    def collect_options(self):
        options=dict(quality=self.quality_spin.value(),bitrate=self.bitrate_combo.currentText(),speed=self.speed_spin.value()/100,
            fps=self.fps_spin.value() or None,sheet=self.sheet_spin.value(),ocr=self.ocr_check.isChecked(),
            ocr_language=self.language_combo.currentData(),dpi=self.dpi_spin.value(),metadata=self.metadata_combo.currentData(),
            target_mb=self.target_mb.value(),denoise=self.denoise_check.isChecked(),start=self.trim_start.value(),end=self.trim_end.value(),
            watermark_text=self.watermark_text.text(),watermark_logo=self.watermark_logo.text(),watermark_opacity=self.watermark_opacity.value())
        if self.resize_check.isChecked():options.update(width=self.width_spin.value(),height=self.height_spin.value())
        if self.crop_check.isChecked():options['crop']=[s.value() for s in self.crop_spins]
        return options

    def output_stem(self,path,index,pattern=None):
        name=Path(path).stem
        if pattern is None and not self.naming_check.isChecked():return name
        import string
        pattern=self.naming_pattern.text() if pattern is None else pattern
        for _,field,spec,conversion in string.Formatter().parse(pattern):
            if field is not None and (field not in ('name','n') or conversion or (spec and (field!='n' or spec not in ('03d','04d','05d','d')))):
                raise ValueError('Usa solo {name}, {n}, {n:03d}, {n:04d} o {n:05d}.')
        result=pattern.format(name=name,n=index)
        if not result.strip() or len(result)>180 or any(c in result for c in '/\\<>:"|?*') or result.endswith(('.', ' ')):
            raise ValueError('Lo schema deve produrre un nome semplice, senza separatori o caratteri riservati.')
        if result.split('.')[0].upper() in ('CON','PRN','AUX','NUL',*[f'COM{n}' for n in range(1,10)],*[f'LPT{n}' for n in range(1,10)]):raise ValueError('Il nome è riservato da Windows.')
        return result

    def choose_output(self):
        return QFileDialog.getExistingDirectory(self,'Cartella di destinazione',self.settings.value('output_folder',''))

    def start_conversion(self):
        if self.worker is not None or not self.rows():return
        if not self.mixed_check.isChecked() and not self.format_combo.currentData():return
        folder=self.choose_output()
        if not folder:return
        jobs=[];options=self.collect_options()
        try:
            for n,row in enumerate(self.rows(),1):
                path=self.files[row];output=Path(folder)
                if self.preserve_check.isChecked() and path in self.import_roots:
                    output=output/Path(path).parent.relative_to(self.import_roots[path])
                fmt=self.table.cellWidget(row,4).currentData() if self.mixed_check.isChecked() else self.format_combo.currentData()
                jobs.append(dict(row=row,sources=[path],format=fmt,options=options,folder=str(output),stem=self.output_stem(path,n)))
        except ValueError as error:QMessageBox.warning(self,'Nome risultato',str(error));return
        self.launch_jobs(jobs,folder)

    def launch_jobs(self,jobs,folder):
        if self.worker is not None or not jobs:return
        self.retry_jobs=[];self.retry_btn.setEnabled(False)
        self.output_folder=folder;self.settings.setValue('output_folder',folder)
        self.completed=self.successes=self.errors=self.cancelled=0;self.total_jobs=len(jobs);self.batch={j['row']:j for j in jobs}
        self.progress.setRange(0,100);self.progress.setValue(0)
        for job in jobs:self.table.setItem(job['row'],3,QTableWidgetItem('In coda…'))
        self.worker=Worker(jobs);self.worker.result.connect(self.on_result);self.worker.active.connect(self.on_active)
        self.worker.progress.connect(self.on_progress);self.worker.finished.connect(self.on_finished)
        for widget in self.busy_widgets():widget.setEnabled(False)
        self.cancel_btn.setEnabled(True);self.status.setText('Conversione in corso…');self.worker.start()

    def busy_widgets(self):
        return [self.open_btn,self.remove_btn,self.clear_btn,self.retry_btn,self.drop_zone,self.table,self.format_combo,self.options_scroll,
                self.tools_btn,self.update_btn,self.compact_updates,self.folder_btn,self.convert_btn,self.search,self.status_filter,self.compact_tools,self.compact_category,self.watch_btn,
                *self.feature_buttons,*self.nav_buttons.values()]

    def retry_failed(self):
        if self.worker is not None or not self.retry_jobs:return
        jobs=[dict(job) for job in self.retry_jobs]
        missing=[p for job in jobs for p in job['sources'] if not Path(p).is_file()]
        if missing:
            QMessageBox.warning(self,'Originali mancanti','Ripristina questi file prima di riprovare:\n'+'\n'.join(dict.fromkeys(missing)))
            return
        self.add_files([p for job in jobs for p in job['sources']])
        for job in jobs:job['row']=self.files.index(str(Path(job['sources'][0]).resolve()))
        self.launch_jobs(jobs,jobs[0]['folder'])

    def on_progress(self,row,fraction,phase,eta):
        if fraction is None:self.progress.setRange(0,0)
        else:self.progress.setRange(0,100);self.progress.setValue(round(fraction*100))
        percentage=f'{fraction*100:.0f}%' if fraction is not None else 'In corso'
        remaining=f' · circa {eta:.0f} s rimanenti' if eta is not None else ''
        self.progress_caption.setText(f'{percentage}{remaining} · {self.completed}/{self.total_jobs} file')
        self.status.setText(f'{Path(self.files[row]).name}: {phase}')

    def apply_preset(self,name):
        values=self.store.recipes().get(name.removeprefix('Sequenza: '),{}) if name.startswith('Sequenza: ') else PRESETS.get(name,{})
        if not values:return
        self.quality_spin.setValue(values.get('quality',90));self.bitrate_combo.setCurrentText(values.get('bitrate','192k'))
        self.fps_spin.setValue(values.get('fps') or 0);self.resize_check.setChecked(bool(values.get('width')))
        self.width_spin.setValue(values.get('width') or 1920);self.height_spin.setValue(values.get('height') or 1080)
        if name.startswith('Sequenza: '):
            for control,key in [(self.target_mb,'target_mb'),(self.trim_start,'start'),(self.trim_end,'end')]:control.setValue(values.get(key,0))
            self.speed_spin.setValue(round(values.get('speed',1)*100));self.denoise_check.setChecked(values.get('denoise',False))
            self.metadata_combo.setCurrentIndex(max(0,self.metadata_combo.findData(values.get('metadata','remove'))))
            self.watermark_text.setText(values.get('watermark_text',''));self.watermark_logo.setText(values.get('watermark_logo',''))
            self.watermark_opacity.setValue(values.get('watermark_opacity',70));self.crop_check.setChecked(bool(values.get('crop')))
            for control,value in zip(self.crop_spins,values.get('crop',[0,0,500,500])):control.setValue(value)
            self.ocr_check.setChecked(values.get('ocr',False));self.language_combo.setCurrentIndex(max(0,self.language_combo.findData(values.get('ocr_language','ita+eng'))))
            self.sheet_spin.setValue(values.get('sheet',1));self.dpi_spin.setValue(values.get('dpi',150))
            idx=self.format_combo.findData(values.get('recipe_format'))
            if idx>=0:self.format_combo.setCurrentIndex(idx)
            if self.mixed_check.isChecked():
                for row in self.rows():
                    combo=self.table.cellWidget(row,4);index=combo.findData(values.get('recipe_format'))
                    if index>=0:combo.setCurrentIndex(index)
        if values.get('audio_only'):
            self.mixed_check.setChecked(True)
            for row in self.rows():
                combo=self.table.cellWidget(row,4);idx=combo.findData('mp3')
                if idx>=0:combo.setCurrentIndex(idx)
        self.format_changed()

    def save_recipe(self):
        name,ok=QInputDialog.getText(self,'Salva sequenza','Nome della sequenza:')
        if ok and name.strip():
            name=name.strip();values=self.collect_options();values['recipe_format']=self.format_combo.currentData();self.store.save_recipe(name,values);label='Sequenza: '+name
            if self.preset_combo.findText(label)<0:self.preset_combo.addItem(label)
            self.preset_combo.setCurrentText(label)

    def choose_logo(self):
        path,_=QFileDialog.getOpenFileName(self,'Logo filigrana','','Immagini (*.png *.jpg *.webp)')
        if path:self.watermark_logo.setText(path)

    def open_folder(self):
        if self.worker:return
        folder=QFileDialog.getExistingDirectory(self,'Importa cartella e sottocartelle')
        if folder:self.add_files([folder])

    def open_tools(self):
        if self.worker:return
        dialog=ToolsDialog(self,[self.files[r] for r in self.rows()])
        if dialog.exec():
            folder=self.choose_output()
            if not folder:return
            job=dialog.job;job['options']=dict(self.collect_options(),**job['options'])
            self.add_files(job['sources']);job['row']=self.files.index(str(Path(job['sources'][0]).resolve()))
            job['folder']=folder;job['stem']=Path(job['sources'][0]).stem+'_'+job['operation'];self.launch_jobs([job],folder)

    def open_history(self):
        if self.worker is None:HistoryDialog(self).exec()

    def repeat_history(self,entry):
        if self.worker:return
        job=dict(entry['job'])
        if not all(Path(p).is_file() for p in job['sources']):QMessageBox.warning(self,'Originali mancanti','Ripristina i file originali prima di ripetere.');return
        folder=self.choose_output()
        if folder:
            self.add_files(job['sources']);job.update(row=self.files.index(str(Path(job['sources'][0]).resolve())),folder=folder);self.launch_jobs([job],folder)

    def open_comparison(self):
        if self.worker:return
        rows=self.rows()
        if len(rows)!=1 or kind(self.files[rows[0]])!='image':QMessageBox.information(self,'Confronto','Seleziona una sola immagine.');return
        fmt=self.table.cellWidget(rows[0],4).currentData() if self.mixed_check.isChecked() else self.format_combo.currentData()
        if fmt not in ('jpg','png','webp','bmp','gif','tiff','ico'):QMessageBox.information(self,'Formato','Scegli un formato immagine per il confronto.');return
        ComparisonDialog(self,self.files[rows[0]],fmt,self.collect_options()).exec()

    def open_info(self):
        if self.worker is None and len(self.rows())==1:InfoDialog(self,self.files[self.rows()[0]]).exec()

    def toggle_watch(self):
        if self.worker:return
        if self.monitor:
            self.watch_timer.stop();self.monitor=None;self.watch_btn.setText('Sorveglia cartella');return
        source=QFileDialog.getExistingDirectory(self,'Cartella da sorvegliare: solo nuovi file')
        if not source:return
        output=self.choose_output()
        if not output:return
        try:self.monitor=FolderMonitor(source,output)
        except ValueError as error:QMessageBox.warning(self,'Cartella',str(error));return
        if self.naming_check.isChecked():
            try:self.output_stem('esempio.txt',1)
            except ValueError as error:self.monitor=None;QMessageBox.warning(self,'Nome risultato',str(error));return
        self.watch_count=0
        self.watch_options=self.collect_options();self.watch_naming=self.naming_check.isChecked();self.watch_pattern=self.naming_pattern.text();self.watch_preserve=self.preserve_check.isChecked();self.watch_audio_only=self.preset_combo.currentText()=='Solo audio'
        self.watch_recipe_format=self.watch_options.get('recipe_format') or (self.format_combo.currentData() if self.preset_combo.currentText().startswith('Sequenza: ') else None)
        self.watch_btn.setText('Ferma sorveglianza');self.watch_timer.start();self.status.setText('Sorveglianza attiva mentre l’app è aperta. Copia nuovi file nella cartella.')

    def poll_watch(self):
        if not self.monitor or self.worker:return
        paths=[p for p in self.monitor.poll() if kind(p)]
        if not paths:return
        self.add_files(paths);jobs=[]
        for n,path in enumerate(paths,1):
            if path not in self.files or not Path(path).is_file():continue
            self.import_roots[path]=str(self.monitor.folder)
            folder=self.monitor.output/Path(path).parent.relative_to(self.monitor.folder) if self.watch_preserve else self.monitor.output
            self.watch_count+=1
            fmt=self.watch_recipe_format if self.watch_recipe_format in FORMATS[kind(path)] else default_format(path,self.watch_audio_only)
            stem=self.output_stem(path,self.watch_count,self.watch_pattern) if self.watch_naming else Path(path).stem
            jobs.append(dict(row=self.files.index(path),sources=[path],folder=str(folder),format=fmt,options=self.watch_options,stem=stem))
        if jobs:self.launch_jobs(jobs,str(self.monitor.output))

    def check_dependencies(self):
        if self.worker is None:ComponentDialog(self).exec()

    def cancel_queue(self):
        if self.worker is not None:
            self.worker.requestInterruption()
            self.cancel_btn.setEnabled(False)
            self.status.setText('Annullamento del file in corso…')

    def on_active(self, row):
        self.progress.setRange(0,0)
        self.table.setItem(row, 3, QTableWidgetItem('Conversione in corso…'))
        self.decorate_status(row)

    def on_result(self, row, success, message):
        if success is not True:self.retry_jobs.append(dict(self.batch[row]))
        self.completed += 1
        self.successes += int(success is True)
        self.session_successes += int(success is True)
        self.session_errors += int(success is False)
        self.errors += int(success is False);self.cancelled += int(success is None)
        try:self.store.add_history(self.batch[row],success,message)
        except OSError:self.status.setText('Conversione terminata, ma la cronologia non è stata salvata.')
        item = QTableWidgetItem('Fatto' if success else 'Annullato' if success is None else 'Errore — apri dettagli')
        item.setToolTip(message)
        self.table.setItem(row, 3, item)
        self.decorate_status(row)
        self.refresh_dashboard()
        self.progress.setRange(0,100);self.progress.setValue(100)

    def on_finished(self):
        cancelled = self.worker.isInterruptionRequested()
        self.worker.deleteLater()
        self.worker = None
        self.cancel_btn.setEnabled(False)
        for row in range(self.table.rowCount()):
            if self.table.item(row, 3).text() == 'In coda…':
                if row in self.batch:self.retry_jobs.append(dict(self.batch[row]))
                self.table.setItem(row, 3, QTableWidgetItem('Annullato'))
                self.decorate_status(row)
        for widget in self.busy_widgets():widget.setEnabled(True)
        self.retry_btn.setEnabled(bool(self.retry_jobs))
        self.selection_changed()
        self.folder_btn.setEnabled(bool(self.successes))
        self.apply_filter()
        self.search.setEnabled(True)
        self.compact_tools.setEnabled(True)
        self.compact_category.setEnabled(True)
        for button in self.nav_buttons.values():
            button.setEnabled(True)
        self.update_progress_caption(self.completed)
        prefix = 'Coda fermata' if cancelled else 'Completato'
        self.status.setText(f'{prefix}: {self.successes} riusciti, {self.errors} errori, {self.total_jobs - self.completed + self.cancelled} annullati. Doppio clic sullo stato per dettagli.')

    def details(self, item):
        status = self.table.item(item.row(), 3)
        if status and status.toolTip():
            QMessageBox.information(self, 'Dettagli conversione', status.toolTip())

    def closeEvent(self, event):
        if self.worker is not None:
            self.status.setText('Attendi la fine della conversione prima di chiudere.')
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    if sys.platform=='win32':
        import ctypes
        # Keep the handle alive until process exit so setup can detect a running app.
        main.mutex=ctypes.windll.kernel32.CreateMutexW(None,False,'ConvertitoreUniversaleDesktop')
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    import multiprocessing
    if sys.platform == 'win32' and not getattr(sys, 'frozen', False):
        pythonw = Path(sys.executable).with_name('pythonw.exe')
        if pythonw.is_file():
            multiprocessing.set_executable(str(pythonw))
    multiprocessing.freeze_support()
    main()
