import os
import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF

# === Read API key from Streamlit Secrets ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === App title ===
st.title("🧾 Invoice Coding AI with COA")
st.markdown("Upload your **invoice (CSV, Excel, PDF)** and your **Chart of Accounts (Excel)** to get **AI-based coding recommendations** and ask questions.")

# === File Uploaders ===
invoice_file = st.file_uploader("Upload Invoice File (CSV, Excel, or PDF)", type=["csv", "xlsx", "pdf"])
coa_file = st.file_uploader("Upload Chart of Accounts File (Excel)", type=["xlsx"])

df = None
pdf_text = ""
coa_df = None

# === Load Invoice Data ===
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
            st.dataframe(df)
    except Exception as e:
        st.error(f"Error reading invoice file: {e}")
        st.stop()

# === Load Chart of Accounts ===
if coa_file:
    try:
        coa_df = pd.read_excel(coa_file)
        st.subheader("📘 Chart of Accounts Preview")
        st.dataframe(coa_df)
    except Exception as e:
        st.error(f"Error reading COA file: {e}")
        st.stop()

# === Run AI Analysis Button ===
if (df is not None or pdf_text) and coa_df is not None and st.button("🔍 Generate AI Coding Recommendation"):
    # Prepare AI prompt
    invoice_data = df.head(10).to_markdown(index=False) if df is not None else pdf_text[:3000]
    coa_sample = coa_df.head(10).to_markdown(index=False)

    prompt = f"""
You are a financial assistant. Based on the following invoice data, recommend appropriate Chart of Account (COA) codes.

Provide your answer as a table that includes:
- Invoice Line Description
- Recommended Account Code
- COA Description
- Notes

Use the Chart of Accounts as your reference.

Invoice Data:
{invoice_data}

Chart of Accounts:
{coa_sample}
"""

    # === Call Groq API ===
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )
        result = response.json()
        ai_output = result["choices"][0]["message"]["content"]

        # === Display Result ===
        st.subheader("📥 AI-Coded Invoice Output")
        st.markdown(f"```markdown\n{ai_output}\n```")

    except Exception as e:
        st.error(f"API call failed: {e}")

# === Optional Q&A Section ===
if (df is not None or pdf_text) and coa_df is not None:
    st.subheader("🤖 Ask a Question About the Invoice or COA")
    user_question = st.text_area("Ask something like: 'Which expenses fall under admin costs?'")

    if st.button("💬 Ask AI"):
        invoice_context = df.head(10).to_markdown(index=False) if df is not None else pdf_text[:3000]
        coa_context = coa_df.head(10).to_markdown(index=False)

        q_prompt = f"""
You are a financial assistant. Help answer this question based on the data provided.

Invoice Data:
{invoice_context}

Chart of Accounts:
{coa_context}

User Question:
{user_question}
"""

        try:
            q_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-70b-8192",
                    "messages": [{"role": "user", "content": q_prompt}],
                    "temperature": 0.3
                }
            )
            q_result = q_response.json()
            answer = q_result["choices"][0]["message"]["content"]
            st.markdown(f"```markdown\n{answer}\n```")

        except Exception as e:
            st.error(f"Q&A failed: {e}")
