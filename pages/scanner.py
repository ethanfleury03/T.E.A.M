import sqlite3

import streamlit as st

from database import get_item_by_barcode, get_outbound_dashboard_totals, normalize_barcode, record_scan_out
from ui.components import render_kpi_cards, render_page_header


render_page_header(
    "Take Items",
    "Scan barcodes to record items leaving the pantry.",
)

if "scanner_clear" not in st.session_state:
    st.session_state["scanner_clear"] = False

# Streamlit: assigning "" to a widget key often does not reset the text input; deleting the key does.
# Without a real clear, the same barcode stays set and every rerun records another transaction.
if st.session_state["scanner_clear"]:
    st.session_state["scanner_clear"] = False
    st.session_state.pop("scanner_barcode", None)

if flash := st.session_state.pop("scanner_flash", None):
    st.success(flash)


@st.cache_data(ttl=10)
def load_scanner_kpis() -> dict:
    return get_outbound_dashboard_totals()


totals = load_scanner_kpis()
render_kpi_cards(
    [
        {"label": "Known Items", "value": int(totals["known_items"]), "icon": "📦"},
        {"label": "Total Scanned Out", "value": int(totals["total_scanned_out"]), "icon": "📤"},
        {"label": "Unique Items Scanned", "value": int(totals["unique_items_scanned"]), "icon": "🧾"},
    ]
)

st.markdown("")
with st.container(border=True):
    st.markdown(
        """
        <div class="home-panel-heading">
            <div class="home-panel-title">Student Scan Station</div>
            <div class="home-panel-subtitle">Leave this page open on the laptop. Each successful scan records one item leaving the pantry.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    barcode = st.text_input(
        "Scan or enter barcode",
        key="scanner_barcode",
        placeholder="Scan a barcode — each scan counts as 1 item out\u2026",
        help="Press Enter after typing, or let your scanner send Enter. Barcode must already exist on Add Item.",
    )

code = normalize_barcode(barcode)
if code:
    item = get_item_by_barcode(code)

    if not item:
        st.error(
            f"No item found for barcode **{code}**. Add it under **Add Item** first, then scan it here."
        )
    else:
        try:
            record_scan_out(
                item_id=int(item["id"]),
                quantity=1,
                notes="Scanned out via Take Items",
            )
            load_scanner_kpis.clear()
            st.session_state["scanner_flash"] = f"Scanned out **1 × {item['name']}**."
            st.toast(f"Scanned out 1 × {item['name']}", icon="📤")
            st.session_state["scanner_clear"] = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except sqlite3.Error as exc:
            st.error("Database error while saving this scan. Try again.")
            st.caption(str(exc))
