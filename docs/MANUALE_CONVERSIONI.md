# Manuale conversioni — versione 2.1

App desktop locale in italiano, con selezione multipla, drag & drop,
interfaccia scura e conversioni in background. Tutte le funzioni delle
versioni precedenti sono incluse in questo pacchetto unico.

> Per installazione, setup e aggiornamenti consulta il README nella cartella principale.

## Formati e conversioni
| Categoria | File in ingresso | Risultati |
| --- | --- | --- |
| Immagini | JPG/JPEG, PNG, WEBP, BMP, GIF, TIFF, ICO, HEIC/HEIF | JPG, PNG, WEBP, BMP, TIFF, GIF, ICO, PDF; TXT/DOCX con OCR |
| RAW fotografici | NEF, CR2/CR3, ARW, DNG, RAF, RW2, ORF, PEF, SRW, se compatibili con LibRaw | JPG, PNG, WEBP, TIFF, BMP, PDF |
| Vettori | SVG | PNG, JPG, WEBP, BMP, TIFF, ICO, PDF |
| Audio | MP3, WAV, OGG, FLAC, AAC, M4A, AIFF, OPUS, WMA | MP3, WAV, OGG, FLAC, AAC, M4A |
| Video | MP4, AVI, MOV, WEBM, MKV, M4V, MPEG, MPG, WMV, TS | MP4, MKV, MOV, AVI, WEBM, GIF; estrazione MP3/WAV |
| Testo/Markdown | TXT, MD, MARKDOWN, LOG | TXT, DOCX, PDF, HTML, EPUB |
| Word | DOCX | TXT/HTML; PDF, ODT, RTF, EPUB tramite LibreOffice |
| Documenti Office | DOC, ODT, RTF | PDF, DOCX, ODT, RTF, TXT, EPUB tramite LibreOffice |
| Tabelle | CSV, TSV, JSON tabellare | CSV, TSV, XLSX, JSON |
| Excel | XLSX | CSV, TSV, JSON, XLSX; ODS/PDF tramite LibreOffice |
| Altri fogli | XLS, ODS | XLSX, ODS, PDF tramite LibreOffice |
| Presentazioni | PPT, PPTX, ODP | PPTX, ODP, PDF tramite LibreOffice |
| PDF | PDF | TXT, DOCX, HTML, EPUB; tutte le pagine in immagini PNG/JPG dentro uno ZIP |
| E-book | EPUB | TXT, DOCX, PDF, HTML, EPUB (testo) |
| Pagine web | HTML, HTM, XHTML | TXT, DOCX, PDF, HTML, EPUB (testo) |
| Archivi | 7Z, ZIP, TAR, TAR.GZ/TGZ, TAR.BZ2/TBZ2, TAR.XZ/TXZ | ZIP, 7Z, TAR, TAR.GZ, TAR.BZ2, TAR.XZ |
| Sottotitoli | SRT, VTT | SRT, VTT |

## Programmi esterni
Le librerie Python vengono installate da Installa.bat. Questi programmi
esterni vanno installati separatamente per le rispettive funzioni:
- **FFmpeg e ffprobe** nel PATH: audio/video. I codec disponibili dipendono dalla build.
- **LibreOffice**: conversioni Office. L'app cerca il PATH, i percorsi Windows
  standard o la cartella Applicazioni su macOS. Per un percorso diverso,
  imposta `LIBREOFFICE_CMD` all'eseguibile.
- **Tesseract OCR**: lettura del testo da foto/scansioni. Installa anche le
  lingue ita/eng che selezioni nell'app. Percorso Windows standard:
  `C:/Program Files/Tesseract-OCR/tesseract.exe`; alternativa: PATH o
  variabile `TESSERACT_CMD`.

## Uso e nuove funzioni 2.0
Carica file o usa **Cartella** per importarli ricorsivamente. Seleziona le righe
con Ctrl/Shift. Scegli il formato comune oppure attiva **Formato diverso per
ogni file** e usa i menu nella coda. Con **Conserva sottocartelle importate**,
l'uscita riproduce le sottocartelle della cartella importata.

**Preset**: Riduci dimensione, Alta qualità, Solo audio, Immagini per il web.
**Impostazioni avanzate** contiene taglio in secondi, peso video indicativo,
riduzione del rumore video, metadati, ritaglio immagini, filigrana di testo/logo,
rinomina e impostazioni OCR. Una fine pari a zero significa fino alla fine del
file. La qualità dipende dal formato; PNG e BMP non usano la qualità JPEG.
La sequenza immagini è ritaglio → ridimensionamento → filigrana → conversione.
**Salva come sequenza** memorizza opzioni e formato; scegli il nome dal menu
per riutilizzarli. I percorsi dei loghi devono restare disponibili.

**Strumenti** include:
- Unione di PDF nell'ordine della lista, modificabile con Su/Giù o trascinamento.
- Divisione delle pagine selezionate in PDF singoli, raccolti in uno ZIP.
- Rotazione delle sole pagine indicate, conservando le altre.
- Compressione PDF senza perdita dei flussi delle pagine indicate
  (campo vuoto: tutte; se selezioni pagine, l'uscita contiene solo quelle).
- PDF ricercabile con OCR: conserva la vista delle pagine rasterizzata ai DPI
  scelti e aggiunge testo selezionabile. Richiede Tesseract e la lingua scelta.
- Più immagini in un PDF unico (primo fotogramma di ciascun file).
- Cambio contenitore video senza ricodifica (remux), se i codec sono compatibili.
- Sostituzione dell'audio: prima il video, poi l'audio; il video è copiato,
  l'audio convertito in AAC e il risultato termina con la traccia più breve.

**Confronta** esegue una vera conversione temporanea della singola immagine
selezionata, mostra prima/dopo e i pesi reali. Puoi cambiare la qualità
nell'anteprima; per usarla nel risultato definitivo impostala anche nel pannello
principale. **Info** legge dimensioni/EXIF delle immagini, tracce e durata dei
media, pagine e metadati PDF. Per altri file mostra tipo, percorso e peso.
**Cronologia** conserva le ultime 1000 operazioni tra gli avvii, permette di
aprire il risultato e ripetere l'operazione con gli originali ancora disponibili.
Cronologia e sequenze si trovano nei dati locali dell'app, fuori dal progetto.

**Sorveglia cartella** converte i nuovi file mentre l'app è aperta. Scegli una
cartella sorgente e un'uscita esterna alla sorgente. Le impostazioni vengono
copiate all'avvio della sorveglianza; di norma il formato è quello predefinito
per categoria, oppure quello della sequenza salvata se compatibile.
I file già presenti non sono convertiti; i nuovi file vengono considerati
pronti dopo due controlli di dimensione/data uguali a distanza di due secondi.
Per copie con pause lunghe, deposita prima fuori e sposta il file completo
nella cartella. La sorveglianza attende il termine della coda manuale.

**Ferma coda** interrompe anche il file in corso, termina il processo di lavoro
e i programmi da lui avviati, elimina l'uscita parziale e i temporanei del job,
poi annulla i successivi. Le conversioni già riuscite restano disponibili.
L'avanzamento FFmpeg usa i tempi realmente codificati e stima il tempo
rimanente; immagini/PDF/archivi mostrano il progresso per fotogramma, pagina o
voce. Durante fasi senza misure disponibili la barra è indeterminata.
**Risultati** apre la cartella d'uscita; doppio clic sullo stato apre i dettagli.

Gli originali restano intatti. I nomi predefiniti sono nome_convertito.ext,
con un contatore se esistono già. La rinomina supporta {name}, {n}, {n:03d},
{n:04d}, {n:05d}; resta il suffisso _convertito per distinguere i risultati.
Il campo metadati riguarda immagini e audio/video: rimuove EXIF e metadati
copiati oppure conserva quelli compatibili. Non rimuove informazioni visibili
nelle immagini e non è uno strumento generale di anonimizzazione dei documenti.

## Dettagli e limiti reali
- Il peso video richiesto imposta un bitrate medio stimato: non garantisce un
  limite esatto. Anche la compressione PDF può produrre un file più grande.
- RAW usa LibRaw tramite rawpy: estensione riconosciuta non significa che ogni
  modello di fotocamera sia supportato. Prova reale inclusa con DNG sintetico;
  i file delle singole fotocamere vanno verificati.
- Non sono inclusi installer dei programmi esterni, modelli OCR o codec aggiuntivi.
- Non ogni formato può essere trasformato in qualsiasi altro. Il registro
  in engine.py indica le coppie implementate. RAR, CAD, eseguibili e formati proprietari non inclusi nella tabella non sono supportati.
- PDF → Word/HTML/EPUB e HTML/EPUB → documenti sono conversioni del testo,
  senza ricostruire grafica, immagini o impaginazione originali.
  L'OCR può sbagliare: controlla il testo riconosciuto, soprattutto la scrittura a mano.
- PDF → immagini salva ogni pagina numerata in .png.zip/.jpg.zip. PDF
  protetti da password richiedono una copia sbloccata.
- Tabelle: CSV/TSV devono essere UTF-8; CSV riconosce virgola, punto e
  virgola, tabulazione e barra verticale. I numeri CSV restano stringhe,
  così codici come 001 non perdono gli zeri iniziali.
- XLSX → dati usa solo il foglio scelto, numerato da 1. Non esporta stili
  o grafici; conserva le formule come testo, senza calcolarle. Le conversioni
  Office con LibreOffice coinvolgono invece il documento completo.
- JSON deve essere una lista di righe o di oggetti con valori semplici.
  L'output JSON è sempre una lista di righe. JSON annidati vengono rifiutati.
- Le animazioni vengono conservate quando l'output è GIF/WEBP; TIFF conserva
  più frame/pagine. Gli altri output immagine usano il primo fotogramma.
  SVG viene rasterizzato e non produce un nuovo file vettoriale.
- Testo → HTML conserva il testo; Markdown → HTML rende titoli, tabelle e
  codice. L'EPUB generato è un e-book semplice, senza copertina.
  L'estrazione EPUB segue l'ordine dei capitoli nel libro; EPUB protetti
  o non UTF-8 non sono supportati.
- Gli archivi cambiano contenitore, senza cambiare i formati dei file
  interni. File/cartelle sono mantenuti; permessi/date possono cambiare.
  Link, file speciali, nomi duplicati e cifratura non sono supportati.
  Limiti: 100000 elementi e 2 GiB totali non compressi.
- SRT/VTT: conversione di sottotitoli testuali UTF-8. Commenti, stili e
  regioni VTT non vengono esportati. La conversione rifiuta impostazioni
  di posizione VTT quando l'output SRT non può rappresentarle.
- I PDF da testo usano Helvetica: alcuni caratteri Unicode non sono coperti.
  Per layout Office complessi, controlla font, grafici e salti di pagina.

## Componenti e documentazione
- https://ffmpeg.org/documentation.html
- https://help.libreoffice.org/latest/en-US/text/shared/guide/convertfilters.html
- https://tesseract-ocr.github.io/tessdoc/Installation.html
- https://pillow-heif.readthedocs.io/en/latest/pillow-plugin.html
- https://openpyxl.readthedocs.io/en/stable/tutorial.html
- https://pymupdf.readthedocs.io/en/latest/about.html (licenza del motore PDF)
- https://pyinstaller.org/en/stable/usage.html


## Interfaccia
- Categorie laterali che filtrano la coda: tutti i file, immagini, audio/video,
  documenti e archivi. Su finestre compatte le categorie sono in un menu.
- Ricerca per nome: i file nascosti non entrano nella selezione da convertire.
- Impostazioni a destra con anteprima delle immagini leggibili da Qt;
  per altri formati viene mostrata l'icona della categoria.
- Tema chiaro/scuro con scelta ricordata tra gli avvii.
- Stati con testo e icone, contatori della sessione e pulsanti distinti.
- Opzioni scorrevoli e coda scorrevole: funzionano anche a 960×720.
- Ctrl+O aggiunge file; Ctrl+Invio avvia la conversione; Canc nella tabella
  rimuove le righe selezionate. La zona di trascinamento funziona anche da tastiera.

Le conversioni delle versioni precedenti restano disponibili.
L'interfaccia usa Qt Widgets/PyQt6, un tema QSS e icone SVG originali.
Gli SVG dei controlli sono inclusi nella cartella assets e nello script EXE.
