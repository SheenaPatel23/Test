import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz, process
import fitz  # PyMuPDF for PDF parsing

st.title("🧾 Invoice to COA Matching (Local AI-Like)")

# === Hardcoded Chart of Accounts ===
coa_data = {
    "Shipsure Account Description": [
        "Office Rent",
        "Staff Salaries",
        "Travel Expenses",
        "IT Software Subscriptions",
        "Maintenance & Repairs"
    ],
    "Shipsure Account Number": [
        "6101",
        "6201",
        "6301",
        "6401",
        "6501"
    ]
}
coa_df = pd.DataFrame(coa_data)
st.subheader("📘 Chart of Accounts")
st.dataframe(coa_df)

# === Upload Invoice File ===
invoice_file = st.file_uploader("📤 Upload Invoice File (CSV, Excel, or PDF)", type=["csv", "xlsx", "pdf"])
df = None
pdf_text = ""

if invoice_file:
    try:
        if invoice_file.name.endswith(".csv"):
            df = pd.read_csv(invoice_file)
        elif invoice_file.name.endswith(".xlsx"):
            df = pd.read_excel(invoice_file)
        elif invoice_file.name.endswith(".pdf"):
            with fitz.open(stream=invoice_file.read(), filetype="pdf") as doc:
                pdf_text = "\n".join(page.get_text() for page in doc)
            st.subheader("📄 Extracted PDF Text")
            st.text_area("PDF Content", pdf_text, height=300)
        if df is not None:
            st.subheader("📊 Invoice Data Preview")
            st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"Error reading invoice file: {e}")
        st.stop()

# === Local Matching Logic ===
if df is not None and st.button("🔍 Match Invoices to COA"):
    # Detect relevant column
    desc_col = None
    for col in df.columns:
        if "description" in col.lower():
            desc_col = col
            break

    if not desc_col:
        st.error("No column found with 'description' in its name.")
        st.stop()

    results = []

    for line in df[desc_col].dropna():
        best_match, score = process.extractOne(
            line,
            coa_df["Shipsure Account Description"],
            scorer=fuzz.token_sort_ratio
        )
        coa_row = coa_df[coa_df["Shipsure Account Description"] == best_match].iloc[0]
        results.append({
            "Invoice Line Description": line,
            "Suggested COA Code": coa_row["Shipsure Account Number"],
            "COA Description": best_match,
            "Confidence Score": score,
            "Notes": "Auto-matched using fuzzy logic"
        })

    match_df = pd.DataFrame(results)
    st.subheader("✅ Matched Results")
    st.dataframe(match_df)

    # Optional: download
    csv = match_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Matched Results", data=csv, file_name="invoice_matched.csv", mime="text/csv")
