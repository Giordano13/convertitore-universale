"""Read-only dependency checks for the app's Help panel and command line."""
import importlib.util
import shutil
import subprocess
from runtime_paths import media_executable,tessdata_arguments
from converters.office_converter import libreoffice_executable
from converters.ocr_converter import tesseract_executable


def dependency_report():
    lines = ['Convertitore Universale — controllo componenti', '']
    for name in ('PyQt6', 'PIL', 'docx', 'pypdf', 'reportlab', 'openpyxl', 'pymupdf', 'pillow_heif', 'markdown', 'defusedxml', 'py7zr', 'rawpy'):
        lines.append(f'{name}: ' + ('OK' if importlib.util.find_spec(name) else 'MANCANTE — esegui Setup.vbs'))
    lines.append('')
    try:ffmpeg=media_executable('ffmpeg')
    except RuntimeError:ffmpeg=None
    lines.append('FFmpeg: ' + (ffmpeg or 'MANCANTE — richiesto per audio/video; aggiungilo al PATH'))
    try:ffprobe=media_executable('ffprobe')
    except RuntimeError:ffprobe=None
    lines.append('FFprobe: '+(ffprobe or 'MANCANTE — installalo insieme a FFmpeg'))
    try:
        lines.append('LibreOffice: ' + libreoffice_executable())
    except RuntimeError:
        lines.append('LibreOffice: MANCANTE — richiesto per conversioni Office')
    try:
        executable = tesseract_executable()
        lines.append('Tesseract: ' + executable)
        result = subprocess.run([executable, '--list-langs']+tessdata_arguments('eng'), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, text=True, errors='replace', timeout=5)
        lines.append('Lingue OCR disponibili:\n' + result.stdout.strip())
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        lines.append('Tesseract: non disponibile — ' + str(error))
    return '\n'.join(lines)

if __name__ == '__main__':
    print(dependency_report())
