# Syntexa AI — App Desktop (Windows)

App desktop que abre o Syntexa no Windows (instalador completo).

## O que é gerado

- **Windows:** `dist/SyntexaAI-Setup-1.0.0.exe` (NSIS) — instalador real; após `npm run build` os ficheiros estáveis vão para `frontend/public/download/` (incluídos no site em `/download/...`).
- **Linux (no mesmo `npm run build` em Windows):** `.deb` e `.tar.gz` para Ubuntu/amd64.
- **macOS:** correr `npm run build:mac` num Mac; o `.dmg` é copiado com o mesmo script. Sem `.dmg`, o site mostra macOS como «em breve».

## Pré-requisitos

- Node.js 18+ instalado
- Windows (build é só para Win)

## Comandos (PowerShell)

### 1. Instalar dependências

```powershell
cd "C:\Users\luisp\OneDrive\Área de Trabalho\syntexabr\desktop"
npm install
```

### 2. Rodar o app (testar sem instalar)

```powershell
npm start
```

### 3. Gerar instaladores (Windows + Linux)

```powershell
npm run build
```

Saída em `desktop\dist\` e cópia estável em `frontend\public\download\` (nomes fixos para o CDN).

### Só portable (sem instalador)

```powershell
npm run build:portable
```

## Ícone (opcional)

Coloque um `.ico` em:

```
desktop\build\icon.ico
```

Recomendado: 256x256. Se não existir, o Electron usa o ícone padrão.

## Distribuir

O deploy do site (`deploy-syntexa.ps1 deploy-front`) executa `npm run build` aqui e publica os ficheiros em `https://syntexabr.com.br/download/...` (binários reais no CDN).
