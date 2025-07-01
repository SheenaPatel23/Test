import streamlit as st
import pandas as pd
import os
import requests
import fitz  # PyMuPDF

# Use secrets to load API key in Streamlit Cloud
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# App title
st.title("🧾 Invoice Coding AI")
st.markdown("Upload your **sales or purchase invoices** (CSV, Excel, or PDF) and get **coded recommendations** using AI.")

# File uploader
uploaded_file = st.file_uploader("Upload Invoice File (CSV, Excel, or PDF)", type=["csv", "xlsx", "pdf"])

df = None
pdf_text = ""

# Data preview
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
            st.subheader("📊 Data Preview")
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()
else:
    st.info("Please upload a file to begin.")

# Action button
if uploaded_file and st.button("🔍 Run AI Analysis"):
    if not GROQ_API_KEY:
        st.error("🚨 GROQ_API_KEY not found. Please set it in Streamlit Secrets.")
        st.stop()

    # Prepare prompt
    if df is not None:
        invoice_data = df.head(10).to_markdown(index=False)
    else:
        invoice_data = pdf_text[:3000]  # Limit to first 3000 characters

    prompt = f"""
You are a financial assistant. Based on the following invoice data, return a coded version of the invoice using a standard chart of accounts.
Include account codes, descriptions, and any relevant notes or recommendations.

Invoice Data:
{invoice_data}
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
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )
        result = response.json()
        ai_output = result["choices"][0]["message"]["content"]

        # Display result
        st.subheader("📥 AI-Coded Invoice Output")
        st.markdown(f"```markdown\n{ai_output}\n```")

    except Exception as e:
        st.error(f"API call failed: {e}")
