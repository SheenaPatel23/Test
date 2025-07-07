import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import pdfplumber

st.set_page_config(page_title="Invoice Coding Tool", layout="wide")
st.title("📊 Finance Invoice Coding Tool")

st.markdown("""
This app helps finance teams code invoices using the **Chart of Accounts** for **Shipsure** and **HFM**.

Upload an invoice file to begin. The Chart of Accounts is preloaded from the repository.
""")

# --- Load Chart of Accounts from repo ---
coa_path = "coa_data/chart_of_accounts.csv"
try:
    coa = pd.read_csv(coa_path)
except FileNotFoundError:
    st.error("❌ Chart of Accounts file not found. Please ensure `chart_of_accounts.csv` exists in the `coa_data/` folder.")
    st.stop()

# --- Upload Invoice File ---
st.sidebar.header("Upload Invoice File")
invoice_file = st.sidebar.file_uploader("Upload .xlsx, .csv, or .pdf", type=["xlsx", "csv", "pdf"])

if invoice_file:
    # --- Read Invoice File ---
    if invoice_file.name.endswith(".xlsx"):
        invoices = pd.read_excel(invoice_file)
    elif invoice_file.name.endswith(".csv"):
        invoices = pd.read_csv(invoice_file)
    elif invoice_file.name.endswith(".pdf"):
        with pdfplumber.open(invoice_file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        st.subheader("📄 Extracted PDF Text")
        st.text_area("Invoice Content", text, height=300)
        invoices = pd.DataFrame([{
            "Invoice Number": "PDF001",
            "Description": text[:100],
            "Amount": 0.0
        }])

    st.subheader("📄 Uploaded Invoices")
    st.dataframe(invoices, use_container_width=True)

    st.subheader("📘 Chart of Accounts (Preloaded)")
    st.dataframe(coa, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Invoice Coding Suggestions")

    coded_invoices = invoices.copy()

    def suggest_accounts(description, coa_df, top_n=3):
        choices = coa_df['Shipsure Account Description'].fillna("").tolist()
        results = process.extract(description, choices, limit=top_n)
        return results

    account_mapping = []
    for idx, row in invoices.iterrows():
        st.markdown(f"**Invoice {row.get('Invoice Number', idx+1)} - {row.get('Description', '')}**")
        suggestions = suggest_accounts(str(row.get("Description", "")), coa)
        selected = st.selectbox(
            f"Select account for invoice {row.get('Invoice Number', idx+1)}:",
            options=[s[0] for s in suggestions],
            index=0,
            key=f"select_{idx}"
        )
        coa_row = coa[coa['Shipsure Account Description'] == selected].iloc[0]
        account_mapping.append({
            "Invoice Number": row.get("Invoice Number", ""),
            "Description": row.get("Description", ""),
            "Amount": row.get("Amount", 0),
            "Mapped Account": selected,
            "Account Type": coa_row.get("Account Type", ""),
            "HFM Account Number": coa_row.get("HFM Account Number", ""),
            "HFM Description": coa_row.get("HFM Account Description", "")
        })

    result_df = pd.DataFrame(account_mapping)
    st.markdown("---")
    st.subheader("✅ Final Coded Invoices")
    st.dataframe(result_df, use_container_width=True)

    csv = result_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Coded Invoices",
        data=csv,
        file_name="coded_invoices.csv",
        mime="text/csv"
    )
else:
    st.info("Please upload an invoice file to begin.")
