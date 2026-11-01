import json
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw, ImageFont
from engine import convert, common_formats
from converters.ocr_converter import tesseract_executable
try:
    TESSERACT_AVAILABLE = bool(tesseract_executable())
except RuntimeError:
    TESSERACT_AVAILABLE = False

class ExtendedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_csv_excel_json(self):
        from openpyxl import load_workbook
        source = self.root / 'dati.csv'
        source.write_text('nome;codice;nota\nGiordano;001;"ciao; mondo"\nAnna;002;=1+1\n', encoding='utf-8')
        excel = convert(source, self.root, 'xlsx')
        book = load_workbook(excel)
        self.assertEqual(book.active['B2'].value, '001')
        self.assertEqual(book.active['C3'].data_type, 's')
        book.close()
        result = convert(excel, self.root, 'json')
        rows = json.loads(Path(result).read_text(encoding='utf-8'))
        self.assertEqual(rows[1], ['Giordano', '001', 'ciao; mondo'])
        self.assertEqual(rows[2][2], '=1+1')
        tsv = convert(result, self.root, 'tsv')
        self.assertIn('Giordano\t001', Path(tsv).read_text(encoding='utf-8-sig'))
        csv = convert(tsv, self.root, 'csv')
        self.assertIn('ciao; mondo', Path(csv).read_text(encoding='utf-8-sig'))
        self.assertCountEqual(common_formats(['a.xlsx', 'b.json']), ['csv','tsv','xlsx','json','jsonl'])

    def test_selected_sheet_and_nested_json(self):
        from openpyxl import Workbook
        book = Workbook(); book.active.append(['first'])
        book.create_sheet('Secondo').append(['second'])
        source = self.root / 'sheets.xlsx';book.save(source);book.close()
        target = convert(source, self.root, 'json', {'sheet': 2})
        self.assertEqual(json.loads(Path(target).read_text()), [['second']])
        with self.assertRaisesRegex(ValueError, 'non esiste'):
            convert(source, self.root, 'csv', {'sheet': 3})
        nested = self.root / 'nested.json'; nested.write_text('[{"a": {"b": 1}}]')
        with self.assertRaisesRegex(ValueError, 'annidato'):
            convert(nested, self.root, 'xlsx')
        self.assertFalse(list(self.root.glob('nested_convertito*')))

    def test_records_union_and_unicode(self):
        source = self.root / 'record.json'
        source.write_text('[{"nome":"Perù","n":1},{"nome":"città","extra":true}]', encoding='utf-8')
        target = convert(source, self.root, 'json')
        self.assertEqual(json.loads(Path(target).read_text(encoding='utf-8')), [['nome','n','extra'],['Perù',1,None],['città',None,True]])

    def test_all_pdf_pages(self):
        from reportlab.pdfgen import canvas
        source = self.root / 'pages.pdf'
        pdf = canvas.Canvas(str(source), pagesize=(180, 180))
        for number in (1, 2):
            pdf.drawString(20, 90, f'Page {number}');pdf.showPage()
        pdf.save()
        for fmt in ('png.zip', 'jpg.zip'):
            target = convert(source, self.root, fmt, {'dpi': 72})
            with ZipFile(target) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), 2)
                with Image.open(BytesIO(archive.read(names[0]))) as image:
                    self.assertEqual(image.size, (180, 180))

    @unittest.skipUnless(TESSERACT_AVAILABLE, 'Tesseract assente')
    def test_actual_ocr_image_and_scanned_pdf(self):
        image = Image.new('RGB', (1100, 200), 'white')
        candidates = [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('C:/Windows/Fonts/arial.ttf')]
        font_path = next((p for p in candidates if p.exists()), None)
        if font_path is None:
            self.skipTest('Font per il test OCR non disponibile')
        font = ImageFont.truetype(str(font_path), 60)
        ImageDraw.Draw(image).text((30, 50), 'HELLO CONVERTER 123', fill='black', font=font)
        source = self.root / 'text.png';image.save(source)
        text = convert(source, self.root, 'txt', {'ocr_language': 'eng'})
        self.assertIn('HELLO CONVERTER 123', Path(text).read_text())
        docx = convert(source, self.root, 'docx', {'ocr_language': 'eng'})
        self.assertGreater(Path(docx).stat().st_size, 0)
        pdf = self.root / 'scan.pdf'; image.save(pdf, 'PDF', resolution=150)
        extracted = convert(pdf, self.root, 'txt', {'ocr': True, 'ocr_language': 'eng'})
        self.assertIn('HELLO CONVERTER 123', Path(extracted).read_text())

    @unittest.skipUnless(TESSERACT_AVAILABLE, 'Tesseract assente')
    def test_missing_language_is_explained(self):
        source = self.root / 'image.png';Image.new('RGB',(100,100),'white').save(source)
        with self.assertRaisesRegex(RuntimeError, 'lingue selezionate'):
            convert(source,self.root,'txt',{'ocr_language':'nonexistent_lang'})
        self.assertFalse(list(self.root.glob('image_convertito*')))

if __name__ == '__main__':
    unittest.main()
