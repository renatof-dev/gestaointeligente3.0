"""Registro de erros e eventos em arquivo, para facilitar o suporte.

Os logs ficam em %LOCALAPPDATA%\\GestaoInteligente\\logs\\sistema.log (quando instalado)
ou na pasta do projeto em modo de desenvolvimento. O arquivo faz rotacao automatica
para nao crescer sem limite.
"""
from __future__ import annotations

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from app.config import BASE_DIR, ensure_directories

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "sistema.log"

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """Retorna o logger do sistema (cria e configura na primeira chamada)."""
    global _logger
    if _logger is not None:
        return _logger

    ensure_directories()
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("gestao_inteligente")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_000_000,  # ~1 MB por arquivo
            backupCount=3,       # mantem ate 3 arquivos antigos
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%d/%m/%Y %H:%M:%S")
        )
        logger.addHandler(handler)
    _logger = logger
    return logger


def log_info(message: str) -> None:
    get_logger().info(message)


def log_error(message: str, exc: BaseException | None = None) -> None:
    """Registra um erro, incluindo o traceback quando houver excecao."""
    logger = get_logger()
    if exc is not None:
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error("%s\n%s", message, details)
    else:
        logger.error("%s", message)


def install_exception_hook() -> None:
    """Captura erros nao tratados e grava no log em vez de apenas fechar/travar."""
    def _hook(exc_type, exc_value, exc_tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        get_logger().error("Erro nao tratado:\n%s", details)

    sys.excepthook = _hook
