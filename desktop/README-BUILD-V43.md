# SYNTEXA DESKTOP — Build V43 Enterprise

## Distribuição Soberana Desktop + Runtime 70B + Chat Cinematográfico

### Builds Gerados

| Plataforma | Formato | Arquivo |
|---|---|---|
| Windows | NSIS Installer | `SyntexaAI-{version}-Setup.exe` |
| Windows | MSI Installer | `SyntexaAI-{version}-Installer.msi` |
| Windows | Portable | `SyntexaAI-{version}-Portable.exe` |
| Linux | AppImage | `SyntexaAI-{version}-linux-x64.AppImage` |
| Linux | Debian | `SyntexaAI-{version}-linux-x64.deb` |
| Linux | Tarball | `SyntexaAI-{version}-linux-x64.tar.gz` |

### Requisitos

- **Node.js** 18+ e npm
- **Python** 3.10+ (para empacotar runtime)
- **electron-builder** 24.9.1+
- Windows: PowerShell 7+, opcional signtool.exe para assinatura
- Linux: bash, venv, opcional fusermount para AppImage

### Build Windows

```powershell
# Build completo (frontend + runtime + electron)
cd desktop
npm run build:full

# Ou passo a passo:
npm run copy-artifacts    # Copia artefatos para vereda_backend/static/desktop
npm run verify            # Verifica integridade do build
```

### Build Linux

```bash
cd desktop
npm run build:full:linux
```

### Parâmetros de Build

| Variável | Descrição |
|---|---|
| `SYNTEXA_CERT_FILE` | Caminho do certificado de assinatura (.pfx) |
| `SYNTEXA_CERT_PASS` | Senha do certificado |
| `SYNTEXA_GGUF_PATH` | Caminho do modelo GGUF para llama.cpp |
| `SYNTEXA_LOCAL_MODEL` | Nome/caminho do modelo transformers |

### Runtime Empacotado

O build inclui automaticamente:
- Python embeddable (Windows) ou venv (Linux)
- Dependências: fastapi, uvicorn, torch, transformers, llama-cpp-python
- Módulos vereda_ai (foundation model, multimodal)
- Backend server (`desktop_server.py`)

### Anti-Download-Broken

- **SHA256SUMS.txt**: Checksums de todos os artefatos
- **runtime-manifest.json**: Manifesto com SHA256 de cada arquivo do runtime
- **syntexa-manifest-v43.json**: Manifesto assinado do build
- Verificação automática via `npm run verify`

### Fail-Fast

O backend desktop_server.py implementa:
- Erro real se nenhum modelo carregado (HTTP 503)
- Erro real se resposta vazia do LLM
- Fallback GGUF → transformers → erro claro
- Streaming com error propagation real

### Chat Cinematográfico

- `NeuralTopologyCanvas`: Fundo procedural com nodes, edges, particles
- Integração no chat quando `visible.length === 0` ou `desktopMode === true`
- Badge desktop indicando estado do runtime

### Integração Frontend

O chat detecta modo desktop via:
- `window.__DESKTOP_MODE__` (setado pelo preload.js)
- Se desktop e backend pronto: usa `desktopChatStream()` (offline)
- Se desktop e backend não pronto: mostra erro real
- Se web: fallback para API online
