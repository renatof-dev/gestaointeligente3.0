"""Testes do Dashboard: cancelamentos 'pedido teste' nao sao contabilizados."""
from __future__ import annotations

from datetime import datetime

from app.services.sales_service import SalesService
from app.ui.main_window import DashboardPage


def _make_sale(db, sale_id=None):
    now = datetime.now().isoformat(timespec="seconds")
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO sales (created_at, user_id, gross_total, net_total, discount_total, fee_total, cost_total, profit_total, status) "
            "VALUES (?, 1, 10.0, 10.0, 0, 0, 2.0, 8.0, 'ATIVA')",
            (now,),
        )


def test_pedido_teste_nao_conta_no_card(qapp, db, user):
    for _ in range(3):
        _make_sale(db)

    svc = SalesService(db)
    svc.cancel_sale(1, 1, "Cliente desistiu")       # conta
    svc.cancel_sale(2, 1, "Pedido teste")           # NAO conta
    svc.cancel_sale(3, 1, "PEDIDO TESTE do sistema")  # NAO conta (maiusculo)

    dash = DashboardPage(db, user)
    dash.date_start.setDate(dash.date_start.date().addDays(-1))
    dash.date_end.setDate(dash.date_end.date().addDays(1))
    dash.refresh()

    assert dash.lbl_cancelled.text() == "1"
    assert "10,00" in dash.lbl_cancelled_delta.text()
    # Faturamento: todas as canceladas saem, independente do motivo
    assert dash.lbl_count.text() == "0"


def test_cancelamento_normal_conta(qapp, db, user):
    _make_sale(db)
    SalesService(db).cancel_sale(1, 1, "Defeito no produto")

    dash = DashboardPage(db, user)
    dash.date_start.setDate(dash.date_start.date().addDays(-1))
    dash.date_end.setDate(dash.date_end.date().addDays(1))
    dash.refresh()

    assert dash.lbl_cancelled.text() == "1"
