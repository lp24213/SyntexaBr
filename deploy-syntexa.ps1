# SyntexaBR - Script de gerenciamento
# Uso: .\deploy-syntexa.ps1 [comando]
#
# === DEPLOY (envia codigo, extrai no servidor, pip, sobe uvicorn, testa /health) ===
#   .\deploy-syntexa.ps1 deploy-back    -> so backend Hetzner (no fim: [OK] API no ar)
#   .\deploy-syntexa.ps1 deploy         -> Cloudflare Pages + deploy-back
# === SSH (so login Linux em /opt/syntexa — NAO e deploy, NAO publica nada) ===
#   .\deploy-syntexa.ps1 ssh
#
# Comandos:
#   dev          - Sobe frontend + backend localmente
#   dev-front    - So o frontend (Next.js dev)
#   dev-back     - So o backend (uvicorn --reload)
#   migrate      - Migra banco SQLite (adiciona colunas novas)
#   install      - Instala dependencias locais (pip + npm)
#   deploy       - Deploy completo (Cloudflare Pages + Hetzner)
#   deploy-front - So frontend (build + Cloudflare Pages)
#   deploy-back  - So backend (Hetzner via SSH/SCP)
#   fix-proxy    - nginx + HTTPS (Let's Encrypt) para api.syntexabr.com.br -> :8000
#   ssh          - Abre sessao SSH interativa no servidor
#   logs         - Le backend.log do servidor em tempo real
#   status       - Verifica se API e site estao no ar
#   restart      - Reinicia uvicorn sem redeploy

Param([string]$Cmd = "help")

$ErrorActionPreference = "Stop"

# --- Configuracao ---
$SshKeyPath = "C:\Users\luisp\.ssh\id_ed25519"
$RemoteUser = "root"
$RemoteHost = "91.98.123.197"
$RemoteBase = "/opt/syntexa"
$Root       = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontDir   = Join-Path $Root "frontend"
$Wrangler   = Join-Path $FrontDir "node_modules\.bin\wrangler.cmd"
$TarName    = "syntexa-deploy.tar.gz"

# --- Detecta Python global instalado ---
function Get-PythonExe {
    $p = Get-Command python -ErrorAction SilentlyContinue
    if ($p) { return $p.Source }
    $p = Get-Command python3 -ErrorAction SilentlyContinue
    if ($p) { return $p.Source }
    throw "Python nao encontrado. Instale em https://python.org"
}

function Check-SshKey {
    if (-not (Test-Path -LiteralPath $SshKeyPath)) {
        throw "Chave SSH nao encontrada: $SshKeyPath"
    }
}

function Check-Wrangler {
    if (-not (Test-Path -LiteralPath $Wrangler)) {
        Write-Host "[syntexa] Instalando npm..." -ForegroundColor Yellow
        Push-Location $FrontDir
        npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install falhou" }
        Pop-Location
    }
}

# ======================================================================
# DEV - Frontend + Backend em paralelo
# ======================================================================
if ($Cmd -eq "dev") {
    Write-Host ""
    Write-Host "SYNTEXA DEV" -ForegroundColor Cyan
    Write-Host "  Frontend : http://localhost:3000" -ForegroundColor Green
    Write-Host "  Backend  : http://localhost:8000" -ForegroundColor Green
    Write-Host "  Docs API : http://localhost:8000/docs" -ForegroundColor Green
    Write-Host ""

    $py = Get-PythonExe
    Write-Host "  Python   : $py" -ForegroundColor DarkGray

    $backendCmd = "Write-Host 'BACKEND - http://localhost:8000' -ForegroundColor Cyan; " +
                  "Set-Location '" + $Root + "'; " +
                  "& '" + $py + "' -m pip install -r requirements.txt -q; " +
                  "& '" + $py + "' -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 --reload"

    Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", $backendCmd

    Write-Host "  Backend abrindo em janela separada..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3

    Set-Location $FrontDir
    if (-not (Test-Path "node_modules")) { npm install }
    npm run dev
    Set-Location $Root
    exit 0
}

# ======================================================================
# DEV-FRONT - So o frontend
# ======================================================================
if ($Cmd -eq "dev-front") {
    Write-Host ""
    Write-Host "FRONTEND DEV - http://localhost:3000" -ForegroundColor Cyan
    Set-Location $FrontDir
    if (-not (Test-Path "node_modules")) { npm install }
    npm run dev
    Set-Location $Root
    exit 0
}

# ======================================================================
# DEV-BACK - So o backend
# ======================================================================
if ($Cmd -eq "dev-back") {
    Write-Host ""
    Write-Host "BACKEND DEV - http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Green
    Set-Location $Root
    $py = Get-PythonExe
    Write-Host "  Python: $py" -ForegroundColor DarkGray
    & $py -m pip install -r requirements.txt -q
    & $py -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 --reload
    exit 0
}

# ======================================================================
# MIGRATE - Migra o banco SQLite local
# ======================================================================
if ($Cmd -eq "migrate") {
    Write-Host ""
    Write-Host "MIGRANDO BANCO DE DADOS..." -ForegroundColor Cyan
    Set-Location $Root
    $py = Get-PythonExe
    Write-Host "  Python: $py" -ForegroundColor DarkGray
    Write-Host "  Instalando dependencias..." -ForegroundColor Yellow
    & $py -m pip install -r requirements.txt -q
    Write-Host "  Executando migracao..." -ForegroundColor Yellow
    & $py scripts/migrate_db.py
    exit 0
}

# ======================================================================
# INSTALL - Instala dependencias locais
# ======================================================================
if ($Cmd -eq "install") {
    Write-Host ""
    Write-Host "INSTALANDO DEPENDENCIAS..." -ForegroundColor Cyan
    Set-Location $Root
    $py = Get-PythonExe
    Write-Host "  Python: $py" -ForegroundColor DarkGray
    & $py -m pip install --upgrade pip -q
    & $py -m pip install -r requirements.txt
    Write-Host "[OK] Python/pip OK" -ForegroundColor Green
    Set-Location $FrontDir
    npm install
    Write-Host "[OK] Node/npm OK" -ForegroundColor Green
    Set-Location $Root
    exit 0
}

# ======================================================================
# SSH - Sessao interativa no servidor
# ======================================================================
if ($Cmd -eq "ssh") {
    Check-SshKey
    Write-Host ""
    Write-Host "ATENCAO: isto e so SSH (shell no servidor). NAO e deploy." -ForegroundColor Yellow
    Write-Host "  Para publicar backend: .\deploy-syntexa.ps1 deploy-back" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "SSH -> $RemoteUser@$RemoteHost" -ForegroundColor Cyan
    Write-Host "  (exit para sair)" -ForegroundColor Yellow
    ssh -i $SshKeyPath -o ServerAliveInterval=30 -t "${RemoteUser}@${RemoteHost}" "cd $RemoteBase && exec bash --login"
    exit 0
}

# ======================================================================
# LOGS - Backend log em tempo real
# ======================================================================
if ($Cmd -eq "logs") {
    Check-SshKey
    Write-Host ""
    Write-Host "LOGS DO BACKEND (Ctrl+C para sair)" -ForegroundColor Cyan
    ssh -i $SshKeyPath -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" "tail -f $RemoteBase/backend.log"
    exit 0
}

# ======================================================================
# STATUS - Verifica saude do servidor
# ======================================================================
if ($Cmd -eq "status") {
    Check-SshKey
    Write-Host ""
    Write-Host "STATUS DO SERVIDOR" -ForegroundColor Cyan

    $r = Invoke-WebRequest -Uri "https://syntexabr.com.br" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($r -and $r.StatusCode -eq 200) {
        Write-Host "  [OK]    Site: https://syntexabr.com.br" -ForegroundColor Green
    } else {
        Write-Host "  [FALHA] Site: https://syntexabr.com.br" -ForegroundColor Red
    }

    $a = Invoke-WebRequest -Uri "https://api.syntexabr.com.br/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($a -and $a.StatusCode -eq 200) {
        Write-Host "  [OK]    API : https://api.syntexabr.com.br/health" -ForegroundColor Green
    } else {
        Write-Host "  [FALHA] API : https://api.syntexabr.com.br/health" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  Processo uvicorn:" -ForegroundColor Cyan
    ssh -i $SshKeyPath -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" "ps aux | grep uvicorn | grep -v grep || echo '  (nenhum processo uvicorn)'"

    Write-Host ""
    Write-Host "  Ultimas 20 linhas do backend.log:" -ForegroundColor Cyan
    ssh -i $SshKeyPath -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" "tail -n 20 $RemoteBase/backend.log 2>/dev/null || echo '  (backend.log vazio)'"
    exit 0
}

# ======================================================================
# RESTART - Reinicia uvicorn no servidor
# ======================================================================
if ($Cmd -eq "restart") {
    Check-SshKey
    Write-Host ""
    Write-Host "REINICIANDO BACKEND NO SERVIDOR..." -ForegroundColor Cyan
    $script = @"
cd $RemoteBase
pkill -9 -f uvicorn 2>/dev/null || true
sleep 3
rm -f backend.log
source .venv/bin/activate
export PYTHONPATH=$RemoteBase PYTHONDONTWRITEBYTECODE=1
nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 10
if curl -sf --connect-timeout 5 http://127.0.0.1:8000/health > /dev/null; then
  echo '[OK] API respondeu em /health'
else
  echo '[ERRO] API nao respondeu. Veja backend.log:'
  tail -30 backend.log
fi
"@
    ssh -i $SshKeyPath -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" $script
    exit 0
}

# ======================================================================
# FIX-PROXY - nginx + HTTPS no servidor (api.syntexabr.com.br -> uvicorn :8000)
# ======================================================================
if ($Cmd -eq "fix-proxy") {
    Check-SshKey
    Write-Host ""
    Write-Host "FIX-PROXY -> nginx + HTTPS em $RemoteHost" -ForegroundColor Cyan
    Write-Host "  1) Rode deploy-back antes (scripts/ no servidor)" -ForegroundColor Yellow
    Write-Host "  2) DNS: api.syntexabr.com.br -> IP deste servidor" -ForegroundColor Yellow
    Write-Host "  3) Opcional: `$env:CERTBOT_EMAIL = 'voce@email.com'" -ForegroundColor DarkGray
    $prefix = ""
    if ($env:CERTBOT_EMAIL -and $env:CERTBOT_EMAIL.Trim().Length -gt 0) {
        $em = $env:CERTBOT_EMAIL.Trim() -replace '"', '\"'
        $prefix = "export CERTBOT_EMAIL=`"$em`"; "
    }
    $remoteFix = $prefix + "set -e; chmod +x $RemoteBase/scripts/setup_nginx_api.sh 2>/dev/null || true; bash $RemoteBase/scripts/setup_nginx_api.sh"
    ssh -i $SshKeyPath -o ServerAliveInterval=120 "${RemoteUser}@${RemoteHost}" $remoteFix
    if ($LASTEXITCODE -ne 0) { throw "fix-proxy falhou" }
    Write-Host ""
    Write-Host "[OK] Proxy aplicado. Teste no PC: curl.exe -sS https://api.syntexabr.com.br/health" -ForegroundColor Green
    exit 0
}

# ======================================================================
# DEPLOY-FRONT - Build + Cloudflare Pages
# ======================================================================
if ($Cmd -eq "deploy-front") {
    Write-Host ""
    Write-Host "DEPLOY FRONTEND -> Cloudflare Pages" -ForegroundColor Cyan
    Check-Wrangler
    Set-Location $FrontDir
    Remove-Item Env:NEXT_PUBLIC_API_BASE -ErrorAction SilentlyContinue
    if (-not $env:NEXT_PUBLIC_DESKTOP_WIN_URL) { $env:NEXT_PUBLIC_DESKTOP_WIN_URL = "" }
    if (-not $env:NEXT_PUBLIC_DESKTOP_MAC_URL) { $env:NEXT_PUBLIC_DESKTOP_MAC_URL = "" }
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install falhou" }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build falhou" }
    & $Wrangler pages deploy out --project-name syntexa-frontend --commit-dirty=true
    if ($LASTEXITCODE -ne 0) { throw "wrangler pages deploy falhou" }
    Set-Location $Root
    Write-Host "[OK] Frontend publicado no Cloudflare Pages." -ForegroundColor Green
    exit 0
}

# ======================================================================
# DEPLOY-BACK - Backend no Hetzner
# ======================================================================
if ($Cmd -eq "deploy-back") {
    Write-Host ""
    Write-Host "DEPLOY BACKEND -> Hetzner ($RemoteHost)" -ForegroundColor Cyan
    Check-SshKey
    Set-Location $Root

    ssh -i $SshKeyPath "${RemoteUser}@${RemoteHost}" "mkdir -p $RemoteBase"

    $tarList = @("vereda_backend", "vereda_ai", "llm-server", "requirements.txt", "scripts")
    if (Test-Path "$Root\.env") { $tarList += ".env" }
    Remove-Item "$Root\$TarName" -ErrorAction SilentlyContinue
    $tarArgs = @("-czf", $TarName) + $tarList
    & tar @tarArgs
    if ($LASTEXITCODE -ne 0) { throw "tar falhou" }

    Write-Host "  Enviando pacote..." -ForegroundColor Yellow
    scp -i $SshKeyPath -o ServerAliveInterval=30 "$Root\$TarName" "${RemoteUser}@${RemoteHost}:$RemoteBase/"
    if ($LASTEXITCODE -ne 0) { throw "SCP falhou" }

    $deployScript = @"
set -e
cd $RemoteBase
tar -xzf $TarName
apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 -q 2>/dev/null || true
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
grep -v '^FRONTEND_ORIGIN' .env > .env.tmp 2>/dev/null || cp .env .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'FRONTEND_ORIGIN=https://syntexabr.com.br,https://www.syntexabr.com.br' >> .env
grep -v '^OLLAMA_ENDPOINT\|^OLLAMA_MODEL\|^DEFAULT_LLM' .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true
echo 'OLLAMA_ENDPOINT=http://127.0.0.1:11434' >> .env
echo 'OLLAMA_MODEL=llama3.2:1b' >> .env
echo 'DEFAULT_LLM=ollama' >> .env
cd llm-server
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
cd ..
python3 scripts/patch_vereda_ai_config.py
pkill -9 -f uvicorn 2>/dev/null || true
sleep 4
rm -f backend.log
export PYTHONPATH=$RemoteBase PYTHONDONTWRITEBYTECODE=1 SYNTEXA_USE_AI_ENV=1
unset FRONTEND_ORIGIN
nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo 'Aguardando API (15s)...'
sleep 15
if curl -sf --connect-timeout 5 http://127.0.0.1:8000/health >/dev/null; then
  echo '[OK] API no ar'
  curl -s http://127.0.0.1:8000/health
else
  echo '[ERRO] API nao respondeu'
  cat backend.log
  exit 1
fi
"@
    ssh -i $SshKeyPath -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" $deployScript
    Remove-Item "$Root\$TarName" -ErrorAction SilentlyContinue
    Write-Host "[OK] Backend Hetzner atualizado." -ForegroundColor Green
    exit 0
}

# ======================================================================
# DEPLOY - Completo: frontend + backend
# ======================================================================
if ($Cmd -eq "deploy") {
    Write-Host ""
    Write-Host "DEPLOY COMPLETO: Frontend (Cloudflare) + Backend (Hetzner)" -ForegroundColor Cyan
    $deploySelf = Join-Path $PSScriptRoot "deploy-syntexa.ps1"
    & $deploySelf deploy-front
    if ($LASTEXITCODE -ne 0) { throw "Deploy frontend falhou" }
    & $deploySelf deploy-back
    if ($LASTEXITCODE -ne 0) { throw "Deploy backend falhou" }
    Write-Host ""
    Write-Host "[OK] DEPLOY CONCLUIDO!" -ForegroundColor Green
    Write-Host "  Site: https://syntexabr.com.br" -ForegroundColor Green
    Write-Host "  API : https://api.syntexabr.com.br" -ForegroundColor Green
    exit 0
}

# ======================================================================
# HELP
# ======================================================================
Write-Host ""
Write-Host "SyntexaBR - Comandos disponiveis:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  DEV LOCAL:" -ForegroundColor Yellow
Write-Host "    .\deploy-syntexa.ps1 dev          Frontend + Backend (2 janelas)"
Write-Host "    .\deploy-syntexa.ps1 dev-front     So Next.js (porta 3000)"
Write-Host "    .\deploy-syntexa.ps1 dev-back      So uvicorn (porta 8000)"
Write-Host "    .\deploy-syntexa.ps1 migrate       Migra banco SQLite local"
Write-Host "    .\deploy-syntexa.ps1 install       Instala pip + npm"
Write-Host ""
# Aspas simples: evita que [OK] em aspas duplas vire classe de caracteres do PowerShell
Write-Host '  PRODUCAO (deploy real - no fim do deploy-back aparece OK da API):' -ForegroundColor Yellow
Write-Host "    .\deploy-syntexa.ps1 deploy        Cloudflare + Hetzner"
Write-Host "    .\deploy-syntexa.ps1 deploy-front  So Cloudflare Pages"
Write-Host "    .\deploy-syntexa.ps1 deploy-back   So Hetzner (tar + scp + remoto)"
Write-Host "    .\deploy-syntexa.ps1 fix-proxy     nginx + HTTPS para api.syntexabr.com.br"
Write-Host ""
Write-Host '  SERVIDOR (SSH so terminal; nao substitui deploy-back):' -ForegroundColor Yellow
Write-Host "    .\deploy-syntexa.ps1 ssh           SSH interativo (ja cai em $RemoteBase)"
Write-Host "    .\deploy-syntexa.ps1 logs          backend.log em tempo real"
Write-Host "    .\deploy-syntexa.ps1 status        Verifica site + API"
Write-Host "    .\deploy-syntexa.ps1 restart       Reinicia uvicorn"
Write-Host ""
Write-Host "  SSH MANUAL (copie no PowerShell, mesma chave do script):" -ForegroundColor Yellow
Write-Host ('    ssh -i "' + $SshKeyPath + '" -o ServerAliveInterval=30 -t "' + $RemoteUser + '@' + $RemoteHost + '" "cd ' + $RemoteBase + ' && exec bash --login"')
Write-Host ""
Write-Host ('  No servidor: pasta ' + $RemoteBase + ' | health: curl -s http://127.0.0.1:8000/health | log: tail -f ' + $RemoteBase + '/backend.log')
Write-Host ""
