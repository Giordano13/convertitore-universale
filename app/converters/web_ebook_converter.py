"""HTML/EPUB text reading, Markdown rendering, and basic text EPUB export."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import posixpath
from urllib.parse import unquote, urlsplit
from uuid import uuid4
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from defusedxml import ElementTree as ET


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0
        self.pre = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head'):
            self.hidden += 1
        if not self.hidden:
            if tag == 'pre':
                self.pre += 1
            if tag in ('p','div','br','li','h1','h2','h3','h4','tr','section','pre'):
                self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head') and self.hidden:
            self.hidden -= 1
        if not self.hidden:
            if tag == 'pre':
                self.pre = max(0, self.pre - 1)
            if tag in ('p','div','li','h1','h2','h3','h4','tr','section','pre'):
                self.parts.append('\n')
    def handle_data(self, text):
        if not self.hidden:
            self.parts.append(text if self.pre else ' '.join(text.split()) + (' ' if text.strip() else ''))


def html_text(text):
    parser = TextParser();parser.feed(text);parser.close()
    result = ''.join(parser.parts)
    return '\n'.join(line.strip() for line in result.splitlines() if line.strip())


def read_epub(source):
    with ZipFile(source) as archive:
        def read(name):
            if archive.getinfo(name).file_size > 20 * 1024**2:
                raise ValueError('Capitolo EPUB troppo grande (limite 20 MiB).')
            return archive.read(name)
        container = ET.fromstring(read('META-INF/container.xml'))
        entry = container.find('.//{*}rootfile')
        if entry is None:
            raise ValueError('EPUB privo del documento principale.')
        package_path = entry.attrib['full-path']
        package = ET.fromstring(read(package_path))
        manifest = {item.attrib['id']: item.attrib for item in package.findall('.//{*}manifest/{*}item')}
        chapters = []
        total = 0
        for itemref in package.findall('.//{*}spine/{*}itemref'):
            item = manifest.get(itemref.attrib.get('idref'))
            if not item:
                raise ValueError('EPUB con capitolo mancante nel manifest.')
            if item.get('media-type') not in ('application/xhtml+xml', 'text/html'):
                continue
            href = unquote(urlsplit(item['href']).path)
            name = posixpath.normpath(posixpath.join(posixpath.dirname(package_path), href))
            if name.startswith(('../', '/')):
                raise ValueError('Percorso capitolo EPUB non valido.')
            data = read(name);total += len(data)
            if total > 100 * 1024**2:
                raise ValueError('Testo EPUB troppo grande (limite 100 MiB).')
            chapters.append(html_text(data.decode('utf-8-sig')))
        if not chapters or not any(chapters):
            raise ValueError('EPUB privo di testo leggibile, o contenuti protetti.')
        return '\n\n'.join(chapters)


def text_epub(text, target, title='Documento'):
    identifier = 'urn:uuid:' + str(uuid4())
    title = escape(title)
    chapter = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{title}</title></head>
<body><h1>{title}</h1><pre style="white-space:pre-wrap">{escape(text)}</pre></body></html>'''
    modified = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    package = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">{identifier}</dc:identifier>
<dc:title>{title}</dc:title><dc:language>it</dc:language><meta property="dcterms:modified">{modified}</meta></metadata>
<manifest><item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest>
<spine><itemref idref="chapter"/></spine></package>'''
    nav = f'''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Indice</title></head><body><nav epub:type="toc"><h1>Indice</h1><ol>
<li><a href="chapter.xhtml">{title}</a></li></ol></nav></body></html>'''
    with ZipFile(target, 'w') as archive:
        archive.writestr('mimetype', 'application/epub+zip', compress_type=ZIP_STORED)
        archive.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', compress_type=ZIP_DEFLATED)
        for name, data in (('book.opf', package), ('chapter.xhtml', chapter), ('nav.xhtml', nav)):
            archive.writestr('EPUB/' + name, data.encode('utf-8'), compress_type=ZIP_DEFLATED)


def write_html(text, target, markdown_source=False):
    if markdown_source:
        import markdown
        # Escape raw HTML: local Markdown content remains static markup.
        body = markdown.markdown(escape(text), extensions=['tables', 'fenced_code'])
    else:
        body = '<pre>' + escape(text) + '</pre>'
    Path(target).write_text('<!DOCTYPE html>\n<html lang="it"><head><meta charset="utf-8"><title>Documento convertito</title></head><body>' + body + '</body></html>', encoding='utf-8')
