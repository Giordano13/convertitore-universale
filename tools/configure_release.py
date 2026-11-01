from pathlib import Path
import argparse,json,re,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'app'))
from updater import https_host

def configure(repo=None,url=None,hosts=None):
    if repo:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise ValueError('Usa proprietario/repository, senza indirizzo web.')
        allowed=['github.com','release-assets.githubusercontent.com','objects.githubusercontent.com']
        # Manifest on the raw branch avoids the cross-host release asset redirect.
        url='https://raw.githubusercontent.com/'+repo+'/main/release/update.json'
    else:
        allowed=hosts or [https_host(url)]
    https_host(url)
    config=dict(manifest_url=url,allowed_download_hosts=allowed)
    (ROOT/'release/config.json').write_text(json.dumps(config,indent=2)+'\n');return config

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--github',help='proprietario/repository');group.add_argument('--manifest-url');parser.add_argument('--download-host',action='append',default=[])
    args=parser.parse_args();print(json.dumps(configure(args.github,args.manifest_url,args.download_host),indent=2))
