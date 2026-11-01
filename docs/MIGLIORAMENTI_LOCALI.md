# Miglioramenti locali — 1 novembre 2026

Revisione della versione 2.1.2, non ancora pubblicata come nuova release.

## Novità

- **Riprova** nella barra della coda: ripete errori e annullamenti dell'ultima
  elaborazione mantenendo le impostazioni e le destinazioni originali. I file
  riusciti non vengono ripetuti. Se gli originali mancano, mostra quali ripristinare.
- Il motore rifiuta destinazioni coincidenti con l'originale (anche attraverso
  collegamenti) e destinazioni che contengono già dati.
- Controllo anticipato degli originali mancanti e creazione delle cartelle di
  destinazione; i nomi dei risultati non possono includere separatori di percorso.
- Cronologia: recupero delle voci valide se il JSON contiene dati incompatibili;
  salvataggio atomico con file temporanei univoci e pulizia in caso di errore.
- Sorveglianza: rimozione dei file spariti dallo stato interno, riconoscimento
  dei file ricreati dopo una scansione che ne ha rilevato l'eliminazione e controllo
  della presenza della cartella iniziale.
- La coda sorvegliata ignora i file spariti tra il rilevamento e l'importazione.
- CSV Windows: rilevamento corretto del separatore anche con CRLF, virgolette e
  punto e virgola all'interno delle celle, conservando le righe interne ai valori.
- Processi: un lavoro già annullato non avvia un processo; un errore di avvio
  libera la destinazione riservata e le cartelle temporanee.

## Verifica

I test di regressione aggiunti sono in `tests/test_reliability.py` e
`tests/test_gui.py`. Per eseguire la suite in PowerShell dalla cartella sorgenti:

```powershell
$env:PYTHONPATH = "$PWD/app;$PWD/tools"
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Le prove di conversione multimediale, Office e OCR richiedono i relativi
componenti esterni. Questa revisione non implica che il nuovo installer EXE
sia stato compilato o verificato.

### Risultati locali

- **21 test mirati superati**: tutti i 10 test di affidabilità, tutti i 9 test
  dell'interfaccia e i 2 test CSV/Unicode coinvolti nella correzione.
- Altri **5 test del launcher superati** in un'esecuzione separata: 26 verifiche
  mirate superate complessivamente.
- Anteprima della finestra controllata visivamente con rendering Qt.
- La suite completa è stata tentata, ma non completata: FFmpeg locale è una
  build del 2013 senza il filtro testsrc2 e Tesseract non è disponibile.
  La prova LibreOffice per documenti e fogli è passata; quella per presentazioni
  è stata saltata perché manca python-pptx, necessario alla fixture del test.
  La suite è stata interrotta durante i test del launcher; i risultati parziali
  non equivalgono a una suite completa superata. Audio/video e OCR restano da verificare.
- Corretto anche un test che leggeva JSON UTF-8 usando la codifica predefinita
  di Windows, producendo un falso errore sui caratteri accentati.
- Nessuna pubblicazione GitHub e nessun installer EXE nuovo.

Comando della verifica mirata (aggiungere `tests` a PYTHONPATH):

```powershell
$env:PYTHONPATH = "$PWD/app;$PWD/tools;$PWD/tests"
.\.venv\Scripts\python.exe -m unittest test_reliability test_gui test_extended.ExtendedTests.test_csv_excel_json test_extended.ExtendedTests.test_records_union_and_unicode -v
```
