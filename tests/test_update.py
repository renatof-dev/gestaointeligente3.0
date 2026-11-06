"""Testes do auto-update (GitHub Releases)."""
from __future__ import annotations

from unittest import mock

from app.config import APP_VERSION
from app.services.update_service import _parse_version, check_for_update


def test_parse_version():
    assert _parse_version("3.0.3") > _parse_version("3.0.2")
    assert _parse_version("v3.1.0") > _parse_version("3.0.2")
    assert _parse_version("3.0.2") == _parse_version("v3.0.2")
    assert _parse_version("3.0.10") > _parse_version("3.0.9")


def _fake_release(tag):
    return {
        "tag_name": tag,
        "body": "Correcoes",
        "assets": [
            {"name": f"atualizacao_gestaointeligente{tag}.exe", "browser_download_url": "https://x/att.exe", "size": 100},
            {"name": f"gestaointeligente{tag}.exe", "browser_download_url": "https://x/full.exe", "size": 200},
        ],
    }


def test_detecta_versao_mais_nova():
    with mock.patch("app.services.update_service.requests.get") as mget:
        mget.return_value.status_code = 200
        mget.return_value.json.return_value = _fake_release("99.0.0")
        info = check_for_update()
    assert info is not None
    assert info.version == "99.0.0"
    # Deve escolher o asset de ATUALIZACAO, nao o instalador completo
    assert info.download_url == "https://x/att.exe"


def test_nao_oferece_quando_ja_esta_na_mais_recente():
    with mock.patch("app.services.update_service.requests.get") as mget:
        mget.return_value.status_code = 200
        mget.return_value.json.return_value = _fake_release(APP_VERSION)
        assert check_for_update() is None


def test_tolera_falta_de_internet():
    with mock.patch("app.services.update_service.requests.get", side_effect=Exception("sem net")):
        assert check_for_update() is None


def test_tolera_resposta_invalida():
    with mock.patch("app.services.update_service.requests.get") as mget:
        mget.return_value.status_code = 404
        assert check_for_update() is None
