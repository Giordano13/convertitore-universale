"""Shared format registry and non-destructive conversion dispatcher."""
from pathlib import Path
import os
from converters.image_converter import convert_image
from converters.audio_converter import convert_audio
from converters.video_converter import convert_video
from converters.document_converter import convert_document, write_text_document
from converters.table_converter import convert_table
from converters.ocr_converter import ocr_image, ocr_pdf
from converters.pdf_converter import pdf_to_images
from converters.office_converter import convert_office
from converters.archive_converter import convert_archive
from converters.vector_converter import convert_svg
from converters.subtitle_converter import convert_subtitle

FORMATS = {
    'image': ('jpg', 'png', 'webp', 'bmp', 'tiff', 'gif', 'ico', 'tga', 'ppm', 'pdf', 'txt', 'docx'),
    'audio': ('mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'opus', 'aiff'),
    'video': ('mp4', 'mkv', 'mov', 'avi', 'webm', 'gif', 'mp3', 'wav'),
    'text': ('txt', 'docx', 'pdf', 'html', 'epub'),
    'table': ('csv', 'tsv', 'xlsx', 'json', 'jsonl'),
    'docx': ('txt', 'pdf', 'odt', 'rtf', 'epub', 'html'),
    'pdf': ('txt', 'docx', 'html', 'epub', 'png.zip', 'jpg.zip'),
    'office': ('pdf', 'docx', 'odt', 'rtf', 'txt', 'epub'),
    'spreadsheet': ('csv', 'tsv', 'json', 'jsonl', 'xlsx', 'ods', 'pdf'),
    'legacy_sheet': ('xlsx', 'ods', 'pdf'),
    'presentation': ('pptx', 'odp', 'pdf'),
    'archive': ('zip', '7z', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz'),
    'raw': ('jpg','png','webp','tiff','bmp','pdf'),
    'vector': ('png', 'jpg', 'webp', 'bmp', 'tiff', 'ico', 'pdf'),
    'ebook': ('txt', 'docx', 'pdf', 'html', 'epub'),
    'web': ('txt', 'docx', 'pdf', 'html', 'epub'),
    'subtitle': ('srt', 'vtt'),
}
EXTENSIONS = {
    'image': ('jpg','jpeg','png','webp','bmp','gif','tif','tiff','ico','heic','heif','tga','ppm','pgm','pbm','pcx'),
    'audio': ('mp3','wav','ogg','flac','aac','m4a','aiff','aif','opus','wma'),
    'video': ('mp4','avi','mov','webm','mkv','m4v','mpeg','mpg','wmv','ts'),
    'table': ('csv', 'tsv', 'json', 'jsonl', 'ndjson'),
    'text': ('txt','md','markdown','log','yaml','yml','toml','ini','cfg','xml'), 'docx': ('docx',), 'pdf': ('pdf',),
    'office': ('doc','odt','rtf'),
    'spreadsheet': ('xlsx',), 'legacy_sheet': ('xls', 'ods'),
    'presentation': ('ppt', 'pptx', 'odp'),
    'archive': ('zip', '7z', 'tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'tar.xz', 'txz'),
    'raw': ('nef','cr2','cr3','arw','dng','raf','rw2','orf','pef','srw'),
    'vector': ('svg',), 'ebook': ('epub',), 'web': ('html', 'htm', 'xhtml'),
    'subtitle': ('srt', 'vtt'),
}

CATEGORY_LABELS = {
    'image':'Immagini', 'audio':'Audio', 'video':'Video', 'text':'Testi e configurazioni',
    'table':'Dati tabellari', 'docx':'Word', 'pdf':'PDF', 'office':'Documenti Office',
    'spreadsheet':'Excel', 'legacy_sheet':'Fogli Office', 'presentation':'Presentazioni',
    'archive':'Archivi', 'raw':'Foto RAW', 'vector':'SVG', 'ebook':'EPUB',
    'web':'Pagine HTML', 'subtitle':'Sottotitoli',
}

def kind(path):
    name = Path(path).name.lower()
    for suffix in ('tar.gz', 'tar.bz2', 'tar.xz'):
        if name.endswith('.' + suffix):
            return 'archive'
    ext = Path(path).suffix.lower().lstrip('.')
    return next((k for k, values in EXTENSIONS.items() if ext in values), None)


def common_formats(paths):
    choices = [FORMATS.get(kind(p), ()) for p in paths]
    return [f for f in choices[0] if all(f in c for c in choices)] if choices else []


def reserve_output(folder, stem, fmt):
    if not stem or any(c in stem for c in '/\\\x00') or any(c in fmt for c in '/\\\x00'):
        raise ValueError('Nome del risultato non valido.')
    Path(folder).mkdir(parents=True, exist_ok=True)
    index = 0
    while True:
        name = f'{stem}_convertito' + (f'_{index}' if index else '') + f'.{fmt}'
        path = Path(folder) / name
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            return path
        except FileExistsError:
            index += 1


def convert(source, folder, fmt, options=None, target=None):
    options = options or {}
    source = Path(source)
    if not source.is_file():
        raise ValueError('Il file originale non esiste o non è accessibile.')
    if target is not None:
        destination = Path(target)
        if destination.resolve() == source.resolve() or (destination.exists() and os.path.samefile(source, destination)):
            raise ValueError('Il risultato non può sostituire il file originale.')
        if destination.exists() and destination.stat().st_size:
            raise ValueError('Il file di destinazione contiene già dati. Scegli un nuovo nome.')
    category = kind(source)
    if fmt not in FORMATS.get(category, ()):
        raise ValueError('Conversione non supportata per questo file.')
    target = Path(target) if target is not None else reserve_output(folder, Path(source).stem, fmt)
    try:
        if category == 'raw':
            from converters.raw_converter import convert_raw
            convert_raw(source,target,fmt,options)
        elif category == 'archive':
            convert_archive(source, target, fmt)
        elif category == 'vector':
            convert_svg(source, target, fmt, options.get('width'), options.get('height'), options.get('quality', 90))
        elif category == 'subtitle':
            convert_subtitle(source, target, fmt)
        elif category == 'presentation':
            convert_office(source, target, fmt, 'impress')
        elif category == 'legacy_sheet' or (category == 'spreadsheet' and fmt in ('ods', 'pdf')):
            convert_office(source, target, fmt, 'calc')
        elif category == 'office' or (category == 'docx' and fmt in ('pdf', 'odt', 'rtf', 'epub')):
            convert_office(source, target, fmt, 'writer')
        elif category in ('table', 'spreadsheet'):
            convert_table(source, target, fmt, options.get('sheet', 1))
        elif category == 'pdf' and fmt in ('png.zip', 'jpg.zip'):
            pdf_to_images(source, target, fmt.split('.')[0], options.get('dpi', 150))
        elif category == 'image' and fmt in ('txt', 'docx'):
            text = ocr_image(source, options.get('ocr_language', 'ita+eng'))
            write_text_document(text, target, fmt)
        elif category == 'pdf' and options.get('ocr'):
            text = ocr_pdf(source, options.get('ocr_language', 'ita+eng'))
            write_text_document(text, target, fmt)
        elif category == 'image':
            convert_image(source, str(target), fmt, options.get('width'), options.get('height'), options.get('quality', 90), options=options)
        elif category == 'audio' or (category == 'video' and fmt in ('mp3', 'wav')):
            from media import convert_media
            convert_media(source, target, fmt, options, audio_only=True)
        elif category == 'video':
            from media import convert_media
            convert_media(source, target, fmt, options)
        else:
            convert_document(source, str(target), fmt)
        if not target.stat().st_size:
            raise RuntimeError('Il file convertito è vuoto.')
        return str(target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
