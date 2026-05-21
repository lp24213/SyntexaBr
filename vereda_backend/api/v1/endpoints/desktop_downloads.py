"""Instaladores desktop: ficheiros em vereda_backend/static/desktop/ (FileResponse)."""

from pathlib import Path, PurePosixPath
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse

from vereda_backend.core.config import settings

router = APIRouter(prefix="/desktop", tags=["desktop"])

_ASSET_TO_SETTING = {
    "SyntexaAI-Setup-1.0.0.exe": "desktop_windows_url",
    "SyntexaAI-macos-universal.dmg": "desktop_macos_url",
    "SyntexaAI-linux-x64.tar.gz": "desktop_linux_url",
    "SyntexaAI-android-arm64.apk": "desktop_android_url",
}


def _safe_filename(raw: str) -> str:
    name = PurePosixPath(raw.strip()).name
    if not name or name != raw.strip() or "/" in raw or raw.startswith("."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de ficheiro inválido.",
        )
    return name


def _desktop_artifacts_dir() -> Path:
    # desktop_downloads.py → parents[3] = vereda_backend/
    return (Path(__file__).resolve().parents[3] / "static" / "desktop").resolve()


def _api_binary_url(filename: str) -> str:
    base = getattr(settings, "api_public_base_url", "https://api.syntexabr.com.br").rstrip("/")
    return f"{base}/v1/desktop/binary/{quote(filename, safe='')}"


@router.get("/binary/")
@router.head("/binary/")
def redirect_binary_root() -> RedirectResponse:
    """Redireciona /v1/desktop/binary/ → página pública de downloads."""
    base = getattr(settings, "frontend_base_url", "https://syntexabr.com.br").rstrip("/")
    return RedirectResponse(url=f"{base}/download", status_code=302)


@router.get("/binary/{filename}")
@router.head("/binary/{filename}")
def serve_desktop_binary(filename: str) -> FileResponse:
    """Entrega o binário real (Electron) guardado no disco do servidor após deploy-back."""
    safe = _safe_filename(filename)
    base_dir = _desktop_artifacts_dir()
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    target = (base_dir / safe).resolve()
    try:
        target.relative_to(base_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caminho inválido.",
        ) from None
    if not target.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Pacote desktop não está neste servidor. "
                "É necessário: (1) cd desktop && npm run build, "
                "(2) deploy-back para enviar vereda_backend/static/desktop/."
            ),
        )
    return FileResponse(
        path=str(target),
        filename=safe,
        media_type="application/octet-stream",
        content_disposition_type="attachment",
    )


@router.get("/assets/{filename:path}")
@router.head("/assets/{filename:path}")
def redirect_desktop_asset(filename: str) -> RedirectResponse:
    safe = _safe_filename(filename)
    # .deb não é gerado no build Windows; link antigo → mesmo pacote .tar.gz na API.
    if safe == "SyntexaAI-ubuntu-22.04-amd64.deb":
        override = (getattr(settings, "desktop_ubuntu_url", None) or "").strip()
        if override:
            return RedirectResponse(url=override, status_code=302)
        return RedirectResponse(url=_api_binary_url("SyntexaAI-linux-x64.tar.gz"), status_code=302)
    setting_name = _ASSET_TO_SETTING.get(safe)
    if not setting_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pacote não encontrado.",
        )
    url = (getattr(settings, setting_name, None) or "").strip()
    if url:
        return RedirectResponse(url=url, status_code=302)
    return RedirectResponse(url=_api_binary_url(safe), status_code=302)
