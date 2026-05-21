#!/usr/bin/env bash
# SYNTEXA DESKTOP BUILD — Linux Enterprise Pipeline V45
# Build completo de distribuição desktop Linux:
# - Empacota Python + dependências
# - Build Electron com AppImage, .deb, tar.gz
# - Gera checksums SHA256
# - Cria manifesto de runtime
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DESKTOP_DIR="${ROOT}/desktop"
FRONTEND_DIR="${ROOT}/frontend"
RUNTIME_DIR="${DESKTOP_DIR}/runtime"
DIST_DIR="${DESKTOP_DIR}/dist"
MANIFEST_PATH="${DESKTOP_DIR}/runtime-manifest.json"

PYTHON_VERSION="${PYTHON_VERSION:-3.11.9}"
CONFIG="${CONFIG:-Release}"
SKIP_PYTHON_PACK="${SKIP_PYTHON_PACK:-0}"
SKIP_FRONTEND_BUILD="${SKIP_FRONTEND_BUILD:-0}"
SKIP_ELECTRON_BUILD="${SKIP_ELECTRON_BUILD:-0}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SYNTEXA DESKTOP BUILD V45 — LINUX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Root:        ${ROOT}"
echo "Desktop:     ${DESKTOP_DIR}"
echo "Frontend:    ${FRONTEND_DIR}"
echo "Runtime:     ${RUNTIME_DIR}"
echo "Output:      ${DIST_DIR}"
echo "Config:      ${CONFIG}"
echo ""

step() { echo -e "\n▶ $1"; }
ok()   { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; exit 1; }

# ── PREREQUISITES ──────────────────────────────────────────
step "Verificando pré-requisitos..."
command -v node >/dev/null 2>&1 || fail "Node.js não encontrado"
command -v npm >/dev/null 2>&1 || fail "npm não encontrado"
ok "Node.js $(node --version)"

# Detect CUDA / ROCm
if command -v nvidia-smi >/dev/null 2>&1; then
    CUDA_AVAILABLE=1
    ok "CUDA detectado: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
else
    CUDA_AVAILABLE=0
    echo "  ! CUDA não detectado. Build usará CPU fallback."
fi

# ── FRONTEND BUILD ─────────────────────────────────────────
if [ "$SKIP_FRONTEND_BUILD" != "1" ]; then
    step "Build do frontend (Next.js)..."
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        echo "  → Instalando dependências frontend..."
        npm ci --prefer-offline --no-audit --no-fund
    fi
    NODE_ENV=production npm run build
    if [ ! -d "dist" ] && [ -d "out" ]; then
        mv out dist
    fi
    [ -d "dist" ] || fail "Build do frontend não gerou dist/"
    ok "Frontend build concluído"
else
    ok "Frontend build pulado"
fi

# ── PYTHON RUNTIME PACKAGING ─────────────────────────────
if [ "$SKIP_PYTHON_PACK" != "1" ]; then
    step "Empacotando Python runtime soberano..."

    # Usa python do sistema ou pyenv
    PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python || echo '')}"
    [ -n "$PYTHON_BIN" ] || fail "Python não encontrado. Instale python3."
    ok "Python: $($PYTHON_BIN --version)"

    PY_MAJOR=$($PYTHON_BIN -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$($PYTHON_BIN -c "import sys; print(sys.version_info.minor)")
    PY_VER="${PY_MAJOR}.${PY_MINOR}"

    # Cria venv isolado para o runtime
    VENV_DIR="${RUNTIME_DIR}/python"
    if [ ! -d "$VENV_DIR" ]; then
        echo "  → Criando venv em ${VENV_DIR}..."
        mkdir -p "$RUNTIME_DIR"
        "$PYTHON_BIN" -m venv "$VENV_DIR"
        ok "Venv criado"
    fi

    PIP="${VENV_DIR}/bin/pip"
    [ -f "$PIP" ] || PIP="${VENV_DIR}/bin/pip3"

    echo "  → Instalando dependências Python soberanas..."
    "$PIP" install --upgrade pip setuptools wheel

    REQ_FILE="${ROOT}/requirements.txt"
    [ -f "$REQ_FILE" ] && "$PIP" install -r "$REQ_FILE" --prefer-binary

    # Instala extras desktop
    DESKTOP_EXTRAS=(
        "fastapi" "uvicorn[standard]" "pydantic>=2.0" "python-multipart"
        "transformers" "accelerate" "bitsandbytes"
        "sentencepiece" "protobuf"
        "openai-whisper" "easyocr" "pdf2image"
        "pillow" "numpy" "requests"
    )

    # Torch com CUDA se disponível
    if [ "$CUDA_AVAILABLE" = "1" ]; then
        DESKTOP_EXTRAS+=("torch --index-url https://download.pytorch.org/whl/cu121")
        DESKTOP_EXTRAS+=("torchaudio --index-url https://download.pytorch.org/whl/cu121")
    else
        DESKTOP_EXTRAS+=("torch --index-url https://download.pytorch.org/whl/cpu")
    fi

    for pkg in "${DESKTOP_EXTRAS[@]}"; do
        echo "    → $pkg"
        $PIP install $pkg --prefer-binary 2>/dev/null || echo "      ! aviso: falha ao instalar $pkg"
    done

    # llama-cpp-python com CUDA se disponível
    if [ "$CUDA_AVAILABLE" = "1" ]; then
        CMAKE_ARGS="-DLLAMA_CUDA=on" FORCE_CMAKE=1 $PIP install llama-cpp-python --no-cache-dir 2>/dev/null || echo "      ! aviso: llama-cpp-python com CUDA falhou"
    else
        $PIP install llama-cpp-python --no-cache-dir 2>/dev/null || echo "      ! aviso: llama-cpp-python falhou"
    fi

    # TTS
    $PIP install TTS --prefer-binary 2>/dev/null || echo "      ! aviso: TTS falhou"

    ok "Dependências Python instaladas"

    # Copia vereda_ai
    VEREDA_SRC="${ROOT}/vereda_ai"
    SITE_PACKAGES="${VENV_DIR}/lib/python${PY_VER}/site-packages"
    VEREDA_DST="${SITE_PACKAGES}/vereda_ai"
    if [ -d "$VEREDA_SRC" ]; then
        rm -rf "$VEREDA_DST" 2>/dev/null || true
        cp -r "$VEREDA_SRC" "$VEREDA_DST"
        ok "vereda_ai copiado para site-packages"
    fi

    # Copia backend server
    BACKEND_DST="${RUNTIME_DIR}/backend"
    mkdir -p "$BACKEND_DST"
    cp -r "${DESKTOP_DIR}/backend/"* "$BACKEND_DST/"
    ok "Backend server copiado"

    # Gera manifesto
    python3 -c "
import json, os, hashlib
from pathlib import Path
root = Path('${RUNTIME_DIR}')
manifest = {
    'version': '45.0.0',
    'platform': 'linux',
    'arch': 'x64',
    'python_version': '${PY_VER}',
    'timestamp': __import__('datetime').datetime.now().isoformat(),
    'cuda_available': ${CUDA_AVAILABLE} == 1,
    'files': []
}
for f in root.rglob('*'):
    if f.is_file():
        rel = str(f.relative_to(root)).replace('\\', '/')
        manifest['files'].append({
            'path': rel,
            'size': f.stat().st_size,
            'sha256': hashlib.sha256(f.read_bytes()).hexdigest()
        })
with open('${MANIFEST_PATH}', 'w', encoding='utf-8') as fp:
    json.dump(manifest, fp, indent=2, ensure_ascii=False)
"
    ok "Manifesto de runtime gerado"
else
    ok "Python packaging pulado"
fi

# ── ELECTRON BUILD ───────────────────────────────────────
if [ "$SKIP_ELECTRON_BUILD" != "1" ]; then
    step "Build Electron (electron-builder)..."
    cd "$DESKTOP_DIR"
    if [ ! -d "node_modules" ]; then
        echo "  → Instalando dependências desktop..."
        npm ci --prefer-offline --no-audit --no-fund
    fi

    rm -rf "$DIST_DIR"
    mkdir -p "$DIST_DIR"

    NODE_ENV=production npm run build:linux

    artifacts=($(ls -1 "$DIST_DIR" 2>/dev/null || true))
    if [ ${#artifacts[@]} -eq 0 ]; then
        fail "Electron build não gerou artefatos"
    fi
    ok "Electron build concluído: ${#artifacts[@]} artefatos"
    for a in "${artifacts[@]}"; do
        size=$(du -h "$DIST_DIR/$a" | cut -f1)
        echo "    → $a ($size)"
    done
else
    ok "Electron build pulado"
fi

# ── CHECKSUMS ──────────────────────────────────────────────
step "Gerando checksums..."
cd "$DIST_DIR"
sha256sum * > SHA256SUMS.txt 2>/dev/null || true
ok "SHA256SUMS gerado"

# Manifesto final
python3 -c "
import json, os, hashlib
from pathlib import Path
dist = Path('${DIST_DIR}')
manifest = {
    'product': 'Syntexa AI',
    'version': '45.0.0',
    'build_id': __import__('uuid').uuid4().hex,
    'timestamp': __import__('datetime').datetime.now().isoformat(),
    'platform': 'linux',
    'arch': 'x64',
    'artifacts': []
}
for f in dist.iterdir():
    if f.is_file():
        manifest['artifacts'].append({
            'name': f.name,
            'size': f.stat().st_size,
            'sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
            'signed': False
        })
with open('syntexa-manifest-v45.json', 'w', encoding='utf-8') as fp:
    json.dump(manifest, fp, indent=2, ensure_ascii=False)
"
ok "Manifesto final gerado"

# ── FINAL ──────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BUILD V45 CONCLUÍDO COM SUCESSO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Artefatos em: ${DIST_DIR}"
echo ""
ls -lh "$DIST_DIR"
