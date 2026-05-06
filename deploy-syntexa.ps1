# SyntexaBR - Script de gerenciamento
# Uso: .\deploy-syntexa.ps1 [comando]
#
# === DEPLOY (envia codigo, extrai no servidor, pip, sobe uvicorn, testa /health) ===
#   .\deploy-syntexa.ps1 deploy-back    -> backend na VM Azure /opt/syntexa (no fim: [OK] API no ar)
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
#   deploy       - Deploy completo (Cloudflare Pages + backend na VM Azure)
#   deploy-front - So frontend (build + Cloudflare Pages)
#   deploy-back  - So backend (VM Azure via SSH/SCP para /opt/syntexa)
#   fix-proxy    - nginx + HTTPS (Let's Encrypt) para api.syntexabr.com.br -> :8000
#   ssh          - Abre sessao SSH interativa no servidor
#   logs         - Le backend.log do servidor em tempo real
#   status       - Verifica se API e site estao no ar
#   restart      - Reinicia uvicorn sem redeploy

Param([string]$Cmd = "help")

$ErrorActionPreference = "Stop"

# --- Configuracao ---
# Pode sobrescrever por variáveis de ambiente (recomendado):
#   $env:SYNTEXA_SSH_KEY="C:\caminho\chave.pem"
#   $env:SYNTEXA_REMOTE_USER="azureuser"
#   $env:SYNTEXA_REMOTE_HOST="74.163.97.52"
#   $env:SYNTEXA_REMOTE_BASE="/opt/syntexa"
$SshKeyPath = $env:SYNTEXA_SSH_KEY
if (-not $SshKeyPath) {
    # id_ed25519 costuma ser o par publicado na VM Azure (deploy); id_rsa pode ser outro par (falha se nao estiver no servidor).
    $tryEd  = "C:\Users\luisp\.ssh\id_ed25519"
    $tryRsa = "C:\Users\luisp\.ssh\id_rsa"
    if (Test-Path -LiteralPath $tryEd) { $SshKeyPath = $tryEd }
    elseif (Test-Path -LiteralPath $tryRsa) { $SshKeyPath = $tryRsa }
    else { $SshKeyPath = $tryEd }
}

$RemoteUser = $env:SYNTEXA_REMOTE_USER
if (-not $RemoteUser) { $RemoteUser = "azureuser" }

$RemoteHost = $env:SYNTEXA_REMOTE_HOST
if (-not $RemoteHost) {
    $HostFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "azure-vm-host.txt"
    if (Test-Path -LiteralPath $HostFile) {
        try {
            $h = (Get-Content -LiteralPath $HostFile -Raw).Trim()
            if ($h -match '^[0-9a-fA-F:.]+$') { $RemoteHost = $h }
        } catch {}
    }
}
if (-not $RemoteHost) { $RemoteHost = "74.163.97.52" }

$RemoteBase = $env:SYNTEXA_REMOTE_BASE
if (-not $RemoteBase) { $RemoteBase = "/opt/syntexa" }
# Troca de VM / reinstall: aceita nova host key automaticamente (após ssh-keygen -R <IP> se a antiga conflitar).
$SshExtraOpts = "-o StrictHostKeyChecking=accept-new"
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

# Here-strings no Windows usam CRLF; bash remoto precisa de LF (senao: tar.gz\r, true\r, paths quebrados).
function ConvertTo-BashScriptLf {
    param([string]$Script)
    if ([string]::IsNullOrEmpty($Script)) { return $Script }
    return ($Script -replace "`r`n", "`n") -replace "`r", "`n"
}

# Assina o .exe portátil após copy-artifacts — evita winCodeSign do electron-builder (symlinks em %LOCALAPPDATA% exigem Modo de desenvolvedor).
function Sign-SyntexaWindowsPortable {
    param([string]$RepoRoot, [string]$PfxPath)
    if (-not (Test-Path -LiteralPath $PfxPath)) { return }
    $desktopStatic = Join-Path $RepoRoot "vereda_backend\static\desktop"
    $exe = Get-ChildItem -Path $desktopStatic -Filter "SyntexaAI-Setup-*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $exe) {
        Write-Host "      [aviso] Nenhum SyntexaAI-Setup-*.exe em static/desktop para assinar." -ForegroundColor Yellow
        return
    }
    try {
        if ($env:SYNTEXA_WIN_PFX_PASSWORD) {
            $sec = ConvertTo-SecureString -String $env:SYNTEXA_WIN_PFX_PASSWORD -AsPlainText -Force
            $pfxData = Get-PfxData -FilePath $PfxPath -Password $sec -ErrorAction Stop
            $cert = $pfxData.EndEntityCertificates[0]
        } else {
            $cert = Get-PfxCertificate -FilePath $PfxPath -ErrorAction Stop
        }
        Set-AuthenticodeSignature -LiteralPath $exe.FullName -Certificate $cert -TimestampServer "http://timestamp.digicert.com" -ErrorAction Stop | Out-Null
        Write-Host "      [ok] Authenticode: $($exe.Name)" -ForegroundColor DarkGray
    } catch {
        Write-Host "      [aviso] Falha ao assinar .exe (o binário segue sem assinatura): $($_.Exception.Message)" -ForegroundColor Yellow
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
    Write-Host "SSH -> ${RemoteUser}@${RemoteHost}" -ForegroundColor Cyan
    Write-Host "  (exit para sair)" -ForegroundColor Yellow
    ssh -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=30 -t "${RemoteUser}@${RemoteHost}" "cd $RemoteBase && exec bash --login"
    exit 0
}

# ======================================================================
# LOGS - Backend log em tempo real
# ======================================================================
if ($Cmd -eq "logs") {
    Check-SshKey
    Write-Host ""
    Write-Host "LOGS DO BACKEND (Ctrl+C para sair)" -ForegroundColor Cyan
    ssh -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" "tail -f $RemoteBase/backend.log"
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

    $apiCode = "000"
    try {
        $apiCode = (& curl.exe -4 -sS -o NUL -w "%{http_code}" "https://api.syntexabr.com.br/health" 2>$null)
    } catch { $apiCode = "000" }
    if ($apiCode -eq "200") {
        Write-Host "  [OK]    API : https://api.syntexabr.com.br/health" -ForegroundColor Green
    } else {
        Write-Host "  [FALHA] API : https://api.syntexabr.com.br/health (HTTP $apiCode; use curl -4 se IPv6 antigo)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  Processo uvicorn:" -ForegroundColor Cyan
    ssh -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" "ps aux | grep uvicorn | grep -v grep || echo '  (nenhum processo uvicorn)'"

    Write-Host ""
    Write-Host "  Ultimas 20 linhas do backend.log:" -ForegroundColor Cyan
    ssh -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" "tail -n 20 $RemoteBase/backend.log 2>/dev/null || echo '  (backend.log vazio)'"
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
    $script = ConvertTo-BashScriptLf $script
    ssh -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=30 "${RemoteUser}@${RemoteHost}" $script
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
    $remoteFix = $prefix + "set -e; chmod +x $RemoteBase/scripts/setup_nginx_api.sh 2>/dev/null || true; sudo bash $RemoteBase/scripts/setup_nginx_api.sh"
    ssh -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=120 "${RemoteUser}@${RemoteHost}" $remoteFix
    if ($LASTEXITCODE -ne 0) { throw "fix-proxy falhou" }
    Write-Host ""
    Write-Host "[OK] Proxy aplicado. Teste no PC: curl.exe -sS https://api.syntexabr.com.br/health" -ForegroundColor Green
    exit 0
}

# ======================================================================
# DEPLOY-FRONT - Worker (gateway) + Build + Cloudflare Pages
# ======================================================================
if ($Cmd -eq "deploy-front") {
    Write-Host ""
    Write-Host "Publica apenas o build do site (frontend/out/). Testes E2E em e2e/ NAO sobem para o CDN." -ForegroundColor DarkGray
    Write-Host "DEPLOY CLOUDFLARE: Gateway Worker + Pages" -ForegroundColor Cyan
    Check-Wrangler
    if ($env:SYNTEXA_SKIP_DESKTOP -eq "1") {
        Write-Host "  [skip] SYNTEXA_SKIP_DESKTOP=1 — sem build Electron (pacotes /download/ ficam como na última cópia)." -ForegroundColor Yellow
    } else {
        Write-Host "  [0/4] Electron (Windows + Linux) -> frontend/public/download ..." -ForegroundColor Yellow
        $DesktopDir = Join-Path $Root "desktop"
        Push-Location $DesktopDir
        try {
            Write-Host "      npm install (desktop)..." -ForegroundColor DarkGray
            # Cache de download do Electron: por defeito fica em AppData\Local\electron\Cache; em C: quase cheio falha a meio. Permite D: ou SYNTEXA_ELECTRON_CACHE.
            $electronCache = $env:SYNTEXA_ELECTRON_CACHE
            if (-not $electronCache) {
                if (Test-Path -LiteralPath "D:\") { $electronCache = "D:\.syntexa-electron-cache" }
                else { $electronCache = Join-Path $env:LOCALAPPDATA "electron\Cache" }
            }
            New-Item -ItemType Directory -Path $electronCache -Force | Out-Null
            $env:ELECTRON_CACHE = $electronCache
            Write-Host "      ELECTRON_CACHE=$electronCache" -ForegroundColor DarkGray
            Get-ChildItem -LiteralPath $electronCache -Filter "*.part*" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
            npm install
            if ($LASTEXITCODE -ne 0) { throw "desktop npm install falhou" }
            # Saída em %TEMP%: OneDrive/antivírus costumam bloquear desktop/dist (app.asar em uso).
            $ElectronDist = Join-Path ([System.IO.Path]::GetTempPath()) ("syntexa-electron-" + [DateTime]::UtcNow.ToString("yyyyMMddHHmmss"))
            New-Item -ItemType Directory -Path $ElectronDist -Force | Out-Null
            Write-Host "      electron-builder -> $ElectronDist" -ForegroundColor DarkGray
            # Sem CSC_LINK: evita extrair winCodeSign (7z + symlinks sem privilégio falham). Assinatura: Sign-SyntexaWindowsPortable após copy-artifacts.
            $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
            npx.cmd electron-builder --win --linux --config.directories.output="$ElectronDist"
            $ebCode = $LASTEXITCODE
            Remove-Item Env:CSC_IDENTITY_AUTO_DISCOVERY -ErrorAction SilentlyContinue
            if ($ebCode -ne 0) { throw "electron-builder falhou (código $ebCode). Ative Modo de desenvolvedor no Windows para instalador NSIS ou use build portable." }
            node copy-artifacts.js "$ElectronDist"
            if ($LASTEXITCODE -ne 0) { throw "copy-artifacts.js falhou" }
            Sign-SyntexaWindowsPortable -RepoRoot $Root -PfxPath (Join-Path $Root "Syntexa-codesign.pfx")
            try { Remove-Item -LiteralPath $ElectronDist -Recurse -Force -ErrorAction SilentlyContinue } catch {}
            Remove-Item Env:ELECTRON_CACHE -ErrorAction SilentlyContinue
        } finally {
            Pop-Location
        }
    }

    Write-Host "  [1/4] wrangler deploy (syntexa-gateway)..." -ForegroundColor Yellow
    # Usar wrangler pinado em frontend/package.json — npx puxa versao nova que pode quebrar (miniflare).
    Push-Location $Root
    try {
        & $Wrangler deploy
        if ($LASTEXITCODE -ne 0) { throw "wrangler deploy (gateway) falhou" }
    } finally {
        Pop-Location
    }

    # Build em pasta temporária: OneDrive costuma travar `frontend/out` (EBUSY) quando o Next apaga/recria a pasta.
    # Pasta nova a cada run: evita falha se a anterior ficou bloqueada por antivirus/Node.
    # Se C: estiver sem espaço, defina antes: $env:SYNTEXA_FRONTEND_BUILD_PARENT = 'D:\tmp' (disco com vários GB livres).
    $buildParent = $env:SYNTEXA_FRONTEND_BUILD_PARENT
    if (-not $buildParent -or -not (Test-Path -LiteralPath $buildParent)) { $buildParent = $env:TEMP }
    $TempBuild = Join-Path $buildParent ("syntexa-frontend-deploy-" + [DateTime]::UtcNow.ToString("yyyyMMddHHmmss"))
    Write-Host "  [2/4] Build Next.js em pasta temporaria (evita lock OneDrive)..." -ForegroundColor Yellow
    Write-Host "      $TempBuild" -ForegroundColor DarkGray
    New-Item -ItemType Directory -Path $TempBuild -Force | Out-Null
    # Pacotes >25 MiB vão para a VM (vereda_backend/static/desktop → /v1/desktop/binary), não para o Pages.
    $pubDl = Join-Path $FrontDir "public\download"
    if (Test-Path -LiteralPath $pubDl) {
        Get-ChildItem -LiteralPath $pubDl -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    & robocopy.exe $FrontDir $TempBuild /MIR /XD node_modules .next out test-results .wrangler /NFL /NDL /NJH /NJS | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) { throw "robocopy falhou (codigo $rc)" }
    # Evita erro do Wrangler com metadados de submodule do workspace.
    Remove-Item -LiteralPath (Join-Path $TempBuild ".git") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $TempBuild ".gitmodules") -Force -ErrorAction SilentlyContinue

    Push-Location $TempBuild
    try {
        $env:NEXT_PUBLIC_API_BASE = "https://api.syntexabr.com.br"
        if (-not $env:NEXT_PUBLIC_DESKTOP_WIN_URL) { $env:NEXT_PUBLIC_DESKTOP_WIN_URL = "" }
        if (-not $env:NEXT_PUBLIC_DESKTOP_MAC_URL) { $env:NEXT_PUBLIC_DESKTOP_MAC_URL = "" }
        $macDmgPath = Join-Path $TempBuild "public\download\SyntexaAI-macos-universal.dmg"
        if (Test-Path -LiteralPath $macDmgPath) {
            $env:NEXT_PUBLIC_SHOW_MAC_DESKTOP = "1"
        } else {
            Remove-Item Env:NEXT_PUBLIC_SHOW_MAC_DESKTOP -ErrorAction SilentlyContinue
        }
        Write-Host "  npm install (temp)..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install (temp) falhou" }
        Write-Host "  npm run build (NEXT_PUBLIC_API_BASE=$env:NEXT_PUBLIC_API_BASE)..." -ForegroundColor Yellow
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build falhou" }
        Write-Host "  [3/4] wrangler pages deploy..." -ForegroundColor Yellow
        $WranglerTemp = Join-Path $TempBuild "node_modules\.bin\wrangler.cmd"
        if (-not (Test-Path -LiteralPath $WranglerTemp)) { throw "wrangler nao encontrado em $TempBuild (apos npm install)" }
        $DeployBranch = "main"
        $DeployCommitHash = [DateTime]::UtcNow.ToString("yyyyMMddHHmmss")
        $DeployCommitMessage = "Syntexa frontend deploy"
        & $WranglerTemp pages deploy out --project-name syntexa-frontend --branch $DeployBranch --commit-hash $DeployCommitHash --commit-message $DeployCommitMessage --commit-dirty=true
        if ($LASTEXITCODE -ne 0) { throw "wrangler pages deploy falhou" }
    } finally {
        Pop-Location
        Remove-Item Env:NEXT_PUBLIC_API_BASE -ErrorAction SilentlyContinue
        Remove-Item Env:NEXT_PUBLIC_SHOW_MAC_DESKTOP -ErrorAction SilentlyContinue
    }
    Set-Location $Root
    Write-Host "[OK] Gateway Worker + Pages publicados." -ForegroundColor Green
    exit 0
}

# ======================================================================
# DEPLOY-BACK - Backend na VM de producao (Azure)
# ======================================================================
if ($Cmd -eq "deploy-back") {
    Write-Host ""
    Write-Host "DEPLOY BACKEND -> VM ($RemoteHost)" -ForegroundColor Cyan
    try {
        & ssh-keygen -R "${RemoteHost}" 2>$null | Out-Null
        Write-Host "  (ssh-keygen -R $RemoteHost - limpa host key antiga se existir)" -ForegroundColor DarkGray
    } catch {}
    if (Test-Path -LiteralPath (Join-Path $Root "azure-vm-host.txt")) {
        Write-Host "  (host de azure-vm-host.txt; sobrescreva com SYNTEXA_REMOTE_HOST se precisar)" -ForegroundColor DarkGray
    }
    Check-SshKey
    Set-Location $Root

    # /opt/syntexa costuma ser root: garantir pasta gravavel pelo usuario SSH (ex.: azureuser)
    $prepRemote = "sudo mkdir -p $RemoteBase && sudo chown -R " + $RemoteUser + ":" + $RemoteUser + " $RemoteBase"
    ssh -i $SshKeyPath $SshExtraOpts "${RemoteUser}@${RemoteHost}" $prepRemote
    if ($LASTEXITCODE -ne 0) {
        throw "SSH prep falhou (sudo na VM). Ajuste permissoes em $RemoteBase ou use um usuario com escrita."
    }

    $tarList = @("vereda_backend", "vereda_ai", "llm-server", "requirements.txt", "scripts")
    # Não incluir .env por defeito: o .env de desenvolvimento no PC sobrescreve produção e pode derrubar uvicorn (systemd exit 2).
    if ($env:SYNTEXA_DEPLOY_INCLUDE_ENV -eq "1" -and (Test-Path "$Root\.env")) { $tarList += ".env" }
    # Tar fora do OneDrive: pasta do repo pode falhar com "Write error" / disco; %TEMP% costuma ter espaço.
    $tarParent = [System.IO.Path]::GetTempPath()
    if ($env:SYNTEXA_DEPLOY_TAR_DIR -and (Test-Path -LiteralPath $env:SYNTEXA_DEPLOY_TAR_DIR)) {
        $tarParent = $env:SYNTEXA_DEPLOY_TAR_DIR.TrimEnd('\', '/')
    }
    $tarPath = Join-Path $tarParent $TarName
    Remove-Item -LiteralPath $tarPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $Root $TarName) -Force -ErrorAction SilentlyContinue
    $tarArgs = @("-czf", $tarPath) + $tarList
    Write-Host "      (tar.gz -> $tarPath)" -ForegroundColor DarkGray
    & tar @tarArgs
    if ($LASTEXITCODE -ne 0) { throw "tar falhou (disco cheio? Libere espaço ou defina SYNTEXA_DEPLOY_TAR_DIR=D:\pasta)" }

    Write-Host "  Enviando pacote..." -ForegroundColor Yellow
    scp -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=30 $tarPath "${RemoteUser}@${RemoteHost}:$RemoteBase/"
    if ($LASTEXITCODE -ne 0) { throw "SCP falhou" }

    # Sem script bash embutido no PS (here-string/pipe corrompe no Windows). O tar ja inclui scripts/ — executa o .sh no servidor.
    # --overwrite: tar criado no Windows (bsdtar/pax) + GNU tar na VM sem isto falha com "Cannot open: File exists".
    $remoteCmd = "cd $RemoteBase && tar --overwrite -xzf $TarName && bash scripts/remote_deploy_back.sh"
    & ssh.exe -i $SshKeyPath $SshExtraOpts -o ServerAliveInterval=120 "${RemoteUser}@${RemoteHost}" $remoteCmd
    $sshExit = $LASTEXITCODE
    if ($sshExit -ne 0) {
        throw "Deploy remoto falhou (SSH codigo $sshExit). No servidor: cd $RemoteBase && tar --overwrite -xzf $TarName && bash scripts/remote_deploy_back.sh"
    }
    Remove-Item -LiteralPath $tarPath -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Backend atualizado na VM." -ForegroundColor Green
    exit 0
}

# ======================================================================
# DEPLOY - Completo: frontend + backend
# ======================================================================
if ($Cmd -eq "deploy") {
    Write-Host ""
    Write-Host "DEPLOY COMPLETO: Frontend (Cloudflare) + Backend (VM)" -ForegroundColor Cyan
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
Write-Host '  PRODUCAO (Azure API + Cloudflare Worker + Pages):' -ForegroundColor Yellow
Write-Host "    .\deploy-syntexa.ps1 deploy-front  Gateway (wrangler) + build + Pages [principal]"
Write-Host "    .\deploy-syntexa.ps1 deploy        deploy-front + backend na VM (legado)"
Write-Host "    .\deploy-syntexa.ps1 deploy-back   So VM (tar + scp + remoto)"
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
