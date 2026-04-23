import streamlit as st

from database import init_db
from ui.components import render_sidebar
from ui.styles import configure_page, inject_global_styles


configure_page(page_title="Niagara Pantry", page_icon=":shopping_trolley:")
inject_global_styles()
init_db()

home = st.Page("pages/home.py", title="Home", icon=":material/home:", default=True)
scanner = st.Page("pages/scanner.py", title="Take Items", icon=":material/qr_code_scanner:")
item_sheet = st.Page("pages/inventory.py", title="Item Sheet", icon=":material/table_view:")
analytics = st.Page("pages/analytics.py", title="Analytics", icon=":material/monitoring:")
history = st.Page("pages/history.py", title="History", icon=":material/history:")
item_entry = st.Page("pages/item_entry.py", title="Add Item", icon=":material/post_add:")

# Outbound-first: scan/take items before admin setup flows.
nav = st.navigation([home, scanner, item_sheet, analytics, history, item_entry])
active_title = getattr(nav, "title", "Home")
render_sidebar(active_title)
nav.run()
