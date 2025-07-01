import streamlit as st
import pandas as pd
import os
import requests
import fitz  # PyMuPDF

st.title("🧾 Invoice Coding AI with Chart of Accounts")
st.markdown("""
Upload your **invoices** (CSV, Excel, or PDF) and your **Chart of Accounts** file (Excel).
The AI will return coded recommendations based on your company's nominal accounts.
""")

# Get API key from Streamlit secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("GROQ_API_KEY not found in Streamlit Secrets. Please add it under Secrets & Variables.")
    st.stop()

# Upload Chart of Accounts
coa_file = st.file_uploader("Upload Chart of Accounts Excel file", type=["xlsx"])
coa_df = None
if coa_file:
    try:
        coa_df = pd.read_excel(coa_file, engine="openpyxl")
        st.subheader("📁 Chart of Accounts Preview")
        st.dataframe(coa_df.head(10))
    except Exception as e:
        st.error(f"Error reading Chart of Accounts file: {e}")
        st.stop()

# Upload invoice file
uploaded_file = st.file_uploader("Upload Invoice File (CSV, Excel, or PDF)", type=["csv", "xlsx", "pdf"])

df = None
pdf_text = ""

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        elif uploaded_file.name.endswith(".pdf"):
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                pdf_text = "\n".join(page.get_text() for page in doc)
            st.subheader("📄 Extracted PDF Text")
            st.text_area("PDF Content", pdf_text, height=300)
        if df is not None:
            st.subheader("📊 Invoice Data Preview")
            st.dataframe(df)
    except Exception as e:
        st.error(f"Error reading invoice file: {e}")
        st.stop()
else:
    st.info("Please upload an invoice file to begin.")

if st.button("🔍 Run AI Analysis"):
    if not uploaded_file:
        st.error("Please upload an invoice file to analyze.")
        st.stop()

    if coa_df is None:
        st.error("Please upload a valid Chart of Accounts Excel file.")
        st.stop()

    # Prepare invoice data snippet
    if df is not None:
        try:
            invoice_data = df.head(10).to_markdown(index=False)
        except ImportError:
            invoice_data = df.head(10).to_string(index=False)
    else:
        invoice_data = pdf_text[:3000]  # Limit to first 3000 chars if PDF

    # Prepare COA snippet for prompt context (first 10 rows)
    try:
        coa_sample = coa_df.head(10).to_markdown(index=False)
    except ImportError:
        coa_sample = coa_df.head(10).to_string(index=False)

    prompt = f"""
You are a financial assistant AI.

Given the following Chart of Accounts used by the company:

{coa_sample}

And the invoice data below:

{invoice_data}

Please provide a coded version of the invoice using the Chart of Accounts.
Include Shipsure Account Number, Description, and any relevant notes or recommendations.
"""

    # Call Groq API
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )

        if response.status_code != 200:
            st.error(f"API call failed with status {response.status_code}: {response.text}")
            st.stop()

        result = response.json()
        ai_output = result.get("choices", [{}])[0].get("message", {}).get("content", None)

        if not ai_output:
            st.error("No valid response content returned from API.")
            st.stop()

        st.subheader("📥 AI-Coded Invoice Output")
        st.markdown(f"```markdown\n{ai_output}\n```")

    except Exception as e:
        st.error(f"API call failed: {e}")
