import streamlit as st
import requests

st.title("🔌 Groq API Test")

# Load the API key from Streamlit secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception as e:
    st.error("❌ GROQ_API_KEY not found in secrets!")
    st.stop()

# Create a simple test prompt
prompt = "What is 5 + 7?"

# Call Groq API
if st.button("▶️ Test Groq API"):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )

        result = response.json()
        st.write("🧠 Raw API response:", result)

        if "choices" in result:
            st.success("✅ Model response:")
            st.write(result["choices"][0]["message"]["content"])
        else:
            st.error("❌ Unexpected response format (missing 'choices')")
            st.json(result)

    except Exception as e:
        st.error(f"❌ API call failed: {e}")
