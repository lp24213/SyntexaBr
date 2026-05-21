#!/usr/bin/env pwsh
# ============================================================
# DEPLOY SYNTEXA GPU NA AWS - executar quando limite for liberado
# ============================================================
$ErrorActionPreference = "Stop"

$AWS_KEY = "$env:USERPROFILE\.aws\syntexa-key.pem"
$AMI = "ami-0f979fdc16bde9f1b"  # Deep Learning OSS Nvidia Driver AMI GPU Ubuntu 22.04
$INSTANCE_TYPE = "g5.xlarge"      # 1x A10G 24GB - ~$0.60/h spot
$KEY_NAME = "syntexa-key"
$SUBNET = "subnet-04e96e276840811a1"
$SG = "sg-016b1829de127591b"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SYNTEXA GPU DEPLOY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Verificar se limite foi liberado
try {
    $test = aws ec2 run-instances --image-id $AMI --instance-type $INSTANCE_TYPE --dry-run 2>&1
    if ($test -match "DryRunOperation") {
        Write-Host "[OK] Limite GPU liberado!" -ForegroundColor Green
    } else {
        Write-Host "[ERRO] Limite ainda bloqueado. Aguarde aprovacao AWS." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERRO] Falha no teste dry-run: $_" -ForegroundColor Red
    exit 1
}

# Criar spot instance GPU
Write-Host "[INFO] Criando spot instance GPU..." -ForegroundColor Yellow
$runResult = aws ec2 run-instances `
    --image-id $AMI `
    --instance-type $INSTANCE_TYPE `
    --key-name $KEY_NAME `
    --subnet-id $SUBNET `
    --security-group-ids $SG `
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=200,VolumeType=gp3}" `
    --instance-market-options "MarketType=spot,SpotOptions={MaxPrice=1.00,SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}" `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=syntexa-gpu-train}]" `
    --count 1 --no-cli-pager | ConvertFrom-Json

$instanceId = $runResult.Instances[0].InstanceId
Write-Host "[OK] Instancia criada: $instanceId" -ForegroundColor Green

# Aguardar IP publico
Write-Host "[INFO] Aguardando IP publico..." -ForegroundColor Yellow
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 5
    $desc = aws ec2 describe-instances --instance-ids $instanceId --query "Reservations[0].Instances[0].PublicIpAddress" --output text --no-cli-pager
    if ($desc -and $desc -ne "None") {
        $publicIp = $desc
        break
    }
}

if (-not $publicIp) {
    Write-Host "[ERRO] Timeout aguardando IP" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] IP publico: $publicIp" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CONECTE-SE VIA SSH:" -ForegroundColor Cyan
Write-Host "  ssh -i $AWS_KEY ubuntu@$publicIp" -ForegroundColor Yellow
Write-Host ""
Write-Host "  OU AGUARDE O SETUP AUTOMATICO..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Setup automatico via SSH
Start-Sleep -Seconds 30  # Aguardar boot

$setupScript = @"
#!/bin/bash
set -e
echo "[SYNTEXA] Setup GPU iniciado..."

# Verificar GPU
nvidia-smi

# Clonar repo
sudo mkdir -p /opt/syntexa
sudo chown ubuntu:ubuntu /opt/syntexa
cd /opt/syntexa

# Instalar dependencias
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -q transformers accelerate datasets sentencepiece protobuf
pip install -q deepspeed ninja

echo "[SYNTEXA] Setup completo!"
echo "[SYNTEXA] GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
"@

$setupScript | ssh -i $AWS_KEY -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 "ubuntu@$publicIp" "cat > /tmp/setup.sh && bash /tmp/setup.sh" 2>$null

Write-Host ""
Write-Host "[OK] Setup completo na GPU!" -ForegroundColor Green
Write-Host "[INFO] Proximo passo: copiar codigo e iniciar treinamento 7B" -ForegroundColor Yellow
