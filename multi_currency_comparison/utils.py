import os
import streamlit as st
import requests

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
MODEL_NAME = "google/gemma-2-9b-it:free"
GROQ_API_URL = f"https://api.groq.ai/v1/models/{MODEL_NAME}/predict"

def ask_llm(question: str, context: str) -> str:
    """
    Ask Groq LLM a question given some context, returning a structured answer.
    """
    if not GROQ_API_KEY:
        return "Error: Groq API key is not configured."

    prompt = (
        "You are a helpful assistant analyzing FX rate data. "
        "Given the following recent FX rate data:\n\n"
        f"{context}\n\n"
        "Answer this question with a concise and structured response:\n"
        f"{question}\n"
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.3,
            "max_new_tokens": 300,
        }
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # Groq API returns 'results' with generated text, adjust as needed
        answer = result.get("results", [{}])[0].get("text", "").strip()

        if not answer:
            return "LLM response was empty."

        return answer

    except Exception as e:
        return f"Error communicating with Groq LLM: {e}"
