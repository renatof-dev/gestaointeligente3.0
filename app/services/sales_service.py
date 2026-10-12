from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database import Database


PAYMENT_RATE_COLUMNS = {
    "DEBITO": "debito",
    "CREDITO_AVISTA": "credito_avista",
    "CREDITO_PARCELADO": "credito_parcelado",
    "PIX_MAQUININHA": "pix_maquininha",
    "PIX": None,
    "DINHEIRO": None,
}


@dataclass
class CartItem:
    product_id: int
    name: str
    qty: float
    unit_price: float
    unit_cost: float


@dataclass
class PaymentPart:
    method: str
    amount: float


class SalesService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_rates(self) -> dict[str, float]:
        row = self.db.fetch_one("SELECT * FROM machine_rates WHERE id = 1")
        if not row:
            return {k: 0.0 for k in PAYMENT_RATE_COLUMNS}
        return {
            "DEBITO": float(row["debito"]),
            "CREDITO_AVISTA": float(row["credito_avista"]),
            "CREDITO_PARCELADO": float(row["credito_parcelado"]),
            "PIX_MAQUININHA": float(row["pix_maquininha"]),
            "PIX": 0.0,
            "DINHEIRO": 0.0,
        }

    def _validate_stock(self, items: list[CartItem], conn=None) -> None:
        totals: dict[int, float] = {}
        for item in items:
            totals[item.product_id] = totals.get(item.product_id, 0.0) + item.qty
        for product_id, qty in totals.items():
            query = "SELECT name, stock_qty FROM products WHERE id = ?"
            row = conn.execute(query, (product_id,)).fetchone() if conn else self.db.fetch_one(query, (product_id,))
            if row is None:
                raise ValueError("Produto do carrinho nao encontrado.")
            available = float(row["stock_qty"] or 0)
            if qty > available + 1e-9:
                raise ValueError(
                    f"Estoque insuficiente para '{row['name']}'. Disponivel: {available:g} | No carrinho: {qty:g}."
                )

    def preview_sale(self, items: list[CartItem], discount: float, payments: list[PaymentPart]) -> dict:
        if not items:
            raise ValueError("Carrinho vazio.")
        self._validate_stock(items)

        gross_total = round(sum(i.qty * i.unit_price for i in items), 2)
        cost_total = round(sum(i.qty * i.unit_cost for i in items), 2)
        discount = round(max(0.0, discount), 2)
        if discount > gross_total:
            raise ValueError("Desconto maior que o total bruto da venda.")
        net_total = round(gross_total - discount, 2)

        payment_sum = round(sum(p.amount for p in payments), 2)
        if abs(payment_sum - net_total) > 0.01:
            raise ValueError("A soma dos pagamentos deve ser igual ao total liquido da venda.")

        rates = self.get_rates()
        payment_details = []
        fee_total = 0.0
        for p in payments:
            if p.method not in rates:
                raise ValueError(f"Forma de pagamento invalida: {p.method}")
            percent = rates[p.method]
            fee_amount = round(p.amount * (percent / 100), 2)
            fee_total += fee_amount
            payment_details.append(
                {
                    "method": p.method,
                    "amount": round(p.amount, 2),
                    "fee_percent": percent,
                    "fee_amount": fee_amount,
                }
            )

        fee_total = round(fee_total, 2)
        effective_total = round(net_total - fee_total, 2)

        line_discounts = self._distribute_discount(items, discount)
        item_lines = []
        for idx, item in enumerate(items):
            line_gross = round(item.qty * item.unit_price, 2)
            line_discount = line_discounts[idx]
            line_net = round(line_gross - line_discount, 2)
            line_cost = round(item.qty * item.unit_cost, 2)
            line_fee = self._calc_line_fee(line_net, payment_details, net_total)
            line_profit = round(line_net - line_fee - line_cost, 2)
            item_lines.append(
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "qty": item.qty,
                    "unit_price": item.unit_price,
                    "unit_cost": item.unit_cost,
                    "line_discount": line_discount,
                    "line_total": line_net,
                    "line_profit": line_profit,
                }
            )

        profit_total = round(effective_total - cost_total, 2)

        return {
            "gross_total": gross_total,
            "discount_total": discount,
            "net_total": net_total,
            "fee_total": fee_total,
            "effective_total": effective_total,
            "cost_total": cost_total,
            "profit_total": profit_total,
            "payments": payment_details,
            "items": item_lines,
        }

    def _distribute_discount(self, items: list[CartItem], discount: float) -> list[float]:
        if discount <= 0:
            return [0.0] * len(items)
        gross = sum(i.qty * i.unit_price for i in items)
        if gross == 0:
            return [0.0] * len(items)

        distributed = []
        accumulated = 0.0
        for idx, item in enumerate(items):
            if idx == len(items) - 1:
                line_discount = round(discount - accumulated, 2)
            else:
                line_discount = round((item.qty * item.unit_price / gross) * discount, 2)
                accumulated += line_discount
            distributed.append(line_discount)
        return distributed

    def _calc_line_fee(self, line_total: float, payments: list[dict], net_total: float) -> float:
        if net_total <= 0:
            return 0.0
        fee = 0.0
        for payment in payments:
            weight = payment["amount"] / net_total
            fee += payment["fee_amount"] * weight
        return round((line_total / net_total) * fee, 2)

    def finalize_sale(
        self,
        user_id: int,
        client_id: int | None,
        preview: dict,
        notes: str = "",
    ) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with self.db.connect() as conn:
            self._validate_stock(
                [
                    CartItem(
                        product_id=i["product_id"], name="", qty=float(i["qty"]),
                        unit_price=float(i["unit_price"]), unit_cost=float(i["unit_cost"]),
                    )
                    for i in preview["items"]
                ],
                conn,
            )
            cur = conn.execute(
                """
                INSERT INTO sales(
                    created_at, user_id, client_id, gross_total, discount_total, net_total,
                    fee_total, cost_total, profit_total, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    user_id,
                    client_id,
                    preview["gross_total"],
                    preview["discount_total"],
                    preview["net_total"],
                    preview["fee_total"],
                    preview["cost_total"],
                    preview["profit_total"],
                    notes,
                ),
            )
            sale_id = int(cur.lastrowid)

            for item in preview["items"]:
                conn.execute(
                    """
                    INSERT INTO sale_items(
                        sale_id, product_id, qty, unit_cost, unit_price, line_discount, line_total, line_profit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sale_id,
                        item["product_id"],
                        item["qty"],
                        item["unit_cost"],
                        item["unit_price"],
                        item["line_discount"],
                        item["line_total"],
                        item["line_profit"],
                    ),
                )

                conn.execute(
                    "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?",
                    (item["qty"], item["product_id"]),
                )

            for p in preview["payments"]:
                conn.execute(
                    """
                    INSERT INTO sale_payments(sale_id, method, amount, fee_percent, fee_amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (sale_id, p["method"], p["amount"], p["fee_percent"], p["fee_amount"]),
                )

            conn.execute(
                """
                INSERT INTO cashflow_entries(
                    entry_date, type, amount, description, reference_sale_id, created_by, created_at
                ) VALUES (?, 'VENDA', ?, ?, ?, ?, ?)
                """,
                (now[:10], preview["effective_total"], f"Venda #{sale_id}", sale_id, user_id, now),
            )
            conn.execute(
                """
                INSERT INTO cashflow_entries(
                    entry_date, type, amount, description, reference_sale_id, created_by, created_at
                ) VALUES (?, 'LUCRO', ?, ?, ?, ?, ?)
                """,
                (now[:10], preview["profit_total"], f"Lucro da venda #{sale_id}", sale_id, user_id, now),
            )

            return sale_id

    def cancel_sale(self, sale_id: int, user_id: int, reason: str = "") -> None:
        """Cancela a venda: devolve o estoque, remove do fluxo de caixa/lucro e mantem o registro como CANCELADA."""
        now = datetime.now().isoformat(timespec="seconds")
        with self.db.connect() as conn:
            sale = conn.execute("SELECT status FROM sales WHERE id = ?", (sale_id,)).fetchone()
            if sale is None:
                raise ValueError("Venda nao encontrada.")
            if str(sale["status"] or "ATIVA") == "CANCELADA":
                raise ValueError("Esta venda ja foi cancelada.")

            for item in conn.execute("SELECT product_id, qty FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall():
                conn.execute(
                    "UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?",
                    (item["qty"], item["product_id"]),
                )
            conn.execute(
                "DELETE FROM cashflow_entries WHERE reference_sale_id = ? AND type IN ('VENDA', 'LUCRO')",
                (sale_id,),
            )
            conn.execute(
                "UPDATE sales SET status = 'CANCELADA', cancelled_at = ?, cancelled_by = ?, cancel_reason = ? WHERE id = ?",
                (now, user_id, reason.strip(), sale_id),
            )
