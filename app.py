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
body {
    background-color: #EAF6FF;
}
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

# -------------------- DATA PREP --------------------
df[date_col] = pd.to_datetime(df[date_col])
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
    st.markdown(
        f"<div class='metric-card'><h3>Total Demand</h3><h2>{int(filtered_df[demand_col].sum()):,}</h2></div>",
        unsafe_allow_html=True
    )

with col2:
    avg_demand = filtered_df[demand_col].mean()
    st.markdown(
        f"<div class='metric-card'><h3>Average Demand</h3><h2>{int(avg_demand):,}</h2></div>",
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

fig, ax = plt.subplots()
ax.plot(trend_df[x_col], trend_df[demand_col], marker="o")
ax.set_xlabel(x_col)
ax.set_ylabel("Demand")
ax.grid(True)
plt.xticks(rotation=45)

st.pyplot(fig)

# -------------------- PER-PRODUCT FORECAST (SIMPLE) --------------------
st.subheader("🔮 Per-Product Demand Forecast")

forecast_horizon = st.slider("Forecast Periods (Months)", 1, 12, 3)

forecast_results = []

for product, group in df.groupby(product_col):
    series = group.sort_values(date_col)[demand_col]

    if len(series) < 2:
        continue

    avg_growth = series.pct_change().mean()
    last_value = series.iloc[-1]

    forecast_value = last_value * (1 + avg_growth) ** forecast_horizon

    forecast_results.append({
        "Product": product,
        "Last Actual Demand": int(last_value),
        "Predicted Demand": int(forecast_value)
    })

forecast_df = pd.DataFrame(forecast_results)

st.dataframe(forecast_df, use_container_width=True)

# -------------------- INVENTORY SHORTAGE ALERTS --------------------
st.subheader("🚨 Inventory Shortage Alerts")

if inventory_col != "None":
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
    st.info("ℹ️ Inventory column not selected — shortage alerts skipped")

# -------------------- DOWNLOAD --------------------
st.subheader("⬇️ Download Forecast Results")

csv = forecast_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Forecast CSV",
    data=csv,
    file_name="demand_forecast_results.csv",
    mime="text/csv"
)
