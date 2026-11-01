# Novità 2.0

Tutte le funzioni aggiunte sono collegate all'interfaccia. Le conversioni
richiedono i programmi esterni indicati nel README quando applicabili.

| Funzione | Dove usarla / comportamento |
| --- | --- |
| Avanzamento per file e tempo rimanente | Barra: FFmpeg usa i tempi codificati; altri motori contano pagine/frame/voci o mostrano una fase indeterminata |
| Annullamento del file in corso | Ferma coda: termina il processo isolato e i suoi programmi; elimina risultato parziale e temporanei |
| Preset | Menu Preset / sequenza: riduzione, alta qualità, solo audio, immagini web |
| Unire, dividere, ruotare, comprimere PDF | Strumenti; selezione pagine 1-3,5; divisione in ZIP di PDF |
| Cronologia persistente | Cronologia; risultati apribili e operazioni ripetibili |
| Qualità / dimensione | Qualità immagine/video, bitrate audio, peso video indicativo; Confronta mostra pesi reali |
| Installer Windows | Crea_EXE.bat, Crea_Installer.bat, installer.iss; compilazione Windows ancora da verificare |
| Prima / dopo reale | Confronta su una singola immagine; qualità regolabile nell'anteprima |
| Taglio audio/video | Impostazioni avanzate: inizio/fine in secondi |
| Cartelle e sottocartelle | Cartella o trascinamento; opzione per preservare la struttura relativa |
| Formato diverso per ogni file | Casella nel pannello e menu per riga |
| PDF scansionato ricercabile | Strumenti, con Tesseract, lingua e DPI |
| Più immagini in un PDF | Strumenti; ordine modificabile |
| Metadati | Conservazione/rimozione EXIF compatibili e metadati audio/video; Info per ispezione |
| Archivi 7Z | Menu archivi; repack tramite py7zr, mantenendo i contenuti |
| Foto RAW | Sviluppo tramite rawpy/LibRaw, con bilanciamento camera |
| Cartella sorvegliata | Sorveglia cartella; solo nuovi file, mentre l'app è aperta |
| Remux | Strumenti: cambio contenitore senza ricodifica se le tracce sono compatibili |
| Sostituzione audio | Strumenti: video seguito da nuova traccia audio |
| Filigrana testo/logo | Impostazioni avanzate; viene applicata alle immagini del batch |
| Rinomina automatica | Impostazioni avanzate: {name}, {n}, {n:03d}, {n:04d}, {n:05d} |
| Sequenze salvate | Salva come sequenza: ritaglio → resize → filigrana → conversione, opzioni e formato riutilizzabili |
| Riduzione rumore video | Impostazioni avanzate: filtro hqdn3d |

L'app mantiene la grafica scura/chiara, filtri, ricerca, scorciatoie e
anteprime della versione precedente. L'interfaccia compatta nasconde la grande
anteprima per lasciare spazio alle impostazioni. Tutte le operazioni sono
locali; la sorveglianza non è un servizio di sistema in background.

Per i limiti dei formati, metadati, OCR, compressione e build Windows,
consulta README.md. In particolare RAW è stato provato con un DNG sintetico:
non si garantisce compatibilità con ogni fotocamera.
