"""Repack regular files and directories without extracting paths to disk."""
from pathlib import PurePosixPath
from contextlib import ExitStack
import shutil
import stat
import tarfile
import zipfile
from pathlib import Path
import tempfile
from conversion_progress import report

MAX_BYTES = 2 * 1024**3
MAX_ENTRIES = 100000


def valid_name(name):
    normalized = name.replace('\\', '/')
    parts = PurePosixPath(normalized).parts
    if not parts or normalized.startswith('/') or '..' in parts or any(':' in p for p in parts):
        raise ValueError(f'Percorso non valido nell’archivio: {name!r}')
    return '/'.join(parts)


def _convert_standard(source, target, fmt):
    modes = {'tar': 'w', 'tar.gz': 'w:gz', 'tar.bz2': 'w:bz2', 'tar.xz': 'w:xz'}
    seen, size = set(), 0
    with ExitStack() as stack:
        source_zip = zipfile.is_zipfile(source)
        archive = stack.enter_context(zipfile.ZipFile(source) if source_zip else tarfile.open(source, 'r:*'))
        out = stack.enter_context(zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
                                  if fmt == 'zip' else tarfile.open(target, modes[fmt]))
        members=archive.infolist() if source_zip else archive.getmembers()
        for number,member in enumerate(members,start=1):
            report(number/max(1,len(members)),'Ricreazione archivio')
            raw_name = member.filename if source_zip else member.name
            directory = member.is_dir() if source_zip else member.isdir()
            if directory and raw_name.replace('\\', '/') in ('.', './'):
                continue
            name = valid_name(raw_name)
            if source_zip:
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError('Archivi con collegamenti simbolici non sono supportati.')
                length = member.file_size
            else:
                if not (member.isfile() or directory):
                    raise ValueError('Archivi con link o file speciali non sono supportati.')
                length = member.size
            if name in seen:
                raise ValueError(f'Nome duplicato nell’archivio: {name}')
            seen.add(name)
            size += length
            if len(seen) > MAX_ENTRIES or size > MAX_BYTES:
                raise ValueError('Limite archivi: 100000 elementi e 2 GiB di dati non compressi.')
            if directory:
                if fmt == 'zip':
                    out.writestr(name + '/', b'')
                else:
                    info = tarfile.TarInfo(name); info.type = tarfile.DIRTYPE; info.mode = 0o755
                    out.addfile(info)
                continue
            with archive.open(member) if source_zip else archive.extractfile(member) as stream:
                if fmt == 'zip':
                    with out.open(name, 'w', force_zip64=True) as dest:
                        shutil.copyfileobj(stream, dest, 1024 * 1024)
                else:
                    info = tarfile.TarInfo(name);info.size = length;info.mode = 0o644
                    out.addfile(info, stream)


def convert_archive(source,target,fmt):
    if str(source).lower().endswith('.7z') or fmt=='7z':
        _convert_sevenzip(source,target,fmt)
    else:
        _convert_standard(source,target,fmt)


def _convert_sevenzip(source,target,fmt):
    import py7zr
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);staging=root/'staging.zip'
        if str(source).lower().endswith('.7z'):
            with py7zr.SevenZipFile(source,'r') as archive:
                if archive.needs_password():raise ValueError('Archivio 7Z cifrato non supportato.')
                members=archive.list();names=set();total=0;dirs=[]
                for member in members:
                    name=valid_name(member.filename)
                    if name in names:raise ValueError('Nome duplicato nell’archivio 7Z.')
                    names.add(name);total+=member.uncompressed
                    if member.is_symlink or not (member.is_file or member.is_directory):raise ValueError('Link o file speciali non supportati.')
                    if member.is_directory:dirs.append(name)
                if len(members)>MAX_ENTRIES or total>MAX_BYTES:raise ValueError('Archivio oltre i limiti di elementi/dimensione.')
                written=[0]
                class Sink(py7zr.Py7zIO):
                    def __init__(self,path):self.path=path;self.file=open(path,'w+b')
                    def write(self,data):
                        written[0]+=len(data)
                        if written[0]>MAX_BYTES:raise ValueError('7Z oltre il limite reale di 2 GiB.')
                        return self.file.write(data)
                    def read(self,size=None):return self.file.read(-1 if size is None else size)
                    def seek(self,offset,whence=0):return self.file.seek(offset,whence)
                    def flush(self):self.file.flush()
                    def size(self):self.flush();return self.path.stat().st_size
                class Factory(py7zr.WriterFactory):
                    def __init__(self):self.products={}
                    def create(self,filename):
                        name=valid_name(filename)
                        if name not in names:raise ValueError('Nome 7Z inatteso.')
                        sink=Sink(root/f'content_{len(self.products)}');self.products[name]=sink;return sink
                factory=Factory();report(None,'Decompressione 7Z')
                try:
                    archive.extractall(factory=factory)
                    with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as zipped:
                        for name in dirs:zipped.writestr(name+'/',b'')
                        for name,sink in factory.products.items():
                            sink.flush();zipped.write(sink.path,name)
                finally:
                    for sink in factory.products.values():sink.file.close()
        else:
            _convert_standard(source,staging,'zip')
        if fmt!='7z':
            _convert_standard(staging,target,fmt);return
        with zipfile.ZipFile(staging) as zipped,py7zr.SevenZipFile(target,'w') as archive:
            for i,member in enumerate(zipped.infolist()):
                name=valid_name(member.filename)
                if member.is_dir():
                    empty=root/f'dir_{i}';empty.mkdir();archive.write(empty,name)
                else:
                    path=root/f'file_{i}'
                    with zipped.open(member) as src,open(path,'wb') as dst:shutil.copyfileobj(src,dst)
                    archive.write(path,name)
                report((i+1)/max(1,len(zipped.infolist())),'Compressione 7Z')
