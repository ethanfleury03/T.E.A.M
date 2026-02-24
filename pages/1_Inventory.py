import sqlite3

import pandas as pd
import streamlit as st

from database import SETTINGS, add_item, get_all_items, init_db


init_db()
st.title("Inventory Overview")
st.caption("View current pantry stock and add new items.")

items_df = get_all_items()

if items_df.empty:
    st.info("No items in inventory yet.")
else:
    display_df = items_df[["barcode", "name", "unit", "quantity"]].copy()
    display_df.columns = ["Barcode", "Item", "Unit", "Quantity"]

    low_stock = SETTINGS["LOW_STOCK_THRESHOLD"]

    def style_quantity(row: pd.Series) -> list[str]:
        if int(row["Quantity"]) <= low_stock:
            return ["", "", "", "background-color: #ffdddd; font-weight: 600;"]
        return ["", "", "", "background-color: #ddffdd;"]

    st.dataframe(display_df.style.apply(style_quantity, axis=1), use_container_width=True)
    st.caption(f"Low stock threshold: {low_stock} units")

if "show_add_item_form" not in st.session_state:
    st.session_state["show_add_item_form"] = False

if st.button("Add Item"):
    st.session_state["show_add_item_form"] = not st.session_state["show_add_item_form"]

if st.session_state["show_add_item_form"]:
    with st.form("add_item_form", clear_on_submit=True):
        st.subheader("Add New Item")
        name = st.text_input("Item name")
        barcode = st.text_input("Barcode")
        unit = st.text_input("Unit", value="units")
        initial_quantity = st.number_input("Initial quantity", min_value=0, step=1)
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Save Item")

        if submitted:
            if not name.strip() or not barcode.strip():
                st.error("Item name and barcode are required.")
            else:
                try:
                    add_item(
                        name=name,
                        barcode=barcode,
                        unit=unit,
                        initial_quantity=int(initial_quantity),
                        notes=notes,
                    )
                    st.success(f"Added '{name}' with barcode {barcode}.")
                    st.session_state["show_add_item_form"] = False
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That barcode already exists. Use a unique barcode.")
                except ValueError as exc:
                    st.error(str(exc))
