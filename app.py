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
st.title("📊 Smart Inventory & Demand Forecasting")

# -------------------- FILE UPLOAD --------------------
uploaded_file = st.file_uploader("📂 Upload your sales dataset (CSV)", type=["csv"])

if uploaded_file is None:
    st.info("👆 Please upload a CSV file to get started.")
    st.stop()

df = pd.read_csv(uploaded_file)

# -------------------- MAIN DATA CONFIGURATION --------------------
with st.expander("🛠️ Step 1: Data Configuration", expanded=True):
    st.write("Confirm which columns represent your data:")
    
    # Show a small preview so user knows what to select
    st.dataframe(df.head(3), use_container_width=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        date_col = st.selectbox("Date Column", df.columns)
    with c2:
        product_col = st.selectbox("Product Column", df.columns)
    with c3:
        demand_col = st.selectbox("Units Sold Column", df.columns)
    with c4:
        inventory_col = st.selectbox("Inventory Column (optional)", ["None"] + list(df.columns))

# -------------------- DATA PREP & CLEANING --------------------
# Force conversion to datetime
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# Check if conversion worked
if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
    st.error(f"❌ '{date_col}' is not a valid date. Please select a column containing dates.")
    st.stop()

# Remove invalid dates and ensure demand is numeric
df = df.dropna(subset=[date_col])
df[demand_col] = pd.to_numeric(df[demand_col], errors='coerce').fillna(0)

# Create period columns
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# -------------------- FILTERS (Now in a clean horizontal bar) --------------------
st.divider()
f1, f2 = st.columns([2, 1])
with f1:
    unique_prods = sorted(df[product_col].astype(str).unique().tolist())
    selected_product = st.selectbox("🔍 Filter by Product", ["All Products"] + unique_prods)
with f2:
    time_view = st.radio("View Frequency", ["Monthly", "Yearly"], horizontal=True)

# Apply Filter
filtered_df = df.copy()
if selected_product != "All Products":
    filtered_df = df[df[product_col].astype(str) == selected_product]

# -------------------- KPI METRICS --------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-card'><h3>Total Demand</h3><h2>{int(filtered_df[demand_col].sum()):,}</h2></div>", unsafe_allow_html=True)
with col2:
    avg_d = filtered_df[demand_col].mean()
    st.markdown(f"<div class='metric-card'><h3>Avg Demand</h3><h2>{int(avg_d):,}</h2></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><h3>Unique Items</h3><h2>{filtered_df[product_col].nunique()}</h2></div>", unsafe_allow_html=True)

# -------------------- TREND CHART --------------------
st.subheader("📈 Demand Trend")

if time_view == "Monthly":
    trend_df = filtered_df.groupby("Month")[[demand_col]].sum().reset_index()
    x_axis = "Month"
else:
    trend_df = filtered_df.groupby("Year")[[demand_col]].sum().reset_index()
    x_axis = "Year"

if not trend_df.empty:
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(trend_df[x_axis].astype(str), trend_df[demand_col], marker="o", color="#007BFF", linewidth=2)
    ax.set_facecolor('#f9f9f9')
    plt.xticks(rotation=45)
    st.pyplot(fig)

# -------------------- FORECASTING --------------------
st.divider()
st.subheader("🔮 3-Month Automated Forecast")

forecast_results = []
for product, group in df.groupby(product_col):
    monthly_series = group.sort_values(date_col).groupby("Month")[demand_col].sum()
    if len(monthly_series) < 2: continue

    growth = monthly_series.pct_change().replace([np.inf, -np.inf], np.nan).mean()
    if pd.isna(growth): growth = 0
    
    last_val = monthly_series.iloc[-1]
    pred = last_val * (1 + growth) ** 3
    
    forecast_results.append({
        "Product": product,
        "Current Sales": int(last_val),
        "Predicted Demand (3M)": int(max(0, pred))
    })

forecast_df = pd.DataFrame(forecast_results)
if not forecast_df.empty:
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    # -------------------- INVENTORY ALERTS --------------------
    if inventory_col != "None
