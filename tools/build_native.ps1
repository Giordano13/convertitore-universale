$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
if (!(Test-Path -LiteralPath $vswhere)) { throw 'Installa Visual Studio Build Tools con gli strumenti C++.' }
$installation = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'Compilatore Visual C++ x64 non trovato.' }
$vcvars = Join-Path $installation 'VC/Auxiliary/Build/vcvars64.bat'
$destination = Join-Path $projectRoot 'app/native'
$buildDirectory = Join-Path $projectRoot 'build/native'
New-Item -ItemType Directory -Force -Path $destination,$buildDirectory | Out-Null
$source = Join-Path $projectRoot 'native/file_hash.cpp'
$binary = Join-Path $destination 'file_hash.dll'
$objectFile = Join-Path $buildDirectory 'file_hash.obj'
$importLibrary = Join-Path $buildDirectory 'file_hash.lib'
$command = 'call "{0}" >nul && cl /nologo /std:c++17 /O2 /EHsc /MT /LD "{1}" /Fo"{2}" /link bcrypt.lib /OUT:"{3}" /IMPLIB:"{4}"' -f $vcvars,$source,$objectFile,$binary,$importLibrary
& $env:ComSpec /d /s /c $command
if ($LASTEXITCODE -ne 0) { throw 'Compilazione del modulo nativo fallita.' }
Write-Output "Modulo C++ pronto: $binary"
