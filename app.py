import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Inventory Demand Forecasting",
    page_icon="📦",
    layout="wide"
)

# -------------------- SKY BLUE THEME --------------------
st.markdown("""
<style>
.stApp {
    background-color: #EAF6FF;
}
h1, h2, h3 {
    color: #003366;
}
div[data-testid="metric-container"] {
    background-color: #D6ECFF;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.title("📦 Smart Inventory Demand Forecasting Dashboard")
st.markdown(
    "Upload your **historical sales dataset** to analyze **actual demand, predicted demand, and inventory decisions**."
)

# -------------------- REQUIRED COLUMNS INFO --------------------
with st.expander("📌 Dataset Requirements"):
    st.write("""
Your file should contain **at least** these columns:
- Date  
- Product ID  
- Category  
- Units Sold  
- Actual_Demand *(or Units Sold used as demand)*  
- Predicted_Demand *(optional, if model already trained)*  
- Seasonality *(optional)*  
""")

# -------------------- FILE UPLOAD --------------------
uploaded_file = st.file_uploader(
    "📂 Upload CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:
    # -------------------- READ DATA --------------------
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("✅ File uploaded successfully")

    # -------------------- DATA CLEANING --------------------
    df.columns = df.columns.str.strip()

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    if "Actual_Demand" not in df.columns:
        df["Actual_Demand"] = df["Units Sold"]

    if "Predicted_Demand" not in df.columns:
        df["Predicted_Demand"] = df["Actual_Demand"].rolling(3).mean().fillna(df["Actual_Demand"])

    # -------------------- SIDEBAR FILTERS --------------------
    st.sidebar.header("🔍 Filters")

    category = st.sidebar.selectbox(
        "Select Category",
        df["Category"].unique()
    )

    product = st.sidebar.selectbox(
        "Select Product",
        df[df["Category"] == category]["Product ID"].unique()
    )

    filtered_df = df[
        (df["Category"] == category) &
        (df["Product ID"] == product)
    ]

    # -------------------- KPI METRICS --------------------
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📈 Avg Actual Demand",
        round(filtered_df["Actual_Demand"].mean(), 2)
    )

    col2.metric(
        "🔮 Avg Predicted Demand",
        round(filtered_df["Predicted_Demand"].mean(), 2)
    )

    col3.metric(
        "📦 Total Units Sold",
        int(filtered_df["Units Sold"].sum())
    )

    st.divider()

    # -------------------- LINE CHART --------------------
    st.subheader("📊 Demand Trend Over Time")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(filtered_df["Date"], filtered_df["Actual_Demand"], label="Actual Demand", linewidth=2)
    ax.plot(filtered_df["Date"], filtered_df["Predicted_Demand"], label="Predicted Demand", linestyle="--")

    ax.set_xlabel("Date")
    ax.set_ylabel("Units")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # -------------------- BAR CHART --------------------
    st.subheader("📊 Monthly Sales Distribution")

    filtered_df["Month"] = filtered_df["Date"].dt.month
    monthly_sales = filtered_df.groupby("Month")["Units Sold"].sum()

    fig2, ax2 = plt.subplots(figsize=(10, 4))
    monthly_sales.plot(kind="bar", ax=ax2)
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Units Sold")
    ax2.grid(axis="y")

    st.pyplot(fig2)

    # -------------------- DATA TABLE --------------------
    st.subheader("📋 Product-Level Details")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("👆 Upload a dataset to begin analysis")
