"""Image conversion, EXIF orientation, alpha handling and animation preservation."""
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pathlib import Path
from conversion_progress import report


def get_image_info(path):
    with Image.open(path) as image:
        return image.size


def convert_image(input_path, output_path, out_format, width=None, height=None, quality=90, keep_ratio=True, options=None):
    options = options or {}
    if str(input_path).lower().endswith(('.heic', '.heif')):
        from pillow_heif import register_heif_opener
        register_heif_opener()
    fmt = {'JPG': 'JPEG', 'TIF': 'TIFF'}.get(out_format.upper(), out_format.upper())
    with Image.open(input_path) as original:
        multi = getattr(original, 'n_frames', 1) > 1 and fmt in ('GIF', 'WEBP', 'TIFF')
        frames, durations = [], []
        for index in range(original.n_frames if multi else 1):
            original.seek(index)
            durations.append(original.info.get('duration', 100))
            image = ImageOps.exif_transpose(original.copy())
            if index==0:normalized_exif=image.getexif()
            if fmt in ('JPEG', 'PDF', 'BMP', 'PPM') and image.mode != 'RGB':
                rgba = image.convert('RGBA')
                image = Image.new('RGB', rgba.size, 'white')
                image.paste(rgba, mask=rgba.getchannel('A'))
            crop=options.get('crop')
            if crop and crop[2] and crop[3]:
                x,y,w,h=map(int,crop)
                if x<0 or y<0 or x+w>image.width or y+h>image.height:
                    raise ValueError('Il ritaglio supera le dimensioni dell’immagine.')
                image=image.crop((x,y,x+w,y+h))
            if width and height:
                if keep_ratio:
                    ratio = min(width / image.width, height / image.height)
                    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
                else:
                    size = (width, height)
                image = image.resize(size, Image.Resampling.LANCZOS)
            if options.get('watermark_text') or options.get('watermark_logo'):
                base=image.convert('RGBA');overlay=Image.new('RGBA',base.size,(0,0,0,0));margin=max(8,base.width//40)
                opacity=int(options.get('watermark_opacity',70))
                if options.get('watermark_logo'):
                    with Image.open(options['watermark_logo']) as logo_original:logo=logo_original.convert('RGBA')
                    logo.thumbnail((max(1,base.width//4),max(1,base.height//4)))
                    logo.putalpha(logo.getchannel('A').point(lambda a:round(a*opacity/100)))
                    overlay.alpha_composite(logo,(max(0,base.width-logo.width-margin),max(0,base.height-logo.height-margin)))
                if options.get('watermark_text'):
                    draw=ImageDraw.Draw(overlay);font_size=max(12,base.width//25)
                    font_path=next((p for p in [Path('C:/Windows/Fonts/arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')] if p.exists()),None)
                    font=ImageFont.truetype(str(font_path),font_size) if font_path else ImageFont.load_default(size=font_size)
                    text=options['watermark_text'];bounds=draw.textbbox((0,0),text,font=font)
                    x=max(margin,base.width-(bounds[2]-bounds[0])-margin);y=max(margin,base.height-font_size-margin)
                    draw.text((x,y),text,font=font,fill=(255,255,255,round(255*opacity/100)),stroke_width=1,stroke_fill=(0,0,0,round(255*opacity/100)))
                image=Image.alpha_composite(base,overlay)
                if fmt in ('JPEG','PDF','BMP','PPM'):image=image.convert('RGB')
            if options.get('metadata','remove')=='remove':
                image.info.clear();image.getexif().clear()
            frames.append(image)
            report((index+1)/(original.n_frames if multi else 1),'Elaborazione immagini')
        kwargs = {'quality': max(1, min(100, quality))} if fmt in ('JPEG', 'WEBP') else {}
        if options.get('metadata')=='keep':
            exif=normalized_exif
            for tag,value in [(256,frames[0].width),(257,frames[0].height),(40962,frames[0].width),(40963,frames[0].height)]:
                if tag in exif:exif[tag]=value
            if exif and fmt in ('JPEG','PNG','WEBP','TIFF'):kwargs['exif']=exif.tobytes()
            if original.info.get('icc_profile') and fmt in ('JPEG','PNG','WEBP','TIFF'):kwargs['icc_profile']=original.info['icc_profile']
        if multi:
            kwargs.update(save_all=True, append_images=frames[1:])
            if fmt in ('GIF', 'WEBP'):
                kwargs.update(duration=durations, loop=original.info.get('loop', 0))
        report(None,'Salvataggio immagine')
        frames[0].save(output_path, format=fmt, **kwargs)
    return output_path
