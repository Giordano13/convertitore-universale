import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import wave

from engine import convert, kind
from file_integrity import sha256_file
from operations import execute
from PIL import Image


class NewFormatTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def test_jsonl_objects_arrays_and_roundtrip(self):
        source=self.root/'events.ndjson'
        source.write_text('{"nome":"città","n":1}\n\n{"extra":true}\n',encoding='utf-8')
        self.assertEqual(kind(source),'table')
        target=convert(source,self.root,'jsonl')
        lines=[json.loads(line) for line in Path(target).read_text(encoding='utf-8').splitlines()]
        self.assertEqual(lines,[['nome','n','extra'],['città',1,None],[None,None,True]])
        back=convert(target,self.root,'json')
        self.assertEqual(json.loads(Path(back).read_text(encoding='utf-8')),lines)

    def test_jsonl_reports_line_and_cleans_output(self):
        source=self.root/'bad.jsonl';source.write_text('{}\n{bad}\n')
        with self.assertRaisesRegex(ValueError,'riga 2'):convert(source,self.root,'xlsx')
        self.assertEqual(list(self.root.glob('*convertito*')),[])

    def test_unicode_and_windows_text_encodings(self):
        from converters.table_converter import read_rows
        from converters.document_converter import read_text
        for encoding in ('utf-8-sig','utf-16','utf-32','cp1252'):
            source=self.root/'data.csv';source.write_bytes('città;codice\r\nPerù;001\r\n'.encode(encoding))
            self.assertEqual(read_rows(source),[['città','codice'],['Perù','001']])
            source=self.root/'config.yaml';source.write_bytes('città: Perù'.encode(encoding))
            self.assertEqual(kind(source),'text')
            self.assertEqual(read_text(source),'città: Perù')
            target=convert(source,self.root,'txt')
            self.assertEqual(Path(target).read_text(encoding='utf-8'),'città: Perù')

    def test_new_image_outputs_and_inputs(self):
        source=self.root/'alpha.png';Image.new('RGBA',(33,17),(255,0,0,0)).save(source)
        for fmt in ('tga','ppm'):
            target=convert(source,self.root,fmt)
            with Image.open(target) as picture:
                self.assertEqual(picture.size,(33,17))
                if fmt=='ppm':self.assertEqual(picture.getpixel((0,0)),(255,255,255))
            back=convert(target,self.root,'png');self.assertGreater(Path(back).stat().st_size,0)
        for ext,mode,format in [('pgm','L','PPM'),('pbm','1','PPM'),('pcx','RGB','PCX')]:
            source=self.root/('input.'+ext);Image.new(mode,(16,16)).save(source,format=format)
            with Image.open(convert(source,self.root,'png')) as picture:self.assertEqual(picture.size,(16,16))

    def test_hash_native_and_python_match_on_empty_unicode_and_large_files(self):
        for size in (0,3,2*1024*1024+17):
            source=self.root/'città 文件.bin';data=(b'abc1234'*(size//7+1))[:size];source.write_bytes(data)
            for native in (True,False):
                digest,backend=sha256_file(source,prefer_native=native)
                self.assertEqual(digest,hashlib.sha256(data).hexdigest())
                if native and os.name=='nt' and (Path(__file__).parents[1]/'app/native/file_hash.dll').exists():
                    self.assertEqual(backend,'C++ / Windows CNG')

    def test_hash_falls_back_if_library_cannot_load(self):
        source=self.root/'file.txt';source.write_bytes(b'abc')
        with patch('file_integrity.ctypes.CDLL',side_effect=OSError('Bad DLL')):
            digest,backend=sha256_file(source)
        self.assertEqual(digest,hashlib.sha256(b'abc').hexdigest());self.assertEqual(backend,'Python')

    def test_file_info_checksum_integration(self):
        source=self.root/'file.txt';source.write_bytes(b'abc');target=self.root/'info.json'
        execute('file_info',[source],target,'json',{'checksum':True})
        self.assertEqual(json.loads(target.read_text())['sha256'],hashlib.sha256(b'abc').hexdigest())

    def test_obsolete_path_binary_does_not_hide_compatible_winget_install(self):
        from runtime_paths import media_executable
        directory=self.root/'Microsoft/WinGet/Packages/Gyan.FFmpeg_test/version/bin'
        directory.mkdir(parents=True);candidate=directory/'ffmpeg.exe';candidate.touch()
        old=self.root/'old.exe';old.touch()
        with patch('runtime_paths.shutil.which',return_value=str(old)),patch.dict(os.environ,{'LOCALAPPDATA':str(self.root),'FFMPEG_CMD':''}),patch('runtime_paths.media_compatible',side_effect=lambda path,stamp:path==str(candidate)):
            if os.name=='nt':self.assertEqual(media_executable('ffmpeg'),str(candidate))

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg/FFprobe assenti')
    def test_real_opus_and_aiff_conversion(self):
        source=self.root/'sound.wav'
        with wave.open(str(source),'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(48000);stream.writeframes(b'\x00\x00'*9600)
        for fmt in ('opus','aiff'):
            target=convert(source,self.root,fmt)
            self.assertGreater(Path(target).stat().st_size,0)
