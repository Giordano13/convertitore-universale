"""Tabular conversions: CSV/TSV, one Excel sheet, and JSON rows/records."""
import csv
import json
import io
from datetime import date, datetime, time
from pathlib import Path


def scalar(value):
    if isinstance(value, (dict, list)):
        raise ValueError('JSON annidato non tabellare: sono ammessi solo valori semplici nelle celle.')
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    return value


def read_rows(source, sheet=1):
    ext = Path(source).suffix.lower()
    if ext == '.xlsx':
        from openpyxl import load_workbook
        book = load_workbook(source, read_only=True, data_only=False)
        try:
            if not 1 <= sheet <= len(book.worksheets):
                raise ValueError(f'Il foglio {sheet} non esiste: questo Excel contiene {len(book.worksheets)} fogli.')
            return [[scalar(c) for c in row] for row in book.worksheets[sheet - 1].iter_rows(values_only=True)]
        finally:
            book.close()
    if ext in ('.json', '.jsonl', '.ndjson'):
        from text_encoding import read_text_file
        text = read_text_file(source)
        if ext == '.json':
            data = json.loads(text)
        else:
            data = []
            for number, line in enumerate(text.splitlines(), 1):
                if not line.strip():continue
                try:data.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f'JSON Lines non valido alla riga {number}: {error.msg}') from error
        if not isinstance(data, list):
            raise ValueError('Serve un JSON tabellare: una lista di righe oppure una lista di oggetti.')
        if not data:
            return []
        if all(isinstance(row, dict) for row in data):
            keys = list(dict.fromkeys(key for row in data for key in row))
            return [keys] + [[scalar(row.get(key)) for key in keys] for row in data]
        if all(isinstance(row, list) for row in data):
            return [[scalar(cell) for cell in row] for row in data]
        raise ValueError('Il JSON deve contenere solo righe oppure solo oggetti con valori semplici.')
    from text_encoding import read_text_file
    with io.StringIO(read_text_file(source), newline='') as stream:
        if ext == '.tsv':
            dialect = csv.excel_tab
        else:
            sample = stream.read(8192)
            stream.seek(0)
            try:
                # Sniffer can miscount quoted separators with Windows CRLF.
                # Normalize only the sample; preserve original cell newlines.
                dialect = csv.Sniffer().sniff(sample.replace('\r\n', '\n').replace('\r', '\n'), delimiters=',;\t|')
            except csv.Error:
                dialect = csv.excel
        return list(csv.reader(stream, dialect))


def convert_table(source, target, fmt, sheet=1):
    rows = read_rows(source, sheet)
    if fmt == 'xlsx':
        if len(rows) > 1048576:
            raise ValueError('Troppe righe per Excel (massimo 1048576).')
        from openpyxl import Workbook
        from openpyxl.cell import WriteOnlyCell
        book = Workbook(write_only=True)
        ws = book.create_sheet('Dati')
        for row in rows:
            if len(row) > 16384:
                raise ValueError('Troppe colonne per Excel (massimo 16384).')
            cells = []
            for value in row:
                if isinstance(value, str) and len(value) > 32767:
                    raise ValueError('Una cella supera il limite Excel di 32767 caratteri.')
                cell = WriteOnlyCell(ws, value=value)
                if isinstance(value, str):
                    cell.data_type = 's'  # CSV/JSON content stays text, never executable formulas.
                cells.append(cell)
            ws.append(cells)
        book.save(target)
    elif fmt == 'jsonl':
        with open(target, 'w', encoding='utf-8', newline='\n') as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    elif fmt == 'json':
        Path(target).write_text(json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    elif fmt in ('csv', 'tsv'):
        with open(target, 'w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream, delimiter='\t' if fmt == 'tsv' else ',')
            writer.writerows(rows)
    else:
        raise ValueError('Formato tabella non supportato.')
