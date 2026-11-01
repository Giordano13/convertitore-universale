"""Open the author's optional donation page in the system browser."""
import json
from urllib.parse import urlsplit
from runtime_paths import distribution_root

def donation_url():
    try:
        data = json.loads((distribution_root() / 'release/support.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ''
    if not isinstance(data, dict):
        raise ValueError('Configurazione donazioni non valida.')
    url = data.get('donation_url', '')
    if not url:
        return ''
    if not isinstance(url, str) or any(c.isspace() for c in url):
        raise ValueError('Il link donazioni deve essere un indirizzo HTTPS valido.')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Il link donazioni deve essere HTTPS e senza credenziali.')
    return url
