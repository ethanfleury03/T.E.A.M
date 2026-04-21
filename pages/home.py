import streamlit as st

from database import get_dashboard_totals
from ui.components import render_kpi_cards, render_page_header


render_page_header(
    "Food Pantry Dashboard",
    "Focused on items going out: volunteers scan when food is taken. Restocking uses Inventory or Stocking.",
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
            "help": "All movement logs (mostly check-outs from scanning)",
        },
    ]
)

st.markdown(
    """
### Workspace (take items first)

- **Take items**: scan barcodes — each scan removes **1** unit (main volunteer workflow)
- **Inventory**: see what’s low, **check out** quantities, or restock when needed
- **Analytics**: what’s moving **out** by item and category
- **History**: audit trail (defaults to **check-outs**)
- **Stocking**: add new SKUs or rare restock context — not the day-to-day path
"""
)
