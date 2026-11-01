import os,time,json,tempfile,unittest,subprocess
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageDraw,ImageFont
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from engine import convert
from operations import execute,page_numbers
from state_store import StateStore
from watch_folder import FolderMonitor
from media import probe
from process_worker import run_job
import conversion_progress

class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def pdf(self,name,text):
        path=self.root/name;c=canvas.Canvas(str(path));c.drawString(70,750,text);c.showPage();c.drawString(70,750,text+' page two');c.save();return path
    def test_pdf_merge_split_rotate_compress(self):
        a=self.pdf('a.pdf','FIRST');b=self.pdf('b.pdf','SECOND');out=self.root/'out.pdf'
        execute('merge_pdf',[a,b],out,'pdf');self.assertEqual(len(PdfReader(out).pages),4);self.assertIn('SECOND',PdfReader(out).pages[2].extract_text())
        split=self.root/'split.zip';execute('split_pdf',[out],split,'pdf.zip',dict(pages='2-3'))
        with ZipFile(split) as z:self.assertEqual(z.namelist(),['pagina_0002.pdf','pagina_0003.pdf']);self.assertIn('SECOND',PdfReader(__import__('io').BytesIO(z.read('pagina_0003.pdf'))).pages[0].extract_text())
        rotated=self.root/'rotated.pdf';execute('rotate_pdf',[out],rotated,'pdf',dict(pages='2',rotation=90));reader=PdfReader(rotated)
        self.assertEqual(len(reader.pages),4);self.assertEqual(reader.pages[1].rotation,90);self.assertEqual(reader.pages[0].rotation,0)
        compressed=self.root/'compressed.pdf';execute('compress_pdf',[out],compressed,'pdf');self.assertEqual(len(PdfReader(compressed).pages),4)
        self.assertIn('FIRST',PdfReader(compressed).pages[0].extract_text())
        with self.assertRaises(ValueError):page_numbers('9',4)
    def test_images_pdf(self):
        source=self.root/'scan.png';Image.new('RGB',(1200,300),'white').save(source)
        pdf=self.root/'scan.pdf';execute('images_pdf',[source,source],pdf,'pdf');self.assertEqual(len(PdfReader(pdf).pages),2)

    def test_searchable_ocr(self):
        from converters.ocr_converter import tesseract_executable
        try:tesseract_executable()
        except RuntimeError:self.skipTest('Tesseract assente')
        font=next((path for path in ('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') if Path(path).exists()),None)
        if not font:self.skipTest('Font di prova non disponibile')
        source=self.root/'scan.png';image=Image.new('RGB',(1200,300),'white');ImageDraw.Draw(image).text((30,60),'HELLO CONVERTER',font=ImageFont.truetype(font,70),fill='black');image.save(source)
        pdf=self.root/'scan.pdf';execute('images_pdf',[source,source],pdf,'pdf');self.assertEqual(len(PdfReader(pdf).pages),2)
        result=self.root/'searchable.pdf';execute('searchable_pdf',[pdf],result,'pdf',dict(ocr_language='eng',dpi=150));self.assertIn('HELLO',PdfReader(result).pages[0].extract_text())
        import pymupdf
        with pymupdf.open(result) as doc:self.assertTrue(doc[0].get_images());self.assertEqual(len(doc),2)
    def test_workflow_metadata_and_logo(self):
        source=self.root/'photo.jpg';image=Image.new('RGB',(240,180),'blue');exif=Image.Exif();exif[315]='Photographer';image.save(source,exif=exif)
        kept=convert(source,self.root,'jpg',dict(metadata='keep'));removed=convert(source,self.root,'jpg',dict(metadata='remove'))
        with Image.open(kept) as im:self.assertEqual(im.getexif()[315],'Photographer')
        with Image.open(removed) as im:self.assertFalse(im.getexif())
        logo=self.root/'logo.png';Image.new('RGBA',(20,20),'red').save(logo)
        options=dict(metadata='keep',crop=[10,10,200,140],width=100,height=100,watermark_logo=str(logo),watermark_text='TEST',watermark_opacity=100)
        out=convert(source,self.root,'png',options)
        with Image.open(out) as im:self.assertEqual(im.size,(100,70));self.assertGreater(im.convert('RGB').getpixel((78,48))[0],100);self.assertEqual(im.getexif()[315],'Photographer')
    def test_sevenzip_roundtrip_and_unsafe_paths(self):
        source=self.root/'files.zip'
        with ZipFile(source,'w') as z:z.writestr('nested/hello.txt','CIAO');z.writestr('empty/',b'')
        seven=convert(source,self.root,'7z');back=convert(seven,self.root,'zip')
        with ZipFile(back) as z:self.assertEqual(z.read('nested/hello.txt'),b'CIAO');self.assertIn('empty/',z.namelist())
        import py7zr
        file=self.root/'file.txt';file.write_text('bad');bad=self.root/'bad.7z'
        with py7zr.SevenZipFile(bad,'w') as z:z.write(file,'../outside.txt')
        with self.assertRaises(ValueError):convert(bad,self.root,'zip')
        self.assertFalse((self.root.parent/'outside.txt').exists())
    def test_history_workflows_watch_stability(self):
        store=StateStore(self.root/'state');source=self.root/'source.txt';source.write_text('test')
        store.save_recipe('web',dict(width=400,quality=80));self.assertEqual(StateStore(self.root/'state').recipes()['web']['width'],400)
        job=dict(sources=[str(source)],format='txt');store.add_history(job,True,str(source));self.assertEqual(store.history()[0]['output_bytes'],4)
        incoming=self.root/'incoming';incoming.mkdir();monitor=FolderMonitor(incoming,self.root/'output');file=incoming/'new.txt';file.write_text('one')
        self.assertEqual(monitor.poll(),[]);file.write_text('longer');self.assertEqual(monitor.poll(),[]);self.assertEqual(monitor.poll(),[str(file)]);self.assertEqual(monitor.poll(),[])
        with self.assertRaises(ValueError):FolderMonitor(incoming,incoming/'output')
    def video(self,duration=3):
        path=self.root/'video.mp4'
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'testsrc2=size=160x120:rate=25:duration={duration}','-f','lavfi','-i',f'sine=frequency=440:duration={duration}','-c:v','libx264','-c:a','aac',str(path)],check=True);return path
    def test_trim_denoise_remux_audio_replace_and_progress(self):
        source=self.video();events=[];conversion_progress.CALLBACK=lambda *v:events.append(v);self.addCleanup(setattr,conversion_progress,'CALLBACK',None)
        out=convert(source,self.root,'mp4',dict(start=.5,end=1.5,denoise=True,width=120,height=100,target_mb=.1))
        info=probe(out);self.assertAlmostEqual(info['duration'],1,delta=.2);self.assertEqual(info['streams'][0]['width'],120);self.assertTrue(any(isinstance(e[0],float) for e in events))
        remux=self.root/'copy.mkv';execute('remux',[source],remux,'mkv');self.assertEqual(probe(remux)['streams'][0]['codec_name'],'h264')
        audio=self.root/'new.wav';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','sine=frequency=880:duration=1','-ar','22050',str(audio)],check=True)
        replaced=self.root/'replaced.mp4';execute('replace_audio',[source,audio],replaced,'mp4');data=probe(replaced)
        self.assertEqual(next(s for s in data['streams'] if s['codec_type']=='audio')['sample_rate'],'22050')
        trimmed=convert(source,self.root,'wav',dict(start=.5,end=1.5));self.assertAlmostEqual(probe(trimmed)['duration'],1,delta=.1)
        with self.assertRaises(ValueError):convert(source,self.root,'mp4',dict(start=2,end=1))
    def test_cancel_running_ffmpeg_cleans_output(self):
        source=self.video(30);target=self.root/'partial.mp4';seen=[];cancel_at=[None]
        def progress(fraction,phase,eta):
            seen.append((fraction,phase))
            if fraction is not None and fraction<1 and cancel_at[0] is None:cancel_at[0]=time.monotonic()+.15
        started=time.monotonic()
        success,value=run_job(dict(sources=[str(source)],format='mp4',options=dict(width=2560,height=1920)),target,
            lambda:(cancel_at[0] is not None and time.monotonic()>=cancel_at[0]) or time.monotonic()-started>15,progress)
        self.assertIsNone(success);self.assertEqual(value,'Annullato');self.assertFalse(target.exists());self.assertTrue(seen);self.assertLess(time.monotonic()-cancel_at[0],4)
    def test_file_info_actual_data(self):
        source=self.root/'photo.png';Image.new('RGB',(42,28),'red').save(source);target=self.root/'info.json'
        execute('file_info',[source],target,'json');data=json.loads(target.read_text());self.assertEqual(data['larghezza'],42);self.assertEqual(data['bytes'],source.stat().st_size)

    def test_real_raw_dng_development(self):
        import numpy as np
        from PIL import TiffImagePlugin
        source=self.root/'camera.dng';tags=TiffImagePlugin.ImageFileDirectory_v2()
        values={271:'Codex',272:'Test Camera',50706:b'\x01\x04\x00\x00',50707:b'\x01\x01\x00\x00',50708:'Codex Test Camera',33421:(2,2),33422:b'\x00\x01\x01\x02',50710:b'\x00\x01\x02',50711:1,50714:0,50717:4095,50721:(1,0,0,0,1,0,0,0,1),50728:(1,1,1),50778:21,262:32803}
        for key,value in values.items():tags[key]=value
        for key in (50721,50728):tags.tagtype[key]=5
        Image.fromarray(np.full((128,128),2000,dtype=np.uint16)).save(source,format='TIFF',tiffinfo=tags)
        result=convert(source,self.root,'png',dict(width=64,height=64))
        with Image.open(result) as image:self.assertEqual(image.size,(64,64));self.assertEqual(image.mode,'RGB');self.assertGreater(image.getpixel((0,0))[0],0)
