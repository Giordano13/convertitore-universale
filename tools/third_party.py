"""Collect exact versions and installed license/notice files for redistribution."""
from pathlib import Path
import importlib.metadata as metadata,json,re

def collect(target):
    target=Path(target);target.mkdir(parents=True,exist_ok=True);packages=[]
    for distribution in metadata.distributions():
        name=distribution.metadata.get('Name','unknown');safe=re.sub(r'[^A-Za-z0-9_.-]','_',name)
        notices=[]
        for file in distribution.files or []:
            path=Path(str(file));lower=path.name.lower()
            if not (lower.startswith(('license','copying','notice','copyright')) or 'licenses' in [p.lower() for p in path.parts]):continue
            source=Path(distribution.locate_file(file))
            if not source.is_file():continue
            destination=target/safe/path.name
            if destination.exists():destination=target/safe/(str(len(notices))+'_'+path.name)
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(source.read_bytes());notices.append(str(destination.relative_to(target)))
        packages.append(dict(name=name,version=distribution.version,license=distribution.metadata.get('License-Expression') or distribution.metadata.get('License'),project_urls=distribution.metadata.get_all('Project-URL') or [],notices=notices))
    (target/'dependencies.json').write_text(json.dumps(sorted(packages,key=lambda p:p['name'].lower()),ensure_ascii=False,indent=2),encoding='utf-8')
    return packages
