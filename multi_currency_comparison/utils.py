import requests
import os

# You can also store this securely in Streamlit Community Cloud via secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Or replace with your key directly (not recommended in prod)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "google/gemma-2-9b-it:free"

def ask_llm(user_question: str, fx_summary: str) -> str:
    if not GROQ_API_KEY:
        return "⚠️ Missing GROQ_API_KEY. Please set it as an environment variable or in secrets."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "You are an AI assistant specializing in currency and FX data. "
        "Use the summary provided from the app to answer in a concise, structured, and data-aware way. "
        "Include numbers, context, and don't hallucinate. Answer in markdown bullet format if appropriate."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"FX data summary:\n{fx_summary}"},
        {"role": "user", "content": user_question}
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 512,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        return reply.strip()
    except Exception as e:
        return f"❌ Error from Groq API: {str(e)}"
