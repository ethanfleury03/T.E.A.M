import streamlit as st

from database import get_dashboard_totals, init_db


st.set_page_config(page_title="Food Pantry Dashboard", page_icon=":shopping_trolley:", layout="wide")
init_db()

st.title("Food Pantry Dashboard")
st.caption("Track inventory, item checkouts, and incoming donations/restocks.")

totals = get_dashboard_totals()
col1, col2, col3 = st.columns(3)
col1.metric("Unique Items", int(totals["unique_items"]))
col2.metric("Current Units In Stock", int(totals["total_quantity"]))
col3.metric("Total Transactions", int(totals["total_transactions"]))

st.markdown(
    """
Use the pages in the sidebar:

- **Inventory**: view current stock and add new pantry items
- **Check Out**: scan barcode and log items going out
- **Receive Items**: scan barcode and log items coming in
- **Analytics**: view stock trends and most checked-out items
- **History**: review full transaction log
"""
)
