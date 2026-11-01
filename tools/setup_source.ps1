$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$root = Split-Path $PSScriptRoot -Parent
$script:busy = $false
$script:step = 0
$script:process = $null
$form = New-Object System.Windows.Forms.Form
$form.Text = 'Installazione - Convertitore Universale'
$form.ClientSize = New-Object System.Drawing.Size(700,540)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font('Segoe UI',10)
$title = New-Object System.Windows.Forms.Label
$title.Font = New-Object System.Drawing.Font('Segoe UI',18)
$title.SetBounds(25,20,650,45)
$form.Controls.Add($title)
$description = New-Object System.Windows.Forms.Label
$description.SetBounds(25,75,650,65)
$form.Controls.Add($description)
$panel = New-Object System.Windows.Forms.Panel
$panel.SetBounds(25,145,650,235)
$form.Controls.Add($panel)
$checks = @{}
$y = 0
foreach ($row in @(@('ffmpeg','Audio e video - FFmpeg'),@('office','Documenti Office - LibreOffice'),@('ocr','Scansioni e foto - Tesseract'),@('italian','OCR in italiano'))) {
    $check = New-Object System.Windows.Forms.CheckBox
    $check.Text = $row[1]; $check.Checked = $true
    $check.SetBounds(0,$y,640,30)
    $panel.Controls.Add($check); $checks[$row[0]] = $check; $y += 35
}
$agreement = New-Object System.Windows.Forms.CheckBox
$agreement.Text = 'Accetto i termini dei pacchetti scelti e della sorgente WinGet.'
$agreement.SetBounds(0,155,640,40)
$panel.Controls.Add($agreement)
$hint = New-Object System.Windows.Forms.Label
$hint.Text = 'Internet necessario. Alcuni installer possono chiedere conferma amministratore.'
$hint.SetBounds(0,200,640,35)
$panel.Controls.Add($hint)
$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Multiline = $true; $logBox.ReadOnly = $true
$logBox.ScrollBars = 'Both'; $logBox.WordWrap = $false
$logBox.SetBounds(25,145,650,275)
$logBox.Visible = $false
$form.Controls.Add($logBox)
$bar = New-Object System.Windows.Forms.ProgressBar
$bar.SetBounds(25,435,650,15); $bar.Visible = $false
$form.Controls.Add($bar)
$back = New-Object System.Windows.Forms.Button
$back.Text = 'Indietro'; $back.SetBounds(25,475,110,38)
$form.Controls.Add($back)
$copy = New-Object System.Windows.Forms.Button
$copy.Text = 'Copia dettagli'; $copy.SetBounds(145,475,135,38); $copy.Visible = $false
$form.Controls.Add($copy)
$logs = New-Object System.Windows.Forms.Button
$logs.Text = 'Apri log'; $logs.SetBounds(290,475,110,38); $logs.Visible = $false
$form.Controls.Add($logs)
$next = New-Object System.Windows.Forms.Button
$next.SetBounds(440,475,145,38)
$form.Controls.Add($next)
$close = New-Object System.Windows.Forms.Button
$close.Text = 'Chiudi'; $close.SetBounds(595,475,80,38)
$form.Controls.Add($close)
function Show-Step([int]$value) {
    $script:step = $value
    $panel.Visible = ($value -eq 1)
    $back.Enabled = ($value -eq 1)
    if ($value -eq 0) {
        $title.Text = 'Benvenuto nel setup'
        $description.Text = 'Il wizard prepara il convertitore e ti fa scegliere i componenti. I progressi e gli eventuali errori compariranno in questa finestra. Premi Avanti per iniziare.'
        $next.Text = 'Avanti >'
    } elseif ($value -eq 1) {
        $title.Text = 'Scegli i componenti'
        $description.Text = 'Il programma base verra installato sempre. Seleziona le funzioni aggiuntive. Se manca Python compatibile, il wizard puo installare Python 3.12 con il tuo consenso ai termini.'
        $next.Text = 'Installa'
    }
}
function Read-Log([string]$path) {
    if (-not (Test-Path $path)) { return '' }
    $stream = New-Object System.IO.FileStream($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
    $reader = New-Object System.IO.StreamReader($stream)
    try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 700
$timer.Add_Tick({
    try {
        $text = (Read-Log $script:outLog) + "`r`n" + (Read-Log $script:errLog)
        if ($logBox.Text -ne $text) { $logBox.Text = $text; $logBox.SelectionStart = $logBox.TextLength; $logBox.ScrollToCaret() }
        $phases = [regex]::Matches($text,'\[FASE\] ([^\r\n]+)')
        if ($phases.Count) { $description.Text = $phases[$phases.Count - 1].Groups[1].Value }
        if ($script:process.HasExited) {
            $timer.Stop(); $script:busy = $false
            $bar.Style = 'Blocks'; $close.Enabled = $true; $next.Enabled = $true
            $copy.Visible = $true; $logs.Visible = $true
            if ($script:process.ExitCode -eq 0) {
                $title.Text = 'Installazione completata'; $next.Text = 'Avvia'; $script:step = 3; $bar.Value = 100
            } else {
                $title.Text = 'Installazione non completata'; $description.Text = 'Leggi i dettagli qui sotto. Puoi copiarli, aprire i log o riprovare.'
                $next.Text = 'Riprova'; $script:step = 4
            }
            $script:process.Dispose()
        }
    } catch { $description.Text = "Lettura registro: $($_.Exception.Message)" }
})
$next.Add_Click({
    if ($script:step -eq 0) { Show-Step 1; return }
    if ($script:step -eq 3) {
        Start-Process wscript.exe -ArgumentList ('"'+(Join-Path $root 'Avvia.vbs')+'"')
        $form.Close(); return
    }
    if ($script:step -eq 4) {
        $logBox.Visible = $false; $bar.Visible = $false; $copy.Visible = $false; $logs.Visible = $false
        Show-Step 1; return
    }
    $selected = @('ffmpeg','office','ocr','italian' | Where-Object { $checks[$_].Checked })
    if ($selected.Count -and -not $agreement.Checked) {
        [System.Windows.Forms.MessageBox]::Show('Accetta i termini oppure deseleziona i componenti esterni.') | Out-Null; return
    }
    if ($checks['italian'].Checked -and -not $checks['ocr'].Checked) {
        [System.Windows.Forms.MessageBox]::Show('Seleziona Tesseract per utilizzare l OCR italiano.') | Out-Null; return
    }
    try {
        $script:logDirectory = Join-Path $env:LOCALAPPDATA 'ConvertitoreUniversale\logs'
        New-Item -ItemType Directory -Force -Path $script:logDirectory | Out-Null
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
        $script:outLog = Join-Path $script:logDirectory "setup-$stamp.log"
        $script:errLog = Join-Path $script:logDirectory "setup-$stamp-error.log"
        $arguments = '-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $PSScriptRoot 'install_source.ps1')+'"'
        if ($selected.Count) { $arguments += ' -Components '+($selected -join ',') }
        if ($agreement.Checked) { $arguments += ' -AcceptAgreements' }
        $script:process = Start-Process (Join-Path $PSHOME 'powershell.exe') -ArgumentList $arguments -WindowStyle Hidden -RedirectStandardOutput $script:outLog -RedirectStandardError $script:errLog -PassThru
        $script:busy = $true; $script:step = 2
        $panel.Visible = $false; $logBox.Visible = $true; $bar.Visible = $true; $bar.Style = 'Marquee'
        $title.Text = 'Installazione in corso'; $description.Text = 'Preparazione...'
        $back.Enabled = $false; $next.Enabled = $false; $close.Enabled = $false
        $timer.Start()
    } catch { [System.Windows.Forms.MessageBox]::Show($_.Exception.ToString(),'Errore avvio setup') | Out-Null }
})
$back.Add_Click({ Show-Step 0 })
$copy.Add_Click({ [System.Windows.Forms.Clipboard]::SetText($logBox.Text + "`r`nLog: $script:outLog") })
$logs.Add_Click({ Start-Process explorer.exe -ArgumentList ('"'+$script:logDirectory+'"') })
$close.Add_Click({ $form.Close() })
$form.Add_FormClosing({
    if ($script:busy) { $_.Cancel = $true; [System.Windows.Forms.MessageBox]::Show('Attendi la fine dell installazione dei componenti.') | Out-Null }
})
Show-Step 0
[void]$form.ShowDialog()
$timer.Dispose(); $form.Dispose()
