"""Explicit HTTPS update checks and verified installer downloads."""
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
import hashlib,json,re,os
from version import PRODUCT_ID,VERSION
from runtime_paths import release_config_path
MAX_MANIFEST=262144
MAX_INSTALLER=2*1024**3

class UpdateError(ValueError):pass
class CancelledUpdate(UpdateError):pass

def version_tuple(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{1,6}\.\d{1,6}\.\d{1,6}',value):raise UpdateError('Versione non valida.')
    return tuple(map(int,value.split('.')))

def https_host(url):
    try:
        parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError()
        return parsed.hostname.lower()
    except (ValueError,TypeError):raise UpdateError('Sono ammessi solo indirizzi HTTPS senza credenziali.')

class TrustedRedirect(HTTPRedirectHandler):
    def __init__(self,hosts):self.hosts=hosts
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if https_host(newurl) not in self.hosts:raise UpdateError('Reindirizzamento verso un dominio non autorizzato.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def open_trusted(url,hosts):
    if https_host(url) not in hosts:raise UpdateError('Dominio di download non autorizzato.')
    request=Request(url,headers={'User-Agent':'ConvertitoreUniversale/'+VERSION})
    return build_opener(TrustedRedirect(set(hosts))).open(request,timeout=20)

def read_config(path=None):
    try:data=json.loads(Path(path or release_config_path()).read_text(encoding='utf-8'))
    except (OSError,ValueError):return dict(manifest_url='',allowed_download_hosts=[])
    url=data.get('manifest_url','')
    if url:https_host(url)
    hosts=data.get('allowed_download_hosts',[])
    if not isinstance(hosts,list) or not all(isinstance(h,str) and re.fullmatch(r'[a-zA-Z0-9.-]+',h) for h in hosts):raise UpdateError('Configurazione domini non valida.')
    return dict(manifest_url=url,allowed_download_hosts=[h.lower() for h in hosts])

def validate_release(data,hosts,current=VERSION):
    if not isinstance(data,dict) or data.get('product_id')!=PRODUCT_ID or data.get('platform')!='windows-x64':raise UpdateError('Aggiornamento destinato a un altro prodotto o sistema.')
    version=version_tuple(data.get('version'));version_tuple(current)
    if https_host(data.get('download_url','')) not in hosts:raise UpdateError('Dominio del setup non autorizzato.')
    if not re.fullmatch(r'[0-9a-fA-F]{64}',str(data.get('sha256',''))):raise UpdateError('SHA256 del setup mancante o non valido.')
    size=data.get('size')
    if isinstance(size,bool) or not isinstance(size,int) or not 0<size<=MAX_INSTALLER:raise UpdateError('Dimensione del setup non valida.')
    if not urlsplit(data['download_url']).path.lower().endswith('.exe'):raise UpdateError('Il risultato deve essere un installer EXE.')
    notes=data.get('notes','')
    if not isinstance(notes,str) or len(notes)>20000:raise UpdateError('Note della versione non valide.')
    return dict(data,newer=version>version_tuple(current))

def check_release(config,current=VERSION):
    url=config.get('manifest_url','')
    if not url:raise UpdateError('Canale aggiornamenti non configurato. Configuralo prima di pubblicare il programma.')
    host=https_host(url);hosts=set(config.get('allowed_download_hosts',[]))|{host}
    with open_trusted(url,{host}) as response:
        if https_host(response.geturl())!=host:raise UpdateError('Dominio del canale cambiato.')
        payload=response.read(MAX_MANIFEST+1)
    if len(payload)>MAX_MANIFEST:raise UpdateError('Elenco aggiornamenti troppo grande.')
    try:data=json.loads(payload.decode('utf-8'))
    except (UnicodeError,ValueError):raise UpdateError('Elenco aggiornamenti non valido.')
    return validate_release(data,hosts,current)

def download_release(release,folder,hosts,progress=lambda *a:None,cancelled=lambda:False):
    data=validate_release(release,set(hosts));folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    target=folder/('ConvertitoreUniversale-Setup-'+data['version']+'.exe');temporary=folder/(target.name+'.part')
    digest=hashlib.sha256();count=0
    try:
        with open_trusted(data['download_url'],set(hosts)) as response,open(temporary,'wb') as stream:
            if https_host(response.geturl()) not in hosts:raise UpdateError('Dominio finale non autorizzato.')
            while True:
                if cancelled():raise CancelledUpdate('Download annullato.')
                chunk=response.read(1024*256)
                if not chunk:break
                count+=len(chunk)
                if count>data['size']:raise UpdateError('Il setup supera la dimensione dichiarata.')
                digest.update(chunk);stream.write(chunk);progress(count/data['size'],count)
        if cancelled():raise CancelledUpdate('Download annullato.')
        if count!=data['size'] or digest.hexdigest()!=data['sha256'].lower():raise UpdateError('Verifica del setup fallita: il file è incompleto o modificato.')
        temporary.replace(target);return target
    except Exception:
        temporary.unlink(missing_ok=True);raise


def verify_installer(path,release):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=release['size']:raise UpdateError('Il setup verificato non è più disponibile o è cambiato.')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    if digest.hexdigest()!=release['sha256'].lower():raise UpdateError('Il setup è stato modificato dopo il download.')
    return True
