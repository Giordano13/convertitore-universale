"""Windows build: PyInstaller -> Inno Setup -> source archive and hashes."""
from pathlib import Path
import sys,subprocess,os,json,hashlib,shutil,argparse,zipfile
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'app'))
from version import VERSION,APP_ID
from third_party import collect
from updater import read_config

def run(args):subprocess.run(list(map(str,args)),cwd=ROOT,check=True)

def validate():
    read_config(ROOT/'release/config.json')
    if APP_ID not in (ROOT/'installer/setup.iss').read_text():raise ValueError('AppId del setup non corrispondente.')
    modelroot=ROOT/'installer/payload/tessdata';provenance=json.loads((modelroot/'provenance.json').read_text())
    for name,entry in provenance.items():
        path=modelroot/name
        if path.stat().st_size!=entry['size'] or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Modello o licenza non corrispondente: '+name)
    for source in (ROOT/'app').rglob('*.py'):compile(source.read_text(encoding='utf-8'),str(source),'exec')
    return True

def source_archive(output):
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(ROOT.rglob('*')):
            relative=file.relative_to(ROOT)
            if file.is_file() and not any(part in ('.venv','.git','__pycache__','dist','build','output') for part in relative.parts):archive.write(file,Path('Convertitore_Universale')/relative)

def find_iscc():
    found=shutil.which('ISCC.exe') or os.environ.get('ISCC_PATH')
    if found and Path(found).is_file():return found
    for base in [os.environ.get('ProgramFiles(x86)',''),os.environ.get('ProgramFiles',''),os.environ.get('LOCALAPPDATA','')+'/Programs']:
        for version in ('7','6'):
            file=Path(base)/('Inno Setup '+version)/'ISCC.exe'
            if file.is_file():return str(file)
    raise RuntimeError('Installa Inno Setup 6.3 o successivo da jrsoftware.org oppure imposta ISCC_PATH.')

def build():
    validate()
    if os.name!='nt':raise RuntimeError('EXE e setup Windows devono essere compilati su Windows. Usa CreaSetup.bat o il workflow Windows incluso.')
    iscc=find_iscc()
    run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'tools/build_native.ps1'])
    run([sys.executable,'-m','pip','install','-r','requirements-build.txt'])
    run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--name','Convertitore',
         '--paths',ROOT/'app','--collect-all','rawpy','--collect-all','py7zr','--collect-all','pillow_heif','--collect-all','pymupdf',
         '--hidden-import','PyQt6.QtSvg','--hidden-import','process_worker','--hidden-import','operations',
         '--add-binary',str(ROOT/'app/native/file_hash.dll')+';native',
         '--add-data',str(ROOT/'app/assets')+';assets',ROOT/'app/main.py'])
    collect(ROOT/'build/third-party')
    (ROOT/'output').mkdir(exist_ok=True)
    run([iscc,'/DAppVersion='+VERSION,ROOT/'installer/setup.iss'])
    installer=ROOT/'output'/('ConvertitoreUniversale-Setup-'+VERSION+'.exe')
    if not installer.is_file():raise RuntimeError('Installer non creato.')
    source_archive(ROOT/'output'/('ConvertitoreUniversale-Sorgenti-'+VERSION+'.zip'))
    files=sorted((ROOT/'output').glob('*'))
    lines=[hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name for f in files if f.is_file() and f.suffix in ('.exe','.zip')]
    (ROOT/'output/SHA256SUMS.txt').write_text('\n'.join(lines)+'\n')
    config=read_config(ROOT/'release/config.json')
    print('Setup e sorgenti pronti in output. '+('Canale aggiornamenti configurato.' if config['manifest_url'] else 'Configura il canale prima della build pubblica.'))
    if not (ROOT/'LICENSE').is_file():print('Distribuzione pubblica: manca la licenza del tuo progetto. Leggi docs/PUBBLICAZIONE.md prima di pubblicare.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--validate-only',action='store_true');args=parser.parse_args()
    try:
        if args.validate_only:validate();print('Struttura, configurazione, modelli e sorgenti validi.')
        else:build()
    except Exception as error:print('ERRORE: '+str(error),file=sys.stderr);sys.exit(1)
