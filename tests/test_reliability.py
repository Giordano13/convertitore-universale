import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine import convert, reserve_output
from state_store import StateStore
from watch_folder import FolderMonitor
from process_worker import run_job
from process_worker import remove_partial


class ReliabilityTests(unittest.TestCase):
    def test_partial_cleanup_retries_temporary_windows_file_lock(self):
        with patch.object(Path,'unlink',side_effect=[PermissionError('busy'),PermissionError('busy'),None]) as unlink,patch('process_worker.time.sleep'):
            remove_partial('partial.mp4')
            self.assertEqual(unlink.call_count,3)

    def test_partial_cleanup_reports_persistent_lock(self):
        with patch.object(Path,'unlink',side_effect=PermissionError('busy')),patch('process_worker.time.sleep'):
            with self.assertRaises(PermissionError):remove_partial('partial.mp4')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_original_and_existing_output_are_never_overwritten(self):
        source = self.root / 'original.txt'
        source.write_text('Prezioso originale', encoding='utf-8')
        target = self.root / 'existing.docx'
        target.write_bytes(b'Existing document')
        for destination in (source, target):
            before = destination.read_bytes()
            with self.assertRaises(ValueError):
                convert(source, self.root, 'docx', target=destination)
            self.assertEqual(destination.read_bytes(), before)

    def test_missing_source_does_not_reserve_an_output(self):
        with self.assertRaisesRegex(ValueError, 'originale'):
            convert(self.root / 'missing.txt', self.root, 'docx')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_output_directory_created_and_paths_rejected(self):
        folder = self.root / 'new' / 'nested'
        first = reserve_output(folder, 'documento', 'pdf')
        second = reserve_output(folder, 'documento', 'pdf')
        self.assertTrue(first.exists())
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            reserve_output(folder, '../outside', 'pdf')

    def test_malformed_state_is_recoverable(self):
        store = StateStore(self.root)
        for value in ('null', '{}', '42', 'not json', '[null, {}, 4]'):
            (self.root / 'history.json').write_text(value)
            self.assertEqual(store.history(), [])
        (self.root / 'recipes.json').write_text('{"bad":null,"good":{"quality":80}}')
        self.assertEqual(store.recipes(), {'good': {'quality': 80}})
        store.add_history({'sources': ['missing.txt']}, False, 'File mancante')
        self.assertEqual(len(store.history()), 1)

    def test_failed_atomic_write_preserves_previous_state(self):
        store = StateStore(self.root)
        store.save_recipe('original', {'quality': 80})
        with patch.object(Path, 'replace', side_effect=OSError('Disk error')):
            with self.assertRaises(OSError):
                store.save_recipe('new', {'quality': 90})
        self.assertEqual(store.recipes(), {'original': {'quality': 80}})
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_watch_handles_deleted_pending_and_recreated_files(self):
        folder = self.root / 'incoming'
        folder.mkdir()
        monitor = FolderMonitor(folder, self.root / 'out')
        source = folder / 'new.txt'
        source.write_text('first')
        self.assertEqual(monitor.poll(), [])
        source.unlink()
        self.assertEqual(monitor.poll(), [])
        self.assertFalse(monitor.pending)
        source.write_text('second')
        self.assertEqual(monitor.poll(), [])
        self.assertEqual(monitor.poll(), [str(source)])
        source.unlink()
        monitor.poll()
        source.write_text('third')
        self.assertEqual(monitor.poll(), [])
        self.assertEqual(monitor.poll(), [str(source)])

    def test_missing_watch_folder_is_rejected(self):
        with self.assertRaises(ValueError):
            FolderMonitor(self.root / 'missing', self.root / 'out')

    def test_windows_csv_preserves_columns_quotes_and_multiline_cells(self):
        from converters.table_converter import read_rows
        for ending in ('\n','\r\n'):
            source=self.root/'data.csv'
            text=ending.join(['nome;codice;nota','Anna;001;"ciao; mondo"','Luca;002;"prima'+ending+'seconda"',''])
            source.write_bytes(text.encode('utf-8'))
            self.assertEqual(read_rows(source),[
                ['nome','codice','nota'],['Anna','001','ciao; mondo'],['Luca','002','prima'+ending+'seconda']])

    def test_pre_cancelled_job_does_not_start_a_process(self):
        target=self.root/'reserved.txt';target.touch()
        with patch('process_worker.mp.get_context') as context:
            self.assertEqual(run_job({},target,lambda:True,lambda *args:None),(None,'Annullato'))
            context.assert_not_called()
        self.assertFalse(target.exists())

    def test_process_start_failure_cleans_reserved_output_and_temp_folder(self):
        target=self.root/'reserved.txt';target.touch()
        from unittest.mock import MagicMock
        process=MagicMock();process.start.side_effect=OSError('Cannot start');process.is_alive.return_value=False
        with patch('process_worker.mp.get_context') as context:
            context.return_value.Process.return_value=process
            with self.assertRaises(OSError):
                run_job({},target,lambda:False,lambda *args:None)
            temporary=context.return_value.Process.call_args.kwargs['args'][-1]
            self.assertFalse(Path(temporary).exists())
        self.assertFalse(target.exists())
