# Verifiche della versione 2.0

Suite completa: **33 test superati, nessun errore e nessun test saltato**.
Comando: `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v`.
Esecuzione sul runtime Linux, Python 3.12.14, durata 37,888 secondi.
Il log completo è incluso in `verifica_v2.txt`.

## Prove effettuate
- Conversioni di immagini, animazioni, HEIC/SVG e gestione collisioni/errori.
- Word, testo, Markdown, HTML/EPUB, tabelle e sottotitoli.
- Conversioni LibreOffice di documenti, fogli e presentazioni con contenuti verificati.
- PDF: tutte le pagine in immagini, merge/split/rotazione/compressione.
- OCR reale con Tesseract in inglese, anche PDF ricercabile con immagini preservate.
- ZIP/TAR/7Z con controllo dei contenuti e rifiuto di percorsi non validi.
- Sviluppo di un vero DNG sintetico tramite LibRaw/rawpy e ridimensionamento.
- Metadati EXIF conservati/rimossi, ritaglio, ridimensionamento e logo/testo.
- Codifica audio/video, taglio, rumore, remux, sostituzione audio e progressi FFmpeg.
- Annullamento mentre FFmpeg sta codificando: processo fermato, nessuna uscita parziale.
- UI reale: conversione in background, coda mista, filtri, temi e layout compatto.
- Importazione ricorsiva e conservazione sottocartelle, rinomina, sequenze e cronologia.
- Cartella sorvegliata: nuovo file convertito realmente, senza duplicazione.
- Confronto prima/dopo: immagine realmente convertita; chiusura durante lavoro senza crash.
- Rendering dell'app a 1280×840 e 960×720, temi scuro e chiaro,
  con conversione PNG → WEBP reale; anteprima inclusa nel pacchetto.

## Dipendenze presenti nell'ambiente di prova
- PyQt6: 6.11.0
- Pillow: 12.3.0
- pypdf: 6.10.0
- PyMuPDF: 1.26.6
- py7zr: 1.1.3
- rawpy: 0.27.1

FFmpeg/ffprobe, Tesseract inglese e LibreOffice erano disponibili.
La lingua italiana OCR non era installata: il relativo messaggio di errore
è stato verificato. I file RAW di specifiche fotocamere non sono stati provati.

## Verifiche ancora necessarie sul PC Windows
EXE e installer sono forniti come script/sorgente, **non compilati**.
Vanno verificati su Windows: build PyInstaller, Inno Setup, DLL native,
ricerca dei programmi esterni e annullamento tramite taskkill.
L'installer non include FFmpeg, LibreOffice e Tesseract.
