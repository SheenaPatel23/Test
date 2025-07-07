import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import pdfplumber
import os

st.set_page_config(page_title="Invoice Coding Tool", layout="wide")
st.title("📊 Finance Invoice Coding Tool")

st.markdown("""
This app helps finance teams code invoices using the **Chart of Accounts** for **Shipsure** and **HFM**.
Upload an invoice file (PDF, Excel, or CSV), and we'll help map the descriptions to the correct account codes.
""")

# --- Load Chart of Accounts from internal folder ---
@st.cache_data
def load_coa():
    coa_path = os.path.join("coa_data", "chart_of_accounts.csv")
    return pd.read_csv(coa_path)

coa = load_coa()

# --- Upload Invoice File ---
st.sidebar.header("Step 1: Upload Invoice File")
invoice_file = st.sidebar.file_uploader("Upload Invoice File (.xlsx, .csv, or .pdf)", type=["xlsx", "csv", "pdf"])

if invoice_file:
    # --- Read Invoice File ---
    if invoice_file.name.endswith(".xlsx"):
        invoice_data = pd.read_excel(invoice_file)
    elif invoice_file.name.endswith(".csv"):
        invoice_data = pd.read_csv(invoice_file)
    elif invoice_file.name.endswith(".pdf"):
        st.sidebar.subheader("PDF Parsing Method")
        st.sidebar.info("Using pdfplumber (basic table extraction)")

        all_tables = []
        table_dfs = []
        with pdfplumber.open(invoice_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table_num, table in enumerate(tables):
                    if table and len(table) > 1:
                        headers = table[0]
                        headers = [
                            h if h and h.strip() else f"Column_{i}"
                            for i, h in enumerate(headers)
                        ]
                        # Ensure unique headers
                        seen = {}
                        clean_headers = []
                        for h in headers:
                            if h in seen:
                                seen[h] += 1
                                h = f"{h}_{seen[h]}"
                            else:
                                seen[h] = 0
                            clean_headers.append(h)
                        df = pd.DataFrame(table[1:], columns=clean_headers)
                        table_dfs.append({
                            "page": page_num + 1,
                            "table": table_num + 1,
                            "data": df
                        })

        if not table_dfs:
            st.warning("No tables were extracted from the PDF.")
            st.stop()
        else:
            table_labels = [f"Page {t['page']} - Table {t['table']}" for t in table_dfs]
            selected_idx = st.selectbox("📑 Select Table to Use", options=range(len(table_dfs)), format_func=lambda i: table_labels[i])
            st.subheader("📄 Preview Extracted Table")
            st.dataframe(table_dfs[selected_idx]["data"], use_container_width=True)
            invoice_data = table_dfs[selected_idx]["data"]

    # --- Show Uploaded Invoice Data ---
    st.subheader("📄 Uploaded Invoice Data")
    st.dataframe(invoice_data, use_container_width=True)

    # --- Show Chart of Accounts ---
    st.subheader("📘 Chart of Accounts")
    st.dataframe(coa, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Invoice Coding Suggestions")

    coded_invoices = invoice_data.copy()

    def suggest_accounts(description, coa_df, top_n=3):
        choices = coa_df['Shipsure Account Description'].fillna("").tolist()
        results = process.extract(description, choices, limit=top_n)
        return results

    account_mapping = []
    for idx, row in invoice_data.iterrows():
        desc = str(row.get("Description", row.get("description", "")))  # Case-insensitive fallback
        amount = row.get("Amount", row.get("amount", 0))
        invoice_num = row.get("Invoice Number", f"Row {idx+1}")
        st.markdown(f"**Invoice {invoice_num} - {desc}**")
        suggestions = suggest_accounts(desc, coa)
        selected = st.selectbox(
            f"Select account for invoice {invoice_num}:",
            options=[s[0] for s in suggestions],
            index=0,
            key=f"select_{idx}"
        )
        coa_row = coa[coa['Shipsure Account Description'] == selected].iloc[0]
        account_mapping.append({
            "Invoice Number": invoice_num,
            "Description": desc,
            "Amount": amount,
            "Mapped Account": selected,
            "Account Type": coa_row.get("Account Type", ""),
            "HFM Account Number": coa_row.get("HFM Account Number", ""),
            "HFM Description": coa_row.get("HFM Account Description", "")
        })

    result_df = pd.DataFrame(account_mapping)
    st.markdown("---")
    st.subheader("✅ Final Coded Invoices")
    st.dataframe(result_df, use_container_width=True)

    # --- Download button ---
    csv = result_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Coded Invoices",
        data=csv,
        file_name="coded_invoices.csv",
        mime="text/csv"
    )
else:
    st.info("Please upload an invoice file to begin.")
