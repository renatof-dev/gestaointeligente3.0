"""Configuracao compartilhada dos testes.

Roda a interface Qt em modo offscreen (sem abrir janelas) e fornece
um banco de dados temporario isolado para cada teste.
"""
from __future__ import annotations

import os
import sys
import tempfile
from types import SimpleNamespace

import pytest

# Garante modo offscreen ANTES de importar Qt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Garante que a raiz do projeto esteja no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.database import Database  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    """Uma unica QApplication para todos os testes."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def db(tmp_path):
    """Banco de dados SQLite temporario e isolado."""
    db_file = tmp_path / "test.db"
    database = Database(str(db_file))
    yield database


@pytest.fixture()
def user():
    """Usuario fake com perfil MASTER para os testes."""
    return SimpleNamespace(id=1, name="Teste", username="teste", role="MASTER")


@pytest.fixture()
def product_factory(db):
    """Cria produtos de teste rapidamente."""
    def create(barcode: str, name: str, stock: float = 10, price: float = 5.0, cost: float = 2.0) -> int:
        with db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO products (barcode, name, cost_price, sale_price, stock_qty, min_qty, active, created_at) "
                "VALUES (?, ?, ?, ?, ?, 0, 1, '2026-01-01')",
                (barcode, name, cost, price, stock),
            )
            return int(cur.lastrowid)
    return create
