import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px
import yfinance as yf
from utils import ask_llm

st.set_page_config(page_title="V.Group FX Trend Explorer", layout="wide")

# --- Header ---
st.markdown("""
    <style>
    .main {
        background-color: #f6f8fa;
    }
    .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #003f6b;
    }
    .stButton>button {
        background-color: #003f6b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💱 V.Group FX Trend Explorer with AI")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("🔧 Configuration")

    from_currency = st.selectbox("Base Currency", ["USD", "EUR", "GBP", "JPY", "INR"], index=0)
    to_currencies = st.multiselect("Compare Against", ["EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY"], default=["EUR", "JPY"])
    
    date_range_option = st.selectbox("Select Range", ["1 Day", "1 Week", "30 Days", "60 Days", "90 Days", "1 Year", "2 Years", "5 Years"])
    
    chart_type = st.radio("Chart Type", ["Plotly", "Matplotlib"], index=0)
    normalize = st.checkbox("Normalize Values (%)", value=True)

# --- Date Range Logic ---
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

# --- Data Fetching ---
if not to_currencies:
    st.warning("Please select at least one currency.")
    st.stop()

fx_data = {}
for target in to_currencies:
    pair = f"{from_currency}{target}=X"
    data = yf.download(pair, start=start_date, end=end_date)

    if not data.empty and "Close" in data.columns and len(data["Close"].dropna()) > 1:
        fx_data[target] = data["Close"]
    # Optional debug (disable in prod)
    # else:
    #     st.warning(f"Skipping {pair} — no data.")

if not fx_data:
    st.error("❌ No FX data found for your selection. Try a different range or currency.")
    st.stop()

df = pd.DataFrame(fx_data)
df.index.name = "Date"
df.sort_index(inplace=True)

# Normalize
if normalize:
    df = df / df.iloc[0] * 100

# --- Chart Display ---
st.subheader("📈 FX Trends")

if chart_type == "Plotly":
    fig = px.line(df, x=df.index, y=df.columns, labels={"value": "FX Rate", "Date": "Date"}, title="FX Rate Trends")
    st.plotly_chart(fig, use_container_width=True)
else:
    plt.figure(figsize=(10, 4))
    for col in df.columns:
        plt.plot(df.index, df[col], label=col)
    plt.xlabel("Date")
    plt.ylabel("Normalized FX Rate (%)" if normalize else "FX Rate")
    plt.title("FX Rate Trends")
    plt.legend()
    st.pyplot(plt)

# --- LLM Assistant ---
st.subheader("🤖 Ask the AI Assistant")

recent_summary = df.tail(5).to_string()
question = st.text_input("Ask a question about FX trends (e.g., Which currency performed best?)")

if question:
    with st.spinner("Thinking..."):
        response = ask_llm(question, recent_summary)
        st.markdown(response)
