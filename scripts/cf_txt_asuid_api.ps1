# TXT asuid.api (validacao Azure Container Apps).
#
# IMPORTANTE: o OAuth do `wrangler login` NAO inclui permissao de DNS na API Cloudflare (403 em /dns_records).
# Para este script criar o TXT automaticamente, defina no PowerShell ANTES de rodar:
#   $env:CLOUDFLARE_API_TOKEN = "<API Token com Zone > DNS > Edit na zona syntexabr.com.br>"
# Crie o token em: Cloudflare Dashboard > Manage Account > API Tokens > Create Token > Edit zone DNS (template).
#
# Sem token: adicione manualmente no painel: DNS > Add record > TXT > Name: asuid.api > Content: (valor abaixo).

$ErrorActionPreference = "Stop"
$txtValue = "96ED40A556CE6865348F85C2128D56F94434EDC4CC2F80A34C31B0E47FF2D9BB"

function Get-WranglerOAuthToken {
    $repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
    Push-Location $repoRoot
    try {
        $raw = cmd /c "npx wrangler auth token 2>&1"
    } finally {
        Pop-Location
    }
    $lines = @($raw -split "[`r`n]+" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    for ($i = $lines.Length - 1; $i -ge 0; $i--) {
        $line = $lines[$i]
        if ($line.Length -ge 40 -and $line -match '^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$') {
            return $line
        }
    }
    return $null
}

$token = $env:CLOUDFLARE_API_TOKEN
if (-not $token) {
    $token = $env:CLOUDFLARE_DNS_TOKEN
}
if (-not $token) {
    Write-Host "CLOUDFLARE_API_TOKEN nao definido - tentando OAuth do Wrangler (vai falhar em DNS com 403)."
    $token = Get-WranglerOAuthToken
}
if (-not $token) {
    Write-Error "Sem token. Defina CLOUDFLARE_API_TOKEN ou rode: npx wrangler login"
}

$h = @{
    Authorization  = "Bearer $token"
    "Content-Type" = "application/json"
}

$zones = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones?name=syntexabr.com.br" -Headers $h -Method Get
if (-not $zones.success -or $zones.result.Count -lt 1) {
    Write-Output ($zones | ConvertTo-Json -Depth 6)
    exit 1
}
$zid = $zones.result[0].id
$qUri = 'https://api.cloudflare.com/client/v4/zones/' + $zid + '/dns_records?type=TXT&name=asuid.api.syntexabr.com.br'

try {
    $existing = Invoke-RestMethod -Uri $qUri -Headers $h -Method Get
} catch {
    $err = $_.Exception.Message
    if ($err -match '403|Proibido|Forbidden') {
        Write-Host ""
        Write-Host "FALHA: a sessao do Wrangler nao tem permissao de DNS na API Cloudflare."
        Write-Host "Solucao A - Painel: DNS > Add record > TXT > Name: asuid.api > Content:"
        Write-Host $txtValue
        Write-Host "Solucao B - API Token: crie token Zone DNS Edit e rode:"
        Write-Host '  $env:CLOUDFLARE_API_TOKEN = "..."; .\scripts\cf_txt_asuid_api.ps1'
        exit 2
    }
    throw
}

$payload = @{ type = "TXT"; name = "asuid.api"; content = $txtValue; ttl = 3600 } | ConvertTo-Json
if ($existing.success -and $existing.result.Count -gt 0) {
    $rid = $existing.result[0].id
    $r = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones/$zid/dns_records/$rid" -Headers $h -Method Patch -Body $payload
    Write-Host ('OK: TXT atualizado id=' + $rid)
} else {
    $r = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones/$zid/dns_records" -Headers $h -Method Post -Body $payload
    Write-Host 'OK: TXT criado'
}
Write-Output ($r | ConvertTo-Json -Depth 5)
