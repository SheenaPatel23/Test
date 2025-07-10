import streamlit as st
import requests

st.title("🔍 Test OpenRouter with Mistral")

# Get prompt from user
user_input = st.text_input("Enter your message:", "What is the capital of France?")

if user_input:
    with st.spinner("Asking Mistral via OpenRouter..."):
        try:
            headers = {
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gryphe/mythomist-7b",
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
                st.success("💬 Mistral says:")
                st.markdown(reply)
            else:
                st.error(f"❌ Status: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(f"❌ Exception occurred: {e}")
