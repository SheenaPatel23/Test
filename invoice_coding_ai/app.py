import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF
import io

# === GitHub-hosted Chart of Accounts ===
COA_URL = "https://raw.githubusercontent.com/SheenaPatel23/Test/main/invoice_coding_ai/Chart_of_Accounts.xlsx"

# === Read API key from Streamlit secrets ===
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === App title ===
st.title("🧾 Invoice Coding AI with COA (Preloaded from GitHub)")
st.markdown("Upload your **invoice (CSV, Excel, PDF)** to get **AI-based coding recommendations** using the Chart of Accounts from GitHub.")

# === Load Chart of Accounts from GitHub ===
try:
    coa_df = pd.read_excel(COA_URL)
    st.subheader("📘 Preloaded Chart of Accounts")
    st.dataframe(coa_df.head(10))
except Exception as e:
    st.error(f"Failed to load Chart of Accounts from GitHub: {e}")
    st.stop()

# === Upload Invoice File ===
invoice_file = st.file_uploader("Upload Invoice File (CSV, Excel, or PDF)", type=["csv", "xlsx", "pdf"])
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

# === Run AI Coding Recommendation ===
ai_output = ""

if (df is not None or pdf_text) and st.button("🔍 Generate AI Coding Recommendation"):
    invoice_data = df.head(10).to_markdown(index=False) if df is not None else pdf_text[:3000]
    coa_sample = coa_df[['Shipsure Account Description', 'Shipsure Account Number']].dropna().head(20).to_markdown(index=False)

    prompt = f"""
You are a finance assistant. Based on the following invoice data and the Chart of Accounts (COA), recommend the most appropriate account code for each invoice line.

Match using similarity between the **Invoice Line Description** and **Shipsure Account Description**.

Return a table with:
- Invoice Line Description
- Suggested COA Code
- Shipsure Account Description
- Confidence Score (1-10)
- Notes (reasoning or assumptions)

Invoice Data:
{invoice_data}

Chart of Accounts:
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
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )
        result = response.json()

        if response.status_code != 200:
            st.error(f"Groq API Error {response.status_code}: {result}")
        elif "choices" in result:
            ai_output = result["choices"][0]["message"]["content"]
            st.subheader("📥 AI-Coded Invoice Output")
            st.markdown(f"```markdown\n{ai_output}\n```")
        else:
            st.error("Unexpected response format from Groq API.")
            st.json(result)

    except Exception as e:
        st.error(f"API call failed: {e}")

# === Download Output ===
if ai_output:
    output_bytes = io.BytesIO()
    output_bytes.write(ai_output.encode("utf-8"))
    output_bytes.seek(0)
    st.download_button(
        label="⬇️ Download Output as .txt",
        data=output_bytes,
        file_name="invoice_coding_output.txt",
        mime="text/plain"
    )

# === Optional Q&A Section ===
if (df is not None or pdf_text):
    st.subheader("🤖 Ask a Question About the Invoice or COA")
    user_question = st.text_area("Ask something like: 'Which expenses fall under admin costs?'")

    if st.button("💬 Ask AI"):
        invoice_context = df.head(10).to_markdown(index=False) if df is not None else pdf_text[:3000]
        coa_context = coa_df[['Shipsure Account Description', 'Shipsure Account Number']].dropna().head(20).to_markdown(index=False)

        q_prompt = f"""
You are a finance assistant. Help answer this question based on the data provided.

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

            if q_response.status_code != 200:
                st.error(f"Groq API Error {q_response.status_code}: {q_result}")
            elif "choices" in q_result:
                answer = q_result["choices"][0]["message"]["content"]
                st.markdown(f"```markdown\n{answer}\n```")
            else:
                st.error("Unexpected response format from Groq API.")
                st.json(q_result)

        except Exception as e:
            st.error(f"Q&A failed: {e}")
