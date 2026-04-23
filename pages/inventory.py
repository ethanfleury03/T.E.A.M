import sqlite3

import pandas as pd
import streamlit as st

from database import (
    ITEM_CATEGORIES,
    delete_item,
    get_item_sheet_summary,
    get_outbound_dashboard_totals,
    update_item,
)
from ui.components import render_kpi_cards, render_page_header


if "item_sheet_action_mode" not in st.session_state:
    st.session_state["item_sheet_action_mode"] = "none"

render_page_header(
    "Item Sheet",
    "See the total count of items scanned out of the pantry.",
)


@st.cache_data(ttl=20)
def load_item_sheet() -> pd.DataFrame:
    return get_item_sheet_summary()


@st.cache_data(ttl=20)
def load_item_sheet_totals() -> dict:
    return get_outbound_dashboard_totals()


items_df = load_item_sheet()
totals = load_item_sheet_totals()

render_kpi_cards(
    [
        {"label": "Total Scanned Out", "value": int(totals["total_scanned_out"]), "icon": "📤", "help": "All scan-outs recorded"},
        {"label": "Unique Items Scanned", "value": int(totals["unique_items_scanned"]), "icon": "🧾", "help": "Different items taken"},
        {"label": "Top Item", "value": totals["top_item"], "icon": "🏷️", "help": f"{totals['top_item_count']} scanned out"},
        {"label": "Not Yet Scanned", "value": int(totals["items_not_scanned"]), "icon": "○", "help": "Items on the sheet with no scan-outs"},
    ]
)

if items_df.empty:
    st.info("No items are on the Item Sheet yet. Add known barcodes on the Add Item page before scan-outs begin.")
else:
    st.markdown("")
    with st.container(border=True):
        st.markdown(
            """
            <div class="home-panel-heading">
                <div class="home-panel-title">Item Sheet Filters</div>
                <div class="home-panel-subtitle">Find items by barcode, category, scan status, or recent activity.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            search_text = st.text_input("Search Item Sheet", placeholder="Search by item name or barcode")
        with f2:
            scan_filter = st.selectbox("Scan status", ["All items", "Scanned items", "Never scanned"])
        with f3:
            category_options = ["All"] + sorted(items_df["category"].fillna("Uncategorized").astype(str).unique().tolist())
            category_filter = st.selectbox("Category", category_options)
        with f4:
            sort_option = st.selectbox("Sort", ["Most scanned", "Recently scanned", "Item A-Z"])

    filtered_df = items_df.copy()
    filtered_df["total_scanned_out"] = filtered_df["total_scanned_out"].fillna(0).astype(int)

    if search_text.strip():
        query = search_text.strip().lower()
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(query)
            | filtered_df["barcode"].str.lower().str.contains(query)
        ]
    if scan_filter == "Scanned items":
        filtered_df = filtered_df[filtered_df["total_scanned_out"] > 0]
    elif scan_filter == "Never scanned":
        filtered_df = filtered_df[filtered_df["total_scanned_out"] == 0]
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df["category"] == category_filter]

    if sort_option == "Most scanned":
        filtered_df = filtered_df.sort_values(["total_scanned_out", "name"], ascending=[False, True])
    elif sort_option == "Recently scanned":
        filtered_df["_last_scanned_sort"] = pd.to_datetime(filtered_df["last_scanned_out"], errors="coerce", utc=True)
        filtered_df = filtered_df.sort_values("_last_scanned_sort", ascending=False, na_position="last")
    else:
        filtered_df = filtered_df.sort_values("name", ascending=True)

    if filtered_df.empty:
        st.info("No items match the selected filters.")
    else:
        table_df = filtered_df[["name", "barcode", "category", "unit", "total_scanned_out", "last_scanned_out"]].copy()
        table_df.columns = ["Item", "Barcode", "Category", "Unit", "Total Scanned Out", "Last Scanned Out"]
        last_scanned = pd.to_datetime(table_df["Last Scanned Out"], errors="coerce", utc=True)
        table_df["Last Scanned Out"] = last_scanned.dt.strftime("%Y-%m-%d %I:%M %p").fillna("Never")

        styled = (
            table_df.style
            .format({"Total Scanned Out": "{:.0f}"})
            .set_properties(subset=["Total Scanned Out"], **{"text-align": "right", "font-weight": "600"})
        )
        st.caption(f"Showing **{len(filtered_df)}** of **{len(items_df)}** items.")
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown("#### Item Actions")
        options = {
            f"{row['name']} ({row['barcode']}) - {int(row['total_scanned_out'])} scanned out": int(row["id"])
            for _, row in filtered_df.iterrows()
        }
        selected_label = st.selectbox("Select item", list(options.keys()))
        selected_id = options[selected_label]
        selected_item = filtered_df[filtered_df["id"] == selected_id].iloc[0]

        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("Edit Item", use_container_width=True, type="primary", key="item_sheet_edit"):
                st.session_state["item_sheet_action_mode"] = "edit"
        with a2:
            if st.button("View History", use_container_width=True, key="item_sheet_history"):
                st.session_state["history_item_filter"] = selected_id
                st.toast("History filter pre-set. Open the History page to view this item.", icon="🧾")
        with a3:
            if st.button("Delete", use_container_width=True, key="item_sheet_delete"):
                st.session_state["item_sheet_action_mode"] = "delete"

        if st.session_state["item_sheet_action_mode"] == "edit":
            with st.form("item_sheet_edit_item_form"):
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
                            st.session_state["item_sheet_action_mode"] = "none"
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("That barcode is already in use.")
                        except ValueError as exc:
                            st.error(str(exc))

        if st.session_state["item_sheet_action_mode"] == "delete":
            st.warning(
                f"Delete **{selected_item['name']}**? This removes the item and its scan-out history."
            )
            with st.form("item_sheet_delete_item_form"):
                confirm_delete = st.checkbox("Yes, permanently delete this item")
                d1, d2 = st.columns(2)
                with d1:
                    delete_submitted = st.form_submit_button("Delete Item", type="primary")
                with d2:
                    cancel_submitted = st.form_submit_button("Cancel")

                if cancel_submitted:
                    st.session_state["item_sheet_action_mode"] = "none"
                    st.rerun()

                if delete_submitted:
                    if not confirm_delete:
                        st.error("Please confirm deletion before continuing.")
                    else:
                        try:
                            delete_item(int(selected_item["id"]))
                            st.cache_data.clear()
                            st.toast("Item deleted.", icon="🗑️")
                            st.session_state["item_sheet_action_mode"] = "none"
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
