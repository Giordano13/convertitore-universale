# Convertitore Universale

Versione 2.1.2 per Windows, in anteprima. Progetto di Giordano13.

Conversione di immagini, audio/video, documenti, PDF, tabelle, archivi e OCR. Le combinazioni disponibili dipendono dal formato e dai componenti installati.

## Scaricare e provare

Scarica [Convertitore_GitHub.zip](./Convertitore_GitHub.zip), estrai tutto in una cartella e apri **Setup.vbs**. Scegli i componenti e completa il wizard; poi apri **Avvia.vbs**. I file .vbs avviano le finestre grafiche senza mantenere una console aperta.

Il setup richiede Internet. FFmpeg, LibreOffice e Tesseract vengono installati tramite WinGet; i programmi gia presenti vengono mantenuti. L app base usa Python 3.11-3.13; se necessario il wizard puo installare Python 3.12.

## Installer Windows

Il workflow **Crea setup Windows (bozza)** estrae i sorgenti e compila l installer EXE su Windows. I risultati sono scaricabili dagli artifact della relativa esecuzione. La release EXE sara pubblicata dopo la compilazione e la verifica del setup.

## Sorgenti e aggiornamenti

Lo ZIP contiene tutti i sorgenti, i test, la documentazione, il setup e i modelli OCR con relativa provenienza e licenza. Gli aggiornamenti sono predisposti per questo repository. Il canale diventera operativo quando verra pubblicato il manifesto della prima release.

## Licenza

La licenza del codice del progetto deve ancora essere scelta dall autore. Le dipendenze conservano le proprie licenze; nello ZIP sono incluse le informazioni per la distribuzione. La pubblicazione di questo repository non assegna automaticamente una licenza al codice.
