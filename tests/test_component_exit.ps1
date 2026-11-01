$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$source = Join-Path (Split-Path $PSScriptRoot -Parent) 'installer/install_components.ps1'
$tree = [System.Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$function = $tree.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-ComponentExit'}, $true)
Invoke-Expression $function.Extent.Text
foreach ($code in @(0,-1978335135,2316632161,-1978335189,2316632107)) {
    if (-not (Test-ComponentExit $code 'install')) { throw "Installazione valida rifiutata: $code" }
}
foreach ($code in @(1,-1978335187,-1978335136)) {
    if (Test-ComponentExit $code 'install') { throw "Errore reale ignorato: $code" }
}
if (Test-ComponentExit -1978335135 'upgrade') { throw 'Aggiornamento gia installato ignorato erroneamente' }
Write-Output 'WinGet: gia installato accettato, errori reali conservati (9 verifiche).'
