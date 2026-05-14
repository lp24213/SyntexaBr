# Syntexa Backend — Railway Deploy Script
# Execute este script no PowerShell como Administrador

Write-Host "=== SYNTEXA RAILWAY DEPLOY ===" -ForegroundColor Cyan

# Verificar se Node.js está instalado
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js nao encontrado. Instalando..." -ForegroundColor Yellow
    # Download Node.js installer
    $nodeUrl = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi"
    $nodeInstaller = "$env:TEMP\nodejs.msi"
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller
    Start-Process msiexec.exe -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart" -Wait
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Remove-Item $nodeInstaller -Force
}

# Instalar Railway CLI
Write-Host "Instalando Railway CLI..." -ForegroundColor Green
npm install -g @railway/cli

# Navegar para o projeto
$projectPath = "C:\Users\luisp\OneDrive\Área de Trabalho\syntexabr"
Set-Location $projectPath

# Login no Railway (abre navegador)
Write-Host "Abrindo navegador para login no Railway..." -ForegroundColor Cyan
railway login

# Criar projeto
Write-Host "Criando projeto Syntexa no Railway..." -ForegroundColor Green
railway init --name syntexa-backend

# Adicionar bancos
Write-Host "Adicionando PostgreSQL..." -ForegroundColor Green
railway add --database postgres

Write-Host "Adicionando Redis..." -ForegroundColor Green
railway add --database redis

# Configurar variáveis
Write-Host "Configurando variáveis de ambiente..." -ForegroundColor Green
railway variables set VEREDA_SECRET_KEY="syntexa-sovereign-2026-$(Get-Random -Maximum 999999)"
railway variables set VEREDA_ADMIN_EMAIL="admin@syntexabr.com.br"
railway variables set VEREDA_ADMIN_PASSWORD="SyntexaAdmin$(Get-Random -Maximum 999999)!"
railway variables set DEFAULT_LLM="syntexa_native"
railway variables set API_V1_PREFIX="/v1"
railway variables set FRONTEND_ORIGIN="https://syntexabr.com.br"
railway variables set FRONTEND_BASE_URL="https://syntexabr.com.br"
railway variables set API_PUBLIC_BASE_URL="https://api.syntexabr.com.br"
railway variables set AUTONOMY_EVOLUTION_LOOP_ENABLED="true"
railway variables set CHAT_STRICT_REAL_PROVIDERS="false"
railway variables set UVICORN_WORKERS="2"
railway variables set UVICORN_TIMEOUT_KEEPALIVE="120"
railway variables set PYTHONUNBUFFERED="1"
railway variables set ENVIRONMENT="production"

# Deploy
Write-Host "Iniciando deploy..." -ForegroundColor Green
railway up

# Mostrar URL
Write-Host "=== DEPLOY CONCLUIDO ===" -ForegroundColor Green
Write-Host "URL do projeto:" -ForegroundColor Cyan
railway domain

Write-Host ""
Write-Host "Para ver logs:" -ForegroundColor Yellow
Write-Host "  railway logs" -ForegroundColor White
Write-Host ""
Write-Host "Para abrir no navegador:" -ForegroundColor Yellow
Write-Host "  railway open" -ForegroundColor White
