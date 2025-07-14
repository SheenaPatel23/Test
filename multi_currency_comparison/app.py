import streamlit as st
import pandas as pd
import yfinance as yf
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

# --- Fetch FX Data using yfinance ---
@st.cache_data(ttl=3600)
def fetch_yf_fx_data(base, targets, start, end):
    df_all = pd.DataFrame()
    for tgt in targets:
        if tgt == base:
            continue
        # Yahoo Finance FX ticker format examples:
        # For USD to EUR: EURUSD=X (quote is EUR/USD)
        # We want base as 'from_currency' and target as 'to_currency'
        # Yahoo Finance ticker: TARGET + BASE + "=X" (so invert)
        # So if base=USD, target=EUR, ticker is EURUSD=X, which is EUR/USD, to get USD/EUR invert it

        ticker = f"{tgt}{base}=X"
        fx_data = yf.download(ticker, start=start, end=end)
        if fx_data.empty:
            st.warning(f"No data for pair {base}/{tgt} (Ticker: {ticker})")
            continue
        # Price is for tgt/base, so invert to get base/tgt rate:
        fx_data['Close'] = 1 / fx_data['Close']
        fx_data['Open'] = 1 / fx_data['Open']
        fx_data['High'] = 1 / fx_data['High']
        fx_data['Low'] = 1 / fx_data['Low']
        # Volume usually 0 for FX, ignore

        df_all[tgt] = fx_data['Close']
    df_all.index = pd.to_datetime(df_all.index)
    df_all.sort_index(inplace=True)
    return df_all

with st.spinner("Fetching FX data from Yahoo Finance..."):
    df = fetch_yf_fx_data(from_currency, to_currencies, start_date, end_date)

if df.empty:
    st.warning("⚠️ No FX data available for this selection. Please check your currency selections and time range.")
    st.stop()

if normalize:
    df = df / df.iloc[0] * 100

st.subheader("📈 FX Rate Trends")

if chart_type == "Plotly":
    fig = px.line(df, x=df.index, y=df.columns, labels={"value": "Rate", "index": "Date"}, title=f"FX Rate Over Time ({from_currency} base)")
    st.plotly_chart(fig, use_container_width=True)
else:
    plt.figure(figsize=(10, 4))
    for col in df.columns:
        plt.plot(df.index, df[col], label=col)
    plt.xlabel("Date")
    plt.ylabel("Rate" if not normalize else "Normalized (%)")
    plt.title(f"FX Rate Over Time ({from_currency} base)")
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
