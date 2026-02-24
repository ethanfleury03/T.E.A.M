import streamlit as st

from database import get_item_by_barcode, init_db, record_transaction


init_db()
st.title("Check Out Items")
st.caption("Scan barcode to log pantry items going out.")

barcode = st.text_input("Scan or enter barcode", key="checkout_barcode").strip()

if barcode:
    item = get_item_by_barcode(barcode)
    if not item:
        st.error("No item found for this barcode.")
    else:
        st.success(f"Item: {item['name']} ({item['quantity']} {item['unit']} currently in stock)")

        with st.form("checkout_form", clear_on_submit=True):
            quantity = st.number_input("Quantity taken", min_value=1, step=1)
            notes = st.text_input("Notes (optional)")
            submitted = st.form_submit_button("Log Check Out")

            if submitted:
                try:
                    record_transaction(
                        item_id=int(item["id"]),
                        tx_type="out",
                        quantity=int(quantity),
                        notes=notes,
                    )
                    st.success("Checkout logged successfully.")
                    st.session_state["checkout_barcode"] = ""
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
