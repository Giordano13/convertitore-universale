"""Text extraction and office export. PDF extraction does not perform OCR."""
from pathlib import Path


def read_text(path):
    ext = Path(path).suffix.lower()
    if ext == '.pdf':
        from pypdf import PdfReader
        text = '\n\n'.join(p.extract_text() or '' for p in PdfReader(path).pages)
        if not text.strip():
            raise ValueError('Il PDF non contiene testo estraibile: potrebbe servire OCR.')
        return text
    if ext == '.docx':
        from docx import Document
        doc = Document(path)
        parts = [p.text for p in doc.paragraphs]
        parts.extend('\t'.join(c.text for c in r.cells) for t in doc.tables for r in t.rows)
        return '\n'.join(parts)
    if ext == '.epub':
        from converters.web_ebook_converter import read_epub
        return read_epub(path)
    from text_encoding import read_text_file
    text = read_text_file(path)
    if ext in ('.html', '.htm', '.xhtml'):
        from converters.web_ebook_converter import html_text
        return html_text(text)
    return text


def office_pdf(source, target):
    from converters.office_converter import convert_office
    convert_office(source, target, 'pdf', 'writer')


def convert_document(source, target, fmt):
    if fmt == 'pdf' and Path(source).suffix.lower() in ('.doc', '.docx', '.odt', '.rtf'):
        office_pdf(source, target)
        return
    text = read_text(source)
    if fmt == 'html':
        from converters.web_ebook_converter import write_html
        write_html(text, target, Path(source).suffix.lower() in ('.md', '.markdown'))
    else:
        write_text_document(text, target, fmt)


def write_text_document(text, target, fmt):
    if fmt == 'txt':
        Path(target).write_text(text, encoding='utf-8')
    elif fmt == 'docx':
        from docx import Document
        doc = Document()
        for line in text.splitlines():
            doc.add_paragraph(line)
        doc.save(target)
    elif fmt == 'epub':
        from converters.web_ebook_converter import text_epub
        text_epub(text, target, Path(target).stem)
    elif fmt == 'html':
        from converters.web_ebook_converter import write_html
        write_html(text, target)
    elif fmt == 'pdf':
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.enums import TA_LEFT
        from xml.sax.saxutils import escape
        style = getSampleStyleSheet()['Normal']
        style.alignment = TA_LEFT
        style.fontName = 'Helvetica'
        story = []
        for line in text.splitlines() or ['']:
            story.extend([Paragraph(escape(line) or '&#160;', style), Spacer(1, 5)])
        SimpleDocTemplate(str(target)).build(story)
    else:
        raise ValueError('Formato documento non supportato.')
