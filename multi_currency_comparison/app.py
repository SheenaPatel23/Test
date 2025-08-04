import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from utils import ask_llm

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="FX Trend Explorer", layout="wide")

st.markdown(
    "<h1 style='color:#0a3d62;'>🌐 V.Group FX Trend Explorer</h1>",
    unsafe_allow_html=True
)

# ---------------------- SIDEBAR ----------------------
with st.sidebar:
    st.image("https://vgrouplimited.com/wp-content/uploads/2022/06/vgroup-logo.svg", use_container_width=True)
    st.header("🔧 Controls")

    from_currency = st.selectbox("Base Currency", ["USD", "EUR", "GBP", "JPY", "INR"], index=0)
    to_currencies = st.multiselect("Compare Against", ["EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY", "SGD", "PLN", "AED", "PHP"], default=["EUR", "GBP"])
    date_range_option = st.selectbox("Select Range", ["1 Week", "30 Days", "60 Days", "90 Days", "1 Year", "2 Years", "5 Years"])
    chart_type = st.radio("Chart Type", ["Plotly", "Matplotlib"])
    normalize = st.checkbox("Normalise Rates for Comparison")

# ---------------------- DATE SETUP ----------------------
days_lookup = {
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

if not to_currencies:
    st.warning("Please select at least one target currency.")
    st.stop()

# ---------------------- FETCH DATA ----------------------
@st.cache_data(show_spinner=False)
def fetch_fx_timeseries(from_cur, to_cur, start, end):
    symbol = f"{from_cur}{to_cur}=X"
    data = yf.download(symbol, start=start, end=end)

    if data.empty or "Close" not in data.columns:
        raise ValueError(f"No valid data for symbol {symbol}")

    close_data = data["Close"]

    # Squeeze to ensure it's 1D Series (sometimes yf returns DataFrame with one column)
    if hasattr(close_data, "ndim") and close_data.ndim > 1:
        close_data = close_data.squeeze()

    if not isinstance(close_data, pd.Series):
        raise ValueError(f"Close price data for {symbol} is not 1D")

    close_data.name = to_cur
    return close_data

fx_data = {}
for to_cur in to_currencies:
    try:
        fx_data[to_cur] = fetch_fx_timeseries(from_currency, to_cur, start_date, end_date)
    except Exception as e:
        st.error(f"Error fetching data for {to_cur}: {e}")

if not fx_data:
    st.warning("No FX data available for the selected currencies.")
    st.stop()

df = pd.concat(fx_data.values(), axis=1)
df.columns = fx_data.keys()
df.index.name = "Date"
df.dropna(inplace=True)

if normalize:
    df = df / df.iloc[0] * 100

# ---------------------- PLOT SECTION ----------------------
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

# ---------------------- AI ASSISTANT ----------------------
st.subheader("🤖 Ask AI about FX Trends")
fx_summary = df.tail(5).to_string()
user_question = st.text_input("What would you like to ask?", placeholder="e.g., Which currency gained the most recently?")
if user_question:
    with st.spinner("Asking AI..."):
        llm_response = ask_llm(user_question, fx_summary)
        st.markdown(llm_response)
