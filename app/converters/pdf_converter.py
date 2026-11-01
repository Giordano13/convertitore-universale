"""Export every PDF page as a numbered image inside one ZIP."""
from zipfile import ZipFile, ZIP_DEFLATED


def pdf_to_images(source, target, image_format='png', dpi=150):
    import pymupdf
    if image_format not in ('png', 'jpg'):
        raise ValueError('Formato immagine PDF non supportato.')
    with pymupdf.open(source) as doc:
        if doc.needs_pass:
            raise ValueError('PDF protetto da password: apri prima una copia sbloccata.')
        if not len(doc):
            raise ValueError('Il PDF non contiene pagine.')
        with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
            for number, page in enumerate(doc, start=1):
                pixels = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                archive.writestr(f'pagina_{number:04d}.{image_format}', pixels.tobytes(image_format))
