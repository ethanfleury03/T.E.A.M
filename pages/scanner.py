import sqlite3

import streamlit as st

from database import SETTINGS, get_item_by_barcode, get_item_lookup, record_transaction
from ui.components import render_kpi_cards, render_page_header


def _normalize_barcode(raw: str) -> str:
    """Hardware scanners often append CR/LF or spaces; DB lookup is exact match on stored barcode."""
    return "".join(ch for ch in raw.strip() if ch not in "\r\n\t")


threshold = int(st.session_state.get("low_stock_threshold", SETTINGS["LOW_STOCK_THRESHOLD"]))
render_page_header(
    "Take items",
    "Scan barcodes to record food **leaving** the pantry (1 scan = 1 unit out).",
)

if "scanner_clear" not in st.session_state:
    st.session_state["scanner_clear"] = False
if "scanner_direction" not in st.session_state:
    st.session_state["scanner_direction"] = "Out"

# Streamlit: assigning "" to a widget key often does not reset the text input; deleting the key does.
# Without a real clear, the same barcode stays set and every rerun records another transaction.
if st.session_state["scanner_clear"]:
    st.session_state["scanner_clear"] = False
    st.session_state.pop("scanner_barcode", None)

if flash := st.session_state.pop("scanner_flash", None):
    st.success(flash)


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
        "📤  Check out (take)",
        use_container_width=True,
        type="primary" if st.session_state["scanner_direction"] == "Out" else "secondary",
        key="scanner_btn_out",
    ):
        st.session_state["scanner_direction"] = "Out"
        st.rerun()
with btn_col2:
    if st.button(
        "📥  Check in (restock)",
        use_container_width=True,
        type="primary" if st.session_state["scanner_direction"] == "In" else "secondary",
        key="scanner_btn_in",
    ):
        st.session_state["scanner_direction"] = "In"
        st.rerun()

direction = st.session_state["scanner_direction"]
tx_type = "in" if direction == "In" else "out"

if direction == "Out":
    st.markdown("**Mode:** Items **leaving** the pantry (default).")
else:
    st.info("**Restock mode** — use only when putting inventory back on shelves (not the usual volunteer flow).")
st.markdown("")

barcode = st.text_input(
    "Scan or enter barcode",
    key="scanner_barcode",
    placeholder="Scan a barcode — each scan counts as 1 item\u2026",
    help="Press Enter after typing, or let your scanner send Enter. Barcode must match **Stocking** / catalog exactly.",
)

code = _normalize_barcode(barcode)
if code:
    item = get_item_by_barcode(code)

    if not item:
        st.error(
            f"No item found for barcode **{code}**. Add it under **Stocking** or check for typos / "
            "scanner prefixes (the app matches the stored barcode exactly)."
        )
    else:
        current_qty = int(item["quantity"])

        try:
            record_transaction(
                item_id=int(item["id"]),
                tx_type=tx_type,
                quantity=1,
                notes=f"Scanned {direction.lower()} via Scanner",
            )
            load_scanner_kpis.clear()
            new_qty = current_qty + 1 if tx_type == "in" else current_qty - 1
            label = "Checked in" if tx_type == "in" else "Checked out"
            st.session_state["scanner_flash"] = f"{label} **1 × {item['name']}** — stock now **{new_qty}**."
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
        except sqlite3.Error as exc:
            st.error("Database error while saving this scan. Try again.")
            st.caption(str(exc))
