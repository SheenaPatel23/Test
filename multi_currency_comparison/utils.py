import streamlit as st
import requests

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")
MODEL_NAME = "google/gemma-2-9b-it:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_llm(question: str, context: str) -> str:
    if not OPENROUTER_API_KEY:
        return "❌ Missing OpenRouter API Key."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": "You are a helpful financial assistant that analyzes FX rate data."},
        {"role": "user", "content": f"Recent FX data:\n{context}\n\nQuestion:\n{question}"}
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 300
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"
