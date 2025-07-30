import os
import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import datetime
import requests
import io

# === Page Config ===
st.set_page_config(page_title="Chart of Accounts Assistant", page_icon="📘", layout="wide")

# === V.Group Branding Header ===
st.markdown("""
    <div style='background-color:#052e2b;padding:1.5rem;border-radius:8px;margin-bottom:1rem'>
        <h1 style='color:#ffffff;margin:0;'>V.Group - Finance | Chart of Accounts Assistant</h1>
        <p style='color:#68da6a;margin:0;'>Helping you pick the right account code with AI assistance</p>
    </div>
""", unsafe_allow_html=True)

# === Constants ===
LOG_FILE = "data/query_log.csv"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemma-2-9b-it:free"
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
CSV_URL = "https://raw.githubusercontent.com/SheenaPatel23/Test/main/coa_assistant/data/chart_of_accounts.csv"

# === Load Chart of Accounts ===
def load_data():
    try:
        df = pd.read_csv(CSV_URL, encoding='utf-8')
        df['combined'] = df['Shipsure Account Description'] + " - " + df['HFM Account Description']
        return df
    except Exception as e:
        st.error(f"❌ Error loading Chart of Accounts: {e}")
        return pd.DataFrame()

# === Embed data ===
@st.cache_resource
def embed_data(df):
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        sentences = df['combined'].fillna("").astype(str).tolist()
        embeddings = model.encode(sentences, convert_to_tensor=False)
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings))
        return model, index, embeddings
    except Exception as e:
        st.error(f"❌ Embedding error: {e}")
        return None, None, None

# === Call OpenRouter LLM ===
def ask_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a finance assistant helping users choose chart of account codes."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }
    try:
        response = requests.post(API_URL, headers=headers, json=body)
        return response.json()["choices"][0]["message"]["content"].strip()
    except:
        return "❌ Failed to get response."

# === Log user query ===
def log_query(query, feedback, top_match):
    try:
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        log = pd.DataFrame([{
            "timestamp": timestamp, "query": query,
            "feedback": feedback, "top_match": top_match
        }])
        log.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)
    except Exception as e:
        st.warning(f"⚠️ Feedback not logged: {e}")

# === Load and Embed Data ===
df = load_data()
if df.empty:
    st.stop()
model, index, embeddings = embed_data(df)
if model is None:
    st.stop()

# === Chart of Accounts Table View with Filters and Export ===

st.subheader("📊 Chart of Accounts Explorer")
st.markdown("Filter Chart of Accounts using the dropdowns below:")

# --- Dropdown Filters ---
ship_desc = st.selectbox(
    "📌 Shipsure Account Description",
    options=["All"] + sorted(df['Shipsure Account Description'].dropna().unique().tolist()),
    index=0
)

hfm_desc = st.selectbox(
    "📌 HFM Account Description",
    options=["All"] + sorted(df['HFM Account Description'].dropna().unique().tolist()),
    index=0
)

account_number = st.selectbox(
    "📌 Shipsure Account Number",
    options=["All"] + sorted(df['Shipsure Account Number'].dropna().astype(str).unique().tolist()),
    index=0
)

# --- Apply Filters ---
filtered_df = df.copy()
if ship_desc != "All":
    filtered_df = filtered_df[filtered_df['Shipsure Account Description'] == ship_desc]
if hfm_desc != "All":
    filtered_df = filtered_df[filtered_df['HFM Account Description'] == hfm_desc]
if account_number != "All":
    filtered_df = filtered_df[filtered_df['Shipsure Account Number'].astype(str) == account_number]

st.markdown(f"🔎 Showing **{len(filtered_df)}** matching records.")

# --- Styling ---
def highlight_keywords(val):
    if isinstance(val, str):
        if 'revenue' in val.lower():
            return 'background-color: #d4edda'  # light green
        elif 'expense' in val.lower():
            return 'background-color: #f8d7da'  # light red
    return ''

styled_df = filtered_df.style \
    .applymap(highlight_keywords, subset=['HFM Account Description']) \
    .set_properties(**{'border': '1px solid #ddd', 'font-size': '14px'}) \
    .hide(axis="index")

st.dataframe(styled_df, use_container_width=True, height=350)

# --- Downloads ---
csv_data = filtered_df.to_csv(index=False).encode('utf-8')

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer, index=False, sheet_name='ChartOfAccounts')
excel_buffer.seek(0)
excel_data = excel_buffer.read()

st.download_button("⬇️ Download CSV", csv_data, file_name="chart_of_accounts.csv", mime="text/csv")
st.download_button("⬇️ Download Excel", excel_data, file_name="chart_of_accounts.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === Query Input ===
query = st.text_input("🧾 Describe the invoice or transaction you'd like to code:")
if query:
    try:
        q_embedding = model.encode([query])
        D, I = index.search(np.array(q_embedding), k=3)

        st.subheader("🔍 Top Matches")
        top_matches = []
        for i in I[0]:
            row = df.iloc[i]
            top_matches.append(row['combined'])
            with st.expander(f"{row['Shipsure Account Description']} (#{row['Shipsure Account Number']})"):
                st.markdown(f"""
                - **Shipsure Account Number:** `{row['Shipsure Account Number']}`
                - **Shipsure Account Description:** {row['Shipsure Account Description']}
                - **HFM Account Number:** `{row['HFM Account Number']}`
                - **HFM Account Description:** {row['HFM Account Description']}
                """)

        # === LLM Recommendation ===
        prompt = f"""User query: '{query}'

Here are potential Chart of Account options:
{chr(10).join(top_matches)}

Based on these, recommend the best match and explain why."""
        with st.expander("🤖 View LLM Recommendation"):
            suggestion = ask_openrouter(prompt)
            st.markdown(suggestion)

        feedback = st.radio("Was this recommendation helpful?", ("Yes", "No"), horizontal=True)
        if st.button("Submit Feedback"):
            log_query(query, feedback, top_matches[0])
            st.success("✅ Thanks! Your feedback was logged.")

    except Exception as e:
        st.error(f"❌ Failed to process query: {e}")

# === Footer Branding ===
st.markdown("""
    <hr style="margin-top: 3rem; margin-bottom: 0.5rem;" />
    <div style='text-align:center; color: gray; font-size: small'>
        Powered by V.Group · Built by Finance Data & Analytics using Streamlit and OpenRouter AI
    </div>
""", unsafe_allow_html=True)
