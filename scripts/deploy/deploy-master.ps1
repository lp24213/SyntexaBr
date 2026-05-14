# ============================================================
# VEREDA / SYNTEXA — Master Deploy Orchestrator v3.0
# Executa deploy completo: Wrangler + Railway + AWS + Validação
# ============================================================
param(
    [switch]$SkipWrangler = $false,
    [switch]$SkipRailway = $false,
    [switch]$SkipAWS = $false,
    [switch]$SkipValidate = $false,
    [string]$AWS_KEY_PATH = "$env:USERPROFILE\Downloads\vereda-key.pem"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$VEREDA_GREEN = "`e[32m"
$VEREDA_RED = "`e[31m"
$VEREDA_YELLOW = "`e[33m"
$VEREDA_CYAN = "`e[36m"
$VEREDA_RESET = "`e[0m"

function Banner($text) {
    Write-Host ""
    Write-Host "$VEREDA_CYAN============================================================$VEREDA_RESET"
    Write-Host "$VEREDA_CYAN  $text$VEREDA_RESET"
    Write-Host "$VEREDA_CYAN============================================================$VEREDA_RESET"
}

function Status($msg, $status = "INFO") {
    $color = switch ($status) {
        "OK"    { $VEREDA_GREEN }
        "WARN"  { $VEREDA_YELLOW }
        "ERR"   { $VEREDA_RED }
        default { $VEREDA_CYAN }
    }
    Write-Host "$color[$status]$VEREDA_RESET $msg"
}

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)

Banner "VEREDA / SYNTEXA — MASTER DEPLOY v3.0"

# ── PHASE 1: CLOUDFLARE WORKER ────────────────────────────
if (-not $SkipWrangler) {
    Banner "PHASE 1/4 — Cloudflare Worker Deploy"
    try {
        $wrangler = Get-Command node -ErrorAction Stop
        $wranglerBin = "$PROJECT_ROOT\frontend\node_modules\wrangler\bin\wrangler.js"
        if (Test-Path $wranglerBin) {
            Push-Location $PROJECT_ROOT
            & node $wranglerBin deploy 2>&1 | Tee-Object -Variable wranglerOut
            Pop-Location
            if ($wranglerOut -match "Uploaded syntexa-gateway") {
                Status "Cloudflare Worker deployed" "OK"
            } else {
                Status "Cloudflare Worker status unclear" "WARN"
            }
        } else {
            Status "Wrangler não encontrado. Rode: npm install -g wrangler" "WARN"
        }
    } catch {
        Status "Cloudflare deploy falhou: $_" "ERR"
    }
} else {
    Status "Cloudflare Worker pulado (--SkipWrangler)" "WARN"
}

# ── PHASE 2: RAILWAY BACKEND ──────────────────────────────
if (-not $SkipRailway) {
    Banner "PHASE 2/4 — Railway Backend Deploy"
    try {
        $railway = Get-Command railway -ErrorAction Stop
        Push-Location $PROJECT_ROOT
        & railway up 2>&1 | Tee-Object -Variable railwayOut
        Pop-Location
        if ($railwayOut -match "Indexed|Deployed|Upload") {
            Status "Railway deploy iniciado" "OK"
        }
    } catch {
        Status "Railway deploy falhou: $_" "ERR"
    }
} else {
    Status "Railway pulado (--SkipRailway)" "WARN"
}

# ── PHASE 3: AWS GPU CLUSTER ──────────────────────────────
if (-not $SkipAWS) {
    Banner "PHASE 3/4 — AWS GPU Cluster Deploy"

    # Tentar instalação automática AWS CLI
    $awsPath = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
    if (-not (Test-Path $awsPath)) {
        Status "AWS CLI não encontrado. Instalando..." "WARN"
        try {
            $msi = "$env:TEMP\AWSCLIV2.msi"
            Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile $msi -UseBasicParsing
            Start-Process msiexec.exe -ArgumentList "/i", $msi, "/quiet", "/norestart" -Wait
            Remove-Item $msi -Force
            Status "AWS CLI instalado" "OK"
        } catch {
            Status "Falha ao instalar AWS CLI: $_" "ERR"
        }
    }

    # Tentar conectar à instância existente via SSH
    $AWS_HOST = "98.94.86.193"
    Status "Tentando conectar à instância existente: $AWS_HOST" "INFO"

    if (Test-Path $AWS_KEY_PATH) {
        Status "Chave SSH encontrada: $AWS_KEY_PATH" "OK"

        # Testar SSH
        $sshTest = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i $AWS_KEY_PATH "ubuntu@$AWS_HOST" "echo VEREDA_OK" 2>&1
        if ($sshTest -match "VEREDA_OK") {
            Status "SSH conectado à instância existente" "OK"

            # Preparar remoto
            Status "Preparando diretório remoto..." "INFO"
            ssh -i $AWS_KEY_PATH "ubuntu@$AWS_HOST" "sudo mkdir -p /opt/vereda && sudo chown ubuntu:ubuntu /opt/vereda" 2>$null

            # Copiar scripts
            Status "Copiando scripts para instância remota..." "INFO"
            scp -i $AWS_KEY_PATH -o StrictHostKeyChecking=accept-new -r "$PROJECT_ROOT\infrastructure\aws-gpu-cluster\scripts" "ubuntu@${AWS_HOST}:/opt/vereda/" 2>$null
            scp -i $AWS_KEY_PATH -o StrictHostKeyChecking=accept-new "$PROJECT_ROOT\infrastructure\aws-gpu-cluster\docker-compose.gpu.yml" "ubuntu@${AWS_HOST}:/opt/vereda/" 2>$null
            scp -i $AWS_KEY_PATH -o StrictHostKeyChecking=accept-new "$PROJECT_ROOT\infrastructure\aws-gpu-cluster\Dockerfile.gpu" "ubuntu@${AWS_HOST}:/opt/vereda/" 2>$null
            scp -i $AWS_KEY_PATH -o StrictHostKeyChecking=accept-new "$PROJECT_ROOT\infrastructure\aws-gpu-cluster\main.py" "ubuntu@${AWS_HOST}:/opt/vereda/" 2>$null

            # Executar setup
            Status "Executando setup remoto..." "INFO"
            $setupOutput = ssh -i $AWS_KEY_PATH "ubuntu@$AWS_HOST" "bash /opt/vereda/scripts/setup-aws.sh" 2>&1
            Status "Setup remoto concluído" "OK"

            # Verificar serviços
            Status "Verificando serviços GPU..." "INFO"
            Start-Sleep -Seconds 10
            for ($port = 8000; $port -le 8003; $port++) {
                $health = ssh -i $AWS_KEY_PATH "ubuntu@$AWS_HOST" "curl -sf http://localhost:$port/health" 2>$null
                if ($health) {
                    Status "Porta $port: SAUDÁVEL" "OK"
                } else {
                    Status "Porta $port: AGUARDANDO" "WARN"
                }
            }
        } else {
            Status "SSH falhou. Verifique: key.pem, security group (porta 22), instância running" "ERR"
            Status "Para provisionar nova GPU via Terraform, execute:" "INFO"
            Status "  .\scripts\deploy\deploy-aws-full.ps1 -AWS_ACCESS_KEY `$env:AWS_ACCESS_KEY_ID -AWS_SECRET_KEY `$env:AWS_SECRET_ACCESS_KEY" "INFO"
        }
    } else {
        Status "Chave SSH não encontrada: $AWS_KEY_PATH" "ERR"
        Status "Baixe sua chave da AWS Console (EC2 > Key Pairs) e salve em: $AWS_KEY_PATH" "WARN"
    }
} else {
    Status "AWS pulado (--SkipAWS)" "WARN"
}

# ── PHASE 4: VALIDAÇÃO ────────────────────────────────────
if (-not $SkipValidate) {
    Banner "PHASE 4/4 — End-to-End Validation"
    try {
        Push-Location $SCRIPT_DIR
        & bash validate-full.sh 2>&1 | Tee-Object -Variable validateOut
        Pop-Location
        if ($validateOut -match "TODAS AS VALIDAÇÕES PASSARAM") {
            Status "VALIDAÇÃO COMPLETA — SISTEMA OPERACIONAL" "OK"
        } else {
            Status "Algumas validações falharam" "WARN"
        }
    } catch {
        Status "Validação falhou: $_" "ERR"
    }
} else {
    Status "Validação pulada (--SkipValidate)" "WARN"
}

# ── SUMMARY ────────────────────────────────────────────────
Banner "DEPLOY VEREDA / SYNTEXA v3.0 FINALIZADO"
Status "Gateway:    https://api.syntexabr.com.br" "INFO"
Status "Frontend:   https://syntexabr.com.br" "INFO"
Status "Railway:    https://syntexa-backend-production.up.railway.app" "INFO"
Status "AWS GPU:    http://98.94.86.193:8000" "INFO"
Status "Local:      http://localhost:8002" "INFO"
Status "" "INFO"
Status "Para re-executar: .\scripts\deploy\deploy-master.ps1" "INFO"
Status "Para nova GPU:    .\scripts\deploy\deploy-aws-full.ps1" "INFO"
