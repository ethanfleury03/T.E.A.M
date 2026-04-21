import sqlite3

import pandas as pd
import streamlit as st

from database import (
    ITEM_CATEGORIES,
    SETTINGS,
    add_item,
    delete_item,
    get_all_items,
    import_items_from_csv,
    record_transaction,
    update_item,
)
from ui.components import render_empty_state, render_kpi_cards, render_page_header


low_stock_threshold = int(st.session_state.get("low_stock_threshold", SETTINGS["LOW_STOCK_THRESHOLD"]))

for key in ("show_add_item_form", "inventory_action_mode", "inventory_show_import"):
    if key not in st.session_state:
        st.session_state[key] = False if key != "inventory_action_mode" else "none"

header_actions = render_page_header(
    "Inventory",
    "See levels and **check items out** (or restock). Use **Take items** in the nav to scan barcodes; low-stock cutoff is in the sidebar.",
    actions=[
        {"label": "Import CSV", "key": "inventory_import"},
    ],
)

if header_actions.get("inventory_import"):
    st.session_state["inventory_show_import"] = True

if st.session_state.get("inventory_show_import"):
    with st.expander("Import inventory from CSV", expanded=True):
        st.caption(
            "Required columns: **name**, **barcode**. Optional: **category**, **unit**, **initial_quantity** (default 0)."
        )
        uploaded = st.file_uploader("CSV file", type=["csv"], key="inventory_csv_uploader")
        ic1, ic2 = st.columns(2)
        with ic1:
            run_import = st.button("Run import", type="primary", key="inventory_csv_run")
        with ic2:
            if st.button("Close", key="inventory_csv_close"):
                st.session_state["inventory_show_import"] = False
                st.rerun()
        if run_import:
            if uploaded is None:
                st.error("Choose a CSV file before running import.")
            else:
                summary = import_items_from_csv(uploaded)
                st.cache_data.clear()
                if summary["errors"]:
                    st.warning("Some rows had problems:")
                    for err in summary["errors"][:20]:
                        st.caption(err)
                    if len(summary["errors"]) > 20:
                        st.caption(f"... and {len(summary['errors']) - 20} more.")
                st.success(
                    f"Added **{summary['added']}** item(s). "
                    f"Skipped **{summary['skipped_duplicates']}** (barcode already in database)."
                )
                if summary["added"] > 0:
                    st.session_state["inventory_show_import"] = False
                    st.rerun()


@st.cache_data(ttl=20)
def load_inventory() -> pd.DataFrame:
    return get_all_items()


def get_status(quantity: int, threshold: int) -> str:
    if quantity <= 0:
        return "Out"
    if quantity <= threshold:
        return "Low"
    return "OK"


items_df = load_inventory()
if items_df.empty:
    add_clicked, import_clicked = render_empty_state(
        "No Inventory Yet",
        "Start by adding pantry items. Once items are loaded, this page shows stock levels and quick actions.",
        "Add Item",
        "Import CSV",
    )
    if add_clicked:
        st.session_state["show_add_item_form"] = True
    if import_clicked:
        st.session_state["inventory_show_import"] = True
else:
    items_df["Status"] = items_df["quantity"].apply(lambda value: get_status(int(value), low_stock_threshold))
    total_skus = int(items_df["id"].nunique())
    total_units = int(items_df["quantity"].sum())
    low_stock_count = int((items_df["Status"] == "Low").sum())
    out_stock_count = int((items_df["Status"] == "Out").sum())

    render_kpi_cards(
        [
            {"label": "Total SKUs", "value": total_skus, "icon": "📦", "help": "Unique pantry items"},
            {"label": "Units On Hand", "value": total_units, "icon": "🧮", "help": "All quantities combined"},
            {"label": "Low Stock Items", "value": low_stock_count, "icon": "⚠️", "help": f"At or below {low_stock_threshold}"},
            {"label": "Out of Stock", "value": out_stock_count, "icon": "🛑", "help": "Quantity is zero"},
        ]
    )

    st.markdown("")
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search_text = st.text_input("Search inventory", placeholder="Search by item name or barcode")
    with f2:
        status_filter = st.selectbox("Status", ["All", "OK", "Low", "Out"])
    with f3:
        sort_option = st.selectbox("Sort", ["Item (A-Z)", "Quantity (Low-High)", "Quantity (High-Low)"])

    filtered_df = items_df.copy()
    if search_text.strip():
        query = search_text.strip().lower()
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(query) | filtered_df["barcode"].str.lower().str.contains(query)
        ]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]

    if sort_option == "Item (A-Z)":
        filtered_df = filtered_df.sort_values("name", ascending=True)
    elif sort_option == "Quantity (Low-High)":
        filtered_df = filtered_df.sort_values("quantity", ascending=True)
    else:
        filtered_df = filtered_df.sort_values("quantity", ascending=False)

    table_df = filtered_df[["name", "barcode", "category", "unit", "quantity", "Status"]].copy()
    table_df.columns = ["Item", "Barcode", "Category", "Unit", "Quantity", "Status"]
    table_df["Status"] = table_df["Status"].map({"OK": "✅ OK", "Low": "⚠ Low", "Out": "🛑 Out"})

    def row_style(row: pd.Series) -> list[str]:
        if "Out" in str(row["Status"]):
            return ["background-color: rgba(227, 93, 91, 0.10);"] * len(row)
        if "Low" in str(row["Status"]):
            return ["background-color: rgba(245, 166, 35, 0.10);"] * len(row)
        return [""] * len(row)

    styled = (
        table_df.style.apply(row_style, axis=1)
        .format({"Quantity": "{:.0f}"})
        .set_properties(subset=["Quantity"], **{"text-align": "right", "font-weight": "600"})
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    if not filtered_df.empty:
        st.markdown("#### Quick Actions")
        options = {
            f"{row['name']} ({row['barcode']}) - {row['quantity']} {row['unit']}": int(row["id"])
            for _, row in filtered_df.iterrows()
        }
        selected_label = st.selectbox("Select item", list(options.keys()))
        selected_id = options[selected_label]
        selected_item = filtered_df[filtered_df["id"] == selected_id].iloc[0]

        a1, a2, a3, a4, a5 = st.columns(5)
        with a1:
            if st.button("Check Out", use_container_width=True, type="primary", key="inventory_q_checkout"):
                st.session_state["inventory_action_mode"] = "checkout"
        with a2:
            if st.button("Restock", use_container_width=True, key="inventory_q_receive"):
                st.session_state["inventory_action_mode"] = "receive"
        with a3:
            if st.button("Edit Item", use_container_width=True, key="inventory_q_edit"):
                st.session_state["inventory_action_mode"] = "edit"
        with a4:
            if st.button("View History", use_container_width=True, key="inventory_q_history"):
                st.session_state["history_item_filter"] = selected_id
                st.toast("History filter pre-set. Open the History page to view this item.", icon="🧾")
        with a5:
            if st.button("Delete", use_container_width=True, key="inventory_q_delete"):
                st.session_state["inventory_action_mode"] = "delete"

        if st.session_state["inventory_action_mode"] in {"receive", "checkout"}:
            mode = st.session_state["inventory_action_mode"]
            with st.form(f"inventory_{mode}_form", clear_on_submit=True):
                qty_label = "Quantity to restock" if mode == "receive" else "Quantity to check out"
                qty = st.number_input(qty_label, min_value=1, step=1)
                notes = st.text_input("Notes (optional)")
                submit_label = "Confirm restock" if mode == "receive" else "Confirm check out"
                submitted = st.form_submit_button(submit_label)
                if submitted:
                    try:
                        record_transaction(
                            item_id=int(selected_item["id"]),
                            tx_type="in" if mode == "receive" else "out",
                            quantity=int(qty),
                            notes=notes,
                        )
                        st.cache_data.clear()
                        st.toast("Inventory updated successfully.", icon="✅")
                        st.session_state["inventory_action_mode"] = "none"
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

        if st.session_state["inventory_action_mode"] == "edit":
            with st.form("inventory_edit_item_form"):
                new_name = st.text_input("Item name", value=str(selected_item["name"]))
                new_barcode = st.text_input("Barcode", value=str(selected_item["barcode"]))
                current_cat = str(selected_item.get("category", "Uncategorized"))
                cat_options = ITEM_CATEGORIES if current_cat in ITEM_CATEGORIES else [current_cat] + ITEM_CATEGORIES
                new_category = st.selectbox("Category", cat_options, index=cat_options.index(current_cat))
                new_unit = st.text_input("Unit", value=str(selected_item["unit"]))
                submitted = st.form_submit_button("Save Item Details")
                if submitted:
                    if not new_name.strip() or not new_barcode.strip():
                        st.error("Item name and barcode are required.")
                    else:
                        try:
                            update_item(
                                item_id=int(selected_item["id"]),
                                name=new_name,
                                barcode=new_barcode,
                                unit=new_unit,
                                category=new_category,
                            )
                            st.cache_data.clear()
                            st.toast("Item details updated.", icon="✏️")
                            st.session_state["inventory_action_mode"] = "none"
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("That barcode is already in use.")

        if st.session_state["inventory_action_mode"] == "delete":
            st.warning(
                f"Delete **{selected_item['name']}**? This permanently removes the item and its transaction history."
            )
            with st.form("inventory_delete_item_form"):
                confirm_delete = st.checkbox("Yes, permanently delete this item")
                d1, d2 = st.columns(2)
                with d1:
                    delete_submitted = st.form_submit_button("Delete Item", type="primary")
                with d2:
                    cancel_submitted = st.form_submit_button("Cancel")

                if cancel_submitted:
                    st.session_state["inventory_action_mode"] = "none"
                    st.rerun()

                if delete_submitted:
                    if not confirm_delete:
                        st.error("Please confirm deletion before continuing.")
                    else:
                        try:
                            delete_item(int(selected_item["id"]))
                            st.cache_data.clear()
                            st.toast("Item deleted.", icon="🗑️")
                            st.session_state["inventory_action_mode"] = "none"
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))

if st.session_state["show_add_item_form"]:
    with st.form("inventory_add_item_form", clear_on_submit=True):
        st.subheader("Add New Item")
        name = st.text_input("Item name")
        barcode = st.text_input("Barcode")
        category = st.selectbox("Category", ITEM_CATEGORIES)
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
                        category=category,
                        initial_quantity=int(initial_quantity),
                        notes=notes,
                    )
                    st.cache_data.clear()
                    st.toast(f"Added {name}.", icon="✅")
                    st.session_state["show_add_item_form"] = False
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That barcode already exists. Use a unique barcode.")
                except ValueError as exc:
                    st.error(str(exc))
