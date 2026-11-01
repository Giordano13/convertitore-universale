"""Persistent history and named image/media workflows."""
import json
from pathlib import Path
from datetime import datetime,timezone
import uuid
import os
import tempfile

class StateStore:
    def __init__(self,directory):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
    def read(self,name,default):
        try:
            value=json.loads((self.directory/name).read_text(encoding='utf-8'))
            return value if isinstance(value,type(default)) else default
        except (OSError,ValueError):return default
    def write(self,name,data):
        payload=json.dumps(data,ensure_ascii=False,indent=2)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.directory,
                                             prefix=name+'.',suffix='.tmp',delete=False) as stream:
                temporary=Path(stream.name)
                stream.write(payload);stream.flush();os.fsync(stream.fileno())
            temporary.replace(self.directory/name)
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)
    def history(self):
        rows=[]
        for entry in self.read('history.json',[]):
            try:
                if not isinstance(entry,dict) or not isinstance(entry['job'],dict):continue
                sources=entry['job']['sources']
                if not isinstance(sources,list) or not sources or not all(isinstance(p,str) and p for p in sources):continue
                if not isinstance(entry['result'],str) or not any(entry['success'] is v for v in (True,False,None)):continue
                if not isinstance(entry['time'],str):continue
                datetime.fromisoformat(entry['time'])
                if any(not isinstance(entry.get(k,0),(int,float)) or entry.get(k,0)<0 for k in ('input_bytes','output_bytes')):continue
                rows.append(entry)
            except (KeyError,ValueError,TypeError):continue
        return rows[:1000]
    def add_history(self,job,success,result):
        rows=self.history();entry=dict(id=str(uuid.uuid4()),time=datetime.now(timezone.utc).isoformat(),job=job,success=success,result=result)
        if success and Path(result).is_file():entry['output_bytes']=Path(result).stat().st_size
        entry['input_bytes']=sum(Path(p).stat().st_size for p in job['sources'] if Path(p).is_file())
        rows.insert(0,entry);self.write('history.json',rows[:1000])
    def recipes(self):return {name:options for name,options in self.read('recipes.json',{}).items() if isinstance(options,dict)}
    def save_recipe(self,name,options):
        recipes=self.recipes();recipes[name]=options;self.write('recipes.json',recipes)
