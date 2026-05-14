# Syntexa Backend - Deploy Automatico no Railway
# Execute: .\deploy-backend-railway.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== SYNTEXA BACKEND - RAILWAY DEPLOY ===" -ForegroundColor Cyan

# Verificar login
$status = railway status 2>&1
if ($status -match "not logged in") {
    Write-Host "ERRO: Nao esta logado no Railway. Rode 'railway login' primeiro." -ForegroundColor Red
    exit 1
}

# Selecionar projeto syntexa-br
Write-Host "Selecionando projeto syntexa-br..." -ForegroundColor Green
railway link --project syntexa-br --environment production

# Verificar se servico syntexa-backend existe
$services = railway service list 2>&1
$serviceName = "syntexa-backend"

if ($services -match $serviceName) {
    Write-Host "Servico $serviceName encontrado. Selecionando..." -ForegroundColor Green
    railway service $serviceName
} else {
    Write-Host "Servico $serviceName NAO encontrado. Criando agora..." -ForegroundColor Yellow
    railway service create $serviceName
    railway service $serviceName
}

# Fazer deploy
Write-Host "Iniciando deploy..." -ForegroundColor Green
railway up

# Mostrar status
Write-Host "=== DEPLOY CONCLUIDO ===" -ForegroundColor Green
railway status
railway domain

Write-Host ""
Write-Host "Logs: railway logs" -ForegroundColor Yellow
Write-Host "Abrir dashboard: railway open" -ForegroundColor Yellow
