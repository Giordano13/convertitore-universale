param([string]$Components = '', [switch]$AcceptAgreements)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
function Probe-Python([string]$Exe, [string]$Prefix = '') {
    try {
        $info = New-Object System.Diagnostics.ProcessStartInfo
        $info.FileName = $Exe
        $info.Arguments = "$Prefix -c `"import sys; print(sys.executable); sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)`""
        $info.UseShellExecute = $false
        $info.CreateNoWindow = $true
        $info.RedirectStandardOutput = $true
        $info.RedirectStandardError = $true
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $info
        [void]$p.Start()
        $out = $p.StandardOutput.ReadToEndAsync()
        $err = $p.StandardError.ReadToEndAsync()
        if (-not $p.WaitForExit(20000)) { $p.Kill(); return $null }
        $result = $out.Result.Trim()
        if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $result)) { return $result }
    } catch { Write-Verbose "Interprete non utilizzabile: $Exe" }
    finally { if ($p) { $p.Dispose() } }
    return $null
}
function Find-Python {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($version in @('-3.12','-3.13','-3.11','-3')) {
            $found = Probe-Python $launcher.Source $version
            if ($found) { return $found }
        }
    }
    foreach ($base in @((Join-Path $env:LOCALAPPDATA 'Programs\Python'), $env:ProgramFiles)) {
        foreach ($version in @('Python312','Python313','Python311')) {
            $candidate = Join-Path $base "$version\python.exe"
            if (Test-Path $candidate) {
                $found = Probe-Python $candidate
                if ($found) { return $found }
            }
        }
    }
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notlike '*\WindowsApps\*') { return (Probe-Python $command.Source) }
    return $null
}
function Run-Command([string]$Exe, [string[]]$CommandArgs) {
    # Windows PowerShell 5.1 treats native stderr as an error record.
    # Keep all diagnostics and decide success using the actual exit code.
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Exe @CommandArgs 2>&1 | ForEach-Object { Write-Output "$_" }
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $oldPreference }
    if ($code -ne 0) { throw "Comando non riuscito (codice $code): $Exe $($CommandArgs -join ' ')" }
}
try {
    Write-Output '[FASE] Ricerca di Python compatibile (3.11 - 3.13)'
    $python = Find-Python
    if (-not $python) {
        if (-not $AcceptAgreements) { throw 'Installa Python 3.12 oppure accetta i termini per installarlo automaticamente.' }
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (-not $winget) { throw 'WinGet assente: installa Python 3.12 da python.org e riprova.' }
        Write-Output '[FASE] Installazione di Python 3.12'
        Run-Command $winget.Source @('install','--id','Python.Python.3.12','--exact','--source','winget','--accept-source-agreements','--accept-package-agreements','--disable-interactivity')
        $python = Find-Python
        if (-not $python) { throw 'Python non trovato dopo l installazione. Chiudi e riapri il wizard.' }
    }
    Write-Output "Python: $python"
    $venv = Join-Path $root '.venv'
    $venvPython = Join-Path $venv 'Scripts\python.exe'
    Write-Output '[FASE] Preparazione ambiente del programma'
    if (-not (Test-Path $venvPython)) { Run-Command $python @('-m','venv',$venv) }
    if (-not (Probe-Python $venvPython)) { throw 'Ambiente .venv incompatibile o danneggiato. Rinomina la cartella .venv e riprova.' }
    Write-Output '[FASE] Installazione delle librerie (puo richiedere alcuni minuti)'
    Run-Command $venvPython @('-m','pip','install','-r',(Join-Path $root 'requirements.txt'))
    if ($Components) {
        Write-Output '[FASE] Installazione dei componenti selezionati'
        Run-Command (Join-Path $PSHOME 'powershell.exe') @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $root 'installer\install_components.ps1'),'-Components',$Components,'-ModelsRoot',(Join-Path $root 'installer\payload\tessdata'))
    }
    Write-Output '[FASE] Setup completato. Puoi avviare il convertitore.'
    exit 0
} catch {
    Write-Output ($_ | Format-List * -Force | Out-String)
    Write-Output $_.ScriptStackTrace
    exit 1
}
