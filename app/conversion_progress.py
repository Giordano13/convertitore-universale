"""Progress callbacks shared by converters inside an isolated job process."""
import time
import threading
import subprocess
from collections import deque

CALLBACK = None


def report(fraction=None, phase='Conversione', eta=None):
    if CALLBACK:
        CALLBACK(fraction, phase, eta)


def run_process(command, duration=None, timeout=None, ffmpeg=False, completed_report=True):
    """Drain both pipes and optionally interpret FFmpeg's machine-readable progress."""
    command = list(map(str, command))
    if ffmpeg:
        command[1:1] = ['-nostdin', '-hide_banner', '-nostats', '-progress', 'pipe:1']
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding='utf-8', errors='replace', creationflags=flags)
    errors, output = deque(maxlen=100), deque(maxlen=100)
    started = time.monotonic()
    def drain_errors():
        for line in process.stderr:
            errors.append(line)
    reader = threading.Thread(target=drain_errors, daemon=True);reader.start()
    def drain_output():
        for line in process.stdout:
            output.append(line)
            if ffmpeg and duration:
                key, _, value = line.strip().partition('=')
                if key == 'out_time_us':
                    try:
                        fraction = min(.999, max(0, int(value) / 1_000_000 / duration))
                        elapsed = time.monotonic() - started
                        eta = elapsed * (1 - fraction) / fraction if fraction > .01 else None
                        report(fraction, 'Codifica audio/video', eta)
                    except ValueError:
                        pass
    stdout_reader=threading.Thread(target=drain_output,daemon=True);stdout_reader.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill();process.wait();reader.join();stdout_reader.join()
        process.stdout.close();process.stderr.close()
        raise RuntimeError('Il programma ha superato il tempo massimo.')
    reader.join();stdout_reader.join()
    process.stdout.close();process.stderr.close()
    if process.returncode:
        raise RuntimeError('Conversione fallita: ' + ''.join(errors)[-2000:])
    if completed_report:report(1.0, 'Completato', 0)
    return ''.join(output)
