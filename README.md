# Convertitore Universale

Versione 2.1.2 per Windows, in anteprima. Progetto di Giordano13.

Conversione di immagini, audio/video, documenti, PDF, tabelle, archivi e OCR. Le combinazioni disponibili dipendono dal formato e dai componenti installati.

## Scaricare e provare

Scarica [Convertitore_GitHub.zip](./Convertitore_GitHub.zip), estrai tutto in una cartella e apri **Setup.vbs**. Scegli i componenti e completa il wizard; poi apri **Avvia.vbs**. I file .vbs avviano le finestre grafiche senza mantenere una console aperta.

Il setup richiede Internet. FFmpeg, LibreOffice e Tesseract vengono installati tramite WinGet; i programmi gia presenti vengono mantenuti. L app base usa Python 3.11-3.13; se necessario il wizard puo installare Python 3.12.

## Installer Windows

Il setup EXE della versione 2.1.2 è disponibile nella [release di anteprima](https://github.com/Giordano13/convertitore-universale/releases/tag/v2.1.2). Scarica **ConvertitoreUniversale-Setup-2.1.2.exe** dagli allegati e avvialo per scegliere i componenti. Non serve estrarre uno ZIP.

La build Windows e i 21 test di interfaccia, distribuzione e avvio sono passati. L’installazione su un PC reale richiede ancora verifica. Il workflow **Crea setup Windows (bozza)** permette di compilare le versioni successive.

## Sorgenti e aggiornamenti

Lo ZIP contiene tutti i sorgenti, i test, la documentazione, il setup e i modelli OCR con relativa provenienza e licenza. Gli aggiornamenti sono predisposti per questo repository. Il canale è attivo tramite `release/update.json`; il programma controlla la versione e verifica dimensione e SHA256 del setup prima di avviarlo.

## Licenza

Il codice del progetto e distribuito con licenza **GNU AGPLv3**. Leggi [LICENSE](./LICENSE). Le dipendenze conservano le proprie licenze; gli avvisi e le informazioni per la distribuzione sono inclusi nei sorgenti e nel setup.

## Sostieni il progetto

Nel programma trovi il pulsante **Sostieni il progetto**. Le donazioni sono volontarie; la pagina donazioni non è ancora disponibile. Puoi già aiutare condividendo il progetto e segnalando problemi su GitHub.

Per collegare la pagina dell’autore, inserire il suo indirizzo HTTPS nel campo `donation_url` di `release/support.json` e ricompilare il setup. Il programma apre il browser solo quando premi il pulsante e non raccoglie dati di pagamento.
