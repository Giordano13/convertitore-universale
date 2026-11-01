param(
    [string]$Components = '',
    [ValidateSet('install','upgrade')][string]$Action = 'install',
    [string]$ModelsRoot = '',
    [string]$DataRoot = "$env:LOCALAPPDATA\Programs\ConvertitoreUniversale\tessdata"
)
$ErrorActionPreference = 'Stop'
function Test-ComponentExit([int64]$Code, [string]$Operation) {
    # Official WinGet HRESULTs, including signed and unsigned representations.
    if ($Code -eq 0) { return $true }
    if ($Code -in @(-1978335189,2316632107)) { return $true }
    if ($Operation -eq 'install' -and $Code -in @(-1978335135,2316632161)) { return $true }
    return $false
}
$ids = @{ ffmpeg='Gyan.FFmpeg'; office='TheDocumentFoundation.LibreOffice'; ocr='UB-Mannheim.TesseractOCR' }
$selected = @($Components.Split(',') | Where-Object { $_ })
$unknown = @($selected | Where-Object { $_ -notin @('ffmpeg','office','ocr','italian') })
if ($unknown.Count) { throw 'Componente sconosciuto.' }
$logDirectory = Join-Path $env:LOCALAPPDATA 'ConvertitoreUniversale\logs'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$failures = New-Object System.Collections.Generic.List[string]
$log = Join-Path $logDirectory ('componenti-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
Start-Transcript -Path $log -Force | Out-Null
try {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget -and @($selected | Where-Object { $ids.ContainsKey($_) }).Count) {
        throw 'WinGet non disponibile. Installa o aggiorna Installazione app dal Microsoft Store e riprova.'
    }
    foreach ($component in $selected) {
        if (-not $ids.ContainsKey($component)) { continue }
        $id = $ids[$component]
        Write-Host "`n$Action : $id" -ForegroundColor Cyan
        if ($Action -eq 'upgrade') {
            $arguments = @('upgrade','--id',$id,'--exact','--source','winget','--accept-source-agreements','--accept-package-agreements','--disable-interactivity')
        } else {
            $arguments = @('install','--id',$id,'--exact','--source','winget','--accept-source-agreements','--accept-package-agreements','--disable-interactivity','--no-upgrade')
        }
        $oldPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            & $winget.Source @arguments 2>&1 | ForEach-Object { Write-Host "$_" }
            $code = [int64]$LASTEXITCODE
        } finally { $ErrorActionPreference = $oldPreference }
        if ($Action -eq 'install' -and $code -in @(-1978335135,2316632161)) {
            Write-Host "$id gia presente: continuazione del setup." -ForegroundColor Green
        }
        if (-not (Test-ComponentExit $code $Action)) {
            $failures.Add("$id : codice $code")
        }
    }
    if ($ModelsRoot -and (Test-Path (Join-Path $ModelsRoot 'provenance.json'))) {
        $provenance = Get-Content (Join-Path $ModelsRoot 'provenance.json') -Raw | ConvertFrom-Json
        $models = @()
        if ('ocr' -in $selected) { $models += 'eng.traineddata' }
        if ('italian' -in $selected) { $models += 'ita.traineddata' }
        if ($models.Count) {
            New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
            foreach ($model in $models) {
                $source = Join-Path $ModelsRoot $model
                if ((Get-FileHash -Algorithm SHA256 $source).Hash.ToLowerInvariant() -ne $provenance.$model.sha256) { throw "Hash modello non valido: $model" }
                $destination = Join-Path $DataRoot $model
                if ([IO.Path]::GetFullPath($source) -ne [IO.Path]::GetFullPath($destination)) { Copy-Item $source $destination -Force }
            }
            foreach ($notice in @('LICENSE','provenance.json')) {
                $source = Join-Path $ModelsRoot $notice
                $destination = Join-Path $DataRoot $notice
                if ([IO.Path]::GetFullPath($source) -ne [IO.Path]::GetFullPath($destination)) { Copy-Item $source $destination -Force }
            }
        }
    }
    if ($failures.Count) { throw ($failures -join '; ') }
    Write-Host "`nComponenti selezionati elaborati. Log: $log" -ForegroundColor Green
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Log: $log"
    Stop-Transcript | Out-Null
    exit 1
}
Stop-Transcript | Out-Null
exit 0
