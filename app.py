import streamlit as st
import pandas as pd
import numpy as np


# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="Retail Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# ================== POWER BI STYLE ==================
st.markdown("""
<style>
body {
    background-color: #F5F7FB;
}
h1, h2, h3 {
    font-weight: 700;
}
.kpi-card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    text-align: center;
}
.section {
    background: white;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    margin-bottom: 25px;
}
.alert {
    background-color: #FFEAEA;
    padding: 15px;
    border-radius: 14px;
    border-left: 6px solid #FF4B4B;
}
</style>
""", unsafe_allow_html=True)

# ================== TITLE ==================
st.title("📊 Retail Intelligence Dashboard")
st.caption("Demand Forecasting • Inventory Optimization • Profit Analytics")

# ================== FILE UPLOAD ==================
file = st.file_uploader("📂 Upload Sales Dataset (CSV)", type=["csv"])
if file is None:
    st.stop()

df = pd.read_csv(file)

# ================== COLUMN SELECTION ==================
st.sidebar.header("🔧 Column Mapping")

date_col = st.sidebar.selectbox("Date", df.columns)
product_col = st.sidebar.selectbox("Product", df.columns)
category_col = st.sidebar.selectbox("Category", df.columns)
demand_col = st.sidebar.selectbox("Units Sold", df.columns)
price_col = st.sidebar.selectbox("Selling Price", df.columns)

cost_col = st.sidebar.selectbox(
    "Cost Price (Optional)",
    ["None"] + list(df.columns)
)

inventory_col = st.sidebar.selectbox(
    "Inventory (Optional)",
    ["None"] + list(df.columns)
)

# ================== DATA PREP ==================
df[date_col] = pd.to_datetime(df[date_col])
df["Year"] = df[date_col].dt.year
df["Month"] = df[date_col].dt.to_period("M").astype(str)

# ================== SIDEBAR FILTERS ==================
st.sidebar.header("🎯 Filters")

selected_category = st.sidebar.selectbox(
    "Select Category",
    ["All"] + sorted(df[category_col].astype(str).unique())
)

time_view = st.sidebar.radio("Time View", ["Monthly", "Yearly"])

filtered_df = df.copy()
if selected_category != "All":
    filtered_df = filtered_df[filtered_df[category_col] == selected_category]

# ================== KPI SECTION ==================
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_demand = filtered_df[demand_col].sum()
total_revenue = (filtered_df[demand_col] * filtered_df[price_col]).sum()

with col1:
    st.markdown(f"<div class='kpi-card'><h4>Total Demand</h4><h2>{int(total_demand):,}</h2></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='kpi-card'><h4>Total Revenue</h4><h2>₹ {int(total_revenue):,}</h2></div>", unsafe_allow_html=True)

with col3:
    avg_price = filtered_df[price_col].mean()
    st.markdown(f"<div class='kpi-card'><h4>Avg Price</h4><h2>₹ {avg_price:.2f}</h2></div>", unsafe_allow_html=True)

with col4:
    st.markdown(f"<div class='kpi-card'><h4>Categories</h4><h2>{filtered_df[category_col].nunique()}</h2></div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ================== CATEGORY DASHBOARD ==================
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.subheader("📦 Category-wise Performance")

cat_perf = (
    filtered_df
    .groupby(category_col)
    .agg({
        demand_col: "sum",
        price_col: "mean"
    })
    .reset_index()
)

cat_perf["Revenue"] = cat_perf[demand_col] * cat_perf[price_col]

st.dataframe(cat_perf, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ================== DEMAND TREND ==================
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.subheader("📈 Demand Trend")

if time_view == "Monthly":
    trend = filtered_df.groupby("Month")[demand_col].sum()
else:
    trend = filtered_df.groupby("Year")[demand_col].sum()

fig, ax = plt.subplots()
trend.plot(ax=ax, marker="o")
ax.set_ylabel("Units Sold")
ax.grid(True)
plt.xticks(rotation=45)

st.pyplot(fig)
st.markdown("</div>", unsafe_allow_html=True)

# ================== PROFIT OPTIMIZATION ==================
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.subheader("💰 Profit Optimization")

if cost_col != "None":
    filtered_df["Profit"] = (
        filtered_df[price_col] - filtered_df[cost_col]
    ) * filtered_df[demand_col]

    profit_by_product = (
        filtered_df
        .groupby(product_col)["Profit"]
        .sum()
        .reset_index()
        .sort_values("Profit", ascending=False)
    )

    st.markdown("### 🔝 Top Profitable Products")
    st.dataframe(profit_by_product.head(10), use_container_width=True)

    st.markdown("### ⚠️ Low / Loss-Making Products")
    st.dataframe(profit_by_product.tail(10), use_container_width=True)

else:
    st.info("ℹ️ Cost price not provided — profit optimization skipped")

st.markdown("</div>", unsafe_allow_html=True)

# ================== INVENTORY ALERT ==================
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.subheader("🚨 Inventory Risk Alerts")

if inventory_col != "None":
    latest_stock = (
        df.sort_values(date_col)
        .groupby(product_col)
        .tail(1)
    )

    risk = latest_stock[
        latest_stock[inventory_col] < latest_stock[demand_col]
    ]

    if len(risk) > 0:
        st.markdown("<div class='alert'><b>Inventory Shortage Detected</b></div>", unsafe_allow_html=True)
        st.dataframe(
            risk[[product_col, inventory_col, demand_col]],
            use_container_width=True
        )
    else:
        st.success("✅ Inventory levels are healthy")
else:
    st.info("ℹ️ Inventory column not selected")

st.markdown("</div>", unsafe_allow_html=True)

