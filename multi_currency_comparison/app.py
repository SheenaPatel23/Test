import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from utils import ask_llm
from datetime import datetime, timedelta

st.set_page_config(page_title="FX Trend Explorer", layout="centered")
st.title("💱 FX Converter, Multi-Currency Trends + AI Assistant")

# -- Inputs
currency_list = ["USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "SGD"]
from_currency = st.selectbox("From Currency", currency_list, index=0)
to_currencies = st.multiselect("To Currencies", currency_list, default=["EUR", "JPY", "INR"])
amount = st.number_input("Amount", value=1.0)

# -- Duration Selector
st.subheader("📆 Select Date Range")
duration_options = {
    "1 Day": 1,
    "1 Week": 7,
    "30 Days": 30,
    "60 Days": 60,
    "90 Days": 90,
    "1 Year": 365,
    "2 Years": 730,
    "5 Years": 1825,
}
selected_duration_label = st.selectbox("View trends for", list(duration_options.keys()), index=2)
days_back = duration_options[selected_duration_label]

# -- Normalization and Library Toggles
normalize = st.checkbox("🔁 Normalize trends (start at 100)", value=False)
use_matplotlib = st.checkbox("📊 Use Matplotlib instead of Plotly", value=False)

# -- Conversion (only if one to_currency)
if len(to_currencies) == 1:
    convert_url = f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currencies[0]}&amount={amount}"
    convert_data = requests.get(convert_url).json()
    if convert_data and "result" in convert_data:
        st.metric(label=f"{amount} {from_currency} in {to_currencies[0]}", value=round(convert_data["result"], 4))

# -- Date range
end_date = datetime.today()
start_date = end_date - timedelta(days=days_back)

# -- API call
symbols_param = ",".join(to_currencies)
hist_url = (
    f"https://api.exchangerate.host/timeseries"
    f"?start_date={start_date.strftime('%Y-%m-%d')}"
    f"&end_date={end_date.strftime('%Y-%m-%d')}"
    f"&base={from_currency}&symbols={symbols_param}"
)
hist_data = requests.get(hist_url).json()

# -- Plotting
if hist_data["success"] and hist_data["rates"]:
    rates = hist_data["rates"]
    df = pd.DataFrame(rates).T
    df.index = pd.to_datetime(df.index)
    df = df[to_currencies]

    if normalize:
        df = df.divide(df.iloc[0]) * 100

    # -- Use Plotly or Matplotlib
    if not use_matplotlib:
        fig = go.Figure()
        for curr in to_currencies:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[curr],
                mode='lines+markers',
                name=f"{from_currency} → {curr}"
            ))
        fig.update_layout(
            title=f"{from_currency} to Selected Currencies - {selected_duration_label}",
            xaxis_title="Date",
            yaxis_title="Normalized Rate (100)" if normalize else "Exchange Rate",
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots()
        for curr in to_currencies:
            ax.plot(df.index, df[curr], label=f"{from_currency} → {curr}")
        ax.set_title(f"{from_currency} to Currencies ({selected_duration_label})")
        ax.set_xlabel("Date")
        ax.set_ylabel("Normalized Rate (100)" if normalize else "Exchange Rate")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    # -- Stats & Assistant
    base_curr = to_currencies[0] if to_currencies else None
    if base_curr:
        min_val = df[base_curr].min()
        max_val = df[base_curr].max()
        avg_val = df[base_curr].mean()
        st.write(f"**Stats for {from_currency} → {base_curr} ({selected_duration_label}):**")
        st.write(f"Min: {min_val:.4f} | Max: {max_val:.4f} | Avg: {avg_val:.4f}")

        st.subheader("🤖 Ask the FX Assistant")
        user_question = st.text_input("Ask a question about FX rates or currency trends")

        if user_question:
            with st.spinner("Thinking..."):
                fx_summary = (
                    f"Base currency: {from_currency}\n"
                    f"Compared currencies: {', '.join(to_currencies)}\n"
                    f"Time range: {selected_duration_label}\n"
                    f"Normalization: {'Yes' if normalize else 'No'}\n"
                    f"Stats for {base_curr}:\n"
                    f"  - Min: {min_val:.4f}\n"
                    f"  - Max: {max_val:.4f}\n"
                    f"  - Avg: {avg_val:.4f}\n"
                )
                answer = ask_llm(user_question, fx_summary)
                st.markdown(f"**Answer:**\n\n{answer}")
else:
    st.warning("No FX data available for this selection.")
