# Verifiche 2.1

**42 test superati**, nessun errore e nessun test saltato.
Suite completa sul runtime Linux, Python 3.12.14, in 96,260 secondi.
Il log completo è incluso in LOG_TEST_2.1.txt. Dopo l'ultima rifinitura del tema,
gli 8 test dell'interfaccia sono stati rieseguiti con esito positivo.

Comando: `PYTHONPATH=app QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v`.

## Cosa è stato verificato

- Le 33 prove di conversione/interfaccia della 2.0, conservate nella struttura nuova:
  audio/video, immagini, RAW DNG, PDF/OCR, archivi 7Z, tabelle, documenti,
  LibreOffice, sottotitoli, filigrane, annullamento, cronologia e cartelle.
- Otto prove di distribuzione: versione/prodotto, HTTPS e redirect autorizzati,
  lettura del manifest, dimensione massima, SHA256, download integro,
  download modificato/incompleto/troppo grande, annullamento e pulizia temporanei,
  generazione manifest da un file reale, controllo dei modelli e archivio sorgenti.
  Le prove di download usano risposte simulate: nessun setup è stato eseguito.
- Una prova aggiuntiva della finestra aggiornamenti: vero thread Qt,
  controllo e download simulati, note mostrate e file verificato.
- Rendering delle finestre reali dell'app, temi scuro/chiaro e vista compatta,
  con una conversione WEBP reale. Rendering e controllo visivo della finestra
  Aggiornamenti dopo la rifinitura del tema.
- Prova aggiuntiva OCR reale con i modelli italiano+inglese inclusi:
  riconoscimento di CIAO CONVERTITORE, senza usare i modelli di sistema.
- Validazione della configurazione, sintassi Python, modelli e licenza OCR
  confrontati con le dimensioni/hash della provenienza registrata.
- YAML e permessi del workflow: sola lettura dei contenuti, nessuna pubblicazione
  automatica. SHA delle Actions risolti dalle release ufficiali correnti.
- Identificativi FFmpeg/LibreOffice/Tesseract verificati nei manifest Microsoft
  WinGet; codice WinGet per versione già aggiornata verificato nei sorgenti Microsoft.

## Versioni del runtime di prova
- PyQt6: 6.11.0
- Pillow: 12.3.0
- pypdf: 6.10.0
- PyMuPDF: 1.26.6
- py7zr: 1.1.3
- rawpy: 0.27.1

## Cosa manca prima della pubblicazione

Questo ambiente è Linux: **PowerShell/Inno/Setup.exe non sono stati eseguiti
su Windows**. Sono stati forniti script e workflow per farlo; il workflow non
è ancora stato eseguito in un repository. La compilazione Windows e le prove
end-to-end di installazione, componenti esterni, UAC, aggiornamento e disinstallazione
restano necessarie. La verifica sintattica PowerShell viene eseguita nel workflow.

Il canale aggiornamenti non è attivo: manca il repository/sito dell'autore.
Non è stata scelta una licenza per il codice dell'utente. La guida alla
pubblicazione spiega le condizioni delle dipendenze e i passi da completare.
Modelli OCR inclusi: inglese/italiano, tessdata_fast ufficiale con commit fisso
e hash registrati. RAW è stato provato con DNG sintetico, non con tutte le fotocamere.
