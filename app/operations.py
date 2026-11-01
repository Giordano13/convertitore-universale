"""Multi-file tools with one owned output per operation."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile
from conversion_progress import report,run_process
from runtime_paths import tessdata_arguments


def page_numbers(spec,total):
    if not spec.strip():return list(range(total))
    result=[]
    for part in spec.split(','):
        bits=part.strip().split('-')
        start=int(bits[0]);end=int(bits[-1])
        if len(bits)>2 or start<1 or end<start or end>total:raise ValueError('Intervallo pagine non valido.')
        result.extend(range(start-1,end))
    return list(dict.fromkeys(result))


def execute(operation,sources,target,fmt,options=None):
    options=options or {}
    if not sources:raise ValueError('Seleziona almeno un file.')
    if operation=='file_info':
        import json
        from engine import kind
        path=Path(sources[0]);category=kind(path)
        data=dict(file=str(path.resolve()),bytes=path.stat().st_size,tipo=category)
        if options.get('checksum'):
            from file_integrity import sha256_file
            data['sha256'],data['motore_verifica']=sha256_file(path)
        if category in ('audio','video'):
            from media import probe
            data['media']=probe(path)
        elif category=='image':
            if path.suffix.lower() in ('.heic','.heif'):
                from pillow_heif import register_heif_opener
                register_heif_opener()
            from PIL import Image,ExifTags
            with Image.open(path) as image:
                data.update(larghezza=image.width,altezza=image.height,modo=image.mode,fotogrammi=getattr(image,'n_frames',1),
                    exif={ExifTags.TAGS.get(k,str(k)):str(v) for k,v in image.getexif().items()})
        elif category=='pdf':
            from pypdf import PdfReader
            pdf=PdfReader(path);data.update(pagine=len(pdf.pages),metadati=dict(pdf.metadata or {}))
        Path(target).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding='utf-8');return
    if operation in ('remux','replace_audio'):
        from media import remux,replace_audio
        if operation=='remux':remux(sources[0],target,fmt,options)
        else:
            if len(sources)!=2:raise ValueError('Scegli prima il video e poi il nuovo audio.')
            replace_audio(sources[0],sources[1],target,options)
        return
    from pypdf import PdfReader,PdfWriter
    if operation=='images_pdf':
        from PIL import Image,ImageOps
        writer=PdfWriter()
        for i,path in enumerate(sources):
            from engine import kind
            if kind(path)=='raw':
                from converters.raw_converter import read_raw
                image=read_raw(path)
            else:
                if str(path).lower().endswith(('.heic','.heif')):
                    from pillow_heif import register_heif_opener
                    register_heif_opener()
                with Image.open(path) as original:image=ImageOps.exif_transpose(original).convert('RGBA')
            if image.mode!='RGBA':image=image.convert('RGBA')
            white=Image.new('RGB',image.size,'white');white.paste(image,mask=image.getchannel('A'))
            memory=BytesIO();white.save(memory,'PDF',resolution=150);memory.seek(0)
            writer.append(PdfReader(memory));report((i+1)/len(sources),'Immagini → PDF')
        writer.write(target);return
    if operation=='merge_pdf':
        writer=PdfWriter()
        for i,path in enumerate(sources):
            reader=PdfReader(path)
            if reader.is_encrypted:raise ValueError('Il PDF è protetto. Usa una copia sbloccata.')
            writer.append(reader);report((i+1)/len(sources),'Unione PDF')
        writer.write(target);return
    if operation=='searchable_pdf':
        import pymupdf
        from converters.ocr_converter import tesseract_executable
        writer=PdfWriter();executable=tesseract_executable()
        with tempfile.TemporaryDirectory() as directory,pymupdf.open(sources[0]) as doc:
            if doc.needs_pass:raise ValueError('PDF protetto da password.')
            for i,page in enumerate(doc):
                image=Path(directory)/'page.png';base=Path(directory)/'ocr'
                page.get_pixmap(dpi=int(options.get('dpi',200)),alpha=False).save(image)
                run_process([executable,image,base,'-l',options.get('ocr_language','ita+eng')]+tessdata_arguments(options.get('ocr_language','ita+eng'))+['-c','tessedit_create_pdf=1'],timeout=180,completed_report=False)
                if not Path(str(base)+'.pdf').is_file():
                    raise RuntimeError('Tesseract non ha prodotto il PDF ricercabile. Verifica il componente OCR e i suoi dati PDF.')
                writer.append(PdfReader(str(base)+'.pdf'));report((i+1)/len(doc),'OCR pagine PDF')
        writer.write(target);return
    reader=PdfReader(sources[0])
    if reader.is_encrypted:raise ValueError('PDF protetto da password.')
    pages=page_numbers(options.get('pages',''),len(reader.pages))
    if not pages:raise ValueError('Nessuna pagina selezionata.')
    if operation=='split_pdf':
        with ZipFile(target,'w',ZIP_DEFLATED) as archive:
            for i,index in enumerate(pages):
                writer=PdfWriter();writer.add_page(reader.pages[index]);data=BytesIO();writer.write(data)
                archive.writestr(f'pagina_{index+1:04d}.pdf',data.getvalue());report((i+1)/len(pages),'Divisione PDF')
        return
    writer=PdfWriter()
    output_pages=list(range(len(reader.pages))) if operation=='rotate_pdf' else pages
    for i,index in enumerate(output_pages):
        page=reader.pages[index]
        if operation=='rotate_pdf':
            if index in pages:page.rotate(int(options.get('rotation',90)))
        elif operation=='compress_pdf':pass
        else:raise ValueError('Strumento sconosciuto.')
        writer.add_page(page)
        if operation=='compress_pdf':writer.pages[-1].compress_content_streams(level=9)
        report((i+1)/len(output_pages),'Elaborazione PDF')
    writer.write(target)
