import hashlib

import streamlit as st

from app.core.config import settings
from ui.api_client import InvoiceApiError, extract_invoice
from ui.presentation import build_invoice_field_rows, build_line_item_rows


st.set_page_config(page_title="Sąskaitų nuskaitymas", layout="wide")
st.title("Sąskaitų nuskaitymas")

uploaded_file = st.file_uploader("Pasirinkite PDF sąskaitą", type=["pdf"])

if uploaded_file is None:
    st.stop()

pdf_bytes = uploaded_file.getvalue()
if len(pdf_bytes) > settings.max_file_size_bytes:
    st.error(f"Failas viršija {settings.MAX_FILE_SIZE_MB} MB dydžio limitą.")
    st.stop()

file_fingerprint = hashlib.sha256(pdf_bytes).hexdigest()
if st.session_state.get("file_fingerprint") != file_fingerprint:
    st.session_state["file_fingerprint"] = file_fingerprint
    st.session_state.pop("invoice_result", None)

if st.button("Analizuoti sąskaitą", type="primary"):
    with st.spinner("Analizuojama sąskaita..."):
        try:
            st.session_state["invoice_result"] = extract_invoice(
                uploaded_file.name,
                pdf_bytes,
            )
        except InvoiceApiError as exc:
            st.session_state.pop("invoice_result", None)
            st.error(str(exc))

document_column, results_column = st.columns([1, 1.15], gap="large")

with document_column:
    st.subheader("Dokumentas")
    st.pdf(pdf_bytes, height=720, alt=f"PDF sąskaita {uploaded_file.name}")

with results_column:
    st.subheader("Nuskaitytos reikšmės")
    invoice_result = st.session_state.get("invoice_result")
    if invoice_result is None:
        st.info("Pasirinkite PDF ir spauskite „Analizuoti sąskaitą“.")
    else:
        field_rows = build_invoice_field_rows(invoice_result)
        if field_rows:
            st.dataframe(field_rows, hide_index=True, use_container_width=True)
        else:
            st.info("Azure negrąžino sąskaitos laukų.")

        if invoice_result.items:
            st.subheader("Prekės ir paslaugos")
            item_rows = build_line_item_rows(invoice_result)
            if item_rows:
                st.dataframe(item_rows, hide_index=True, use_container_width=True)