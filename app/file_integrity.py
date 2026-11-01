"""Optional C++ SHA-256 backend with a portable Python implementation."""
import ctypes
import hashlib
import os
import sys
from pathlib import Path


def sha256_file(source, prefer_native=True):
    source = Path(source).resolve(strict=True)
    before = source.stat()
    if not source.is_file():
        raise ValueError('Seleziona un file per calcolare SHA-256.')
    binary = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'native/file_hash.dll'
    digest = None
    backend = 'Python'
    if prefer_native and os.name == 'nt' and binary.is_file():
        try:
            library = ctypes.CDLL(str(binary))
            function = library.hash_file_sha256
            function.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_ulong]
            function.restype = ctypes.c_int
            output = (ctypes.c_ubyte * 32)()
            if function(str(source), output, 32) == 0:
                digest = bytes(output).hex()
                backend = 'C++ / Windows CNG'
        except (OSError, AttributeError):
            pass
    if digest is None:
        value = hashlib.sha256()
        with source.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                value.update(block)
        digest = value.hexdigest()
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Il file è cambiato durante la verifica. Riprova quando la copia è terminata.')
    return digest, backend
