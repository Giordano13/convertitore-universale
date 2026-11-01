"""Local OCR via installed Tesseract; no file leaves the computer."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageOps
from runtime_paths import tessdata_arguments


def tesseract_executable():
    override = os.environ.get('TESSERACT_CMD')
    if override and Path(override).is_file():
        return override
    executable = shutil.which('tesseract')
    if executable:
        return executable
    for base in ('C:/Program Files', 'C:/Program Files (x86)'):
        candidate = Path(base) / 'Tesseract-OCR/tesseract.exe'
        if candidate.exists():
            return str(candidate)
    raise RuntimeError('OCR richiede Tesseract. Installalo, oppure imposta TESSERACT_CMD al percorso di tesseract.exe.')


def ocr_image(source, language='ita+eng'):
    executable = tesseract_executable()
    with tempfile.TemporaryDirectory() as directory:
        image_path = Path(directory) / 'input.png'
        if str(source).lower().endswith(('.heic', '.heif')):
            from pillow_heif import register_heif_opener
            register_heif_opener()
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert('RGBA')
            white = Image.new('RGB', image.size, 'white')
            white.paste(image, mask=image.getchannel('A'))
            white.save(image_path)
        result = subprocess.run([executable, str(image_path), 'stdout', '-l', language]+tessdata_arguments(language),
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, encoding='utf-8', errors='replace', timeout=180)
        if result.returncode:
            raise RuntimeError('Tesseract: controlla che le lingue selezionate siano installate. ' + result.stderr[-800:])
        if not result.stdout.strip():
            raise ValueError('OCR non ha riconosciuto testo. Prova una foto più nitida o una lingua diversa.')
        return result.stdout


def ocr_pdf(source, language='ita+eng'):
    import pymupdf
    texts = []
    recognized_pages = 0
    with pymupdf.open(source) as doc, tempfile.TemporaryDirectory() as directory:
        if doc.needs_pass:
            raise ValueError('PDF protetto da password: apri prima una copia sbloccata.')
        for number, page in enumerate(doc, start=1):
            path = Path(directory) / 'page.png'
            page.get_pixmap(dpi=200, alpha=False).save(path)
            try:
                text = ocr_image(path, language)
                recognized_pages += 1
            except ValueError:
                text = '[Nessun testo riconosciuto su questa pagina]'
            texts.append(f'--- Pagina {number} ---\n{text}')
    if not texts:
        raise ValueError('Il PDF non contiene pagine.')
    if not recognized_pages:
        raise ValueError('OCR non ha riconosciuto testo in nessuna pagina del PDF.')
    return '\n\n'.join(texts)
