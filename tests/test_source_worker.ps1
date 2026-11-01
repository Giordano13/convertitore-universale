$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$tree = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path (Join-Path (Split-Path $PSScriptRoot -Parent) 'tools/install_source.ps1')), [ref]$tokens, [ref]$errors)
$functions = $tree.FindAll({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst]}, $true)
foreach ($function in $functions) { Invoke-Expression $function.Extent.Text }
$python = (Get-Command python).Source
$result = Probe-Python $python
if (-not $result) { throw 'Interprete compatibile non trovato' }
Write-Output "Probe compatibile: $result"
if (Probe-Python '/not/a/python') { throw 'Interprete inesistente accettato' }
$diagnostics = @(Run-Command $python @('-c','import sys; print("stderr retained", file=sys.stderr)')) -join "`n"
if ($diagnostics -notlike '*stderr retained*') { throw 'stderr perso' }
try { Run-Command $python @('-c','raise RuntimeError("full traceback")'); throw 'Exit code non verificato' } catch { if ($_.Exception.Message -notlike '*codice 1*') { throw } }
Write-Output 'stderr acquisito e codice di uscita verificato'
