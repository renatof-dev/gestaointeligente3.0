from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from app.config import DB_PATH, DEFAULT_MASTER_PASSWORD, DEFAULT_MASTER_USERNAME, ensure_directories


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        ensure_directories()
        self.db_path = db_path or str(DB_PATH)
        self._init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('MASTER', 'OPERADOR', 'CAIXA')),
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fantasy_name TEXT NOT NULL,
                    cnpj TEXT,
                    address TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    supplier_id INTEGER,
                    cost_price REAL NOT NULL,
                    sale_price REAL NOT NULL,
                    stock_qty REAL NOT NULL DEFAULT 0,
                    min_qty REAL NOT NULL DEFAULT 0,
                    image_path TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    birth_date TEXT,
                    email TEXT,
                    street TEXT,
                    cep TEXT,
                    neighborhood TEXT,
                    city TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS company_config (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    cnpj TEXT,
                    fantasy_name TEXT,
                    legal_name TEXT,
                    address TEXT,
                    phone TEXT,
                    email TEXT,
                    logo_path TEXT,
                    pix_key TEXT
                );

                CREATE TABLE IF NOT EXISTS printer_config (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    paper_type TEXT NOT NULL DEFAULT '80mm',
                    footer_message TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS machine_rates (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    debito REAL NOT NULL DEFAULT 0.99,
                    credito_avista REAL NOT NULL DEFAULT 2.99,
                    credito_parcelado REAL NOT NULL DEFAULT 5.49,
                    pix_maquininha REAL NOT NULL DEFAULT 0.99
                );

                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    client_id INTEGER,
                    gross_total REAL NOT NULL,
                    discount_total REAL NOT NULL,
                    net_total REAL NOT NULL,
                    fee_total REAL NOT NULL,
                    cost_total REAL NOT NULL,
                    profit_total REAL NOT NULL,
                    notes TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(client_id) REFERENCES clients(id)
                );

                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    qty REAL NOT NULL,
                    unit_cost REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    line_discount REAL NOT NULL,
                    line_total REAL NOT NULL,
                    line_profit REAL NOT NULL,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                );

                CREATE TABLE IF NOT EXISTS sale_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    amount REAL NOT NULL,
                    fee_percent REAL NOT NULL,
                    fee_amount REAL NOT NULL,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS cashflow_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    reference_sale_id INTEGER,
                    created_by INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(reference_sale_id) REFERENCES sales(id),
                    FOREIGN KEY(created_by) REFERENCES users(id)
                );
                """
            )

            client_columns = {row["name"] for row in conn.execute("PRAGMA table_info(clients)")}
            if "cpf" not in client_columns:
                conn.execute("ALTER TABLE clients ADD COLUMN cpf TEXT")

            sale_columns = {row["name"] for row in conn.execute("PRAGMA table_info(sales)")}
            if "status" not in sale_columns:
                conn.execute("ALTER TABLE sales ADD COLUMN status TEXT NOT NULL DEFAULT 'ATIVA'")
            if "cancelled_at" not in sale_columns:
                conn.execute("ALTER TABLE sales ADD COLUMN cancelled_at TEXT")
            if "cancelled_by" not in sale_columns:
                conn.execute("ALTER TABLE sales ADD COLUMN cancelled_by INTEGER")
            if "cancel_reason" not in sale_columns:
                conn.execute("ALTER TABLE sales ADD COLUMN cancel_reason TEXT")

            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                """
                INSERT INTO users(name, username, password_hash, role, active, created_at)
                SELECT ?, ?, ?, 'MASTER', 1, ?
                WHERE NOT EXISTS (SELECT 1 FROM users)
                """,
                ("Administrador", DEFAULT_MASTER_USERNAME, _hash_password(DEFAULT_MASTER_PASSWORD), now),
            )

            conn.execute(
                """
                INSERT INTO company_config(id, fantasy_name)
                SELECT 1, 'Minha Empresa'
                WHERE NOT EXISTS (SELECT 1 FROM company_config WHERE id = 1)
                """
            )
            conn.execute(
                """
                INSERT INTO printer_config(id, paper_type, footer_message)
                SELECT 1, '80mm', 'Obrigado pela preferencia.'
                WHERE NOT EXISTS (SELECT 1 FROM printer_config WHERE id = 1)
                """
            )
            conn.execute(
                """
                INSERT INTO machine_rates(id, debito, credito_avista, credito_parcelado, pix_maquininha)
                SELECT 1, 0.99, 2.99, 5.49, 0.99
                WHERE NOT EXISTS (SELECT 1 FROM machine_rates WHERE id = 1)
                """
            )

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.connect() as conn:
            cur = conn.execute(query, params)
            return cur.fetchall()

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self.connect() as conn:
            cur = conn.execute(query, params)
            return cur.fetchone()

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        with self.connect() as conn:
            cur = conn.execute(query, params)
            return cur.lastrowid

    def reset_to_factory(self) -> None:
        """Remove all operational data and restore the default admin and settings."""
        with self.connect() as conn:
            conn.execute("PRAGMA foreign_keys = OFF")
            for table in (
                "cashflow_entries",
                "sale_payments",
                "sale_items",
                "sales",
                "products",
                "clients",
                "suppliers",
                "users",
                "company_config",
                "printer_config",
                "machine_rates",
            ):
                conn.execute(f"DELETE FROM {table}")
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name IN "
                "('cashflow_entries','sale_payments','sale_items','sales','products','clients','suppliers','users')"
            )
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                "INSERT INTO users(name, username, password_hash, role, active, created_at) "
                "VALUES (?, ?, ?, 'MASTER', 1, ?)",
                ("Administrador", DEFAULT_MASTER_USERNAME, _hash_password(DEFAULT_MASTER_PASSWORD), now),
            )
            conn.execute("INSERT INTO company_config(id, fantasy_name) VALUES (1, 'Minha Empresa')")
            conn.execute(
                "INSERT INTO printer_config(id, paper_type, footer_message) VALUES (1, '80mm', 'Obrigado pela preferencia.')"
            )
            conn.execute(
                "INSERT INTO machine_rates(id, debito, credito_avista, credito_parcelado, pix_maquininha) "
                "VALUES (1, 0.99, 2.99, 5.49, 0.99)"
            )
            conn.commit()
            conn.execute("PRAGMA foreign_keys = ON")
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("VACUUM")
        finally:
            conn.close()

    def execute_many(self, query: str, params: list[tuple[Any, ...]]) -> None:
        with self.connect() as conn:
            conn.executemany(query, params)
