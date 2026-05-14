@echo off
chcp 65001 >nul
title Syntexa Railway Deploy
color 0A

echo =========================================
echo   SYNTEXA SOVEREIGN AI - RAILWAY DEPLOY
echo =========================================
echo.

:: Verificar Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [1/7] Node.js nao encontrado. Baixando...
    powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi' -OutFile '%TEMP%\nodejs.msi'"
    start /wait msiexec /i "%TEMP%\nodejs.msi" /quiet /norestart
    del "%TEMP%\nodejs.msi" /f
    setx PATH "%PATH%;C:\Program Files\nodejs" /M
    echo Node.js instalado!
) else (
    echo [1/7] Node.js OK
    node --version
)

echo.
echo [2/7] Instalando Railway CLI...
npm install -g @railway/cli

echo.
echo [3/7] =========================================
echo  FACA LOGIN NO RAILWAY AGORA
echo  Copie a URL que aparecer abaixo e cole no navegador
echo  Depois de autorizar, volte aqui
echo =========================================
pause
railway login

echo.
echo [4/7] Criando projeto...
cd /d "C:\Users\luisp\OneDrive\Área de Trabalho\syntexabr"
railway init --name syntexa-backend

echo.
echo [5/7] Adicionando PostgreSQL...
railway add --database postgres

echo.
echo [6/7] Adicionando Redis...
railway add --database redis

echo.
echo [7/7] Configurando variaveis...
railway variables set VEREDA_SECRET_KEY="syntexa-key-%RANDOM%%RANDOM%%RANDOM%"
railway variables set VEREDA_ADMIN_EMAIL="admin@syntexabr.com.br"
railway variables set VEREDA_ADMIN_PASSWORD="Syntexa%RANDOM%%RANDOM%!"
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

echo.
echo =========================================
echo   FAZENDO DEPLOY...
echo =========================================
railway up

echo.
echo =========================================
echo   DEPLOY CONCLUIDO!
echo =========================================
echo URL do projeto:
railway domain

echo.
echo Comandos uteis:
echo   railway logs     - ver logs
echo   railway open     - abrir no navegador
echo   railway status   - status do deploy
echo.
pause
