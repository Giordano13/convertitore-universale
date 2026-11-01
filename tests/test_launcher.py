import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from launch_app import launch

class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'cartella con spazi'
        (self.root / 'app').mkdir(parents=True)
        env = patch.dict(os.environ, {'LOCALAPPDATA': self.temp.name})
        env.start(); self.addCleanup(env.stop)
    def logs(self):
        return list((Path(self.temp.name) / 'ConvertitoreUniversale' / 'logs').glob('app-*.log'))
    def test_success_with_spaces_in_path(self):
        (self.root / 'app' / 'main.py').write_text('print("avviato")\n')
        self.assertEqual(launch(self.root), 0)
        self.assertIn('avviato', self.logs()[0].read_text())
    def test_failure_preserves_complete_traceback(self):
        (self.root / 'app' / 'main.py').write_text('raise RuntimeError("errore di prova")\n')
        with patch('launch_app.ctypes'), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(launch(self.root), 1)
        text = self.logs()[0].read_text()
        self.assertIn('Traceback', text)
        self.assertIn('RuntimeError: errore di prova', text)
    def test_missing_executable_reports_error(self):
        with patch('launch_app.subprocess.run', side_effect=OSError('eseguibile mancante')), patch('launch_app.ctypes'), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(launch(self.root), 1)
    def test_pythonw_uses_hidden_console_interpreter_for_error_logging(self):
        import types
        fake_os = types.SimpleNamespace(name='nt', environ=os.environ)
        with patch('launch_app.os', fake_os), patch('launch_app.sys.executable', str(self.root / 'pythonw.exe')), patch('launch_app.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(launch(self.root), 0)
        self.assertEqual(run.call_args.args[0][0], str(self.root / 'python.exe'))
    def test_background_process_receives_log_handles(self):
        with patch('launch_app.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(launch(self.root), 0)
        self.assertEqual(run.call_args.args[0], [sys.executable, str(self.root / 'app' / 'main.py')])
        self.assertEqual(run.call_args.kwargs['cwd'], self.root)
        self.assertEqual(run.call_args.kwargs['stderr'], subprocess.STDOUT)
        self.assertNotIn('shell', run.call_args.kwargs)
