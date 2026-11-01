"""Locate optional Windows tools and per-app OCR data after installation."""
from pathlib import Path
import sys,os,shutil,subprocess
from functools import lru_cache

def distribution_root():
    return Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent

def media_executable(name):
    override=os.environ.get('FFMPEG_CMD' if name=='ffmpeg' else 'FFPROBE_CMD')
    if override and Path(override).is_file():return override
    found=shutil.which(name)
    candidates=[found] if found else []
    bases=[Path(os.environ.get('LOCALAPPDATA',''))/'Microsoft/WinGet',Path(os.environ.get('ProgramFiles','C:/Program Files'))/'WinGet'] if os.name=='nt' else []
    for base in bases:
        candidate=base/'Links'/(name+'.exe')
        if candidate.is_file():candidates.append(str(candidate))
        for package in (base/'Packages').glob('Gyan.FFmpeg_*'):
            for candidate in package.glob('*/bin/'+name+'.exe'):
                if candidate.is_file():candidates.append(str(candidate))
    for candidate in dict.fromkeys(candidates):
        try:
            if media_compatible(candidate,Path(candidate).stat().st_mtime_ns):return candidate
        except OSError:continue
    if candidates:
        raise RuntimeError(f'{name} trovato ma obsoleto o non avviabile. Aggiorna il componente Audio e video da Gestisci componenti.')
    raise RuntimeError(f'{name} non disponibile. Installa il componente Audio e video da Gestisci componenti.')


@lru_cache(maxsize=32)
def media_compatible(executable,modified):
    """Reject old binaries shadowing the app's installed FFmpeg tools."""
    try:
        result=subprocess.run([executable,'-hide_banner','-version'],capture_output=True,
                              timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return result.returncode==0
    except (OSError,subprocess.TimeoutExpired):return False

def tessdata_arguments(language):
    candidates=[]
    if os.environ.get('TESSDATA_PREFIX'):candidates.append(Path(os.environ['TESSDATA_PREFIX']))
    candidates.append(distribution_root()/'tessdata')
    if os.name=='nt':candidates.append(Path(os.environ.get('LOCALAPPDATA',''))/'Programs/ConvertitoreUniversale/tessdata')
    for directory in candidates:
        if all((directory/(name+'.traineddata')).is_file() for name in language.split('+')):
            return ['--tessdata-dir',str(directory)]
    return []

def component_script():
    root=distribution_root()
    return root/('maintenance' if getattr(sys,'frozen',False) else 'installer')/'install_components.ps1'

def release_config_path():
    return distribution_root()/'release/config.json'
