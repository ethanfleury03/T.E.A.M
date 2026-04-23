"""Unit tests for database layer scan-out tracking and item sheet queries."""

from __future__ import annotations

import io

import pandas as pd
import pytest

import database as db


def insert_scan_out_at(item_id: int, quantity: int, timestamp: str) -> None:
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transactions (item_id, type, quantity, timestamp, notes)
            VALUES (?, 'out', ?, ?, 'test scan')
            """,
            (item_id, quantity, timestamp),
        )


def test_init_and_outbound_dashboard_totals(fresh_db):
    assert db.get_outbound_dashboard_totals() == {
        "known_items": 0,
        "total_scanned_out": 0,
        "unique_items_scanned": 0,
        "items_not_scanned": 0,
        "top_item": "None yet",
        "top_item_count": 0,
    }


def test_add_item_and_lookup(fresh_db):
    iid = db.add_item("Beans", "111", "cans", category="Canned Goods")
    assert iid > 0
    row = db.get_item_by_barcode("111")
    assert row is not None
    assert row["name"] == "Beans"
    assert row["quantity"] == 0
    df = db.get_all_items()
    assert len(df) == 1


def test_add_item_initial_quantity_still_creates_legacy_setup_transaction(fresh_db):
    db.add_item("Rice", "222", "bags", initial_quantity=5)
    tx = db.get_transactions()
    assert len(tx) == 1
    assert tx.iloc[0]["type"] == "in"
    assert int(tx.iloc[0]["quantity"]) == 5


def test_add_item_normalizes_scanner_barcode_whitespace(fresh_db):
    db.add_item("Pasta", "  abc123\r\n", "boxes")
    row = db.get_item_by_barcode("abc123")
    assert row is not None
    assert row["barcode"] == "abc123"


def test_record_scan_out_records_out_transaction_without_changing_quantity(fresh_db):
    iid = db.add_item("Soup", "333", "cans", initial_quantity=7)
    db.record_scan_out(iid, quantity=2, notes="demo scan")
    row = db.get_item_by_barcode("333")
    assert int(row["quantity"]) == 7
    out_tx = db.get_transactions(tx_type="out")
    assert len(out_tx) == 1
    assert out_tx.iloc[0]["type"] == "out"
    assert int(out_tx.iloc[0]["quantity"]) == 2
    assert out_tx.iloc[0]["notes"] == "demo scan"


def test_record_scan_out_allows_zero_quantity_items(fresh_db):
    iid = db.add_item("Jam", "444", "jars", initial_quantity=0)
    db.record_scan_out(iid, quantity=3)
    row = db.get_item_by_barcode("444")
    assert int(row["quantity"]) == 0
    assert int(db.get_transactions(tx_type="out").iloc[0]["quantity"]) == 3


def test_record_scan_out_rejects_bad_quantity_and_missing_item(fresh_db):
    iid = db.add_item("X", "555", "u")
    with pytest.raises(ValueError, match="greater than 0"):
        db.record_scan_out(iid, 0)
    with pytest.raises(ValueError, match="Item not found"):
        db.record_scan_out(999, 1)


def test_record_transaction_invalid_type(fresh_db):
    iid = db.add_item("X", "556", "u")
    with pytest.raises(ValueError, match="Transaction type"):
        db.record_transaction(iid, "swap", 1)


def test_update_item(fresh_db):
    iid = db.add_item("Old", "666", "units")
    db.update_item(iid, "New", "666", "boxes", "Snacks")
    row = db.get_item_by_barcode("666")
    assert row["name"] == "New"
    assert row["unit"] == "boxes"
    assert row["category"] == "Snacks"


def test_update_item_rejects_blank_required_fields(fresh_db):
    iid = db.add_item("Crackers", "cr1", "boxes")
    with pytest.raises(ValueError, match="Item name is required"):
        db.update_item(iid, "   ", "cr1", "boxes", "Snacks")
    with pytest.raises(ValueError, match="Barcode is required"):
        db.update_item(iid, "Crackers", " \r\n ", "boxes", "Snacks")


def test_delete_item(fresh_db):
    iid = db.add_item("Temp", "777", "units")
    db.delete_item(iid)
    assert db.get_item_by_barcode("777") is None
    with pytest.raises(ValueError, match="not found"):
        db.delete_item(iid)


def test_get_transactions_filters_scan_outs(fresh_db):
    a = db.add_item("FilterMe", "888", "units")
    b = db.add_item("Other", "889", "units")
    db.record_scan_out(a, 2, notes="a")
    db.record_scan_out(b, 1, notes="b")
    all_tx = db.get_transactions()
    assert len(all_tx) == 2
    outs = db.get_transactions(tx_type="out")
    assert len(outs) == 2
    by_item = db.get_transactions(item_id=a, tx_type="out")
    assert len(by_item) == 1
    assert int(by_item.iloc[0]["quantity"]) == 2


def test_get_top_checked_out_items_uses_scan_out_totals(fresh_db):
    a = db.add_item("A", "a1", "u")
    b = db.add_item("B", "b1", "u")
    db.record_scan_out(a, 3)
    db.record_scan_out(a, 2)
    db.record_scan_out(b, 1)
    top = db.get_top_checked_out_items(limit=5)
    assert list(top["item_name"]) == ["A", "B"]
    assert list(top["total_checked_out"]) == [5, 1]


def test_item_sheet_summary_includes_scanned_and_never_scanned_items(fresh_db):
    scanned = db.add_item("Scanned", "s1", "u")
    db.add_item("Never", "n1", "u")
    db.record_scan_out(scanned, 4)
    sheet = db.get_item_sheet_summary()
    rows = {row["name"]: row for _, row in sheet.iterrows()}
    assert int(rows["Scanned"]["total_scanned_out"]) == 4
    assert rows["Scanned"]["last_scanned_out"] is not None
    assert int(rows["Never"]["total_scanned_out"]) == 0
    assert pd.isna(rows["Never"]["last_scanned_out"])


def test_outbound_dashboard_totals_rank_top_item_and_unscanned_count(fresh_db):
    a = db.add_item("Applesauce", "ap1", "cups")
    b = db.add_item("Beans", "be1", "cans")
    db.add_item("Cereal", "ce1", "boxes")
    db.record_scan_out(a, 2)
    db.record_scan_out(b, 5)
    totals = db.get_outbound_dashboard_totals()
    assert totals["known_items"] == 3
    assert totals["total_scanned_out"] == 7
    assert totals["unique_items_scanned"] == 2
    assert totals["items_not_scanned"] == 1
    assert totals["top_item"] == "Beans"
    assert totals["top_item_count"] == 5


def test_daily_scan_out_summary_groups_outbound_counts(fresh_db):
    iid = db.add_item("Track", "sum1", "u")
    db.record_scan_out(iid, 4)
    db.record_scan_out(iid, 1)
    summary_df = db.get_daily_scan_out_summary()
    assert len(summary_df) == 1
    assert int(summary_df.iloc[0]["total_scanned_out"]) == 5


def test_busiest_scan_out_day_returns_highest_day(fresh_db):
    iid = db.add_item("Track", "busy1", "u")
    insert_scan_out_at(iid, 2, "2026-04-20T09:00:00+00:00")
    insert_scan_out_at(iid, 5, "2026-04-21T09:00:00+00:00")
    insert_scan_out_at(iid, 1, "2026-04-22T09:00:00+00:00")
    busiest = db.get_busiest_scan_out_day()
    assert busiest == {"tx_date": "2026-04-21", "total_scanned_out": 5}


def test_busiest_scan_out_day_empty_returns_zero(fresh_db):
    assert db.get_busiest_scan_out_day() == {"tx_date": None, "total_scanned_out": 0}


def test_busiest_scan_out_day_respects_date_filters(fresh_db):
    iid = db.add_item("Track", "busy2", "u")
    insert_scan_out_at(iid, 8, "2026-04-19T09:00:00+00:00")
    insert_scan_out_at(iid, 3, "2026-04-21T09:00:00+00:00")
    insert_scan_out_at(iid, 6, "2026-04-22T09:00:00+00:00")
    busiest = db.get_busiest_scan_out_day(start_date="2026-04-20", end_date="2026-04-22")
    assert busiest == {"tx_date": "2026-04-22", "total_scanned_out": 6}


def test_import_items_from_csv(fresh_db):
    csv_text = "name,barcode,category,unit,initial_quantity\nMilk,m1,Dairy,cartons,0\nMilk2,m2,Dairy,cartons,0\n"
    summary = db.import_items_from_csv(io.StringIO(csv_text))
    assert summary["added"] == 2
    assert summary["skipped_duplicates"] == 0
    assert not summary["errors"]
    assert db.get_item_by_barcode("m1")["name"] == "Milk"


def test_import_csv_skips_duplicate_barcode(fresh_db):
    db.add_item("Existing", "dup", "units")
    csv_text = "name,barcode\nOther,dup\nNew,d2\n"
    summary = db.import_items_from_csv(io.StringIO(csv_text))
    assert summary["added"] == 1
    assert summary["skipped_duplicates"] == 1


def test_add_item_negative_initial_raises(fresh_db):
    with pytest.raises(ValueError):
        db.add_item("Bad", "neg", "u", initial_quantity=-1)


def test_add_item_rejects_blank_required_fields(fresh_db):
    with pytest.raises(ValueError, match="Item name is required"):
        db.add_item("   ", "ok", "u")
    with pytest.raises(ValueError, match="Barcode is required"):
        db.add_item("Good", " \r\n ", "u")
