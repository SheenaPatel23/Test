import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from groq import Groq
from dotenv import load_dotenv
from operator import attrgetter
from io import BytesIO

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in Streamlit Secrets or a .env file.")
    st.stop()

st.set_page_config(layout="wide")
st.title("🤖 FP&A AI Agent - SaaS Cohort Analysis")

st.markdown("Upload an Excel file, analyze retention, churn, and revenue growth by cohort, and get FP&A insights!")

uploaded_file = st.file_uploader("📂 Upload your cohort data (Excel format)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'])

    # === Apply Filters ===
    if "Business Unit" in df.columns and "Management Type" in df.columns:
        st.subheader("🔍 Filter Options")
        selected_bu = st.multiselect("Select Business Unit(s)", sorted(df["Business Unit"].dropna().unique()), default=None)
        selected_mgmt = st.multiselect("Select Management Type(s)", sorted(df["Management Type"].dropna().unique()), default=None)

        if selected_bu:
            df = df[df["Business Unit"].isin(selected_bu)]
        if selected_mgmt:
            df = df[df["Management Type"].isin(selected_mgmt)]

    # === Build Cohort Data ===
    df['CohortMonth'] = df.groupby('Customer_ID')['Date'].transform('min').dt.to_period('M')
    df['PurchaseMonth'] = df['Date'].dt.to_period('M')
    df['CohortIndex'] = (df['PurchaseMonth'] - df['CohortMonth']).apply(attrgetter('n'))

    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # === Retention Matrix ===
    retention_counts = df.pivot_table(index='CohortMonth', columns='CohortIndex', values='Customer_ID', aggfunc='nunique')
    cohort_sizes = retention_counts.iloc[:, 0]
    retention_rate = retention_counts.divide(cohort_sizes, axis=0)

    st.subheader("🔥 Retention Heatmap")
    plt.figure(figsize=(16, 9))
    sns.heatmap(retention_rate, annot=True, fmt=".0%", cmap="YlGnBu", linewidths=0.5)
    st.pyplot(plt)

    # === Revenue Heatmap ===
    if 'Revenue' in df.columns:
        revenue_matrix = df.pivot_table(index='CohortMonth', columns='CohortIndex', values='Revenue', aggfunc='sum')
        st.subheader("💰 Cohort Revenue Heatmap")
        plt.figure(figsize=(16, 9))
        sns.heatmap(revenue_matrix, annot=True, fmt=".0f", cmap="OrRd", linewidths=0.5)
        st.pyplot(plt)

    # === Churn Report ===
    st.subheader("📉 Customer Churn Report")
    churn_df = retention_rate.copy()
    churn_df = churn_df.fillna(0)
    churn_df = churn_df.applymap(lambda x: 1 - x)
    plt.figure(figsize=(16, 9))
    sns.heatmap(churn_df, annot=True, fmt=".0%", cmap="Reds", linewidths=0.5)
    plt.title("Churn Rate by Cohort", fontsize=14)
    st.pyplot(plt)

    # === Growth Cohort Breakdown ===
    if 'Revenue' in df.columns:
        st.subheader("📈 Growth Cohort Breakdown (Avg Revenue per Customer)")
        avg_revenue_per_user = df.pivot_table(index='CohortMonth', columns='CohortIndex', values='Revenue', aggfunc='sum') / retention_counts
        avg_revenue_per_user = avg_revenue_per_user.fillna(0)
        plt.figure(figsize=(16, 9))
        sns.heatmap(avg_revenue_per_user, annot=True, fmt=".0f", cmap="BuGn", linewidths=0.5)
        plt.title("Average Revenue per Customer", fontsize=14)
        st.pyplot(plt)

    # === Export Options ===
    st.subheader("📥 Download Export Files")
    csv_buffer = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered Data (CSV)", data=csv_buffer, file_name="filtered_data.csv", mime="text/csv")

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        retention_rate.to_excel(writer, sheet_name='Retention Rate')
        churn_df.to_excel(writer, sheet_name='Churn Rate')
        if 'Revenue' in df.columns:
            revenue_matrix.to_excel(writer, sheet_name='Revenue')
            avg_revenue_per_user.to_excel(writer, sheet_name='Avg Revenue/User')
        writer.save()
    st.download_button("⬇️ Download Cohort Matrices (Excel)", data=excel_buffer.getvalue(), file_name="cohort_analysis.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # === AI Commentary Section ===
    st.subheader("🤖 Ask the FP&A AI Agent")
    user_prompt = st.text_area("Enter your question for the AI", "What insights can you derive from the retention, churn, and growth data?")

    if st.button("🚀 Generate Insights"):
        cohort_summary = f"""
Cohort Retention (Sample):
{retention_rate.head().to_string(index=True)}

Churn Rate (Sample):
{churn_df.head().to_string(index=True)}

Average Revenue per User (Sample):
{avg_revenue_per_user.head().to_string(index=True)}
"""
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an AI FP&A analyst providing insights from cohort, churn, and revenue analysis."},
                {"role": "user", "content": f"{cohort_summary}\n{user_prompt}"}
            ],
            model="llama3-8b-8192",
        )
        ai_response = response.choices[0].message.content
        st.subheader("💡 AI-Generated Insights")
        st.markdown(ai_response)
