from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_item_lookup, get_stock_over_time, get_top_checked_out_items, init_db


init_db()
st.title("Analytics")
st.caption("Most checked-out items and stock-level trends.")

default_end = date.today()
default_start = default_end - timedelta(days=30)
date_range = st.date_input("Date range for top checked-out chart", value=(default_start, default_end))

start_date = None
end_date = None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = date_range[0].isoformat()
    end_date = date_range[1].isoformat()

top_df = get_top_checked_out_items(limit=10, start_date=start_date, end_date=end_date)
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
    fig_top.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig_top, use_container_width=True)

st.subheader("Stock Level Over Time")
items_df = get_item_lookup()
if items_df.empty:
    st.info("Add items before viewing stock trends.")
else:
    item_options = {
        f"{row['name']} ({row['barcode']})": int(row["id"])
        for _, row in items_df.iterrows()
    }
    selected_label = st.selectbox("Select an item", list(item_options.keys()))
    selected_item_id = item_options[selected_label]

    stock_df = get_stock_over_time(selected_item_id)
    if stock_df.empty:
        st.info("No transactions yet for this item.")
    else:
        stock_df["timestamp"] = pd.to_datetime(stock_df["timestamp"])
        fig_line = px.line(stock_df, x="timestamp", y="stock_level", labels={"stock_level": "Stock Level"})
        st.plotly_chart(fig_line, use_container_width=True)
