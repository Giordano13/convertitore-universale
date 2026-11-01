# Pubblicazione e aggiornamenti

## Percorso consigliato: GitHub Releases

1. Crea un repository per il progetto. Carica il contenuto di questa cartella
   come radice del repository, senza `.venv`, build, dist e output.
2. Scegli la licenza del tuo progetto prima della distribuzione pubblica.
   Leggi la sezione licenze più sotto; nessuna licenza è stata scelta al tuo posto.
3. Configura il canale prima di compilare:
   `python tools/configure_release.py --github Giordano13/convertitore-universale`.
4. Per compilare localmente, esegui CreaSetup.bat su Windows.
   In alternativa, su GitHub apri Actions → Crea setup Windows (bozza) → Run workflow.
   Il workflow crea artifact privati al repository da scaricare e verificare;
   non pubblica automaticamente alcuna release.
5. Prova il setup su Windows: Base, Completa, Personalizzata, errori/offline,
   collegamenti, primo avvio, conversioni reali, disinstallazione e reinstallazione.
6. Crea una release **bozza** con tag `v2.1.2`. Allega setup, sorgenti e hash.
   Se usi il workflow, l'artifact include anche update.json già pronto.
7. Se compili localmente, genera update.json con i dati dell'EXE reale:

   `python tools/make_manifest.py --installer output/ConvertitoreUniversale-Setup-2.1.2.exe --download-url https://github.com/Giordano13/convertitore-universale/releases/download/v2.1.2/ConvertitoreUniversale-Setup-2.1.2.exe --notes "Prima release pubblica"`

8. Verifica tutti gli allegati e poi pubblica la release. **Solo dopo** che l'EXE
   è scaricabile, copia l'update.json appena generato in `release/update.json`
   sul ramo `main`. È il canale usato dalle app installate.

Il canale GitHub legge update.json da raw.githubusercontent.com. I download
possono essere reindirizzati soltanto ai domini GitHub autorizzati nella
configurazione. Un sito proprio deve usare HTTPS; configura il manifest con
`--manifest-url` e gli eventuali `--download-host` necessari. Non mettere token
GitHub, password o certificati privati nella configurazione o nell'app.

## Pubblicare una versione successiva

- Cambia VERSION in `app/version.py`, per esempio 2.1.1. Mantieni AppId.
- Ricompila, esegui i test e prova l'aggiornamento da una versione precedente.
- Crea la release con tag corrispondente, usando i nuovi file EXE/sorgenti/hash.
- Genera un nuovo update.json dagli stessi byte dell'EXE pubblicato.
- Pubblica il setup, poi aggiorna release/update.json sul canale.

Nessun aggiornamento parte in silenzio. L'utente sceglie se controllare
all'avvio, scaricare e installare. Una versione uguale o inferiore non viene
proposta come aggiornamento. SHA256 controlla integrità e corrispondenza con
il manifest; l'autenticità dipende dal canale HTTPS che controlli. Non è una
firma digitale dell'autore. Per distribuire meglio, firma l'EXE con un
certificato Authenticode: la chiave privata resta fuori dal repository. Non è
incluso un certificato, e non si promette l'assenza di avvisi SmartScreen.

## Licenze della pubblicazione

Il progetto usa PyQt6 (GPLv3 oppure licenza commerciale) e PyMuPDF/MuPDF
(AGPL oppure licenza commerciale). Un progetto chiuso non può semplicemente
ignorare queste condizioni. Per una distribuzione open source, valuta una
licenza compatibile, per esempio AGPLv3 per l'app con le dipendenze attuali;
prima di pubblicare, scegli la licenza del tuo codice e includi il testo
completo, gli avvisi e i sorgenti corrispondenti richiesti dalle dipendenze.
Il fatto che l'app sia gratuita non elimina gli obblighi delle licenze.

Il builder raccoglie le versioni e i testi di licenza presenti nell'ambiente
isolato in build/third-party e li inserisce nell'installer. Questo aiuta la
preparazione, ma non sostituisce la verifica delle condizioni né produce
automaticamente tutti i sorgenti delle librerie native. Conserva le versioni
esatte, i sorgenti corrispondenti e le informazioni di build richieste.

FFmpeg, LibreOffice e Tesseract sono scaricati tramite WinGet, senza inserirne
i binari nel nostro archivio. Se in futuro li includi nel setup offline,
verifica gli obblighi di redistribuzione delle build effettive. I modelli OCR
inclusi provengono da tessdata_fast, commit indicato nel provenance.json,
sotto Apache-2.0; il testo completo della licenza è incluso.

Fonti ufficiali consultate:
- https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- https://jrsoftware.org/ishelp/topic_componentssection.htm
- https://jrsoftware.org/ishelp/topic_setup_appid.htm
- https://learn.microsoft.com/en-us/windows/package-manager/winget/install
- https://www.riverbankcomputing.com/software/pyqt/intro
- https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright
- https://ffmpeg.org/legal.html
- https://github.com/tesseract-ocr/tessdata_fast

## Prove Windows richieste prima della release

Le prove Python/Linux sono registrate in VERIFICHE_2.1.md. Il setup EXE non è
stato compilato o eseguito in questo ambiente Linux. Il workflow è fornito
come percorso di compilazione Windows e va ancora eseguito nel repository.
Esegui almeno: installazione nuova, installazione sopra una versione precedente,
componenti non selezionati, WinGet assente, rete interrotta, UAC negato,
OCR italiano/inglese e mantenimento di cronologia e sequenze dopo aggiornamento.
