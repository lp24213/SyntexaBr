#Requires -Version 7
<#
.SYNOPSIS
    SYNTEXA — Assinatura de executáveis com certificado .pfx local.
.DESCRIPTION
    Usa signtool.exe com o .pfx directamente (sem importar no Windows Store).
    Inclui timestamp DigiCert para validade após expiração do certificado.
.EXAMPLE
    .\sign-with-pfx.ps1 -PfxPath "..\..\Syntexa-codesign.pfx" -PfxPassword "SENHA" -TargetDir "..\dist"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$PfxPath,

    [Parameter(Mandatory=$true)]
    [string]$PfxPassword,

    [string]$TargetDir = (Join-Path $PSScriptRoot ".." "dist"),

    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n▶ $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; throw $msg }

# ── Localiza signtool.exe ──────────────────────────────────
Write-Step "Localizando signtool.exe..."
$signtool = $null
$searchPaths = @(
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe",
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
)
foreach ($p in $searchPaths) {
    if (Test-Path $p) { $signtool = $p; break }
}
if (-not $signtool) {
    $found = Get-ChildItem -Path "${env:ProgramFiles(x86)}\Windows Kits" -Recurse -Filter "signtool.exe" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "x64" } | Select-Object -First 1
    if ($found) { $signtool = $found.FullName }
}
if (-not $signtool) { Write-Fail "signtool.exe não encontrado. Instala o Windows SDK (winget install Microsoft.WindowsSDK)." }
Write-OK "signtool: $signtool"

# ── Valida .pfx ────────────────────────────────────────────
Write-Step "Validando certificado .pfx..."
$pfxAbs = (Resolve-Path $PfxPath).Path
if (-not (Test-Path $pfxAbs)) { Write-Fail "PFX não encontrado: $pfxAbs" }

try {
    $cert = Get-PfxData -FilePath $pfxAbs -Password (ConvertTo-SecureString $PfxPassword -AsPlainText -Force)
    $subject = $cert.EndEntityCertificates[0].Subject
    $expiry  = $cert.EndEntityCertificates[0].NotAfter
    Write-OK "Certificado: $subject"
    Write-OK "Válido até:  $expiry"
    if ($expiry -lt (Get-Date)) {
        Write-Host "  ⚠ AVISO: Certificado expirado. Timestamps garantem validade das assinaturas existentes, mas SmartScreen pode não aceitar novos downloads." -ForegroundColor DarkYellow
    }
} catch {
    Write-Fail "Senha incorrecta ou PFX inválido: $_"
}

# ── Assina executáveis ─────────────────────────────────────
Write-Step "Assinando executáveis em: $TargetDir"
$exes = Get-ChildItem -Path $TargetDir -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue
if ($exes.Count -eq 0) { Write-Host "  ! Nenhum .exe encontrado em $TargetDir" -ForegroundColor DarkYellow }

foreach ($exe in $exes) {
    Write-Host "  → Assinando: $($exe.Name)"
    & $signtool sign `
        /f $pfxAbs `
        /p $PfxPassword `
        /tr $TimestampUrl `
        /td sha256 `
        /fd sha256 `
        /d "Syntexa AI" `
        /du "https://syntexabr.com.br" `
        $exe.FullName

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Falha ao assinar: $($exe.Name)" -ForegroundColor Red
    } else {
        Write-OK "Assinado: $($exe.Name)"
        # Verifica assinatura
        $verify = & $signtool verify /pa /v $exe.FullName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Verificado OK"
        } else {
            Write-Host "  ⚠ Assinado mas verificação retornou aviso (normal para self-signed)" -ForegroundColor DarkYellow
        }
    }
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  ASSINATURA CONCLUÍDA" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
