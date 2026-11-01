# Revisione locale: formati, interfaccia e motore nativo

Questa revisione estende i sorgenti 2.1.2. Non è una release pubblicata e non
modifica il manifest degli aggiornamenti online.

## Nuove conversioni

| Tipo | Ingresso aggiunto | Uscita aggiunta |
| --- | --- | --- |
| Immagini | TGA, PPM, PGM, PBM, PCX | TGA, PPM |
| Tabelle | JSONL, NDJSON | JSONL |
| Audio | Opus e AIFF erano già riconosciuti in ingresso | Opus, AIFF |
| Testi/configurazioni | YAML, YML, TOML, INI, CFG, XML | I formati documento già presenti |

JSON Lines esporta una lista JSON per ogni riga della tabella, compresa
l'intestazione. Accetta sia liste sia record con campi diversi e segnala il
numero di riga in caso di errore. I valori JSON annidati non sono tabellari.
Le configurazioni XML/YAML/TOML/INI vengono esportate come testo: non viene
tradotta la loro struttura in un altro linguaggio di configurazione.

Il lettore riconosce UTF-8, UTF-16/32 con BOM e usa Windows-1252 come ripiego
per i file legacy. Altre codifiche richiedono una conversione preventiva.

## Python e C++

Python gestisce interfaccia Qt, coda e adattatori di conversione. Il nuovo
modulo `native/file_hash.cpp` calcola SHA-256 a blocchi con Windows CNG, senza
caricare tutto il file in memoria. Non vengono eseguiti i file selezionati.
Non sono stati aggiunti Java o altri runtime obbligatori.

Il pulsante **SHA-256** calcola l'impronta del file selezionato e permette di
confrontarla con un valore atteso. La DLL è facoltativa nell'avvio dai sorgenti:
se assente o non caricabile, viene usato il calcolo Python. Non viene affermato
un vantaggio di velocità senza un benchmark.

La compilazione richiede Visual Studio Build Tools con C++ x64:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_native.ps1
```

Il processo di build dell'installer compila e include la DLL. Il modulo usa
il runtime C++ statico e le API crittografiche di Windows. Sorgente e binario
sono distribuiti insieme sotto la licenza del progetto.

Riferimenti API: [BCryptCreateHash](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptcreatehash),
[BCryptHashData](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcrypthashdata),
[BCryptFinishHash](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptfinishhash).

## Interfaccia

- Palette petrolio/turchese per il tema scuro e fondo chiaro ad alto contrasto.
- Catalogo **Formati** consultabile per estensione, origine e destinazione.
- Categoria **Tabelle e dati** e filtro per file in attesa, completati ed errori.
- Nelle finestre piccole, più spazio ai nomi dei file; il tipo è nel pannello
  della selezione. Le opzioni scorrono e le azioni di conversione restano visibili.
- Il sostegno al progetto è nelle impostazioni avanzate.

## Bug corretti

- Un FFmpeg obsoleto nel PATH non nasconde più quello compatibile installato
  con WinGet. Un percorso esplicitamente configurato con FFMPEG_CMD/FFPROBE_CMD
  mantiene la precedenza. Il PATH di sistema non viene modificato.
- Le anteprime ripetute usano destinazioni diverse: il controllo contro le
  sovrascritture non blocca più il secondo aggiornamento della qualità.
- La creazione dei PDF ricercabili non dipende dal file di configurazione
  `pdf` di Tesseract, che può mancare nelle cartelle con soli modelli OCR.
- Viene controllato il limite massimo di righe esportabili in Excel.
- La pulizia dopo annullamento ritenta brevemente quando Windows non ha ancora
  rilasciato gli handle del file di FFmpeg; un blocco persistente resta un errore.
- I test OCR trovano anche l'installazione Windows fuori dal PATH e usano
  font disponibili sul sistema.

## Stato delle verifiche

I risultati definitivi sono nel resoconto `VERIFICA_REVISIONE.txt` accanto
a questo documento. Non è stato compilato un nuovo installer EXE né pubblicata
una release su GitHub.
