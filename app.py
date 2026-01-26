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
    
    # Preview to help user pick columns
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
# 1. Convert Date
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
    st.error(f"❌ '{date_col}' is not a valid date format.")
    st.stop()

# 2. Clean Data
df = df.dropna(subset=[date_col])
df[demand_col] = pd.to_numeric(df[demand_col], errors='coerce').fillna(0)
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# -------------------- FILTERS --------------------
st.divider()
f1, f2 = st.columns([2, 1])
with f1:
