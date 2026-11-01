#ifndef AppVersion
  #define AppVersion "2.1.2"
#endif
#define AppRoot ".."
[Setup]
AppId={{993E4741-9230-4BFE-AB3B-4A559A5BC8BA}
AppName=Convertitore Universale
AppVersion={#AppVersion}
AppPublisher=Giordano Maffione
DefaultDirName={localappdata}\Programs\ConvertitoreUniversale
DefaultGroupName=Convertitore Universale
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
UsePreviousAppDir=yes
UsePreviousTasks=yes
UsePreviousSetupType=yes
CloseApplications=yes
RestartApplications=no
AppMutex=ConvertitoreUniversaleDesktop
OutputDir=..\output
OutputBaseFilename=ConvertitoreUniversale-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Convertitore.exe
SetupLogging=yes
[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
[Types]
Name: "full"; Description: "Completa: tutte le conversioni"
Name: "basic"; Description: "Base: immagini, PDF, testo e archivi"
Name: "custom"; Description: "Personalizzata"; Flags: iscustom
[Components]
Name: "core"; Description: "Convertitore Universale (obbligatorio)"; Types: full basic custom; Flags: fixed
Name: "ffmpeg"; Description: "Audio e video - installa FFmpeg con WinGet (Internet)"; Types: full
Name: "office"; Description: "Word, Excel e presentazioni - installa LibreOffice (Internet)"; Types: full
Name: "ocr"; Description: "OCR da immagini/scansioni - installa Tesseract (Internet)"; Types: full
Name: "ocr\italian"; Description: "Lingua OCR italiana (modello incluso)"; Types: full
[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; Flags: unchecked
Name: "componentagreements"; Description: "Accetto i termini dei componenti selezionati e della sorgente WinGet"; Components: ffmpeg or office or ocr; Flags: unchecked
[Files]
Source: "..\LICENSE"; DestDir: "{app}\licenses"; Flags: ignoreversion; Components: core
Source: "..\dist\Convertitore\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: core
Source: "install_components.ps1"; DestDir: "{app}\maintenance"; Flags: ignoreversion; Components: core
Source: "payload\tessdata\*"; DestDir: "{app}\maintenance\models"; Flags: ignoreversion; Components: core
Source: "..\release\config.json"; DestDir: "{app}\release"; Flags: ignoreversion; Components: core
Source: "..\release\support.json"; DestDir: "{app}\release"; Flags: ignoreversion; Components: core
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: core
Source: "..\build\third-party\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: core
[Icons]
Name: "{group}\Convertitore Universale"; Filename: "{app}\Convertitore.exe"
Name: "{group}\Disinstalla Convertitore"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Convertitore Universale"; Filename: "{app}\Convertitore.exe"; Tasks: desktopicon
[UninstallDelete]
Type: files; Name: "{app}\tessdata\eng.traineddata"
Type: files; Name: "{app}\tessdata\ita.traineddata"
Type: files; Name: "{app}\tessdata\LICENSE"
Type: files; Name: "{app}\tessdata\provenance.json"
[Run]
Filename: "{app}\Convertitore.exe"; Description: "Avvia Convertitore Universale"; Flags: nowait postinstall skipifsilent
[Code]
function HasOptionalComponents: Boolean;
begin
  Result := WizardIsComponentSelected('ffmpeg') or WizardIsComponentSelected('office') or WizardIsComponentSelected('ocr');
end;
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectTasks) and HasOptionalComponents and not WizardIsTaskSelected('componentagreements') then begin
    MsgBox('Per installare i componenti esterni selezionati, accetta i relativi termini. In alternativa torna indietro e scegli la versione Base.', mbInformation, MB_OK);
    Result := False;
  end;
end;
procedure CurStepChanged(CurStep: TSetupStep);
var
  Components, Params: String;
  ResultCode: Integer;
begin
  if (CurStep = ssPostInstall) and HasOptionalComponents then begin
    if not WizardIsTaskSelected('componentagreements') then begin
      MsgBox('Componenti esterni saltati: termini non accettati. Puoi aggiungerli da Gestisci componenti.', mbInformation, MB_OK);
      Exit;
    end;
    Components := '';
    if WizardIsComponentSelected('ffmpeg') then Components := Components + 'ffmpeg,';
    if WizardIsComponentSelected('office') then Components := Components + 'office,';
    if WizardIsComponentSelected('ocr') then Components := Components + 'ocr,';
    if WizardIsComponentSelected('ocr\italian') then Components := Components + 'italian,';
    Params := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\maintenance\install_components.ps1') + '" -Components "' + Components + '" -ModelsRoot "' + ExpandConstant('{app}\maintenance\models') + '" -DataRoot "' + ExpandConstant('{app}\tessdata') + '"';
    WizardForm.StatusLabel.Caption := 'Installazione componenti selezionati...';
    if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), Params, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      MsgBox('Impossibile avviare i componenti. Puoi riprovare dal pulsante Componenti dell''app.', mbInformation, MB_OK)
    else if ResultCode <> 0 then
      MsgBox('App installata, ma alcuni componenti non sono disponibili. Apri Componenti per verificare o riprovare. Il log si trova nei dati locali dell''app.', mbInformation, MB_OK);
  end;
end;
