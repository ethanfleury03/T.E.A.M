from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


DB_PATH = Path(__file__).resolve().parent / "pantry.db"
SETTINGS = {
    "LOW_STOCK_THRESHOLD": 5,
}
ITEM_CATEGORIES = ["Canned Goods", "Frozen Food", "Snacks", "Meals"]

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        _local.conn = conn
    return conn


_db_initialized = False


def init_db() -> None:
    global _db_initialized
    if _db_initialized:
        return

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Uncategorized',
                unit TEXT NOT NULL DEFAULT 'units',
                quantity INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        cols = [row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()]
        if "category" not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN category TEXT NOT NULL DEFAULT 'Uncategorized'")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('in', 'out')),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                timestamp TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            );
            """
        )
    _db_initialized = True


def get_dashboard_totals() -> dict[str, int]:
    with get_connection() as conn:
        unique_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        total_quantity = conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM items").fetchone()[0]
        total_transactions = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    return {
        "unique_items": unique_items,
        "total_quantity": total_quantity,
        "total_transactions": total_transactions,
    }


def add_item(name: str, barcode: str, unit: str, category: str = "Uncategorized", initial_quantity: int = 0, notes: str = "") -> int:
    if initial_quantity < 0:
        raise ValueError("Initial quantity must be 0 or greater.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO items (barcode, name, category, unit, quantity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (barcode.strip(), name.strip(), category.strip() or "Uncategorized", unit.strip() or "units", initial_quantity),
        )
        item_id = int(cursor.lastrowid)

        if initial_quantity > 0:
            conn.execute(
                """
                INSERT INTO transactions (item_id, type, quantity, timestamp, notes)
                VALUES (?, 'in', ?, ?, ?)
                """,
                (item_id, initial_quantity, datetime.utcnow().isoformat(), notes or "Initial stock"),
            )
    return item_id


def get_all_items() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT id, barcode, name, category, unit, quantity FROM items ORDER BY name COLLATE NOCASE",
            conn,
        )
    return df


def get_item_by_barcode(barcode: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, barcode, name, category, unit, quantity FROM items WHERE barcode = ?",
            (barcode.strip(),),
        ).fetchone()
    return dict(row) if row else None


def get_item_lookup() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT id, name, barcode, category, unit, quantity FROM items ORDER BY name COLLATE NOCASE",
            conn,
        )
    return df


def update_item(item_id: int, name: str, barcode: str, unit: str, category: str = "Uncategorized") -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE items
            SET name = ?, barcode = ?, unit = ?, category = ?
            WHERE id = ?
            """,
            (name.strip(), barcode.strip(), unit.strip() or "units", category.strip() or "Uncategorized", item_id),
        )


def delete_item(item_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise ValueError("Item not found.")
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def record_transaction(item_id: int, tx_type: str, quantity: int, notes: str = "") -> None:
    if tx_type not in {"in", "out"}:
        raise ValueError("Transaction type must be 'in' or 'out'.")
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    with get_connection() as conn:
        row = conn.execute("SELECT quantity FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise ValueError("Item not found.")

        current_quantity = int(row["quantity"])
        new_quantity = current_quantity + quantity if tx_type == "in" else current_quantity - quantity

        if new_quantity < 0:
            raise ValueError("Cannot check out more than current stock.")

        conn.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, item_id))
        conn.execute(
            """
            INSERT INTO transactions (item_id, type, quantity, timestamp, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, tx_type, quantity, datetime.utcnow().isoformat(), notes.strip()),
        )


def get_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    item_id: int | None = None,
    tx_type: str | None = None,
) -> pd.DataFrame:
    query = """
        SELECT
            t.id,
            t.timestamp,
            i.name AS item_name,
            i.barcode,
            t.type,
            t.quantity,
            i.unit,
            t.notes
        FROM transactions t
        JOIN items i ON i.id = t.item_id
        WHERE 1=1
    """
    params: list[Any] = []

    if start_date:
        query += " AND DATE(t.timestamp) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND DATE(t.timestamp) <= DATE(?)"
        params.append(end_date)
    if item_id is not None:
        query += " AND i.id = ?"
        params.append(item_id)
    if tx_type in {"in", "out"}:
        query += " AND t.type = ?"
        params.append(tx_type)

    query += " ORDER BY t.timestamp DESC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_top_checked_out_items(limit: int = 10, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    query = """
        SELECT
            i.name AS item_name,
            SUM(t.quantity) AS total_checked_out
        FROM transactions t
        JOIN items i ON i.id = t.item_id
        WHERE t.type = 'out'
    """
    params: list[Any] = []

    if start_date:
        query += " AND DATE(t.timestamp) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND DATE(t.timestamp) <= DATE(?)"
        params.append(end_date)

    query += """
        GROUP BY i.id, i.name
        ORDER BY total_checked_out DESC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_stock_over_time(item_id: int) -> pd.DataFrame:
    with get_connection() as conn:
        tx_df = pd.read_sql_query(
            """
            SELECT timestamp, type, quantity
            FROM transactions
            WHERE item_id = ?
            ORDER BY timestamp ASC
            """,
            conn,
            params=[item_id],
        )

    if tx_df.empty:
        return pd.DataFrame(columns=["timestamp", "stock_level"])

    tx_df["delta"] = tx_df.apply(lambda row: row["quantity"] if row["type"] == "in" else -row["quantity"], axis=1)
    tx_df["stock_level"] = tx_df["delta"].cumsum()
    return tx_df[["timestamp", "stock_level"]]
