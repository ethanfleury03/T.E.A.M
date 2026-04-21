from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import SETTINGS, get_item_lookup, get_stock_over_time, get_top_checked_out_items, get_transactions
from date_utils import streamlit_date_range_to_iso
from ui.components import render_kpi_cards, render_page_header


threshold = int(st.session_state.get("low_stock_threshold", SETTINGS["LOW_STOCK_THRESHOLD"]))
render_page_header("Analytics", "Track usage trends and inventory movement over time.")

default_end = date.today()
default_start = default_end - timedelta(days=30)
date_range = st.date_input("Date range for top checked-out chart", value=(default_start, default_end))

start_date, end_date = streamlit_date_range_to_iso(date_range)

top_df = get_top_checked_out_items(limit=10, start_date=start_date, end_date=end_date)
items_df = get_item_lookup()
tx_df = get_transactions(start_date=start_date, end_date=end_date)
checkout_count = int(tx_df[tx_df["type"] == "out"]["quantity"].sum()) if not tx_df.empty else 0
receive_count = int(tx_df[tx_df["type"] == "in"]["quantity"].sum()) if not tx_df.empty else 0
if items_df.empty:
    low_now = 0
else:
    q = items_df["quantity"].astype(int)
    low_now = int(((q > 0) & (q <= threshold)).sum())

render_kpi_cards(
    [
        {"label": "Units Checked Out", "value": checkout_count, "icon": "📤", "help": "Selected date window"},
        {"label": "Units Received", "value": receive_count, "icon": "📥", "help": "Selected date window"},
        {"label": "Low Stock Items", "value": low_now, "icon": "⚠️", "help": f"At or below {threshold}"},
    ]
)

left, right = st.columns(2)
with left:
    st.subheader("Top 10 Most Checked-Out Items")
    if top_df.empty:
        st.info("No checkout transactions in selected date range.")
    else:
        fig_top = px.bar(
            top_df,
            x="item_name",
            y="total_checked_out",
            labels={"item_name": "Item", "total_checked_out": "Quantity Checked Out"},
        )
        fig_top.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig_top, use_container_width=True)

with right:
    st.subheader("Flow In vs Flow Out")
    flow_df = pd.DataFrame(
        [
            {"type": "Received", "quantity": receive_count},
            {"type": "Checked Out", "quantity": checkout_count},
        ]
    )
    fig_flow = px.bar(flow_df, x="type", y="quantity", labels={"type": "", "quantity": "Quantity"})
    st.plotly_chart(fig_flow, use_container_width=True)

st.subheader("Stock Level Over Time")
if items_df.empty:
    st.info("Add items before viewing stock trends.")
else:
    item_options = {f"{row['name']} ({row['barcode']})": int(row["id"]) for _, row in items_df.iterrows()}
    selected_label = st.selectbox("Select an item", list(item_options.keys()))
    selected_item_id = item_options[selected_label]
    stock_df = get_stock_over_time(selected_item_id)
    if stock_df.empty:
        st.info("No transactions yet for this item.")
    else:
        stock_df["timestamp"] = pd.to_datetime(stock_df["timestamp"])
        fig_line = px.line(stock_df, x="timestamp", y="stock_level", labels={"stock_level": "Stock Level"})
        st.plotly_chart(fig_line, use_container_width=True)
