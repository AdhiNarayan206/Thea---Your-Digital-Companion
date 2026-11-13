<#
.SYNOPSIS
  Build the Thea Windows installer with Inno Setup.

.DESCRIPTION
  Compiles installer\Thea.iss into installer\output\Thea-Setup-<version>.exe,
  then prints size and SHA-256 so the website can quote them.

  Unsigned by default. To sign, install the Windows SDK (signtool.exe) and set:
    $env:THEA_SIGN_CERT     = "C:\path\to\certificate.pfx"
    $env:THEA_SIGN_PASSWORD = "certificate password"
  then run:  .\installer\build.ps1 -Sign

  Timestamping keeps the signature valid after the certificate expires.

.PARAMETER Sign
  Sign the setup executable and the uninstaller.
#>
[CmdletBinding()]
param(
    [switch]$Sign
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw 'ISCC.exe not found. Install Inno Setup 6: winget install --id JRSoftware.InnoSetup --exact'
}

$exe = Join-Path $root 'dist\Thea\Thea.exe'
if (-not (Test-Path $exe)) {
    throw "Missing $exe. Build the app first: .\build.bat"
}
$exeAge = (Get-Date) - (Get-Item $exe).LastWriteTime
Write-Host ("Packaging app built {0:N0} minutes ago." -f $exeAge.TotalMinutes)

$argsList = @((Join-Path $PSScriptRoot 'Thea.iss'))

if ($Sign) {
    if (-not $env:THEA_SIGN_CERT -or -not $env:THEA_SIGN_PASSWORD) {
        throw 'Set THEA_SIGN_CERT and THEA_SIGN_PASSWORD, or run without -Sign.'
    }
    $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if (-not $signtool) {
        throw 'signtool.exe not found. Install the Windows SDK signing tools.'
    }
    $signCommand = '"{0}" sign /f "{1}" /p "{2}" /fd sha256 /tr http://timestamp.digicert.com /td sha256 $f' -f `
        $signtool.Source, $env:THEA_SIGN_CERT, $env:THEA_SIGN_PASSWORD
    # Inno registers $f as the file being signed.
    $argsList += "/Ssigntool=$signCommand"
    $argsList += '/DSign'
    Write-Host 'Signing enabled.' -ForegroundColor Yellow
}

& $iscc @argsList
if ($LASTEXITCODE -ne 0) { throw "ISCC failed with exit code $LASTEXITCODE" }

$version = (Select-String -Path (Join-Path $PSScriptRoot 'Thea.iss') -Pattern '#define AppVersion "([^"]+)"').Matches[0].Groups[1].Value
$out = Join-Path $PSScriptRoot "output\Thea-Setup-$version.exe"
$item = Get-Item $out
$hash = (Get-FileHash $out -Algorithm SHA256).Hash
Write-Host ''
Write-Host ("Installer : {0}" -f $item.FullName)
Write-Host ("Size      : {0:N2} MB ({1:N0} bytes)" -f ($item.Length / 1MB), $item.Length)
Write-Host ("SHA-256   : {0}" -f $hash)
