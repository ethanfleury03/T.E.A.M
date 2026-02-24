from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import get_item_lookup, get_transactions, init_db


init_db()
st.title("Transaction History")
st.caption("View and filter all inventory in/out transactions.")

items_df = get_item_lookup()

col1, col2, col3 = st.columns(3)

with col1:
    default_end = date.today()
    default_start = default_end - timedelta(days=30)
    date_range = st.date_input("Date range", value=(default_start, default_end))

with col2:
    item_option_labels = ["All items"] + [f"{row['name']} ({row['barcode']})" for _, row in items_df.iterrows()]
    selected_item_label = st.selectbox("Item", item_option_labels)

with col3:
    selected_type = st.selectbox("Transaction type", ["All", "in", "out"])

start_date = None
end_date = None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].isoformat()
    end_date = date_range[1].isoformat()

item_id = None
if selected_item_label != "All items":
    selected_row = items_df[
        (items_df["name"] + " (" + items_df["barcode"] + ")") == selected_item_label
    ].iloc[0]
    item_id = int(selected_row["id"])

tx_type = None if selected_type == "All" else selected_type

history_df = get_transactions(start_date=start_date, end_date=end_date, item_id=item_id, tx_type=tx_type)

if history_df.empty:
    st.info("No transactions found for selected filters.")
else:
    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
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
    st.dataframe(history_df, use_container_width=True)
