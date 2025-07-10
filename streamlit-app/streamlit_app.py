import streamlit as st
import requests

st.title("🧠 OpenRouter Model Selector + Chat")

API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_BASE_URL = "https://openrouter.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# === Get available models ===
@st.cache_data(ttl=3600)
def get_available_models():
    try:
        res = requests.get(f"{API_BASE_URL}/models", headers=HEADERS)
        if res.status_code == 200:
            models = res.json()["data"]
            return sorted([m["id"] for m in models])
        else:
            st.error(f"⚠️ Could not fetch model list. Status: {res.status_code}")
            st.text(res.text)
            return ["openrouter/auto"]
    except Exception as e:
        st.error(f"⚠️ Error fetching models: {e}")
        return ["openrouter/auto"]

models = get_available_models()
model_choice = st.selectbox("🧩 Choose a model (or leave as auto)", models, index=models.index("openrouter/auto"))

# === Get user prompt ===
user_input = st.text_input("💬 Your question:", "What are the key trends in AI?")

if user_input:
    with st.spinner("🧠 Thinking..."):
        payload = {
            "model": model_choice,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ]
        }

        try:
            res = requests.post(f"{API_BASE_URL}/chat/completions", headers=HEADERS, json=payload)
            if res.status_code == 200:
                reply = res.json()["choices"][0]["message"]["content"]
                st.success("✅ Response:")
                st.markdown(reply)
            else:
                st.error(f"❌ Status: {res.status_code}")
                st.text(res.text)

        except Exception as e:
            st.error(f"❌ Exception occurred: {e}")
