# ============================================================
# VEREDA / SYNTEXA — AWS Full Deploy (PowerShell)
# Instala AWS CLI + Terraform e executa deploy completo
# ============================================================
param(
    [string]$AWS_ACCESS_KEY = $env:AWS_ACCESS_KEY_ID,
    [string]$AWS_SECRET_KEY = $env:AWS_SECRET_ACCESS_KEY,
    [string]$AWS_REGION = "us-east-1",
    [string]$GPU_TYPE = "g5.xlarge",
    [string]$SSH_KEY_PATH = "$env:USERPROFILE\Downloads\vereda-key.pem",
    [switch]$SkipTerraform = $false
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Status($msg, $status = "INFO") {
    $color = @{ "OK" = "Green"; "WARN" = "Yellow"; "ERR" = "Red"; "INFO" = "Cyan" }[$status]
    Write-Host "[$status] $msg" -ForegroundColor $color
}

# ── VALIDAÇÃO DE CREDENCIAIS ──────────────────────────────
if (-not $AWS_ACCESS_KEY -or -not $AWS_SECRET_KEY) {
    Write-Status "AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY são obrigatórios" "ERR"
    Write-Host ""
    Write-Host "Configure:"
    Write-Host '  $env:AWS_ACCESS_KEY_ID = "AKIA..."' -ForegroundColor Yellow
    Write-Host '  $env:AWS_SECRET_ACCESS_KEY = "..."' -ForegroundColor Yellow
    exit 1
}

$env:AWS_ACCESS_KEY_ID = $AWS_ACCESS_KEY
$env:AWS_SECRET_ACCESS_KEY = $AWS_SECRET_KEY
$env:AWS_DEFAULT_REGION = $AWS_REGION

Write-Status "VEREDA / SYNTEXA — AWS Full Deploy v3.0"
Write-Status "Região: $AWS_REGION | GPU: $GPU_TYPE"

# ── INSTALAR AWS CLI (se não existir) ─────────────────────
$awsPath = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2\aws.exe"
if (-not (Test-Path $awsPath)) {
    Write-Status "AWS CLI não encontrado. Instalando..." "WARN"
    $installer = "$env:TEMP\AWSCLIV2.msi"
    Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile $installer -UseBasicParsing
    Start-Process msiexec.exe -ArgumentList "/i", $installer, "/quiet", "/norestart" -Wait
    Remove-Item $installer -Force -ErrorAction SilentlyContinue
    $awsPath = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2\aws.exe"
    if (-not (Test-Path $awsPath)) {
        Write-Status "Falha ao instalar AWS CLI" "ERR"
        exit 1
    }
    Write-Status "AWS CLI instalado" "OK"
} else {
    Write-Status "AWS CLI encontrado" "OK"
}

# ── INSTALAR TERRAFORM (se não existir) ───────────────────
$tfPath = "$env:LOCALAPPDATA\bin\terraform.exe"
if (-not (Test-Path $tfPath)) {
    Write-Status "Terraform não encontrado. Instalando..." "WARN"
    New-Item -ItemType Directory -Path "$env:LOCALAPPDATA\bin" -Force | Out-Null
    $tfZip = "$env:TEMP\terraform.zip"
    Invoke-WebRequest -Uri "https://releases.hashicorp.com/terraform/1.8.0/terraform_1.8.0_windows_amd64.zip" -OutFile $tfZip -UseBasicParsing
    Expand-Archive -Path $tfZip -DestinationPath "$env:LOCALAPPDATA\bin" -Force
    Remove-Item $tfZip -Force
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LOCALAPPDATA\bin", "User")
    $env:Path += ";$env:LOCALAPPDATA\bin"
    Write-Status "Terraform instalado" "OK"
} else {
    Write-Status "Terraform encontrado" "OK"
}

# ── VALIDAR AWS CREDENCIAIS ──────────────────────────────
Write-Status "Validando credenciais AWS..."
try {
    $identity = & $awsPath sts get-caller-identity --output json | ConvertFrom-Json
    Write-Status "Conectado como: $($identity.Arn)" "OK"
} catch {
    Write-Status "Falha na autenticação AWS: $_" "ERR"
    exit 1
}

# ── DETECTAR INSTÂNCIA EXISTENTE ─────────────────────────
Write-Status "Detectando instância existente i-0068bdc3f2152d1f1..."
try {
    $instance = & $awsPath ec2 describe-instances --instance-ids i-0068bdc3f2152d1f1 --output json | ConvertFrom-Json
    $publicIp = $instance.Reservations[0].Instances[0].PublicIpAddress
    $state = $instance.Reservations[0].Instances[0].State.Name
    Write-Status "Instância encontrada: IP=$publicIp | Estado=$state" "OK"
} catch {
    Write-Status "Instância não encontrada ou sem permissão: $_" "WARN"
    $publicIp = "98.94.86.193"
}

# ── GERAR CHAVE SSH (se não existir) ───────────────────────
if (-not (Test-Path $SSH_KEY_PATH)) {
    $keyName = "vereda-key"
    Write-Status "Criando par de chaves AWS: $keyName" "WARN"
    $keyMaterial = & $awsPath ec2 create-key-pair --key-name $keyName --query 'KeyMaterial' --output text
    if ($keyMaterial) {
        $keyDir = Split-Path $SSH_KEY_PATH -Parent
        New-Item -ItemType Directory -Path $keyDir -Force | Out-Null
        Set-Content -Path $SSH_KEY_PATH -Value $keyMaterial -NoNewline
        # chmod 400 equivalente no Windows
        $acl = Get-Acl $SSH_KEY_PATH
        $acl.SetAccessRuleProtection($true, $false)
        Set-Acl $SSH_KEY_PATH $acl
        Write-Status "Chave salva em: $SSH_KEY_PATH" "OK"
    }
}

# ── DEPLOY TERRAFORM (VPC + GPU + Orchestrator) ──────────
if (-not $SkipTerraform) {
    $tfDir = "$PSScriptRoot\..\..\infrastructure\aws-gpu-cluster\terraform"
    Push-Location $tfDir

    Write-Status "Inicializando Terraform..."
    terraform init

    Write-Status "Planejando infraestrutura..."
    terraform plan -var="aws_region=$AWS_REGION" -var="gpu_instance_type=$GPU_TYPE" -var="ssh_key_name=vereda-key" -out=tfplan

    Write-Status "Aplicando infraestrutura (isso leva ~5 min)..."
    terraform apply -auto-approve tfplan

    $gpuIp = (terraform output -raw gpu_cluster_private_ip)
    $orchIp = (terraform output -raw orchestrator_public_ip)

    Pop-Location

    Write-Status "GPU Cluster IP: $gpuIp (privado, sem IP público)" "OK"
    Write-Status "Orchestrator IP: $orchIp" "OK"
} else {
    Write-Status "Terraform pulado (--SkipTerraform)" "WARN"
    $gpuIp = "10.0.1.10"
    $orchIp = $publicIp
}

# ── DEPLOY NA INSTÂNCIA EXISTENTE (t3.micro) ───────────────
Write-Status "Deployando na instância existente ($orchIp)..."
if (Test-Path $SSH_KEY_PATH) {
    $sshKey = $SSH_KEY_PATH -replace "\\", "/"
    $sshKey = $sshKey -replace "C:/", "/c/"

    # Esperar SSH disponível
    Write-Status "Aguardando SSH na instância $orchIp..."
    $tries = 0
    while ($tries -lt 30) {
        $test = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i $SSH_KEY_PATH "ubuntu@$orchIp" "echo OK" 2>$null
        if ($test -eq "OK") { break }
        Start-Sleep 2
        $tries++
    }

    if ($tries -ge 30) {
        Write-Status "SSH não disponível na instância. Verifique security group e key." "ERR"
    } else {
        Write-Status "SSH conectado" "OK"

        # Copiar arquivos
        $remoteDir = "/opt/vereda"
        ssh -i $SSH_KEY_PATH "ubuntu@$orchIp" "sudo mkdir -p $remoteDir && sudo chown ubuntu:ubuntu $remoteDir" 2>$null

        scp -i $SSH_KEY_PATH -r "$PSScriptRoot\..\..\infrastructure\aws-gpu-cluster\scripts" "ubuntu@${orchIp}:$remoteDir/" 2>$null
        scp -i $SSH_KEY_PATH "$PSScriptRoot\..\..\infrastructure\aws-gpu-cluster\docker-compose.gpu.yml" "ubuntu@${orchIp}:$remoteDir/" 2>$null
        scp -i $SSH_KEY_PATH "$PSScriptRoot\..\..\infrastructure\aws-gpu-cluster\config\nginx.gpu.conf" "ubuntu@${orchIp}:$remoteDir/" 2>$null

        # Executar setup
        ssh -i $SSH_KEY_PATH "ubuntu@$orchIp" "bash $remoteDir/scripts/setup-aws.sh" 2>$null
        Write-Status "Setup remoto executado" "OK"
    }
} else {
    Write-Status "Chave SSH não encontrada em: $SSH_KEY_PATH" "WARN"
    Write-Status "Para deploy na instância existente, configure SSH_KEY_PATH" "WARN"
}

# ── VALIDAÇÃO ──────────────────────────────────────────────
Write-Status "Executando validação..."
& "$PSScriptRoot\validate-deploy.sh" 2>$null

# ── SUMMARY ────────────────────────────────────────────────
Write-Status ""
Write-Status "============================================================"
Write-Status "  DEPLOY AWS VEREDA / SYNTEXA v3.0 CONCLUÍDO"
Write-Status "============================================================"
Write-Status "  Cloudflare Worker: https://syntexabr.com.br"
Write-Status "  Railway Backend:  https://syntexa-backend-production.up.railway.app"
Write-Status "  AWS GPU Cluster:  $gpuIp (privado)"
Write-Status "  Orchestrator:     $orchIp"
Write-Status "============================================================"
Write-Status ""
Write-Status "Próximo passo: Configure Cloudflare Tunnel apontando para $gpuIp"
Write-Status "  cloudflared tunnel create vereda-gpu"
Write-Status ""
