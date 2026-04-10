import streamlit as st

from database import init_db
from ui.components import render_sidebar
from ui.styles import configure_page, inject_global_styles


configure_page(page_title="Niagara Pantry", page_icon=":shopping_trolley:")
inject_global_styles()
init_db()

home = st.Page("pages/home.py", title="Home", icon=":material/home:", default=True)
inventory = st.Page("pages/inventory.py", title="Inventory", icon=":material/inventory_2:")
scanner = st.Page("pages/scanner.py", title="Scanner", icon=":material/qr_code_scanner:")
item_entry = st.Page("pages/item_entry.py", title="Item Entry", icon=":material/post_add:")
analytics = st.Page("pages/analytics.py", title="Analytics", icon=":material/monitoring:")
history = st.Page("pages/history.py", title="History", icon=":material/history:")

nav = st.navigation([home, inventory, scanner, item_entry, analytics, history])
active_title = getattr(nav, "title", "Home")
render_sidebar(active_title)
nav.run()
