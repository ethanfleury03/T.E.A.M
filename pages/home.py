import streamlit as st

from database import get_dashboard_totals
from ui.components import render_kpi_cards, render_page_header


render_page_header(
    "Food Pantry Dashboard",
    "Track inventory, monitor low stock, and capture every incoming/outgoing item.",
)

totals = get_dashboard_totals()
render_kpi_cards(
    [
        {"label": "Total SKUs", "value": int(totals["unique_items"]), "icon": "📦", "help": "Unique pantry items"},
        {
            "label": "Units On Hand",
            "value": int(totals["total_quantity"]),
            "icon": "🧮",
            "help": "Current stock quantity across all items",
        },
        {
            "label": "Total Transactions",
            "value": int(totals["total_transactions"]),
            "icon": "🧾",
            "help": "All check-in and check-out logs",
        },
    ]
)

st.markdown(
    """
### Workspace

- **Inventory**: view stock, filter quickly, and manage items
- **Scanner**: scan barcodes to check food in or out
- **Item Entry**: scan and register new items into the database
- **Analytics**: trend usage and stock movement over time
- **History**: audit all inventory transactions
"""
)
