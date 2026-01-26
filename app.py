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

# -------------------- DATA PREP & CLEANING --------------------
# 1. Convert Date with error handling
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df = df.dropna(subset=[date_col])

# 2. Convert Demand to numeric (FIX FOR THE SUM ERROR)
df[demand_col] = pd.to_numeric(df[demand_col], errors='coerce').fillna(0)

# 3. Create helper columns
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# -------------------- FILTERS --------------------
st.sidebar.header("🔎 Filters")
unique_prods = sorted(df[product_col].astype(str).unique().tolist())
selected_product = st.sidebar.selectbox("Select Product", ["All"] + unique_prods)
time_view = st.sidebar.radio("Time View", ["Monthly", "Yearly"])

filtered_df = df.copy()
if selected_product != "All":
    filtered_df = df[df[product_col].astype(str) == selected_product]

# -------------------- AGGREGATION (FIXED) --------------------
if time_view == "Monthly":
    # Using [[demand_col]] ensures we only aggregate the numeric column
    trend_df = filtered_df.groupby("Month")[[demand_col]].sum().reset_index()
    x_axis = "Month"
else:
    trend_df = filtered_df.groupby("Year")[[demand_col]].sum().reset_index()
    x_axis = "Year"

# -------------------- KPI METRICS --------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-card'><h3>Total Demand</h3><h2>{int(filtered_df[demand_col].sum()):,}</h2></div>", unsafe_allow_html=True)
with col2:
    avg_d = filtered_df[demand_col].mean()
    st.markdown(f"<div class='metric-card'><h3>Avg Demand</h3><h2>{int(avg_d):,}</h2></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><h3>Products</h3><h2>{filtered_df[product_col].nunique()}</h2></div>", unsafe_allow_html=True)

# -------------------- TREND CHART --------------------
st.subheader(f"📈 Demand Trend ({time_view})")
if not trend_df.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(trend_df[x_axis].astype(str), trend_df[demand_col], marker="o", color="#007BFF", linewidth=2)
    plt.xticks(rotation=45)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

# -------------------- FORECASTING --------------------
st.subheader("🔮 3-Month Demand Forecast")
forecast_results = []

for product, group in df.groupby(product_col):
    # Group by month to get a consistent time series
    monthly_series = group.sort_values(date_col).groupby("Month")[demand_col].sum()
    
    if len(monthly_series) < 2:
        continue

    # pct_change can create inf/nan if demand was 0; we clean those
    growth = monthly_series.pct_change().replace([np.inf, -np.inf], np.nan).mean()
    if pd.isna(growth): growth = 0
    
    last_val = monthly_series.iloc[-1]
    # Simple projection for 3 months
    pred = last_val * (1 + growth) ** 3
    
    forecast_results.append({
        "Product": product,
        "Current Month": int(last_val),
        "Growth Rate": f"{growth:.1%}",
        "Forecast (3M)": int(max(0, pred))
    })

forecast_df = pd.DataFrame(forecast_results)
if not forecast_df.empty:
    st.dataframe(forecast_df, use_container_width=True)

    # -------------------- INVENTORY ALERTS --------------------
    if inventory_col != "None":
        st.subheader("🚨 Inventory Shortage Alerts")
        latest_inv = df.sort_values(date_col).groupby(product_col).tail(1)[[product_col, inventory_col]]
        alerts = forecast_df.merge(latest_inv, left_on="Product", right_on=product_col)
        
        shortages = alerts[alerts[inventory_col] < alerts["Forecast (3M)"]]
        if not shortages.empty:
            st.warning(f"Found {len(shortages)} products at risk of stockout.")
            st.table(shortages[["Product", "Forecast (3M)", inventory_col]])
        else:
            st.success("All products have sufficient stock based on forecast.")
