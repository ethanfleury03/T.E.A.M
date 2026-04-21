"""Unit tests for database layer (inventory, transactions, analytics queries)."""

from __future__ import annotations

import io

import pandas as pd
import pytest

import database as db


def test_init_and_dashboard_totals(fresh_db):
    assert db.get_dashboard_totals() == {"unique_items": 0, "total_quantity": 0, "total_transactions": 0}


def test_add_item_and_lookup(fresh_db):
    iid = db.add_item("Beans", "111", "cans", category="Canned Goods", initial_quantity=3)
    assert iid > 0
    row = db.get_item_by_barcode("111")
    assert row is not None
    assert row["name"] == "Beans"
    assert row["quantity"] == 3
    df = db.get_all_items()
    assert len(df) == 1
    assert int(df.iloc[0]["quantity"]) == 3


def test_add_item_initial_quantity_creates_transaction(fresh_db):
    db.add_item("Rice", "222", "bags", initial_quantity=5)
    tx = db.get_transactions()
    assert len(tx) == 1
    assert tx.iloc[0]["type"] == "in"
    assert int(tx.iloc[0]["quantity"]) == 5


def test_record_transaction_in_out(fresh_db):
    iid = db.add_item("Soup", "333", "cans", initial_quantity=10)
    db.record_transaction(iid, "out", 4)
    row = db.get_item_by_barcode("333")
    assert int(row["quantity"]) == 6
    db.record_transaction(iid, "in", 2)
    assert int(db.get_item_by_barcode("333")["quantity"]) == 8


def test_record_transaction_rejects_over_checkout(fresh_db):
    iid = db.add_item("Jam", "444", "jars", initial_quantity=1)
    with pytest.raises(ValueError, match="more than current stock"):
        db.record_transaction(iid, "out", 5)


def test_record_transaction_invalid_type(fresh_db):
    iid = db.add_item("X", "555", "u", initial_quantity=1)
    with pytest.raises(ValueError, match="Transaction type"):
        db.record_transaction(iid, "swap", 1)


def test_update_item(fresh_db):
    iid = db.add_item("Old", "666", "units")
    db.update_item(iid, "New", "666", "boxes", "Snacks")
    row = db.get_item_by_barcode("666")
    assert row["name"] == "New"
    assert row["unit"] == "boxes"
    assert row["category"] == "Snacks"


def test_delete_item(fresh_db):
    iid = db.add_item("Temp", "777", "units")
    db.delete_item(iid)
    assert db.get_item_by_barcode("777") is None
    with pytest.raises(ValueError, match="not found"):
        db.delete_item(iid)


def test_get_transactions_filters(fresh_db):
    iid = db.add_item("FilterMe", "888", "units", initial_quantity=0)
    db.record_transaction(iid, "in", 2, notes="a")
    db.record_transaction(iid, "out", 1, notes="b")
    all_tx = db.get_transactions()
    assert len(all_tx) == 2
    ins = db.get_transactions(tx_type="in")
    assert len(ins) == 1
    outs = db.get_transactions(tx_type="out")
    assert len(outs) == 1
    by_item = db.get_transactions(item_id=iid)
    assert len(by_item) == 2


def test_get_top_checked_out_items(fresh_db):
    a = db.add_item("A", "a1", "u", initial_quantity=10)
    b = db.add_item("B", "b1", "u", initial_quantity=10)
    db.record_transaction(a, "out", 3)
    db.record_transaction(a, "out", 2)
    db.record_transaction(b, "out", 1)
    top = db.get_top_checked_out_items(limit=5)
    assert list(top["item_name"]) == ["A", "B"]


def test_get_stock_over_time(fresh_db):
    iid = db.add_item("Track", "t1", "u", initial_quantity=0)
    db.record_transaction(iid, "in", 5)
    db.record_transaction(iid, "out", 2)
    s = db.get_stock_over_time(iid)
    assert not s.empty
    assert list(s["stock_level"]) == [5, 3]


def test_import_items_from_csv(fresh_db):
    csv_text = "name,barcode,category,unit,initial_quantity\nMilk,m1,Dairy,cartons,2\nMilk2,m2,Dairy,cartons,0\n"
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


def test_get_stock_over_time_empty(fresh_db):
    iid = db.add_item("NoTx", "nt1", "u", initial_quantity=0)
    s = db.get_stock_over_time(iid)
    assert s.empty


def test_add_item_negative_initial_raises(fresh_db):
    with pytest.raises(ValueError):
        db.add_item("Bad", "neg", "u", initial_quantity=-1)
