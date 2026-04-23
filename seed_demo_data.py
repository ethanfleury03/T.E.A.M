from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from database import DB_PATH


@dataclass(frozen=True)
class DemoItem:
    barcode: str
    name: str
    category: str
    unit: str
    scan_count: int


DEMO_ITEMS: tuple[DemoItem, ...] = (
    DemoItem("DEMO-SNK-001", "Welch's Fruit Snacks", "Snacks", "packs", 22),
    DemoItem("DEMO-SNK-002", "Granola Bars", "Snacks", "bars", 19),
    DemoItem("DEMO-SNK-003", "Peanut Butter Crackers", "Snacks", "packs", 13),
    DemoItem("DEMO-SNK-004", "Applesauce Cups", "Snacks", "cups", 10),
    DemoItem("DEMO-SNK-005", "Trail Mix", "Snacks", "bags", 8),
    DemoItem("DEMO-SNK-006", "Oatmeal Packets", "Snacks", "packets", 4),
    DemoItem("DEMO-SNK-007", "Cereal Cups", "Snacks", "cups", 0),
    DemoItem("DEMO-CAN-001", "Canned Chicken Noodle Soup", "Canned Goods", "cans", 14),
    DemoItem("DEMO-CAN-002", "Canned Tomato Soup", "Canned Goods", "cans", 6),
    DemoItem("DEMO-CAN-003", "Canned Green Beans", "Canned Goods", "cans", 3),
    DemoItem("DEMO-CAN-004", "Canned Corn", "Canned Goods", "cans", 2),
    DemoItem("DEMO-CAN-005", "Canned Tuna", "Canned Goods", "cans", 5),
    DemoItem("DEMO-CAN-006", "Canned Peaches", "Canned Goods", "cans", 0),
    DemoItem("DEMO-MEAL-001", "Mac and Cheese", "Meals", "boxes", 17),
    DemoItem("DEMO-MEAL-002", "Instant Ramen", "Meals", "packs", 15),
    DemoItem("DEMO-MEAL-003", "Pasta Meal Kit", "Meals", "kits", 6),
    DemoItem("DEMO-MEAL-004", "Rice Bowl", "Meals", "bowls", 5),
    DemoItem("DEMO-MEAL-005", "Pancake Mix", "Meals", "boxes", 0),
    DemoItem("DEMO-MEAL-006", "Mashed Potatoes", "Meals", "packs", 0),
    DemoItem("DEMO-MEAL-007", "Shelf Stable Milk", "Meals", "cartons", 1),
    DemoItem("DEMO-FRZ-001", "Frozen Pizza", "Frozen Food", "boxes", 6),
    DemoItem("DEMO-FRZ-002", "Frozen Burrito", "Frozen Food", "burritos", 5),
    DemoItem("DEMO-FRZ-003", "Frozen Vegetables", "Frozen Food", "bags", 2),
    DemoItem("DEMO-FRZ-004", "Waffles", "Frozen Food", "boxes", 2),
)

DAILY_SCAN_COUNTS: tuple[int, ...] = (
    3,
    5,
    4,
    6,
    7,
    4,
    6,
    5,
    8,
    7,
    7,
    5,
    6,
    4,
    7,
    8,
    5,
    6,
    4,
    7,
    5,
    6,
    18,
    5,
    3,
    4,
    2,
    3,
    3,
    2,
)


def create_backup(db_path: Path) -> Path | None:
    if not db_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}-{timestamp}.bak")
    with sqlite3.connect(db_path) as source, sqlite3.connect(backup_path) as target:
        source.backup(target)
    return backup_path


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
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


def reset_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM transactions")
    conn.execute("DELETE FROM items")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('items', 'transactions')")
    except sqlite3.OperationalError:
        pass


def upsert_demo_items(conn: sqlite3.Connection) -> dict[str, int]:
    item_ids: dict[str, int] = {}
    for item in DEMO_ITEMS:
        conn.execute(
            """
            INSERT INTO items (barcode, name, category, unit, quantity)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(barcode) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                unit = excluded.unit,
                quantity = 0
            """,
            (item.barcode, item.name, item.category, item.unit),
        )
        row = conn.execute("SELECT id FROM items WHERE barcode = ?", (item.barcode,)).fetchone()
        item_ids[item.barcode] = int(row["id"])
    return item_ids


def build_scan_sequence() -> list[DemoItem]:
    remaining = {item.barcode: item.scan_count for item in DEMO_ITEMS}
    ordered_items = sorted(DEMO_ITEMS, key=lambda item: item.scan_count, reverse=True)
    scans: list[DemoItem] = []

    while sum(remaining.values()) > 0:
        for item in ordered_items:
            if remaining[item.barcode] <= 0:
                continue
            scans.append(item)
            remaining[item.barcode] -= 1
    return scans


def insert_scan_transactions(
    conn: sqlite3.Connection,
    item_ids: dict[str, int],
    today: date,
) -> None:
    scans = build_scan_sequence()
    expected_total = sum(DAILY_SCAN_COUNTS)
    if len(scans) != expected_total:
        raise ValueError(f"Demo item scans ({len(scans)}) do not match daily counts ({expected_total}).")

    scan_index = 0
    first_day = today - timedelta(days=len(DAILY_SCAN_COUNTS) - 1)
    for day_offset, daily_count in enumerate(DAILY_SCAN_COUNTS):
        scan_day = first_day + timedelta(days=day_offset)
        for scan_number in range(daily_count):
            item = scans[scan_index]
            scan_time = datetime.combine(
                scan_day,
                time(hour=9 + (scan_number % 9), minute=(scan_number * 7) % 60, second=0),
                tzinfo=timezone.utc,
            )
            conn.execute(
                """
                INSERT INTO transactions (item_id, type, quantity, timestamp, notes)
                VALUES (?, 'out', 1, ?, ?)
                """,
                (item_ids[item.barcode], scan_time.isoformat(), "Demo scan-out seed"),
            )
            scan_index += 1


def seed_demo_data(
    db_path: Path = DB_PATH,
    today: date | None = None,
    *,
    backup: bool = True,
    keep_existing: bool = False,
) -> dict[str, Any]:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    seed_today = today or date.today()
    backup_path = create_backup(db_path) if backup else None

    with connect(db_path) as conn:
        init_schema(conn)
        if not keep_existing:
            reset_tables(conn)
        item_ids = upsert_demo_items(conn)
        insert_scan_transactions(conn, item_ids, seed_today)

        item_count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        scan_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE type = 'out'").fetchone()[0]
        never_scanned_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM items
            WHERE id NOT IN (SELECT DISTINCT item_id FROM transactions WHERE type = 'out')
            """
        ).fetchone()[0]
        top_row = conn.execute(
            """
            SELECT i.name, COUNT(*) AS total_scanned_out
            FROM transactions t
            JOIN items i ON i.id = t.item_id
            WHERE t.type = 'out'
            GROUP BY i.id, i.name
            ORDER BY total_scanned_out DESC, i.name COLLATE NOCASE
            LIMIT 1
            """
        ).fetchone()
        busiest_row = conn.execute(
            """
            SELECT DATE(timestamp) AS tx_date, COUNT(*) AS total_scanned_out
            FROM transactions
            WHERE type = 'out'
            GROUP BY DATE(timestamp)
            ORDER BY total_scanned_out DESC, DATE(timestamp) ASC
            LIMIT 1
            """
        ).fetchone()

    return {
        "db_path": str(db_path),
        "backup_path": str(backup_path) if backup_path else None,
        "item_count": int(item_count),
        "scan_count": int(scan_count),
        "never_scanned_count": int(never_scanned_count),
        "top_item": top_row["name"] if top_row else None,
        "top_item_count": int(top_row["total_scanned_out"]) if top_row else 0,
        "busiest_day": busiest_row["tx_date"] if busiest_row else None,
        "busiest_day_count": int(busiest_row["total_scanned_out"]) if busiest_row else 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Niagara Pantry with realistic outbound demo data.")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to the SQLite database to seed.")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today(), help="Anchor date in YYYY-MM-DD format.")
    parser.add_argument("--keep-existing", action="store_true", help="Append demo data instead of resetting tables first.")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating a backup before seeding.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = seed_demo_data(
        db_path=args.db,
        today=args.today,
        backup=not args.no_backup,
        keep_existing=args.keep_existing,
    )
    print("Demo data seeded.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
