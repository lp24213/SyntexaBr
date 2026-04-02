# Syntexa AI — App Desktop (Windows)

App desktop que abre o Syntexa no Windows (instalador completo).

## O que é gerado

- **Instalador** `dist/Syntexa AI Setup 1.0.0.exe` — instala no PC, atalho no Menu Iniciar e na área de trabalho.
- **Portable** `dist/Syntexa AI 1.0.0.exe` — executa sem instalar (opcional).

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

### 3. Gerar o instalador completo

```powershell
npm run build
```

Saída em `desktop\dist\`:

- `Syntexa AI Setup 1.0.0.exe` — instalador (escolher pasta, atalhos, desinstalar pelo Painel).
- `Syntexa AI 1.0.0.exe` — versão portable.

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

Suba o arquivo `Syntexa AI Setup 1.0.0.exe` para o seu site ou canal de download. O usuário baixa, executa, escolhe a pasta (ou deixa padrão), instala e passa a abrir o Syntexa pelo atalho.
