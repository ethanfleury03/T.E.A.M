import sqlite3

import streamlit as st

from database import ITEM_CATEGORIES, add_item, get_item_by_barcode, normalize_barcode
from ui.components import render_page_header

render_page_header(
    "Add Item",
    "Register known pantry items before students scan them out.",
)

st.markdown("")

if "item_entry_clear" not in st.session_state:
    st.session_state["item_entry_clear"] = False

if st.session_state["item_entry_clear"]:
    st.session_state["item_entry_clear"] = False
    st.session_state.pop("item_entry_barcode", None)

with st.container(border=True):
    st.markdown(
        """
        <div class="home-panel-heading">
            <div class="home-panel-title">Add to Item Sheet</div>
            <div class="home-panel-subtitle">Register the barcode once so students can scan it out later.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    barcode = st.text_input(
        "Scan or enter barcode",
        key="item_entry_barcode",
        placeholder="Scan a barcode to get started\u2026",
    )

normalized_barcode = normalize_barcode(barcode)

if normalized_barcode:
    existing = get_item_by_barcode(normalized_barcode)

    if existing:
        st.warning(
            f"**\"{existing['name']}\"** is already in the database.  \n"
            "This page is only for adding **new** items. "
            "Use **Take Items** to record it leaving the pantry."
        )
    else:
        st.success("New barcode detected — fill in the details below to add this item.")

        with st.form("item_entry_form", clear_on_submit=True):
            st.markdown(f"**Barcode:** `{normalized_barcode}`")
            name = st.text_input("Item name", placeholder="e.g. Canned Green Beans")
            category = st.selectbox("Category", ITEM_CATEGORIES)
            unit = st.text_input("Unit of measure", value="units", placeholder="e.g. cans, boxes, bags")
            submitted = st.form_submit_button("Add Item to Item Sheet", type="primary")

            if submitted:
                if not name.strip():
                    st.error("Item name is required.")
                else:
                    try:
                        add_item(
                            name=name,
                            barcode=normalized_barcode,
                            unit=unit,
                            category=category,
                            initial_quantity=0,
                            notes="Added via Add Item",
                        )
                        st.cache_data.clear()
                        st.toast(f"Added \"{name.strip()}\" to the Item Sheet.", icon="✅")
                        st.session_state["item_entry_clear"] = True
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("That barcode was just added by someone else. Please try again.")
                    except ValueError as exc:
                        st.error(str(exc))
else:
    st.info("Scan a barcode above to see if it is new, then add the item details for the Item Sheet.")
