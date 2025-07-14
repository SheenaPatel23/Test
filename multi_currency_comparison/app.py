import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt
from utils import ask_llm

st.set_page_config(page_title="FX Trend Explorer", layout="wide")

st.title("💱 FX Trend Explorer with AI Assistant")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("🔧 Controls")

    from_currency = st.selectbox("Base Currency", ["USD", "EUR", "GBP", "JPY", "INR"], index=0)
    to_currencies = st.multiselect("Compare Against", ["EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY"], default=["EUR", "JPY"])
    
    date_range_option = st.selectbox("Select Range", ["1 Day", "1 Week", "30 Days", "60 Days", "90 Days", "1 Year", "2 Years", "5 Years"])
    
    chart_type = st.radio("Chart Library", ["Plotly", "Matplotlib"])
    normalize = st.checkbox("Normalize Values for Comparison")

# --- Date Handling ---
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

# --- Debug Info ---
st.write("🗓️ Date Range:", f"{start_date.strftime('%Y-%m-%d')} ➡ {end_date.strftime('%Y-%m-%d')}")
st.write("💱 Base Currency:", from_currency)
st.write("💱 Target Currencies:", to_currencies)

if not to_currencies:
    st.warning("Please select at least one target currency.")
    st.stop()

# --- Fetch FX Data ---
symbols_param = ",".join(to_currencies)
hist_url = (
    f"https://api.exchangerate.host/timeseries"
    f"?start_date={start_date.strftime('%Y-%m-%d')}"
    f"&end_date={end_date.strftime('%Y-%m-%d')}"
    f"&base={from_currency}&symbols={symbols_param}"
)

# Debug: Show the full API request URL
st.code(f"📡 FX API Request URL:\n{hist_url}", language="text")

hist_response = requests.get(hist_url)
hist_data = hist_response.json()

# Debug: Show raw API response
st.json(hist_data)

if hist_data.get("success") and hist_data.get("rates"):
    df = pd.DataFrame(hist_data["rates"]).T
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    if normalize:
        df = df / df.iloc[0] * 100

    st.subheader("📈 FX Rate Trends")

    if chart_type == "Plotly":
        fig = px.line(df, x=df.index, y=df.columns, labels={"value": "Rate", "index": "Date"}, title="FX Rate Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        plt.figure(figsize=(10, 4))
        for col in df.columns:
            plt.plot(df.index, df[col], label=col)
        plt.xlabel("Date")
        plt.ylabel("Rate" if not normalize else "Normalized (%)")
        plt.title("FX Rate Over Time")
        plt.legend()
        st.pyplot(plt)

    # --- Summarize FX Data for LLM ---
    fx_summary = df.tail(5).to_string()
    st.subheader("🤖 Ask AI about FX Trends")

    user_question = st.text_input("What would you like to ask?", placeholder="e.g., Which currency gained the most recently?")
    if user_question:
        with st.spinner("Asking AI..."):
            llm_response = ask_llm(user_question, fx_summary)
            st.markdown(llm_response)
else:
    st.warning("⚠️ No FX data available for this selection. Please check your currency selections and time range.")
    st.error(f"Debug Info: Success = {hist_data.get('success')}, Rates = {bool(hist_data.get('rates'))}")
