from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'app'))
from version import VERSION,PRODUCT_ID
from updater import https_host,validate_release

def make(installer,url,notes='',output=None):
    path=Path(installer)
    if not path.is_file() or path.suffix.lower()!='.exe':raise ValueError('Indica un installer EXE reale.')
    host=https_host(url)
    data=dict(product_id=PRODUCT_ID,version=VERSION,platform='windows-x64',download_url=url,size=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),notes=notes)
    validate_release(data,{host});destination=Path(output or ROOT/'release/update.json')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return destination

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--installer',required=True);parser.add_argument('--download-url',required=True);parser.add_argument('--notes',default='');parser.add_argument('--output')
    args=parser.parse_args();print(make(args.installer,args.download_url,args.notes,args.output))
