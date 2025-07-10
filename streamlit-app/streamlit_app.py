import streamlit as st
import requests

st.title("🔍 Test OpenRouter with Auto Model")

# Get prompt from user
user_input = st.text_input("Enter your message:", "What is the capital of France?")

if user_input:
    with st.spinner("Asking OpenRouter (auto model)..."):
        try:
            headers = {
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "openrouter/auto",  # ✅ Let OpenRouter choose the best available model
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            }

            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                     headers=headers,
                                     json=payload)

            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                st.success("💬 Response:")
                st.markdown(reply)
            else:
                st.error(f"❌ Status: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(f"❌ Exception occurred: {e}")
