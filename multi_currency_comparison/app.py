import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import plotly.express as px
import matplotlib.pyplot as plt
from utils import ask_llm

# ---- Config ----
st.set_page_config(page_title="FX Trend Explorer", layout="wide")

# ---- Styling ----
st.markdown("""
    <style>
    body {
        background-color: #f9f9f9;
        color: #001a33;
    }
    .stApp {
        font-family: "Segoe UI", sans-serif;
    }
    h1, h2 {
        color: #002b5c;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Title ----
st.title("💱 FX Trend Explorer (Powered by AI)")

# ---- Sidebar ----
with st.sidebar:
    st.image("https://vgrouplimited.com/wp-content/uploads/2022/11/vgroup-logo.svg", width=180)
    st.markdown("## 🔧 Controls")

    from_currency = st.selectbox("Base Currency", ["USD", "EUR", "GBP", "JPY", "INR"], index=0)
    to_currencies = st.multiselect(
        "Compare Against", 
        ["EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY"],
        default=["EUR", "JPY"]
    )

    date_range_option = st.selectbox("Time Range", ["1 Day", "1 Week", "30 Days", "60 Days", "90 Days", "1 Year", "2 Years", "5 Years"])
    chart_type = st.radio("Chart Type", ["Plotly", "Matplotlib"])
    normalize = st.checkbox("Normalize for Comparison", value=True)

# ---- Dates ----
days_lookup = {
    "1 Day": 1,
    "1 Week": 7,
    "30 Days": 30,
    "60 Days": 60,
    "90 Days": 90,
    "1 Year": 365,
    "2 Years": 730,
    "5 Years": 1825
}
end_date = datetime.today()
start_date = end_date - timedelta(days=days_lookup[date_range_option])

# ---- Data Fetch ----
if not to_currencies:
    st.warning("Select at least one currency.")
    st.stop()

fx_data = {}
for target_currency in to_currencies:
    pair = f"{from_currency}{target_currency}=X"
    try:
        data = yf.download(pair, start=start_date, end=end_date)
        if not data.empty:
            fx_data[target_currency] = data["Close"]
    except Exception:
        continue

if not fx_data:
    st.error("⚠️ No FX data available for this selection.")
    st.stop()

df = pd.DataFrame(fx_data)
df.index = pd.to_datetime(df.index)
df.sort_index(inplace=True)

if normalize:
    df = df / df.iloc[0] * 100

# ---- Charts ----
st.subheader("📈 FX Rate Trends")

if chart_type == "Plotly":
    fig = px.line(df, x=df.index, y=df.columns, labels={"value": "Rate", "index": "Date"}, title="")
    fig.update_layout(template="simple_white")
    st.plotly_chart(fig, use_container_width=True)
else:
    plt.figure(figsize=(10, 4))
    for col in df.columns:
        plt.plot(df.index, df[col], label=col)
    plt.xlabel("Date")
    plt.ylabel("Rate (%)" if normalize else "FX Rate")
    plt.title("FX Rate Trends")
    plt.legend()
    st.pyplot(plt)

# ---- AI Assistant ----
st.subheader("🤖 Ask FX Assistant")
user_question = st.text_input("Ask a question (e.g., Which currency gained the most?)")

if user_question:
    with st.spinner("Thinking..."):
        fx_summary = df.tail(5).to_string()
        response = ask_llm(user_question, fx_summary)
        st.markdown(response)
