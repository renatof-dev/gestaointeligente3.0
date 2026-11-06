"""Testes do log de erros em arquivo."""
from __future__ import annotations

import logging
from unittest import mock

import pytest

import app.logger as logger_module
from app.logger import get_logger, log_error, log_info


@pytest.fixture()
def fresh_logger(tmp_path):
    """Reseta o singleton do logger e aponta para um arquivo temporario."""
    log_file = tmp_path / "sistema.log"
    # Fecha e remove handlers antigos do logger real
    existing = logging.getLogger("gestao_inteligente")
    for h in list(existing.handlers):
        h.close()
        existing.removeHandler(h)
    with mock.patch.object(logger_module, "LOG_FILE", log_file), \
         mock.patch.object(logger_module, "LOG_DIR", tmp_path), \
         mock.patch.object(logger_module, "_logger", None):
        yield log_file
    for h in list(existing.handlers):
        h.close()
        existing.removeHandler(h)


def test_log_grava_em_arquivo(fresh_logger):
    log_info("Teste de info")
    log_error("Teste de erro")
    content = fresh_logger.read_text(encoding="utf-8")
    assert "Teste de info" in content
    assert "Teste de erro" in content


def test_log_error_inclui_traceback(fresh_logger):
    try:
        raise ValueError("erro de teste")
    except ValueError as exc:
        log_error("Falha em algo", exc)
    content = fresh_logger.read_text(encoding="utf-8")
    assert "Falha em algo" in content
    assert "ValueError" in content
    assert "erro de teste" in content


def test_logger_reutiliza_instancia(fresh_logger):
    a = get_logger()
    b = get_logger()
    assert a is b
