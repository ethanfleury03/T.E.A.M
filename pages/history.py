from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import get_item_lookup, get_transactions
from date_utils import streamlit_date_range_to_iso
from ui.components import render_page_header


render_page_header("Transaction History", "Audit all inventory actions across check-outs and receipts.")

items_df = get_item_lookup()

col1, col2, col3 = st.columns(3)

with col1:
    default_end = date.today()
    default_start = default_end - timedelta(days=30)
    date_range = st.date_input("Date range", value=(default_start, default_end))

with col2:
    item_option_labels = ["All items"] + [f"{row['name']} ({row['barcode']})" for _, row in items_df.iterrows()]
    default_item_label = "All items"
    history_filter_id = st.session_state.get("history_item_filter")
    if history_filter_id is not None and not items_df.empty and history_filter_id in set(items_df["id"].tolist()):
        row = items_df[items_df["id"] == history_filter_id].iloc[0]
        default_item_label = f"{row['name']} ({row['barcode']})"
    try:
        item_index = item_option_labels.index(default_item_label)
    except ValueError:
        item_index = 0
    selected_item_label = st.selectbox("Item", item_option_labels, index=item_index)
    st.session_state["history_item_filter"] = None

with col3:
    selected_type = st.selectbox("Transaction type", ["All", "Receive", "Check Out"])

start_date, end_date = streamlit_date_range_to_iso(date_range)

item_id = None
if selected_item_label != "All items":
    selected_row = items_df[
        (items_df["name"] + " (" + items_df["barcode"] + ")") == selected_item_label
    ].iloc[0]
    item_id = int(selected_row["id"])

tx_type_map = {"Receive": "in", "Check Out": "out"}
tx_type = None if selected_type == "All" else tx_type_map[selected_type]

history_df = get_transactions(start_date=start_date, end_date=end_date, item_id=item_id, tx_type=tx_type)

if history_df.empty:
    st.info("No transactions found for selected filters.")
else:
    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
    history_df["type"] = history_df["type"].map({"in": "📥 Receive", "out": "📤 Check Out"})
    history_df = history_df.rename(
        columns={
            "id": "Transaction ID",
            "timestamp": "Timestamp",
            "item_name": "Item",
            "barcode": "Barcode",
            "type": "Type",
            "quantity": "Quantity",
            "unit": "Unit",
            "notes": "Notes",
        }
    )
    st.dataframe(history_df, use_container_width=True, hide_index=True)
