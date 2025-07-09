import os
import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import datetime
import requests

# === Config ===
LOG_FILE = "data/query_log.csv"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-7b-instruct"
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]  # Stored securely in Streamlit secrets

# === Load Chart of Accounts ===
def load_data(uploaded_file=None):
    try:
        if uploaded_file:
            st.info("📂 Uploaded file detected. Reading now...")
            df = pd.read_csv(uploaded_file)
        else:
            default_path = "data/chart_of_accounts.csv"
            st.info(f"📁 No upload provided. Using default: `{default_path}`")
            if os.path.exists(default_path):
                df = pd.read_csv(default_path)
            else:
                st.warning("⚠️ Default Chart of Accounts file not found. Please upload a CSV.")
                return pd.DataFrame()

        required_cols = ['Shipsure Account Description', 'HFM Account Description']
        if not all(col in df.columns for col in required_cols):
            st.error(f"❌ CSV must contain columns: {required_cols}")
            return pd.DataFrame()

        df['combined'] = df['Shipsure Account Description'] + " - " + df['HFM Account Description']
        st.success("✅ Chart of Accounts loaded successfully.")
        return df

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return pd.DataFrame()

# === Embed data ===
@st.cache_resource
def embed_data(df):
    if df.empty or 'combined' not in df.columns:
        st.warning("⚠️ No valid data to embed.")
        return None, None, None

    try:
        st.info("📌 Embedding account descriptions...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(df['combined'].tolist(), convert_to_tensor=False)
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings))
        st.success("✅ Embedding complete.")
        return model, index, embeddings
    except Exception as e:
        st.error(f"❌ Embedding error: {e}")
        return None, None, None

# === Log query and feedback ===
def log_query(query, feedback, top_match):
    try:
        timestamp = datetime.datetime.now().isoformat()
        os.makedirs("data", exist_ok=True)
        log_df = pd.DataFrame([{
            "timestamp": timestamp,
            "query": query,
            "feedback": feedback,
            "top_match": top_match
        }])
        if os.path.exists(LOG_FILE):
            log_df.to_csv(LOG_FILE, mode='a', header=False, index=False)
        else:
            log_df.to_csv(LOG_FILE, index=False)
    except Exception as e:
        st.error(f"❌ Failed to log feedback: {e}")

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
    response = requests.post(API_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# === UI ===
st.title("📘 Chart of Accounts Assistant (API-based)")
uploaded_file = st.file_uploader("Upload your Chart of Accounts CSV", type=["csv"])
df = load_data(uploaded_file)

if df.empty:
    st.stop()

model, index, embeddings = embed_data(df)
if model is None or index is None:
    st.stop()

query = st.text_input("🧾 Describe the invoice or transaction")

if query:
    try:
        q_embedding = model.encode([query])
        D, I = index.search(np.array(q_embedding), k=3)

        st.subheader("🔍 Top Matches:")
        for i in I[0]:
            row = df.iloc[i]
            with st.expander(f"{row['Shipsure Account Description']} (#{row['Shipsure Account Number']})"):
                st.markdown(f"""
                - **Shipsure Account Description:** {row['Shipsure Account Description']}
                - **Shipsure Account Number:** `{row['Shipsure Account Number']}`
                - **HFM Description:** {row['HFM Account Description']}
                - **HFM Number:** `{row['HFM Account Number']}`
                """)

        top_matches = [df.iloc[i]['combined'] for i in I[0]]
        joined_matches = "\n".join(top_matches)
        llama_prompt = f"""User query: '{query}'

Here are potential Chart of Account options:
{joined_matches}

Based on the options above, recommend the best matching chart of account and explain why."""

        with st.expander("🤖 LLM Suggestion (via OpenRouter)"):
            try:
                response = ask_openrouter(llama_prompt)
                st.markdown(response)
            except Exception as e:
                st.error(f"❌ Failed to get LLM response: {e}")

        feedback = st.radio("Was this suggestion helpful?", ("Yes", "No"), horizontal=True)
        if st.button("Submit Feedback"):
            log_query(query, feedback, top_matches[0])
            st.success("✅ Feedback logged. Thank you!")

    except Exception as e:
        st.error(f"❌ Error during query processing: {e}")
