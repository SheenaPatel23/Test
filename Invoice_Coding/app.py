import streamlit as st
import pandas as pd
import os
from fuzzywuzzy import process
import pdfplumber

# --- Page Config ---
st.set_page_config(page_title="Invoice Coding Tool", layout="wide")
st.title("📊 Finance Invoice Coding Tool")

st.markdown("""
This app helps finance teams code invoices using the **Chart of Accounts** for **Shipsure** and **HFM**.
Upload an invoice file to begin. The Chart of Accounts is preloaded from the repository.
""")

# --- Load Chart of Accounts from local repo folder ---
@st.cache_data
def load_coa():
    coa_path = os.path.join(os.path.dirname(__file__), "coa_data", "chart_of_accounts.csv")
    return pd.read_csv(coa_path)

coa = load_coa()

# --- File Upload ---
st.sidebar.header("Step 1: Upload Invoice File")
invoice_file = st.sidebar.file_uploader("Upload Invoice File (.xlsx, .csv, or .pdf)", type=["xlsx", "csv", "pdf"])

if invoice_file:
    # --- Read Invoice File ---
    if invoice_file.name.endswith(".xlsx"):
        invoices = pd.read_excel(invoice_file)

    elif invoice_file.name.endswith(".csv"):
        invoices = pd.read_csv(invoice_file)

    elif invoice_file.name.endswith(".pdf"):
        with pdfplumber.open(invoice_file) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        headers = table[0]
                        seen = {}
                        unique_headers = []
                        for h in headers:
                            if h in seen:
                                seen[h] += 1
                                unique_headers.append(f"{h}_{seen[h]}")
                            else:
                                seen[h] = 0
                                unique_headers.append(h)
                        df = pd.DataFrame(table[1:], columns=unique_headers)
                        all_tables.append(df)

        if all_tables:
            try:
                invoices = pd.concat(all_tables, ignore_index=True)
            except Exception as e:
                st.error(f"Error combining tables: {e}")
                st.stop()

            st.subheader("📄 Extracted Table from PDF")
            st.dataframe(invoices.head(), use_container_width=True)
        else:
            st.warning("No tables found in the PDF.")
            st.stop()

    # --- Show Chart of Accounts ---
    st.subheader("📘 Chart of Accounts (Preview)")
    st.dataframe(coa.head(), use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Invoice Coding Suggestions")

    coded_invoices = []
    for idx, row in invoices.iterrows():
        description = str(row.get("Description", "")).strip()
        amount = row.get("Amount", 0)
        invoice_number = row.get("Invoice Number", f"Row {idx+1}")

        # Suggest accounts using fuzzy match
        suggestions = process.extract(description, coa['Shipsure Account Description'].fillna("").tolist(), limit=3)

        st.markdown(f"**Invoice {invoice_number} - {description[:50]}...**")
        selected = st.selectbox(
            f"Select account for invoice {invoice_number}:",
            options=[s[0] for s in suggestions],
            index=0,
            key=f"select_{idx}"
        )

        coa_row = coa[coa['Shipsure Account Description'] == selected].iloc[0]
        coded_invoices.append({
            "Invoice Number": invoice_number,
            "Description": description,
            "Amount": amount,
            "Mapped Account": selected,
            "Account Type": coa_row.get("Account Type", ""),
            "HFM Account Number": coa_row.get("HFM Account Number", ""),
            "HFM Description": coa_row.get("HFM Account Description", "")
        })

    result_df = pd.DataFrame(coded_invoices)

    st.markdown("---")
    st.subheader("✅ Final Coded Invoices")
    st.dataframe(result_df, use_container_width=True)

    # --- Download Result ---
    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Coded Invoices CSV",
        data=csv,
        file_name="coded_invoices.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload an invoice file to continue.")
