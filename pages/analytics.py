from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    SETTINGS,
    get_checked_out_by_category,
    get_item_lookup,
    get_top_checked_out_items,
    get_transactions,
)
from ui.components import render_kpi_cards, render_page_header


threshold = int(st.session_state.get("low_stock_threshold", SETTINGS["LOW_STOCK_THRESHOLD"]))
render_page_header(
    "Analytics",
    "See what’s **going out**: top items, categories, and how outs compare to restocking.",
)

default_end = date.today()
default_start = default_end - timedelta(days=30)
date_range = st.date_input("Date range for charts below", value=(default_start, default_end))

start_date = None
end_date = None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].isoformat()
    end_date = date_range[1].isoformat()

top_df = get_top_checked_out_items(limit=10, start_date=start_date, end_date=end_date)
category_out_df = get_checked_out_by_category(start_date=start_date, end_date=end_date)
items_df = get_item_lookup()
tx_df = get_transactions(start_date=start_date, end_date=end_date)
checkout_count = int(tx_df[tx_df["type"] == "out"]["quantity"].sum()) if not tx_df.empty else 0
receive_count = int(tx_df[tx_df["type"] == "in"]["quantity"].sum()) if not tx_df.empty else 0
low_now = int((items_df["quantity"] <= threshold).sum()) if not items_df.empty else 0

render_kpi_cards(
    [
        {"label": "Units Checked Out", "value": checkout_count, "icon": "📤", "help": "Selected date window"},
        {
            "label": "Units Restocked",
            "value": receive_count,
            "icon": "📥",
            "help": "Receive / restock transactions in range (usually fewer than outs)",
        },
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
    st.subheader("Out vs restock (reference)")
    flow_df = pd.DataFrame(
        [
            {"type": "Restocked", "quantity": receive_count},
            {"type": "Checked out", "quantity": checkout_count},
        ]
    )
    fig_flow = px.bar(flow_df, x="type", y="quantity", labels={"type": "", "quantity": "Quantity"})
    st.plotly_chart(fig_flow, use_container_width=True)

    st.subheader("Checked out by category")
    if category_out_df.empty:
        st.info("No scanned-out (checkout) transactions in the selected date range.")
    else:
        fig_cat = px.bar(
            category_out_df,
            x="category",
            y="total_checked_out",
            labels={"category": "Category", "total_checked_out": "Units scanned out"},
        )
        fig_cat.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig_cat, use_container_width=True)
