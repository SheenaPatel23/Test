import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import datetime
import os
import llama_cpp

# Config
LOG_FILE = "data/query_log.csv"

# Load Chart of Accounts
def load_data(uploaded_file=None):
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv("data/chart_of_accounts.csv")
    df['combined'] = df['Shipsure Account Description'] + " - " + df['HFM Account Description']
    return df

# Embed data using sentence transformers
@st.cache_resource
def embed_data(df):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(df['combined'].tolist(), convert_to_tensor=False)
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings))
    return model, index, embeddings

# Log query
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

# Local LLM inference (llama-cpp)
def ask_llama3(prompt):
    llm = llama_cpp.Llama(model_path="models/llama-3-8b-instruct.Q4_K_M.gguf")
    response = llm(prompt=prompt, max_tokens=256, stop=["\n"])
    return response["choices"][0]["text"].strip()

# UI
st.title("📘 Chart of Accounts Assistant")
st.markdown("Upload your CoA file or use the default one. Then ask where to book an invoice!")

uploaded_file = st.file_uploader("Upload Chart of Accounts CSV", type=["csv"])
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

    top_match = df.iloc[I[0][0]]['combined']

    # Ask llama3 for final recommendation
    with st.expander("🤖 LLM Reasoning (llama3)"):
        llama_prompt = f"You are a finance assistant. Given the user query: '{query}', and these account options: {df['combined'].tolist()}, suggest the best chart of account match and why."
        llama_response = ask_llama3(llama_prompt)
        st.markdown(llama_response)

    # Feedback
    feedback = st.radio("Was this suggestion helpful?", ("Yes", "No"), horizontal=True)
    if st.button("Submit Feedback"):
        log_query(query, feedback, top_match)
        st.success("Feedback logged. Thank you!")

