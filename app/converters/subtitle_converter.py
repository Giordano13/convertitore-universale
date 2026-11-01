"""Convert plain subtitle cues between SRT and WebVTT."""
from pathlib import Path
import re

TIMING = re.compile(r'(?P<start>(?:\d{2,}:)?\d{2}:\d{2}[.,]\d{3})\s*-->\s*(?P<end>(?:\d{2,}:)?\d{2}:\d{2}[.,]\d{3})(?P<settings>.*)')


def timestamp(value, separator):
    value = value.replace(',', '.')
    parts = value.split(':')
    if len(parts) == 2:
        parts.insert(0, '00')
    if int(parts[-2]) > 59 or float(parts[-1]) >= 60:
        raise ValueError('Timestamp del sottotitolo non valido.')
    return ':'.join(parts).replace('.', separator)


def convert_subtitle(source, target, fmt):
    text = Path(source).read_text(encoding='utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    if Path(source).suffix.lower() == '.vtt':
        if not text.startswith('WEBVTT'):
            raise ValueError('Il file VTT deve iniziare con WEBVTT.')
        text = text.split('\n\n', 1)[1] if '\n\n' in text else ''
    cues = []
    for block in re.split(r'\n\s*\n', text.strip()):
        lines = block.splitlines()
        if not lines or lines[0].startswith(('NOTE', 'STYLE', 'REGION')):
            continue
        index = next((i for i, line in enumerate(lines) if '-->' in line), None)
        if index is None:
            raise ValueError('Blocco sottotitoli privo di timestamp.')
        match = TIMING.fullmatch(lines[index])
        if not match or not lines[index + 1:]:
            raise ValueError('Blocco sottotitoli non valido.')
        if fmt == 'srt' and match['settings'].strip():
            raise ValueError('Il VTT contiene impostazioni di posizione non rappresentabili in SRT.')
        sep = ',' if fmt == 'srt' else '.'
        timing = timestamp(match['start'], sep) + ' --> ' + timestamp(match['end'], sep)
        if fmt == 'vtt':
            timing += match['settings']
        prefix = f'{len(cues) + 1}\n' if fmt == 'srt' else ''
        cues.append(prefix + timing + '\n' + '\n'.join(lines[index + 1:]))
    if not cues:
        raise ValueError('Nessun sottotitolo trovato.')
    Path(target).write_text(('WEBVTT\n\n' if fmt == 'vtt' else '') + '\n\n'.join(cues) + '\n', encoding='utf-8')
