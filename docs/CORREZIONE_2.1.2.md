# Correzione 2.1.2

Il log ricevuto mostra che Python e tutte le librerie erano installati. WinGet restituiva -1978335135 (0x8A150061, PACKAGE_ALREADY_INSTALLED) per FFmpeg, LibreOffice e Tesseract: il setup lo interpretava erroneamente come un fallimento.

Ora durante l installazione questo risultato significa componente gia presente: il setup prosegue, inclusa la copia e verifica delle lingue OCR. Gli altri codici di errore rimangono errori. Gli aggiornamenti mantengono il proprio controllo degli esiti.

Verificate entrambe le rappresentazioni del codice (signed e unsigned), il codice di successo, nessun aggiornamento e veri fallimenti: 9 verifiche PowerShell. Test distribuzione e integrita/estrazione ZIP eseguiti. Installazione completa su Windows da provare.

Per mantenere l ambiente Python gia preparato puoi estrarre il nuovo ZIP e copiare i suoi file nella cartella precedente, confermando la sostituzione: la cartella .venv non e inclusa nello ZIP e rimane presente. Poi apri Setup.vbs. In alternativa prova la nuova versione in una cartella separata.

Fonte ufficiale: https://github.com/microsoft/winget-cli/blob/master/doc/windows/package-manager/winget/returnCodes.md
