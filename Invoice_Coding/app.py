import streamlit as st
import pandas as pd
import os
import pdfplumber
from fuzzywuzzy import process
from groq import Groq

# --- Page Config ---
st.set_page_config(page_title="Invoice Coding Tool", layout="wide")
st.title("📊 Finance Invoice Coding Tool with Groq LLM")

st.markdown("""
This app helps finance teams code invoices using the **Chart of Accounts**.
Uses fuzzy matching and Groq LLM for intelligent account suggestions.
""")

# === Read API key from Streamlit Secrets ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# --- Load Chart of Accounts ---
@st.cache_data
def load_coa():
    coa_path = os.path.join(os.path.dirname(__file__), "coa_data", "chart_of_accounts.csv")
    return pd.read_csv(coa_path)

coa = load_coa()
coa_descriptions = coa['Shipsure Account Description'].dropna().tolist()

# --- Groq LLM Suggestion ---
def get_llm_suggestion(description, coa_options):
    prompt = f"""
You are a finance assistant. Based on the invoice description, select the most appropriate account from the Chart of Accounts below.

Invoice Description:
"{description}"

Chart of Accounts Options:
{chr(10).join(f"- {desc}" for desc in coa_options[:50])}

Respond with only the **exact account description** that matches best.
"""
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful finance assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=50,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM Error: {e}"

# --- File Upload ---
st.sidebar.header("Step 1: Upload Invoice File")
invoice_file = st.sidebar.file_uploader("Upload Invoice File (.xlsx, .csv, or .pdf)", type=["xlsx", "csv", "pdf"])

if invoice_file:
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

    st.subheader("📘 Chart of Accounts (Preview)")
    st.dataframe(coa.head(), use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Invoice Coding Suggestions")

    coded_invoices = []
    for idx, row in invoices.iterrows():
        description = str(row.get("Description", "")).strip()
        amount = row.get("Amount", 0)
        invoice_number = row.get("Invoice Number", f"Row {idx+1}")

        # Fuzzy match
        fuzzy_suggestions = process.extract(description, coa_descriptions, limit=3)

        # Groq LLM match
        llm_suggestion = get_llm_suggestion(description, coa_descriptions)

        st.markdown(f"**Invoice {invoice_number} - {description[:60]}...**")
        selected = st.selectbox(
            f"Select fuzzy-matched account for invoice {invoice_number}:",
            options=[s[0] for s in fuzzy_suggestions],
            index=0,
            key=f"select_{idx}"
        )

        coa_row = coa[coa['Shipsure Account Description'] == selected].iloc[0]
        coded_invoices.append({
            "Invoice Number": invoice_number,
            "Description": description,
            "Amount": amount,
            "Mapped Account (Fuzzy)": selected,
            "Mapped Account (Groq LLM)": llm_suggestion,
            "Account Type": coa_row.get("Account Type", ""),
            "HFM Account Number": coa_row.get("HFM Account Number", ""),
            "HFM Description": coa_row.get("HFM Account Description", "")
        })

    result_df = pd.DataFrame(coded_invoices)

    st.markdown("---")
    st.subheader("✅ Final Coded Invoices (Groq-enhanced)")
    st.dataframe(result_df, use_container_width=True)

    # --- Download Option ---
    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Coded Invoices CSV",
        data=csv,
        file_name="coded_invoices_groq.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload an invoice file to continue.")
