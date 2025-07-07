import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import pdfplumber
import tempfile
import os

st.set_page_config(page_title="Invoice Coding Tool", layout="wide")
st.title("📊 Finance Invoice Coding Tool")

st.markdown("""
This app helps finance teams code invoices using the **Chart of Accounts** for **Shipsure** and **HFM**.
Upload an invoice file (Excel, CSV, or PDF), and it will suggest account mappings using fuzzy matching.
""")

# --- Load Chart of Accounts from repo ---
@st.cache_data
def load_coa():
    coa_path = "coa_data/chart_of_accounts.csv"
    return pd.read_csv(coa_path)

coa = load_coa()

# --- Upload Invoice File ---
st.sidebar.header("Step 1: Upload Invoice File")
invoice_file = st.sidebar.file_uploader("Invoice File (.xlsx, .csv, or .pdf)", type=["xlsx", "csv", "pdf"])

invoice_data = None

if invoice_file:
    if invoice_file.name.endswith(".xlsx"):
        invoice_data = pd.read_excel(invoice_file)
    elif invoice_file.name.endswith(".csv"):
        invoice_data = pd.read_csv(invoice_file)
    elif invoice_file.name.endswith(".pdf"):
        st.sidebar.subheader("PDF Parsing Method")
        st.sidebar.info("Using pdfplumber (basic table extraction)")

        with pdfplumber.open(invoice_file) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_tables.append(df)
            if all_tables:
                invoice_data = pd.concat(all_tables, ignore_index=True)
            else:
                st.warning("No tables found using pdfplumber.")

# --- Display Uploaded Content ---
if invoice_data is not None:
    st.subheader("📄 Uploaded Invoices")
    st.dataframe(invoice_data, use_container_width=True)

    st.subheader("📘 Chart of Accounts")
    st.dataframe(coa, use_container_width=True)

    # Normalize columns
    invoice_data.columns = [col.lower().strip() for col in invoice_data.columns]
    rename_map = {
        'invoice no': 'Invoice Number',
        'desc': 'Description',
        'amount ($)': 'Amount',
        'total': 'Amount',
        'description': 'Description',
        'amount': 'Amount'
    }
    invoice_data.rename(columns=rename_map, inplace=True)

    for col in ['Description', 'Amount']:
        if col not in invoice_data.columns:
            invoice_data[col] = ""

    st.markdown("---")
    st.subheader("🔍 Invoice Coding Suggestions")

    def suggest_accounts(description, coa_df, top_n=3):
        choices = coa_df['Shipsure Account Description'].fillna("").tolist()
        results = process.extract(description, choices, limit=top_n)
        return results

    coded = []
    for idx, row in invoice_data.iterrows():
        st.markdown(f"**Invoice {row.get('Invoice Number', f'INV{idx+1}')}** - {row.get('Description', '')}")
        suggestions = suggest_accounts(str(row.get("Description", "")), coa)
        selected = st.selectbox(
            f"Select account for invoice {row.get('Invoice Number', f'INV{idx+1}')}:", 
            [s[0] for s in suggestions], 
            index=0, key=f"select_{idx}"
        )
        coa_row = coa[coa['Shipsure Account Description'] == selected].iloc[0]
        coded.append({
            "Invoice Number": row.get("Invoice Number", f"INV{idx+1}"),
            "Description": row.get("Description", ""),
            "Amount": row.get("Amount", 0),
            "Mapped Account": selected,
            "Account Type": coa_row.get("Account Type", ""),
            "HFM Account Number": coa_row.get("HFM Account Number", ""),
            "HFM Description": coa_row.get("HFM Account Description", "")
        })

    result_df = pd.DataFrame(coded)
    st.markdown("---")
    st.subheader("✅ Final Coded Invoices")
    st.dataframe(result_df, use_container_width=True)

    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Coded Invoices", csv, "coded_invoices.csv", "text/csv")

else:
    st.info("Please upload an invoice file to begin.")
