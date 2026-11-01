"""Poll for new stable files while the application is open."""
from pathlib import Path

class FolderMonitor:
    def __init__(self,folder,output):
        self.folder=Path(folder).resolve();self.output=Path(output).resolve()
        if not self.folder.is_dir():
            raise ValueError('La cartella da sorvegliare non esiste.')
        if self.output==self.folder or self.folder in self.output.parents:
            raise ValueError('La destinazione deve stare fuori dalla cartella sorvegliata.')
        self.seen={str(p.resolve()) for p in self.folder.rglob('*') if p.is_file()}
        self.pending={}
    def poll(self):
        ready=[]
        present=set()
        for path in self.folder.rglob('*'):
            if not path.is_file() or path.is_symlink():continue
            key=str(path.resolve())
            present.add(key)
            if key in self.seen:continue
            try:
                stat=path.stat();signature=(stat.st_size,stat.st_mtime_ns)
            except OSError:continue
            if self.pending.get(key)==signature:
                ready.append(key);self.seen.add(key);self.pending.pop(key,None)
            else:self.pending[key]=signature
        self.seen.intersection_update(present)
        self.pending={key:value for key,value in self.pending.items() if key in present}
        return ready
