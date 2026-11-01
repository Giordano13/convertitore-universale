import tempfile
import unittest
import shutil
from pathlib import Path
from PIL import Image
from docx import Document
from pypdf import PdfReader
from engine import convert, common_formats

class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_documents(self):
        source = self.root / 'test.txt'
        source.write_text('Ciao Giordano!\nSeconda riga.', encoding='utf-8')
        docx = convert(source, self.root, 'docx')
        self.assertEqual(Document(docx).paragraphs[0].text, 'Ciao Giordano!')
        text = convert(docx, self.root, 'txt')
        self.assertIn('Seconda riga.', Path(text).read_text())
        pdf = convert(source, self.root, 'pdf')
        self.assertIn('Ciao Giordano!', PdfReader(pdf).pages[0].extract_text())
        extracted = convert(pdf, self.root, 'docx')
        self.assertIn('Ciao Giordano!', '\n'.join(p.text for p in Document(extracted).paragraphs))

    def test_image_and_collisions(self):
        source = self.root / 'image.png'
        Image.new('RGBA', (30, 20), (255, 0, 0, 0)).save(source)
        first = convert(source, self.root, 'jpg')
        second = convert(source, self.root, 'jpg')
        self.assertNotEqual(first, second)
        with Image.open(first) as image:
            self.assertEqual(image.size, (30, 20))
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))
        self.assertTrue(source.exists())

    def test_failure_cleanup_and_mixed_selection(self):
        source = self.root / 'broken.png'
        source.write_bytes(b'bad image')
        with self.assertRaises(Exception):
            convert(source, self.root, 'jpg')
        self.assertEqual(list(self.root.glob('*_convertito*')), [])
        self.assertEqual(common_formats(['a.mp3', 'b.txt']), [])
        self.assertIn('mp3', common_formats(['a.mp3', 'b.mp4']))

    @unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg assente')
    def test_audio_video(self):
        import subprocess
        audio = self.root / 'source.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=0.2',str(audio)],check=True)
        for fmt in ('mp3','wav','ogg','flac','aac','m4a'):
            self.assertGreater(Path(convert(audio, self.root, fmt)).stat().st_size, 0)
        video = self.root / 'source.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=64x48:d=0.2','-pix_fmt','yuv420p',str(video)], check=True)
        for fmt in ('mp4','mkv','mov','avi','webm','gif'):
            self.assertGreater(Path(convert(video, self.root, fmt)).stat().st_size, 0)

if __name__ == '__main__':
    unittest.main()
