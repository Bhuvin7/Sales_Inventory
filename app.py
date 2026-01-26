import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Smart Inventory & Demand Forecasting",
    page_icon="📦",
    layout="wide"
)

# -------------------- STYLING --------------------
st.markdown("""
<style>
body { background-color: #EAF6FF; }
.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.08);
    text-align: center;
}
.alert-box {
    background-color: #FFE6E6;
    padding: 15px;
    border-radius: 12px;
    border-left: 6px solid red;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.title("📊 Smart Inventory & Demand Forecasting Dashboard")
st.caption("Upload sales data → analyze trends → forecast demand → optimize inventory")

# -------------------- FILE UPLOAD --------------------
uploaded_file = st.file_uploader("📂 Upload your sales dataset (CSV)", type=["csv"])

if uploaded_file is None:
    st.info("👆 Upload a dataset to begin analysis")
    st.stop()

# Load data
df = pd.read_csv(uploaded_file)

# -------------------- COLUMN MAPPING --------------------
st.sidebar.header("🧩 Column Mapping")

date_col = st.sidebar.selectbox("Select Date Column", df.columns)
product_col = st.sidebar.selectbox("Select Product Column", df.columns)
demand_col = st.sidebar.selectbox("Select Demand / Units Sold Column", df.columns)

inventory_col = st.sidebar.selectbox(
    "Select Inventory Column (optional)",
    ["None"] + list(df.columns)
)

# -------------------- DATA PREP (THE FIX) --------------------
# 1. Force conversion, turning errors into NaT (Not a Time)
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# 2. Check for invalid data
invalid_count = df[date_col].isna().sum()
if invalid_count > 0:
    st.sidebar.warning(f"⚠️ Skipped {invalid_count} rows with invalid dates.")
    # Drop rows where dates couldn't be parsed
    df = df.dropna(subset=[date_col])

if df.empty:
    st.error("❌ No valid date data found in the selected column.")
    st.stop()

# 3. Feature engineering
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# -------------------- FILTERS --------------------
st.sidebar.header("🔎 Filters")

selected_product = st.sidebar.selectbox(
    "Select Product",
    ["All"] + sorted(df[product_col].astype(str).unique().tolist())
)

time_view = st.sidebar.radio("Time View", ["Monthly", "Yearly"])

if selected_product != "All":
    filtered_df = df[df[product_col].astype(str) == selected_product]
else:
    filtered_df = df.copy()

# -------------------- AGGREGATION --------------------
if time_view == "Monthly":
    trend_df = filtered_df.groupby("Month")[demand_col].sum().reset_index()
    x_col = "Month"
else:
    trend_df = filtered_df.groupby("Year")[demand_col].sum().reset_index()
    x_col = "Year"

# -------------------- KPI METRICS --------------------
col1, col2, col3 = st.columns(3)

with col1:
    total_demand = filtered_df[demand_col].sum()
    st.markdown(
        f"<div class='metric-card'><h3>Total Demand</h3><h2>{int(total_demand):,}</h2></div>",
        unsafe_allow_html=True
    )

with col2:
    avg_demand = filtered_df[demand_col].mean()
    st.markdown(
        f"<div class='metric-card'><h3>Average Demand</h3><h2>{int(avg_demand) if not pd.isna(avg_demand) else 0:,}</h2></div>",
        unsafe_allow_html=True
    )

with col3:
    unique_products = filtered_df[product_col].nunique()
    st.markdown(
        f"<div class='metric-card'><h3>Products Tracked</h3><h2>{unique_products}</h2></div>",
        unsafe_allow_html=True
    )

# -------------------- TREND CHART --------------------
st.subheader("📈 Demand Trend")

if not trend_df.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(trend_df[x_col].astype(str), trend_df[demand_col], marker="o", color="#007BFF")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Demand")
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.warning("Not enough data to display trend.")

# -------------------- PER-PRODUCT FORECAST --------------------
st.subheader("🔮 Per-Product Demand Forecast")

forecast_horizon = st.slider("Forecast Periods (Months)", 1, 12, 3)
forecast_results = []

# Group by product to calculate growth
for product, group in df.groupby(product_col):
    series = group.sort_values(date_col).groupby("Month")[demand_col].sum()

    if len(series) < 2:
        continue

    # Calculate average growth, handling infinite jumps from 0 to X
    growth_rates = series.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    avg_growth = growth_rates.mean() if not growth_rates.empty else 0
    
    last_value = series.iloc[-1]
    # Simple compounding forecast
    forecast_value = last_value * (1 + avg_growth) ** forecast_horizon

    forecast_results.append({
        "Product": product,
        "Last Month Demand": int(last_value),
        "Avg Monthly Growth": f"{avg_growth:.1%}",
        "Predicted Demand": int(max(0, forecast_value))
    })

forecast_df = pd.DataFrame(forecast_results)

if not forecast_df.empty:
    st.dataframe(forecast_df, use_container_width=True)
else:
    st.write("Insufficient historical data to generate forecasts.")

# -------------------- INVENTORY SHORTAGE ALERTS --------------------
st.subheader("🚨 Inventory Shortage Alerts")

if inventory_col != "None" and not forecast_df.empty:
    # Get the most recent inventory level for each product
    latest_inventory = (
        df.sort_values(date_col)
        .groupby(product_col)
        .tail(1)[[product_col, inventory_col]]
    )

    alert_df = forecast_df.merge(
        latest_inventory,
        left_on="Product",
        right_on=product_col,
        how="left"
    )

    alert_df["Shortage"] = alert_df[inventory_col] < alert_df["Predicted Demand"]
    shortages = alert_df[alert_df["Shortage"] == True]

    if len(shortages) > 0:
        st.markdown("<div class='alert-box'><h4>⚠️ Inventory Shortage Detected</h4></div>", unsafe_allow_html=True)
        st.dataframe(
            shortages[["Product", "Predicted Demand", inventory_col]],
            use_container_width=True
        )
    else:
        st.success("✅ No inventory shortages detected")
else:
    st.info("ℹ️ Inventory column not selected or no forecast available.")

# -------------------- DOWNLOAD --------------------
if not forecast_df.empty:
    st.subheader("⬇️ Download Forecast Results")
    csv = forecast_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Forecast CSV",
        data=csv,
        file_name="demand_forecast_results.csv",
        mime="text/csv"
    )
