import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import tarfile
from PIL import Image
from engine import convert, kind
from converters.document_converter import read_text
from converters.office_converter import libreoffice_executable

class FullTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_archive_all_containers_and_contents(self):
        source = self.root / 'data.zip'
        with ZipFile(source, 'w') as archive:
            archive.writestr('cartella/', b'')
            archive.writestr('cartella/test.txt', 'Ciao Perù'.encode('utf-8'))
            archive.writestr('binary.dat', bytes(range(256)))
        for fmt in ('tar', 'tar.gz', 'tar.bz2', 'tar.xz'):
            result = convert(source, self.root, fmt)
            self.assertEqual(kind(result), 'archive')
            with tarfile.open(result) as archive:
                self.assertEqual(archive.extractfile('binary.dat').read(), bytes(range(256)))
                self.assertTrue(archive.getmember('cartella').isdir())
            zipped = convert(result, self.root, 'zip')
            with ZipFile(zipped) as archive:
                self.assertEqual(archive.read('cartella/test.txt').decode('utf-8'), 'Ciao Perù')
                self.assertIn('cartella/', archive.namelist())
        rooted = self.root / 'root.tar'
        with tarfile.open(rooted, 'w') as archive:
            info = tarfile.TarInfo('.');info.type = tarfile.DIRTYPE;archive.addfile(info)
        convert(rooted, self.root, 'zip')
        bad = self.root / 'bad.zip'
        with ZipFile(bad, 'w') as archive:
            archive.writestr('../outside.txt', b'bad')
        with self.assertRaisesRegex(ValueError, 'Percorso non valido'):
            convert(bad, self.root, 'tar')
        self.assertFalse(list(self.root.glob('bad_convertito*')))

    def test_epub_html_markdown(self):
        text = self.root / 'test.txt';text.write_text('Ciao Perù\nSeconda riga & <test>', encoding='utf-8')
        epub = convert(text, self.root, 'epub')
        extracted = read_text(epub)
        self.assertIn('Seconda riga & <test>', extracted)
        with ZipFile(epub) as archive:
            self.assertEqual(archive.infolist()[0].filename, 'mimetype')
            self.assertEqual(archive.infolist()[0].compress_type, 0)
        html = convert(text, self.root, 'html')
        self.assertIn('Ciao Perù', read_text(html))
        web = self.root / 'web.html';web.write_text('<head><title>hidden</title></head><p>Hello <b>world</b></p><script>alert(1)</script>')
        plain = convert(web, self.root, 'txt')
        self.assertIn('Hello world', Path(plain).read_text())
        self.assertNotIn('alert', Path(plain).read_text())
        md = self.root / 'test.md';md.write_text('# Titolo\n\n**Grassetto**')
        rendered = convert(md, self.root, 'html')
        self.assertIn('<h1>Titolo</h1>', Path(rendered).read_text())
        self.assertIn('<strong>Grassetto</strong>', Path(rendered).read_text())

    def test_subtitles_timestamps_and_text(self):
        source = self.root / 'test.srt'
        source.write_text('1\n00:00:01,100 --> 00:00:03,200\nCiao!\n\n2\n00:00:04,000 --> 00:00:05,000\nSeconda riga\n')
        vtt = convert(source, self.root, 'vtt')
        self.assertTrue(Path(vtt).read_text().startswith('WEBVTT'))
        self.assertIn('00:00:01.100 --> 00:00:03.200', Path(vtt).read_text())
        srt = convert(vtt, self.root, 'srt')
        self.assertEqual(Path(srt).read_text(), source.read_text())
        positioned = self.root / 'position.vtt'
        positioned.write_text('WEBVTT\n\n00:01.000 --> 00:02.000 align:start\nHello\n')
        with self.assertRaisesRegex(ValueError, 'posizione'):
            convert(positioned, self.root, 'srt')

    def test_svg_and_heic(self):
        source = self.root / 'test.svg'
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="red"/></svg>')
        png = convert(source, self.root, 'png', {'width': 60, 'height': 40})
        with Image.open(png) as image:
            self.assertEqual(image.size, (60, 40))
            self.assertEqual(image.convert('RGB').getpixel((20,20)), (255,0,0))
        import pillow_heif
        heic = self.root / 'photo.heic'
        pillow_heif.from_pillow(Image.new('RGB', (32, 32), 'blue')).save(heic)
        jpg = convert(heic, self.root, 'jpg')
        with Image.open(jpg) as image:
            self.assertEqual(image.size, (32,32))

    def test_animation(self):
        source = self.root / 'animation.gif'
        first = Image.new('RGB',(32,32),'red');second = Image.new('RGB',(32,32),'blue')
        first.save(source, save_all=True, append_images=[second], duration=[100,200], loop=0)
        for fmt in ('gif','webp','tiff'):
            result = convert(source,self.root,fmt)
            with Image.open(result) as image:
                self.assertEqual(image.n_frames,2)

    def test_libreoffice_documents_and_spreadsheets(self):
        try:
            libreoffice_executable()
        except RuntimeError:
            self.skipTest('LibreOffice assente')
        from docx import Document
        from openpyxl import Workbook
        from pypdf import PdfReader
        doc = Document();doc.add_paragraph('Ciao Office');source = self.root / 'document.docx';doc.save(source)
        pdf = convert(source, self.root, 'pdf')
        self.assertIn('Ciao Office', '\n'.join(p.extract_text() for p in PdfReader(pdf).pages))
        odt = convert(source, self.root, 'odt')
        rtf = convert(source, self.root, 'rtf')
        for office in (odt,rtf):
            plain = convert(office, self.root, 'txt')
            self.assertIn('Ciao Office', Path(plain).read_text(encoding='utf-8-sig'))
        book = Workbook();book.active.append(['nome','valore']);book.active.append(['Giordano',12])
        xlsx = self.root / 'sheet.xlsx';book.save(xlsx);book.close()
        ods = convert(xlsx, self.root, 'ods')
        back = convert(ods, self.root, 'xlsx')
        self.assertGreater(Path(back).stat().st_size,0)
        self.assertGreater(len(PdfReader(convert(xlsx,self.root,'pdf')).pages),0)

    def test_libreoffice_presentation(self):
        try:
            libreoffice_executable()
        except RuntimeError:
            self.skipTest('LibreOffice assente')
        try:
            from pptx import Presentation
        except ImportError:
            self.skipTest('python-pptx non disponibile per creare la fixture')
        from pypdf import PdfReader
        deck = Presentation(); slide = deck.slides.add_slide(deck.slide_layouts[0]);slide.shapes.title.text='Test presentation'
        source = self.root / 'slides.pptx';deck.save(source)
        pdf = convert(source,self.root,'pdf')
        self.assertIn('Test presentation',PdfReader(pdf).pages[0].extract_text())
        odp = convert(source,self.root,'odp')
        back = convert(odp,self.root,'pptx')
        self.assertEqual(len(Presentation(back).slides),1)
