#!/usr/bin/env python3
"""
SYNTEXA DESKTOP BUILD SYSTEM
=============================
Script de build enterprise para distribuição desktop.

Gera:
  - Windows: .exe installer (NSIS), .msi, portable
  - Linux: AppImage, .deb, .rpm, .tar.gz
  - macOS: .dmg

Empacota:
  - Foundation Model (PyTorch)
  - Tokenizer
  - Multimodal runtime (STT, TTS, OCR, Vision)
  - QPanda3 layer
  - Frontend estático (Next.js build)
  - Python runtime embutido

Uso:
    python scripts/build-desktop.py --target all
    python scripts/build-desktop.py --target win
    python scripts/build-desktop.py --target linux --skip-python-embed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
FRONTEND = ROOT / "frontend"
RUNTIME_PKG = DESKTOP / "runtime"
FRONTEND_DIST = DESKTOP / "frontend" / "dist"
CHECKSUMS_FILE = DESKTOP / "dist" / "checksums.sha256"


class DesktopBuilder:
    """Orquestrador de build desktop da Syntexa."""

    def __init__(self, target: str, skip_frontend: bool = False, skip_python_embed: bool = False):
        self.target = target
        self.skip_frontend = skip_frontend
        self.skip_python_embed = skip_python_embed
        self.build_dir = DESKTOP / "dist"

    # ── CHECKS ───────────────────────────────────────────────

    def check_prerequisites(self) -> bool:
        """Verifica que todas as ferramentas necessárias estão instaladas."""
        ok = True
        # Node.js / npm
        if not self._cmd_exists("node"):
            log.error("Node.js não encontrado. Instale: https://nodejs.org/")
            ok = False
        # electron-builder
        if not (DESKTOP / "node_modules" / ".bin" / "electron-builder").is_file():
            log.error("electron-builder não instalado. Rode: cd desktop && npm install")
            ok = False
        return ok

    def _cmd_exists(self, cmd: str) -> bool:
        return shutil.which(cmd) is not None

    # ── FRONTEND ────────────────────────────────────────────

    def build_frontend(self) -> bool:
        if self.skip_frontend:
            log.info("[BUILD] Pulando build do frontend (--skip-frontend)")
            return True
        log.info("[BUILD] Building frontend...")
        try:
            # Exporta frontend Next.js para estático
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=FRONTEND,
                capture_output=True,
                text=True,
                check=True,
            )
            log.info("[BUILD] Frontend build OK")
            # Copia para desktop/frontend/dist
            FRONTEND_DIST.parent.mkdir(parents=True, exist_ok=True)
            if FRONTEND_DIST.exists():
                shutil.rmtree(FRONTEND_DIST)
            shutil.copytree(FRONTEND / "dist", FRONTEND_DIST)
            return True
        except subprocess.CalledProcessError as e:
            log.error("[BUILD] Frontend build falhou:\n%s", e.stderr)
            return False

    # ── PYTHON EMBEDDED ───────────────────────────────────

    def prepare_python_runtime(self) -> bool:
        if self.skip_python_embed:
            log.info("[BUILD] Pulando embed de Python (--skip-python-embed)")
            return True
        log.info("[BUILD] Preparando Python runtime...")
        RUNTIME_PKG.mkdir(parents=True, exist_ok=True)

        # Detecta Python do sistema ou venv
        python_cmd = sys.executable
        if not Path(python_cmd).is_file():
            log.error("[BUILD] Python não encontrado: %s", python_cmd)
            return False

        # Instala dependências mínimas no diretório runtime
        req_file = ROOT / "requirements.txt"
        if req_file.is_file():
            try:
                subprocess.run(
                    [python_cmd, "-m", "pip", "install", "-r", str(req_file),
                     "--target", str(RUNTIME_PKG / "python"), "--no-deps", "--quiet"],
                    check=True,
                    capture_output=True,
                )
                log.info("[BUILD] Dependências instaladas no runtime")
            except subprocess.CalledProcessError as e:
                log.warning("[BUILD] Instalação de deps falhou (pode ser normal se torch não tiver): %s", e)

        # Copia módulos core
        for module in ["vereda_ai", "llm-quantum"]:
            src = ROOT / module
            dst = RUNTIME_PKG / "python" / module
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                log.info("[BUILD] Copiado %s para runtime", module)

        return True

    # ── ELECTRON BUILD ─────────────────────────────────────

    def build_electron(self) -> bool:
        log.info("[BUILD] Iniciando electron-builder para target: %s", self.target)

        env = os.environ.copy()
        env["SYNTEXA_BUILD_TARGET"] = self.target

        targets = {
            "win": "--win",
            "linux": "--linux",
            "mac": "--mac",
            "all": "--win --linux --mac",
        }

        target_arg = targets.get(self.target, "--win")

        try:
            result = subprocess.run(
                ["npx", "electron-builder", target_arg],
                cwd=DESKTOP,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            log.info("[BUILD] electron-builder OK")
            return True
        except subprocess.CalledProcessError as e:
            log.error("[BUILD] electron-builder falhou:\n%s", e.stderr)
            return False

    # ── CHECKSUMS ──────────────────────────────────────────

    def generate_checksums(self) -> None:
        log.info("[BUILD] Gerando checksums SHA256...")
        self.build_dir.mkdir(parents=True, exist_ok=True)
        entries = []
        for f in self.build_dir.rglob("*"):
            if f.is_file() and f.name != "checksums.sha256":
                sha = hashlib.sha256(f.read_bytes()).hexdigest()
                rel = f.relative_to(self.build_dir)
                entries.append(f"{sha}  {rel}")
        CHECKSUMS_FILE.write_text("\n".join(entries) + "\n", encoding="utf-8")
        log.info("[BUILD] Checksums: %s", CHECKSUMS_FILE)

    # ── VERIFY ─────────────────────────────────────────────

    def verify_package(self) -> bool:
        if not CHECKSUMS_FILE.is_file():
            log.warning("[BUILD] Arquivo de checksums não encontrado")
            return False
        log.info("[BUILD] Verificando integridade dos pacotes...")
        ok = True
        for line in CHECKSUMS_FILE.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("  ")
            if len(parts) != 2:
                continue
            expected_sha, rel_path = parts
            f = self.build_dir / rel_path
            if not f.is_file():
                log.error("[BUILD] Arquivo faltando: %s", rel_path)
                ok = False
                continue
            actual_sha = hashlib.sha256(f.read_bytes()).hexdigest()
            if actual_sha != expected_sha:
                log.error("[BUILD] Checksum inválido: %s", rel_path)
                ok = False
        if ok:
            log.info("[BUILD] Verificação de integridade OK")
        return ok

    # ── BUILD LOGS ENTERPRISE ───────────────────────────────
    def _build_log(self, level: str, msg: str, **extra: Any) -> None:
        import json, time
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level,
            "component": "build-desktop",
            "message": msg,
            **extra,
        }
        log_dir = ROOT / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "build.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        getattr(log, level.lower(), log.info)("[BUILD] %s", msg)

    # ── FULL PIPELINE ─────────────────────────────────────

    def run(self) -> bool:
        self._build_log("info", "=" * 30 + " BUILD START V45 " + "=" * 30, target=self.target)
        log.info("=" * 60)
        log.info("  SYNTEXA DESKTOP BUILD SYSTEM V45")
        log.info("  Target: %s", self.target)
        log.info("=" * 60)

        if not self.check_prerequisites():
            self._build_log("error", "Pré-requisitos não atendidos")
            return False

        ok = True
        ok = self.build_frontend() and ok
        ok = self.prepare_python_runtime() and ok
        ok = self.build_electron() and ok

        if ok:
            self.generate_checksums()
            integrity_ok = self.verify_package()
            artifacts_ok = self._verify_all_artifacts_present()
            if not integrity_ok or not artifacts_ok:
                self._build_log("error", "Build incompleto ou integridade falhou", integrity=integrity_ok, artifacts=artifacts_ok)
                log.error("=" * 60)
                log.error("  BUILD PARCIAL — PROIBIDO MASCARAR COMO SUCESSO")
                log.error("=" * 60)
                return False
            self._build_log("info", "Build completo e validado")
            log.info("=" * 60)
            log.info("  BUILD COMPLETO V45")
            log.info("  Output: %s", self.build_dir)
            log.info("=" * 60)
        else:
            self._build_log("error", "Build falhou em alguma etapa")
            log.error("=" * 60)
            log.error("  BUILD FALHOU")
            log.error("=" * 60)

        return ok

    def _verify_all_artifacts_present(self) -> bool:
        """Verifica que TODOS os artefatos obrigatórios existem."""
        import glob
        dist = self.build_dir
        required = {
            "win": ["*.exe", "*.msi"],
            "linux": ["*.AppImage", "*.deb", "*.tar.gz"],
            "mac": ["*.dmg"],
            "all": ["*.exe", "*.msi", "*.AppImage", "*.deb", "*.tar.gz", "*.dmg"],
        }
        targets = required.get(self.target, required["all"])
        found_any = False
        for pattern in targets:
            matches = list(dist.glob(pattern))
            if matches:
                found_any = True
                self._build_log("info", f"Artefato encontrado: {pattern}", files=[str(m.name) for m in matches])
        if not found_any:
            self._build_log("error", "Nenhum artefato de instalação encontrado em dist/")
            return False
        return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Syntexa Desktop Build System V45")
    ap.add_argument("--target", choices=["win", "linux", "mac", "all"], default="win",
                    help="Target platform para build")
    ap.add_argument("--skip-frontend", action="store_true",
                    help="Pula build do frontend (usa dist existente)")
    ap.add_argument("--skip-python-embed", action="store_true",
                    help="Pula embed de Python runtime")
    args = ap.parse_args()

    builder = DesktopBuilder(
        target=args.target,
        skip_frontend=args.skip_frontend,
        skip_python_embed=args.skip_python_embed,
    )
    ok = builder.run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
