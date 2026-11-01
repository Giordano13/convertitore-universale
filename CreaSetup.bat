@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Esegui prima Setup.bat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" tools\build_release.py
if errorlevel 1 (
    echo Compilazione non completata. Leggi il messaggio sopra.
    pause
    exit /b 1
)
echo Pronto: apri la cartella output.
pause
