import os
import streamlit as st
import requests

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")
MODEL_NAME = "google/gemma-2-9b-it:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_llm(question: str, context: str) -> str:
    if not OPENROUTER_API_KEY:
        return "Missing OpenRouter API Key."

    prompt = (
        "You are a financial assistant specialized in FX rates. "
        "Analyze the following recent FX data:\n\n"
        f"{context}\n\n"
        "Answer this user question clearly and concisely:\n"
        f"{question}\n"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a financial assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 300
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error contacting LLM: {e}"
