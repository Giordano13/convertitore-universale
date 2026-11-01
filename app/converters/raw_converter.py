from PIL import Image
from conversion_progress import report


def read_raw(source):
    import rawpy
    report(None,'Sviluppo foto RAW')
    with rawpy.imread(str(source)) as raw:
        rgb=raw.postprocess(use_camera_wb=True,output_bps=8)
    return Image.fromarray(rgb)


def convert_raw(source,target,fmt,options=None):
    from pathlib import Path
    import tempfile
    from converters.image_converter import convert_image
    image=read_raw(source)
    with tempfile.TemporaryDirectory() as directory:
        png=Path(directory)/'raw.png';image.save(png)
        options=options or {}
        convert_image(png,target,fmt,options.get('width'),options.get('height'),options.get('quality',90),options=options)
