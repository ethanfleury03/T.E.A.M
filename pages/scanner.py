import streamlit as st

from database import SETTINGS, get_item_by_barcode, get_item_lookup, record_transaction
from ui.components import render_kpi_cards, render_page_header


threshold = int(st.session_state.get("low_stock_threshold", SETTINGS["LOW_STOCK_THRESHOLD"]))
render_page_header("Scanner", "Scan items to check food in or out of inventory.")

if "scanner_clear" not in st.session_state:
    st.session_state["scanner_clear"] = False
if "scanner_direction" not in st.session_state:
    st.session_state["scanner_direction"] = "In"

if st.session_state["scanner_clear"]:
    st.session_state["scanner_clear"] = False
    st.session_state["scanner_barcode"] = ""


@st.cache_data(ttl=10)
def load_scanner_kpis() -> tuple[int, int]:
    df = get_item_lookup()
    return (int(df["id"].nunique()), int(df["quantity"].sum())) if not df.empty else (0, 0)


sku_count, unit_count = load_scanner_kpis()
render_kpi_cards(
    [
        {"label": "Tracked SKUs", "value": sku_count, "icon": "📦"},
        {"label": "Units On Hand", "value": unit_count, "icon": "🧮"},
        {"label": "Low Threshold", "value": threshold, "icon": "⚠️"},
    ]
)

st.markdown("")
btn_col1, btn_col2, spacer = st.columns([1, 1, 3])
with btn_col1:
    if st.button(
        "📥  Check In",
        use_container_width=True,
        type="primary" if st.session_state["scanner_direction"] == "In" else "secondary",
        key="scanner_btn_in",
    ):
        st.session_state["scanner_direction"] = "In"
        st.rerun()
with btn_col2:
    if st.button(
        "📤  Check Out",
        use_container_width=True,
        type="primary" if st.session_state["scanner_direction"] == "Out" else "secondary",
        key="scanner_btn_out",
    ):
        st.session_state["scanner_direction"] = "Out"
        st.rerun()

direction = st.session_state["scanner_direction"]
tx_type = "in" if direction == "In" else "out"

st.markdown(f"**Mode:** Checking items **{direction}**")
st.markdown("")

barcode = st.text_input(
    "Scan or enter barcode",
    key="scanner_barcode",
    placeholder="Scan a barcode — each scan counts as 1 item\u2026",
)

if barcode.strip():
    item = get_item_by_barcode(barcode.strip())

    if not item:
        st.error("No item found for this barcode. Use **Item Entry** to add it first.")
    else:
        current_qty = int(item["quantity"])

        try:
            record_transaction(
                item_id=int(item["id"]),
                tx_type=tx_type,
                quantity=1,
                notes=f"Scanned {direction.lower()} via Scanner",
            )
            new_qty = current_qty + 1 if tx_type == "in" else current_qty - 1
            if tx_type == "in":
                st.toast(f"Checked in 1 × {item['name']}  (stock: {new_qty})", icon="📥")
            else:
                st.toast(f"Checked out 1 × {item['name']}  (stock: {new_qty})", icon="📤")
            st.session_state["scanner_clear"] = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
            st.markdown(
                f"**Item:** {item['name']}  \n"
                f"**Current stock:** {current_qty} {item['unit']}"
            )
