"""Decode Unicode BOMs and legacy Windows text without losing characters."""
from pathlib import Path


def read_text_file(path):
    data = Path(path).read_bytes()
    if data.startswith((b'\xff\xfe\x00\x00', b'\x00\x00\xfe\xff')):
        return data.decode('utf-32')
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16')
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            return data.decode('cp1252')
        except UnicodeDecodeError as error:
            raise ValueError('Codifica testo non riconosciuta. Salva il file come UTF-8 o UTF-16 con BOM.') from error
