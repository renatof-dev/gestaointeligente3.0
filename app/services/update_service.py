from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests

from app.config import APP_VERSION

GITHUB_REPO = "renatof-dev/gestaointeligente3.0"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_ASSET_PREFIX = "atualizacao_gestaointeligente"
REQUEST_TIMEOUT = 15


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    size_bytes: int
    notes: str


def _parse_version(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in str(text).strip().lstrip("vV").split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_update() -> UpdateInfo | None:
    """Consulta a release mais recente no GitHub. Retorna UpdateInfo se houver versao maior, senao None."""
    try:
        resp = requests.get(GITHUB_API_LATEST, timeout=REQUEST_TIMEOUT, headers={"Accept": "application/vnd.github+json"})
    except Exception:
        return None  # sem internet ou qualquer falha de rede: nao atrapalha a abertura
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None

    latest_version = str(data.get("tag_name") or data.get("name") or "").strip()
    if not latest_version:
        return None
    if _parse_version(latest_version) <= _parse_version(APP_VERSION):
        return None

    asset = None
    for item in data.get("assets") or []:
        name = str(item.get("name") or "")
        if name.startswith(UPDATE_ASSET_PREFIX) and name.lower().endswith(".exe"):
            asset = item
            break
    if asset is None:
        return None
    url = str(asset.get("browser_download_url") or "")
    if not url:
        return None
    return UpdateInfo(
        version=latest_version.lstrip("vV"),
        download_url=url,
        size_bytes=int(asset.get("size") or 0),
        notes=str(data.get("body") or ""),
    )


def download_update(info: UpdateInfo, progress=None) -> Path:
    """Baixa o pacote de atualizacao para a pasta temporaria. progress(bytes_baixados, total)."""
    target = Path(tempfile.gettempdir()) / f"atualizacao_gestaointeligente{info.version}.exe"
    with requests.get(info.download_url, stream=True, timeout=REQUEST_TIMEOUT) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length") or info.size_bytes or 0)
        downloaded = 0
        with open(target, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=256 * 1024):
                if not chunk:
                    continue
                fh.write(chunk)
                downloaded += len(chunk)
                if progress:
                    progress(downloaded, total)
    return target


def launch_update_and_exit(installer_path: Path) -> None:
    """Executa o pacote de atualizacao e encerra o sistema para liberar os arquivos."""
    subprocess.Popen([str(installer_path)], close_fds=True)
    os._exit(0)
