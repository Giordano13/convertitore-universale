# Versione 2.1.1: wizard e avvio senza console

Setup.vbs apre il wizard Windows con schermata di benvenuto, scelta dei componenti, installazione e risultato. Il lavoro viene eseguito da un processo nascosto, mentre la finestra mostra le fasi e il registro. La barra indica attivita, non una percentuale inventata. In caso di errore sono disponibili Riprova, Copia dettagli e Apri log.

Avvia.vbs avvia il programma senza console e conserva stdout e stderr in un file. Un errore di avvio mostra una finestra con il percorso del registro. I file Setup.bat e Avvia.bat delegano ai nuovi avvii e terminano subito. Per evitare anche il breve passaggio della console, usa direttamente i file .vbs.

La ricerca di Python prova 3.12, 3.13 e 3.11, senza interrompersi se un interprete non e compatibile. Gli errori su stderr delle installazioni non vengono confusi con un fallimento: si controlla il codice di uscita e si conserva tutto il traceback. Sono stati nascosti anche i processi di conversione e gestione dei componenti su Windows.

## Verifiche eseguite

- 5 test dell avvio: percorsi con spazi, traceback completo, eseguibile mancante, interprete senza console e gestione dei flussi di log.
- 8 test della distribuzione e degli aggiornamenti.
- 8 test dell interfaccia Qt, comprese conversione e annullamento.
- Parser PowerShell 7.6.6: sintassi valida per i tre script di setup.
- Prova delle funzioni PowerShell: interprete valido, percorso inesistente, acquisizione stderr e codice di uscita non zero con traceback.
- Verifica di struttura, modelli OCR e sorgenti; controllo integrita ZIP.

Queste prove sono state eseguite su Linux. Il wizard WinForms, VBScript, WinGet, UAC e l installazione completa devono essere provati su Windows. Il workflow incluso controlla anche la sintassi e le funzioni con Windows PowerShell. Questo ZIP contiene il progetto; il Setup.exe per la distribuzione si compila su Windows con CreaSetup.bat.

## Se il setup fallisce

Premi Copia dettagli e invia il testo completo. La sola riga "Traceback (most recent call last):" non identifica la causa. I registri sono in %LOCALAPPDATA%\ConvertitoreUniversale\logs. Non cancellare la vecchia cartella del progetto: estrai questa versione in una cartella separata per provarla.
