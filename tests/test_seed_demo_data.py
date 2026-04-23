from __future__ import annotations

import sqlite3
from datetime import date

import seed_demo_data as seed


def test_seed_demo_data_creates_full_demo_dataset(tmp_path):
    db_path = tmp_path / "pantry.db"

    summary = seed.seed_demo_data(db_path=db_path, today=date(2026, 4, 23), backup=False)

    assert summary["item_count"] == 24
    assert summary["scan_count"] == 165
    assert summary["never_scanned_count"] == 4
    assert summary["top_item"] == "Welch's Fruit Snacks"
    assert summary["top_item_count"] == 22
    assert summary["busiest_day"] == "2026-04-16"
    assert summary["busiest_day_count"] == 18

    with sqlite3.connect(db_path) as conn:
        item_count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        scan_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE type = 'out'").fetchone()[0]
        quantity_total = conn.execute("SELECT SUM(quantity) FROM items").fetchone()[0]
        categories = {
            row[0]
            for row in conn.execute("SELECT DISTINCT category FROM items")
        }

    assert item_count == 24
    assert scan_count == 165
    assert quantity_total == 0
    assert categories == {"Canned Goods", "Frozen Food", "Snacks", "Meals"}


def test_seed_demo_data_backs_up_then_resets_existing_database(tmp_path):
    db_path = tmp_path / "pantry.db"
    with sqlite3.connect(db_path) as conn:
        seed.init_schema(conn)
        conn.execute(
            "INSERT INTO items (barcode, name, category, unit, quantity) VALUES ('old', 'Old Item', 'Snacks', 'units', 9)"
        )

    summary = seed.seed_demo_data(db_path=db_path, today=date(2026, 4, 23), backup=True)

    assert summary["backup_path"] is not None
    with sqlite3.connect(summary["backup_path"]) as backup_conn:
        old_item_count = backup_conn.execute("SELECT COUNT(*) FROM items WHERE barcode = 'old'").fetchone()[0]
    assert old_item_count == 1

    with sqlite3.connect(db_path) as conn:
        old_item_count = conn.execute("SELECT COUNT(*) FROM items WHERE barcode = 'old'").fetchone()[0]
        demo_item_count = conn.execute("SELECT COUNT(*) FROM items WHERE barcode LIKE 'DEMO-%'").fetchone()[0]
    assert old_item_count == 0
    assert demo_item_count == 24


def test_keep_existing_preserves_current_items_and_adds_demo_items(tmp_path):
    db_path = tmp_path / "pantry.db"
    with sqlite3.connect(db_path) as conn:
        seed.init_schema(conn)
        conn.execute(
            "INSERT INTO items (barcode, name, category, unit, quantity) VALUES ('keep', 'Keep Item', 'Snacks', 'units', 0)"
        )

    seed.seed_demo_data(db_path=db_path, today=date(2026, 4, 23), backup=False, keep_existing=True)

    with sqlite3.connect(db_path) as conn:
        kept_item_count = conn.execute("SELECT COUNT(*) FROM items WHERE barcode = 'keep'").fetchone()[0]
        total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]

    assert kept_item_count == 1
    assert total_items == 25
