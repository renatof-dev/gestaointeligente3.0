"""Testes do banco de dados: indices de performance."""
from __future__ import annotations

EXPECTED_INDEXES = {
    "idx_products_name",
    "idx_products_barcode",
    "idx_products_active",
    "idx_sales_created_at",
    "idx_sales_status",
    "idx_sales_client",
    "idx_sales_user",
    "idx_sale_items_sale",
    "idx_sale_items_product",
    "idx_sale_payments_sale",
    "idx_cashflow_date",
    "idx_cashflow_sale",
    "idx_clients_name",
}


def test_indices_existem(db):
    with db.connect() as conn:
        indexes = {r[1] for r in conn.execute("SELECT type, name FROM sqlite_master WHERE type='index'")}
    missing = EXPECTED_INDEXES - indexes
    assert not missing, f"Indices faltando: {missing}"


def test_indices_sao_criados_em_banco_existente(tmp_path):
    """Indices devem ser criados mesmo em um banco que ja existia (migracao)."""
    from app.database import Database

    db_file = tmp_path / "existente.db"
    Database(str(db_file))  # cria
    Database(str(db_file))  # reabre (simula cliente que ja tinha o banco)
    db = Database(str(db_file))
    with db.connect() as conn:
        indexes = {r[1] for r in conn.execute("SELECT type, name FROM sqlite_master WHERE type='index'")}
    assert EXPECTED_INDEXES <= indexes
