import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtCore import QEventLoop, QTimer
from main import QApplication, MainWindow, DARK_STYLE, Worker

class GuiTests(unittest.TestCase):
    def test_checksum_dialog_matches_and_rejects_expected_digest(self):
        import hashlib
        from feature_dialogs import InfoDialog
        window=MainWindow()
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'sample.txt';source.write_bytes(b'abc')
            dialog=InfoDialog(window,str(source),checksum=True)
            loop=QEventLoop();dialog.worker.finished.connect(loop.quit)
            timer=QTimer();timer.setSingleShot(True);timer.timeout.connect(loop.quit);timer.start(15000)
            loop.exec();timer.stop()
            dialog.expected.setText(hashlib.sha256(b'abc').hexdigest().upper())
            self.assertIn('Corrispondenza confermata',dialog.verification.text())
            dialog.expected.setText('0'*64);self.assertIn('NON coincidono',dialog.verification.text())
            dialog.expected.setText('invalid');self.assertIn('64 caratteri',dialog.verification.text())
            dialog.close()
        window.close()

    def test_status_filter_catalog_and_new_data_category(self):
        from main import QTableWidgetItem
        from format_catalog import FormatCatalog
        window=MainWindow()
        with tempfile.TemporaryDirectory() as directory:
            for name in ('input.jsonl','input.png','input.csv'):
                path=Path(directory)/name;path.write_text('example');window.add_files([str(path)])
            window.table.setItem(0,3,QTableWidgetItem('Fatto'))
            window.table.setItem(2,3,QTableWidgetItem('Errore — apri dettagli'))
            window.table.selectAll();window.status_filter.setCurrentIndex(window.status_filter.findData('error'))
            self.assertTrue(window.table.isRowHidden(0));self.assertFalse(window.table.isRowHidden(2))
            self.assertNotIn(0,window.rows())
            window.status_filter.setCurrentIndex(0);window.set_category('data')
            self.assertTrue(window.table.isRowHidden(1));self.assertFalse(window.table.isRowHidden(0))
            dialog=FormatCatalog(window);dialog.search.setText('jsonl')
            self.assertTrue(any(not dialog.table.isRowHidden(row) for row in range(dialog.table.rowCount())))
            dialog.search.setText('nonexistent-format')
            self.assertTrue(all(dialog.table.isRowHidden(row) for row in range(dialog.table.rowCount())))
            dialog.close()
        window.close()

    def test_retry_keeps_job_settings_and_remaps_removed_rows(self):
        window=MainWindow()
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'retry.txt';source.write_text('Hello')
            job=dict(row=42,sources=[str(source)],format='docx',options={'quality':75},folder=directory)
            window.retry_jobs=[job]
            with patch.object(window,'launch_jobs') as launch:
                window.retry_failed()
            jobs,folder=launch.call_args.args
            self.assertEqual(jobs[0]['row'],0)
            self.assertEqual(jobs[0]['options'],{'quality':75})
            self.assertEqual(jobs[0]['format'],'docx')
            self.assertEqual(folder,directory)
        window.close()

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(DARK_STYLE)

    def test_background_conversion_and_format_panels(self):
        window = MainWindow()
        window.show()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'table.csv';source.write_text('nome,codice\nGiordano,001')
            window.add_files([str(source)])
            window.table.selectRow(0)
            window.format_combo.setCurrentIndex(window.format_combo.findData('xlsx'))
            self.assertTrue(window.table_options.isVisible())
            self.assertFalse(window.audio_options.isVisible())
            with patch('main.QFileDialog.getExistingDirectory', return_value=directory):
                window.start_conversion()
            self.assertIsNotNone(window.worker)
            self.assertFalse(window.convert_btn.isEnabled())
            loop = QEventLoop()
            window.worker.finished.connect(loop.quit)
            timer = QTimer();timer.setSingleShot(True);timer.timeout.connect(loop.quit);timer.start(10000)
            loop.exec();timer.stop()
            self.assertIsNone(window.worker)
            self.assertEqual(window.successes, 1)
            self.assertFalse(window.retry_btn.isEnabled())
            self.assertTrue(window.convert_btn.isEnabled())
            self.assertTrue(list(Path(directory).glob('*_convertito.xlsx')))
            window.clear_files()
            pdf = Path(directory) / 'test.pdf';pdf.write_bytes(b'placeholder')
            window.add_files([str(pdf)]);window.table.selectRow(0)
            window.format_combo.setCurrentIndex(window.format_combo.findData('png.zip'))
            self.assertTrue(window.pdf_options.isVisible())
            window.format_combo.setCurrentIndex(window.format_combo.findData('txt'))
            self.assertTrue(window.ocr_options.isVisible())
        window.close()

    def test_stop_queue_cancels_current_and_pending(self):
        window=MainWindow();window.show()
        with tempfile.TemporaryDirectory() as directory:
            paths=[]
            for name in ('first.txt','second.txt'):
                p=Path(directory)/name;p.write_text('Hello');paths.append(str(p))
            window.add_files(paths);window.table.selectAll()
            window.format_combo.setCurrentIndex(window.format_combo.findData('docx'))
            def worker_factory(*args):
                worker=Worker(*args);worker.active.connect(lambda row:window.cancel_queue());return worker
            with patch('main.QFileDialog.getExistingDirectory',return_value=directory),patch('main.Worker',side_effect=worker_factory):
                window.start_conversion();loop=QEventLoop();window.worker.finished.connect(loop.quit)
                QTimer.singleShot(10000,loop.quit);loop.exec()
            self.assertIsNone(window.worker);self.assertEqual(window.successes,0)
            self.assertEqual(len(window.retry_jobs),2)
            self.assertTrue(window.retry_btn.isEnabled())
            self.assertEqual(window.table.item(0,3).text(),'Annullato');self.assertEqual(window.table.item(1,3).text(),'Annullato')
            self.assertFalse(list(Path(directory).glob('*_convertito.docx')))
            window.retry_failed()
            loop=QEventLoop();window.worker.finished.connect(loop.quit)
            timer=QTimer();timer.setSingleShot(True);timer.timeout.connect(loop.quit);timer.start(15000)
            loop.exec();timer.stop()
            self.assertIsNone(window.worker)
            self.assertEqual(window.successes,2)
            self.assertFalse(window.retry_btn.isEnabled())
            self.assertEqual(len(list(Path(directory).glob('*_convertito.docx'))),2)
        window.close()

    def test_filters_never_convert_hidden_rows(self):
        window = MainWindow();window.show()
        with tempfile.TemporaryDirectory() as directory:
            paths=[]
            for name in ('photo.png','recording.wav','notes.txt'):
                p=Path(directory)/name;p.write_bytes(b'example');paths.append(str(p))
            window.add_files(paths);window.table.selectAll()
            window.set_category('image')
            self.assertFalse(window.table.isRowHidden(0))
            self.assertTrue(window.table.isRowHidden(1))
            window.table.selectAll()
            self.assertEqual(window.rows(),[0])
            window.search.setText('does-not-exist')
            self.assertEqual(window.rows(),[])
            self.assertFalse(window.convert_btn.isEnabled())
            window.search.clear();window.set_category('all')
            self.assertFalse(any(window.table.isRowHidden(i) for i in range(3)))
        window.close()

    def test_theme_and_compact_controls(self):
        window=MainWindow();window.show()
        window.set_theme('light');self.app.processEvents()
        self.assertEqual(window.theme,'light')
        window.resize(960,720);self.app.processEvents()
        self.assertFalse(window.sidebar.isVisible())
        self.assertTrue(window.compact_category.isVisible())
        window.compact_category.setCurrentIndex(window.compact_category.findData('archive'))
        self.assertEqual(window.current_category,'archive')
        window.resize(1280,840);self.app.processEvents()
        self.assertTrue(window.sidebar.isVisible())
        window.set_theme('dark');window.close()

    def test_mixed_formats_recursive_import_and_saved_workflow(self):
        from PIL import Image
        from state_store import StateStore
        window=MainWindow();window.show()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);incoming=root/'incoming';(incoming/'nested').mkdir(parents=True);output=root/'output';output.mkdir()
            image=incoming/'nested'/'photo.png';Image.new('RGB',(40,30),'blue').save(image)
            text=incoming/'note.txt';text.write_text('MIXED QUEUE')
            window.store=StateStore(root/'state');window.add_files([str(incoming)]);window.table.selectAll();window.mixed_check.setChecked(True)
            for row,path in enumerate(window.files):
                combo=window.table.cellWidget(row,4);combo.setCurrentIndex(combo.findData('webp' if path.endswith('.png') else 'docx'))
            self.assertTrue(window.convert_btn.isEnabled());self.assertFalse(window.table.isColumnHidden(4))
            window.naming_check.setChecked(True);window.naming_pattern.setText('batch_{name}_{n:03d}')
            with patch('main.QFileDialog.getExistingDirectory',return_value=str(output)):
                window.start_conversion();loop=QEventLoop();window.worker.finished.connect(loop.quit);QTimer.singleShot(10000,loop.quit);loop.exec()
            self.assertIsNone(window.worker);self.assertEqual(window.successes,2)
            self.assertEqual(len(list((output/'nested').glob('batch_photo_*webp'))),1);self.assertEqual(len(list(output.glob('batch_note_*docx'))),1)
            self.assertEqual(len(window.store.history()),2)
            window.table.selectRow(window.files.index(str(image.resolve())));window.format_combo.setCurrentIndex(window.format_combo.findData('webp'))
            window.crop_check.setChecked(True)
            for control,value in zip(window.crop_spins,[0,0,20,20]):control.setValue(value)
            with patch('main.QInputDialog.getText',return_value=('My web images',True)):window.save_recipe()
            window.crop_check.setChecked(False);window.preset_combo.setCurrentText('Personalizzato');window.preset_combo.setCurrentText('Sequenza: My web images')
            self.assertTrue(window.crop_check.isChecked());self.assertEqual(window.store.recipes()['My web images']['recipe_format'],'webp')
        window.close()

    def test_watch_folder_actually_converts_new_file(self):
        from state_store import StateStore
        from watch_folder import FolderMonitor
        from PIL import Image
        window=MainWindow();window.show()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);incoming=root/'incoming';incoming.mkdir();out=root/'out';out.mkdir();window.store=StateStore(root/'state')
            window.monitor=FolderMonitor(incoming,out);window.watch_options=window.collect_options();window.watch_audio_only=False
            window.watch_preserve=True;window.watch_naming=False;window.watch_count=0;window.watch_recipe_format=None
            (incoming/'nested').mkdir();source=incoming/'nested'/'new.png';Image.new('RGB',(32,24),'red').save(source)
            window.poll_watch();self.assertIsNone(window.worker);window.poll_watch();self.assertIsNotNone(window.worker)
            loop=QEventLoop();window.worker.finished.connect(loop.quit);QTimer.singleShot(10000,loop.quit);loop.exec()
            self.assertIsNone(window.worker);self.assertEqual(window.successes,1);self.assertTrue((out/'nested'/'new_convertito.jpg').is_file())
            window.poll_watch();self.assertIsNone(window.worker);window.monitor=None
        window.close()

    def test_preview_is_real_and_can_be_closed_during_work(self):
        from PIL import Image
        from feature_dialogs import ComparisonDialog,InfoDialog
        window=MainWindow()
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'preview.png';Image.new('RGB',(80,60),'red').save(source)
            comparison=ComparisonDialog(window,str(source),'jpg',dict(quality=70))
            loop=QEventLoop();comparison.worker.finished.connect(loop.quit);QTimer.singleShot(10000,loop.quit);loop.exec()
            self.assertIsNone(comparison.worker);self.assertIn('Risultato:',comparison.summary.text());self.assertFalse(comparison.after.pixmap().isNull())
            comparison.quality.setValue(40);comparison.render()
            loop=QEventLoop();comparison.worker.finished.connect(loop.quit);QTimer.singleShot(10000,loop.quit);loop.exec()
            self.assertIsNone(comparison.worker);self.assertIn('Qualità 40%',comparison.summary.text());comparison.close()
            second=ComparisonDialog(window,str(source),'webp',{})
            self.assertTrue(second.close());self.assertIsNone(second.worker)
            info=InfoDialog(window,str(source));self.assertTrue(info.close())
            self.app.processEvents()
        window.close()

    def test_update_dialog_check_download_and_invalid_file(self):
        import json,hashlib
        from update_dialog import UpdateDialog
        from test_distribution import Response
        from version import PRODUCT_ID
        from PyQt6.QtCore import QStandardPaths
        window=MainWindow()
        previous=window.settings.value('update_url','')
        with tempfile.TemporaryDirectory() as directory:
            url='https://updates.example.org/Setup.exe';binary=b'MZ'+b'update-test'*20
            release=dict(product_id=PRODUCT_ID,version='2.2.0',platform='windows-x64',download_url=url,size=len(binary),sha256=hashlib.sha256(binary).hexdigest(),notes='New version')
            dialog=UpdateDialog(window);dialog.show();dialog.url.setText('https://updates.example.org/update.json')
            def finish():
                loop=QEventLoop();dialog.worker.finished.connect(loop.quit);QTimer.singleShot(10000,loop.quit);loop.exec();self.assertIsNone(dialog.worker)
            with patch('updater.open_trusted',return_value=Response(json.dumps(release).encode(),dialog.url.text())):
                dialog.start_check();finish()
            self.assertTrue(dialog.download.isEnabled());self.assertEqual(dialog.notes.toPlainText(),'New version')
            with patch('updater.open_trusted',return_value=Response(binary,url)),patch('update_dialog.QStandardPaths.writableLocation',return_value=directory):
                dialog.start_download();finish()
            self.assertEqual(dialog.installer.read_bytes(),binary);self.assertIn('verificato',dialog.status.text());dialog.close()
        window.settings.setValue('update_url',previous);window.close()
