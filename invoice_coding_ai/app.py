import streamlit as st
import pandas as pd
import os
import requests
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.title("🧾 Invoice Coding AI")
st.markdown("Upload an **invoice** and your **Chart of Accounts**, and receive AI-generated coding suggestions.")

# File uploaders
invoice_file = st.file_uploader("Upload Invoice File (CSV, Excel, or PDF)", type=["csv", "xlsx", "pdf"])
coa_file = st.file_uploader("Upload Chart of Accounts (Excel)", type=["xlsx"])

invoice_df = None
pdf_text = ""
coa_df = None

# Process invoice
if invoice_file:
    try:
        if invoice_file.name.endswith(".csv"):
            invoice_df = pd.read_csv(invoice_file)
        elif invoice_file.name.endswith(".xlsx"):
            invoice_df = pd.read_excel(invoice_file)
        elif invoice_file.name.endswith(".pdf"):
            with fitz.open(stream=invoice_file.read(), filetype="pdf") as doc:
                pdf_text = "\n".join(page.get_text() for page in doc)
            st.subheader("📄 Extracted PDF Text")
            st.text_area("PDF Content", pdf_text, height=300)
        if invoice_df is not None:
            st.subheader("📊 Invoice Data Preview")
            st.dataframe(invoice_df)
    except Exception as e:
        st.error(f"Error reading invoice file: {e}")
        st.stop()

# Process Chart of Accounts
if coa_file:
    try:
        coa_df = pd.read_excel(coa_file)
        st.subheader("📘 Chart of Accounts Preview")
        st.dataframe(coa_df.head(10))
    except Exception as e:
        st.error(f"Error reading Chart of Accounts: {e}")
        st.stop()

# AI button
if invoice_file and coa_file and st.button("🚀 Run AI Coding"):
    if not GROQ_API_KEY:
        st.error("🚨 GROQ_API_KEY is missing. Please set it in the .env file or Streamlit secrets.")
        st.stop()

    # Build prompt
    if invoice_df is not None:
        invoice_sample = invoice_df.head(10).to_markdown(index=False)
    else:
        invoice_sample = pdf_text[:3000]

    coa_sample = coa_df.head(10).to_markdown(index=False)

    prompt = f"""
You are a finance assistant. Based on the following invoice and chart of accounts data, suggest a coded invoice breakdown.
Include appropriate account numbers, descriptions, and any notes.

📄 **Invoice Data**:
{invoice_sample}

📘 **Chart of Accounts**:
{coa_sample}
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )
        result = response.json()
        ai_output = result["choices"][0]["message"]["content"]

        # Show AI response
        st.subheader("📥 AI-Coded Invoice Output")
        st.markdown(f"```markdown\n{ai_output}\n```")

    except Exception as e:
        st.error(f"API call failed: {e}")
