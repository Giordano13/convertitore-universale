"""LibreOffice conversion with explicit export filters and an isolated profile."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

FILTERS = {
    'writer': {'pdf': 'writer_pdf_Export', 'docx': 'Office Open XML Text', 'odt': 'writer8',
               'rtf': 'Rich Text Format', 'txt': 'Text (encoded):UTF8', 'epub': 'EPUB'},
    'calc': {'pdf': 'calc_pdf_Export', 'xlsx': 'Calc MS Excel 2007 XML', 'ods': 'calc8'},
    'impress': {'pdf': 'impress_pdf_Export', 'pptx': 'Impress MS PowerPoint 2007 XML', 'odp': 'impress8'},
}


def libreoffice_executable():
    override = os.environ.get('LIBREOFFICE_CMD')
    if override and Path(override).is_file():
        return override
    found = shutil.which('soffice') or shutil.which('libreoffice')
    if found:
        return found
    for path in ('C:/Program Files/LibreOffice/program/soffice.exe',
                 'C:/Program Files (x86)/LibreOffice/program/soffice.exe',
                 '/Applications/LibreOffice.app/Contents/MacOS/soffice'):
        if Path(path).exists():
            return path
    raise RuntimeError('Questa conversione richiede LibreOffice. Installalo oppure imposta LIBREOFFICE_CMD al suo eseguibile.')


def convert_office(source, target, fmt, family='writer'):
    if fmt not in FILTERS[family]:
        raise ValueError('Formato Office non supportato per questa categoria.')
    if Path(source).suffix.lower() == '.' + fmt:
        shutil.copyfile(source, target)
        return
    executable = libreoffice_executable()
    with tempfile.TemporaryDirectory() as directory:
        profile = (Path(directory) / 'profile').as_uri()
        command = [executable, f'-env:UserInstallation={profile}', '--headless', '--nologo', '--nodefault',
                   '--convert-to', f'{fmt}:{FILTERS[family][fmt]}', '--outdir', directory, str(Path(source).resolve())]
        result = subprocess.run(command, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, text=True, errors='replace', timeout=180)
        generated = Path(directory) / (Path(source).stem + '.' + fmt)
        if result.returncode or not generated.exists() or not generated.stat().st_size:
            raise RuntimeError('LibreOffice non ha creato il risultato. ' + (result.stderr + result.stdout)[-1000:])
        shutil.copyfile(generated, target)
