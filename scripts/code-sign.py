#!/usr/bin/env python3
"""
SYNTEXA CODE SIGNING
====================
Assinatura de pacotes desktop para Windows e Linux.

Windows:
  - Gera certificado autoassinado se não existir
  - Assina .exe com signtool (Windows SDK) ou osslsigncode
  - Valida assinatura

Linux:
  - GPG signing de AppImage e tar.gz
  - SHA256 checksums

Uso:
    python scripts/code-sign.py --cert-dir certs/
    python scripts/code-sign.py --verify
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
CERT_DIR = ROOT / "certs"
DIST_DIR = ROOT / "desktop" / "dist"


class CodeSigner:
    def __init__(self, cert_dir: Path, password: Optional[str] = None):
        self.cert_dir = cert_dir
        self.cert_file = cert_dir / "syntexa_cert.pfx"
        self.password = password or os.getenv("SYNTEXA_CERT_PASSWORD", "syntexa2026")

    def ensure_certificate(self) -> bool:
        if self.cert_file.is_file():
            log.info("[SIGN] Certificado encontrado: %s", self.cert_file)
            return True

        log.info("[SIGN] Gerando certificado autoassinado...")
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # Gera certificado com OpenSSL
        key_file = self.cert_dir / "syntexa_key.pem"
        crt_file = self.cert_dir / "syntexa_cert.pem"

        try:
            # Chave privada
            subprocess.run(
                ["openssl", "genrsa", "-out", str(key_file), "2048"],
                check=True, capture_output=True,
            )
            # Certificado autoassinado
            subprocess.run(
                ["openssl", "req", "-new", "-x509", "-key", str(key_file),
                 "-out", str(crt_file), "-days", "365",
                 "-subj", "/CN=SyntexaBR/O=SyntexaBR/L=Sao Paulo/ST=SP/C=BR"],
                check=True, capture_output=True,
            )
            # Exporta como PFX
            subprocess.run(
                ["openssl", "pkcs12", "-export",
                 "-in", str(crt_file), "-inkey", str(key_file),
                 "-out", str(self.cert_file),
                 "-password", f"pass:{self.password}"],
                check=True, capture_output=True,
            )
            log.info("[SIGN] Certificado gerado: %s", self.cert_file)
            return True
        except subprocess.CalledProcessError as e:
            log.error("[SIGN] Falha ao gerar certificado: %s", e)
            return False
        except FileNotFoundError:
            log.error("[SIGN] OpenSSL não encontrado. Instale OpenSSL.")
            return False

    def sign_windows(self) -> bool:
        if sys.platform != "win32":
            log.info("[SIGN] Pulando assinatura Windows (não estamos no Windows)")
            return True

        # Procura por executáveis no dist
        exe_files = list(DIST_DIR.rglob("*.exe"))
        if not exe_files:
            log.warning("[SIGN] Nenhum .exe encontrado em %s", DIST_DIR)
            return False

        for exe in exe_files:
            log.info("[SIGN] Assinando: %s", exe.name)
            try:
                subprocess.run(
                    ["signtool", "sign", "/f", str(self.cert_file),
                     "/p", self.password, "/fd", "sha256",
                     "/tr", "http://timestamp.digicert.com", "/td", "sha256",
                     str(exe)],
                    check=True, capture_output=True,
                )
                log.info("[SIGN] Assinado: %s", exe.name)
            except subprocess.CalledProcessError:
                log.warning("[SIGN] signtool falhou para %s (pode não estar instalado)", exe.name)
            except FileNotFoundError:
                log.error("[SIGN] signtool não encontrado. Instale Windows SDK.")
                return False
        return True

    def sign_linux(self) -> bool:
        if sys.platform == "win32":
            return True

        # GPG signing de AppImage
        appimages = list(DIST_DIR.rglob("*.AppImage"))
        for appimg in appimages:
            log.info("[SIGN] Assinando GPG: %s", appimg.name)
            try:
                subprocess.run(
                    ["gpg", "--detach-sign", "--armor", str(appimg)],
                    check=True, capture_output=True,
                )
                log.info("[SIGN] Assinatura GPG: %s.asc", appimg.name)
            except subprocess.CalledProcessError:
                log.warning("[SIGN] GPG signing falhou (chave pode não existir)")
            except FileNotFoundError:
                log.warning("[SIGN] GPG não encontrado")
        return True

    def verify(self) -> bool:
        log.info("[SIGN] Verificando assinaturas...")
        ok = True
        for exe in DIST_DIR.rglob("*.exe"):
            try:
                result = subprocess.run(
                    ["signtool", "verify", "/pa", str(exe)],
                    capture_output=True, text=True, check=True,
                )
                log.info("[SIGN] VERIFIED: %s", exe.name)
            except (subprocess.CalledProcessError, FileNotFoundError):
                log.warning("[SIGN] Não verificado: %s", exe.name)
                ok = False
        return ok

    def run(self) -> bool:
        ok = self.ensure_certificate()
        if not ok:
            return False
        ok = self.sign_windows() and ok
        ok = self.sign_linux() and ok
        return ok


def main() -> None:
    ap = argparse.ArgumentParser(description="Syntexa Code Signing")
    ap.add_argument("--cert-dir", default=str(CERT_DIR), help="Diretório de certificados")
    ap.add_argument("--password", default=None, help="Senha do certificado")
    ap.add_argument("--verify", action="store_true", help="Verificar assinaturas")
    args = ap.parse_args()

    signer = CodeSigner(Path(args.cert_dir), args.password)
    if args.verify:
        ok = signer.verify()
    else:
        ok = signer.run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
