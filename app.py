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
    st.write("Confirm your column mapping:")
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

# -------------------- DATA CLEANING --------------------
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
    st.error(f"❌ '{date_col}' is not a valid date format.")
    st.stop()

df = df.dropna(subset=[date_col])
df[demand_col] = pd.to_numeric(df[demand_col], errors='coerce').fillna(0)
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# -------------------- FILTERS --------------------
st.divider()
f1, f2 = st.columns([2, 1])

with f1:
    # This block must be indented exactly like this
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
    avg_val = filtered_df[demand_col].mean()
    st.markdown(f"<div class='metric-card'><h3>Avg Demand</h3><h2>{int(avg_val) if not pd.isna(avg_val) else 0:,}</h2></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><h3>Unique Items</h3><h2>{filtered_df[product_col].nunique()}</h2></div>", unsafe_allow_html=True)

# -------------------- TREND CHART --------------------
st.subheader("📈 Demand Trend")
if time_view == "Monthly":
    trend_df = filtered_df.groupby("Month
