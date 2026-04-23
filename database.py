from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
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


def normalize_barcode(raw: str) -> str:
    """Trim scanner whitespace/control chars while preserving the stored code value."""
    return "".join(ch for ch in str(raw).strip() if ch not in "\r\n\t")


def _require_text(value: str, field_name: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional_text(value: str, default: str) -> str:
    cleaned = str(value).strip()
    return cleaned or default


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


def get_outbound_dashboard_totals() -> dict[str, Any]:
    with get_connection() as conn:
        known_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        total_scanned_out = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM transactions WHERE type = 'out'"
        ).fetchone()[0]
        unique_items_scanned = conn.execute(
            "SELECT COUNT(DISTINCT item_id) FROM transactions WHERE type = 'out'"
        ).fetchone()[0]
        items_not_scanned = conn.execute(
            """
            SELECT COUNT(*)
            FROM items
            WHERE id NOT IN (SELECT DISTINCT item_id FROM transactions WHERE type = 'out')
            """
        ).fetchone()[0]
        top_row = conn.execute(
            """
            SELECT i.name, SUM(t.quantity) AS total_scanned_out
            FROM transactions t
            JOIN items i ON i.id = t.item_id
            WHERE t.type = 'out'
            GROUP BY i.id, i.name
            ORDER BY total_scanned_out DESC, i.name COLLATE NOCASE
            LIMIT 1
            """
        ).fetchone()

    return {
        "known_items": int(known_items),
        "total_scanned_out": int(total_scanned_out),
        "unique_items_scanned": int(unique_items_scanned),
        "items_not_scanned": int(items_not_scanned),
        "top_item": str(top_row["name"]) if top_row else "None yet",
        "top_item_count": int(top_row["total_scanned_out"]) if top_row else 0,
    }


def add_item(name: str, barcode: str, unit: str, category: str = "Uncategorized", initial_quantity: int = 0, notes: str = "") -> int:
    if initial_quantity < 0:
        raise ValueError("Initial quantity must be 0 or greater.")

    cleaned_name = _require_text(name, "Item name")
    cleaned_barcode = normalize_barcode(barcode)
    if not cleaned_barcode:
        raise ValueError("Barcode is required.")
    cleaned_category = _clean_optional_text(category, "Uncategorized")
    cleaned_unit = _clean_optional_text(unit, "units")
    cleaned_notes = str(notes).strip()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO items (barcode, name, category, unit, quantity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cleaned_barcode, cleaned_name, cleaned_category, cleaned_unit, initial_quantity),
        )
        item_id = int(cursor.lastrowid)

        if initial_quantity > 0:
            conn.execute(
                """
                INSERT INTO transactions (item_id, type, quantity, timestamp, notes)
                VALUES (?, 'in', ?, ?, ?)
                """,
                (item_id, initial_quantity, datetime.now(timezone.utc).isoformat(), cleaned_notes or "Initial stock"),
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
    cleaned_barcode = normalize_barcode(barcode)
    if not cleaned_barcode:
        return None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, barcode, name, category, unit, quantity FROM items WHERE barcode = ?",
            (cleaned_barcode,),
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
    cleaned_name = _require_text(name, "Item name")
    cleaned_barcode = normalize_barcode(barcode)
    if not cleaned_barcode:
        raise ValueError("Barcode is required.")
    cleaned_unit = _clean_optional_text(unit, "units")
    cleaned_category = _clean_optional_text(category, "Uncategorized")

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE items
            SET name = ?, barcode = ?, unit = ?, category = ?
            WHERE id = ?
            """,
            (cleaned_name, cleaned_barcode, cleaned_unit, cleaned_category, item_id),
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
            (item_id, tx_type, quantity, datetime.now(timezone.utc).isoformat(), notes.strip()),
        )


def record_scan_out(item_id: int, quantity: int = 1, notes: str = "") -> None:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    with get_connection() as conn:
        row = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise ValueError("Item not found.")

        conn.execute(
            """
            INSERT INTO transactions (item_id, type, quantity, timestamp, notes)
            VALUES (?, 'out', ?, ?, ?)
            """,
            (item_id, quantity, datetime.now(timezone.utc).isoformat(), notes.strip()),
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


def get_item_sheet_summary() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                i.id,
                i.name,
                i.barcode,
                i.category,
                i.unit,
                COALESCE(SUM(t.quantity), 0) AS total_scanned_out,
                MAX(t.timestamp) AS last_scanned_out
            FROM items i
            LEFT JOIN transactions t ON t.item_id = i.id AND t.type = 'out'
            GROUP BY i.id, i.name, i.barcode, i.category, i.unit
            ORDER BY total_scanned_out DESC, i.name COLLATE NOCASE
            """,
            conn,
        )
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


def get_checked_out_by_category(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Total units checked out (scanned out), grouped by item category."""
    query = """
        SELECT
            i.category AS category,
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
        GROUP BY i.category
        ORDER BY total_checked_out DESC
    """

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_low_stock_items(threshold: int) -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT id, name, barcode, category, unit, quantity
            FROM items
            WHERE quantity <= ?
            ORDER BY quantity ASC, name COLLATE NOCASE
            """,
            conn,
            params=[threshold],
        )
    return df


def get_daily_transaction_summary(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    query = """
        SELECT
            DATE(timestamp) AS tx_date,
            SUM(CASE WHEN type = 'out' THEN quantity ELSE 0 END) AS checked_out,
            SUM(CASE WHEN type = 'in' THEN quantity ELSE 0 END) AS restocked
        FROM transactions
        WHERE 1=1
    """
    params: list[Any] = []

    if start_date:
        query += " AND DATE(timestamp) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= DATE(?)"
        params.append(end_date)

    query += """
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) ASC
    """

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_daily_scan_out_summary(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    query = """
        SELECT
            DATE(timestamp) AS tx_date,
            SUM(quantity) AS total_scanned_out
        FROM transactions
        WHERE type = 'out'
    """
    params: list[Any] = []

    if start_date:
        query += " AND DATE(timestamp) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= DATE(?)"
        params.append(end_date)

    query += """
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) ASC
    """

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df


def get_busiest_scan_out_day(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, str | int | None]:
    query = """
        SELECT
            DATE(timestamp) AS tx_date,
            SUM(quantity) AS total_scanned_out
        FROM transactions
        WHERE type = 'out'
    """
    params: list[Any] = []

    if start_date:
        query += " AND DATE(timestamp) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= DATE(?)"
        params.append(end_date)

    query += """
        GROUP BY DATE(timestamp)
        ORDER BY total_scanned_out DESC, DATE(timestamp) ASC
        LIMIT 1
    """

    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()

    if row is None:
        return {"tx_date": None, "total_scanned_out": 0}
    return {"tx_date": row["tx_date"], "total_scanned_out": int(row["total_scanned_out"])}


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


def import_items_from_csv(file_obj: Any) -> dict[str, Any]:
    """
    Import rows from a CSV with columns: name, barcode (required);
    optional: category, unit, initial_quantity (default 0).
    Barcodes already in the database are skipped (counted as skipped_duplicates).
    """
    df = pd.read_csv(file_obj)
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"name", "barcode"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        return {"added": 0, "skipped_duplicates": 0, "errors": [f"Missing required columns: {sorted(missing)}"]}

    added = 0
    skipped_duplicates = 0
    errors: list[str] = []
    seen_in_file: set[str] = set()

    for row_num, (_, row) in enumerate(df.iterrows(), start=1):
        line_no = row_num + 1
        raw_barcode = row.get("barcode")
        raw_name = row.get("name")
        if pd.isna(raw_barcode) or pd.isna(raw_name):
            errors.append(f"Row {line_no}: name and barcode are required.")
            continue
        barcode = normalize_barcode(raw_barcode)
        try:
            name = _require_text(raw_name, "Item name")
        except ValueError:
            errors.append(f"Row {line_no}: name and barcode cannot be empty.")
            continue
        if not barcode:
            errors.append(f"Row {line_no}: name and barcode cannot be empty.")
            continue
        if barcode in seen_in_file:
            errors.append(f"Row {line_no}: duplicate barcode in file ({barcode}).")
            continue
        seen_in_file.add(barcode)

        if get_item_by_barcode(barcode) is not None:
            skipped_duplicates += 1
            continue

        cat_raw = row.get("category", "Uncategorized")
        category = "Uncategorized" if pd.isna(cat_raw) else str(cat_raw).strip() or "Uncategorized"
        unit_raw = row.get("unit", "units")
        unit = "units" if pd.isna(unit_raw) else str(unit_raw).strip() or "units"
        iq_raw = row.get("initial_quantity", 0)
        try:
            initial_quantity = int(iq_raw) if not pd.isna(iq_raw) else 0
        except (TypeError, ValueError):
            errors.append(f"Row {line_no}: initial_quantity must be an integer.")
            continue
        if initial_quantity < 0:
            errors.append(f"Row {line_no}: initial_quantity cannot be negative.")
            continue

        try:
            add_item(
                name=name,
                barcode=barcode,
                unit=unit,
                category=category,
                initial_quantity=initial_quantity,
                notes="CSV import",
            )
            added += 1
        except ValueError as exc:
            errors.append(f"Row {line_no}: {exc}")

    return {"added": added, "skipped_duplicates": skipped_duplicates, "errors": errors}
