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
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]  # Secure in Streamlit Cloud

# === Load Chart of Accounts ===
def load_data(uploaded_file=None):
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv("data/chart_of_accounts.csv")
    df['combined'] = df['Shipsure Account Description'] + " - " + df['HFM Account Description']
    return df

# === Embed data using sentence transformers ===
@st.cache_resource
def embed_data(df):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(df['combined'].tolist(), convert_to_tensor=False)
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings))
    return model, index, embeddings

# === Log query and feedback ===
def log_query(query, feedback, top_match):
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
    return response.json()["choices"][0]["message"]["content"].strip()

# === Streamlit UI ===
st.title("📘 Chart of Accounts Assistant (API-based)")
uploaded_file = st.file_uploader("Upload your Chart of Accounts CSV", type=["csv"])
df = load_data(uploaded_file)
model, index, embeddings = embed_data(df)

query = st.text_input("🧾 Describe the invoice or transaction")

if query:
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
    joined_matches = "\\n".join(top_matches)
    llama_prompt = f"""User query: '{query}'

Here are potential Chart of Account options:
{joined_matches}

Based on the options above, recommend the best matching chart of account and explain why."""
    
    with st.expander("🤖 LLM Suggestion (via OpenRouter)"):
        try:
            response = ask_openrouter(llama_prompt)
            st.markdown(response)
        except Exception as e:
            st.error(f"Failed to get LLM response: {e}")

    feedback = st.radio("Was this suggestion helpful?", ("Yes", "No"), horizontal=True)
    if st.button("Submit Feedback"):
        log_query(query, feedback, top_matches[0])
        st.success("Feedback logged. Thank you!")
