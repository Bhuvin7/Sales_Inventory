# ==============================
# Retail Demand & Inventory App
# ==============================

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="Retail Demand Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# CUSTOM CSS (Power BI style)
# ------------------------------
st.markdown("""
<style>
body {
    background: linear-gradient(to right, #e0f2ff, #f5fbff);
}
.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# TITLE
# ------------------------------
st.title("📊 Retail Demand & Inventory Intelligence Dashboard")
st.caption("AI-based demand forecasting, inventory optimization & alerts")

# ------------------------------
# LOAD DATA
# ------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    return df

df = load_data()

# ------------------------------
# DATE HANDLING (SAFE)
# ------------------------------
date_col = "Date"
df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
df = df.dropna(subset=[date_col])

df["YearMonth"] = df[date_col].dt.to_period("M").astype(str)

# ------------------------------
# MONTHLY AGGREGATION
# ------------------------------
monthly_df = df.groupby(
    ["Product ID", "Category", "Region", "YearMonth"]
).agg({
    "Units Sold": "sum",
    "Inventory Level": "mean",
    "Price": "mean",
    "Discount": "mean",
    "Competitor Pricing": "mean",
    "Holiday/Promotion": "sum"
}).reset_index()

# ------------------------------
# FEATURE ENGINEERING
# ------------------------------
monthly_df["Lag_1"] = monthly_df.groupby("Product ID")["Units Sold"].shift(1)
monthly_df["Lag_3"] = monthly_df.groupby("Product ID")["Units Sold"].shift(3)
monthly_df["Rolling_3"] = (
    monthly_df.groupby("Product ID")["Units Sold"]
    .rolling(3).mean()
    .reset_index(0, drop=True)
)

monthly_df = monthly_df.dropna()

# ------------------------------
# ENCODING
# ------------------------------
encoders = {}
for col in ["Product ID", "Category", "Region"]:
    le = LabelEncoder()
    monthly_df[col] = le.fit_transform(monthly_df[col])
    encoders[col] = le

# ------------------------------
# MODEL TRAINING
# ------------------------------
features = [
    "Inventory Level", "Price", "Discount",
    "Competitor Pricing", "Holiday/Promotion",
    "Lag_1", "Lag_3", "Rolling_3",
    "Product ID", "Category", "Region"
]

X = monthly_df[features]
y = monthly_df["Units Sold"]

model = RandomForestRegressor(
    n_estimators=300,
    random_state=42
)
model.fit(X, y)

monthly_df["Predicted_Demand"] = model.predict(X)

# ------------------------------
# INVENTORY OPTIMIZATION
# ------------------------------
LEAD_TIME = 7
SERVICE_LEVEL = 1.65

monthly_df["Demand_STD"] = monthly_df.groupby("Product ID")["Units Sold"].transform("std")
monthly_df["Avg_Demand"] = monthly_df.groupby("Product ID")["Units Sold"].transform("mean")

monthly_df["Safety_Stock"] = SERVICE_LEVEL * monthly_df["Demand_STD"] * np.sqrt(LEAD_TIME)
monthly_df["Reorder_Point"] = (monthly_df["Avg_Demand"] * LEAD_TIME) + monthly_df["Safety_Stock"]

monthly_df["Inventory_Status"] = np.where(
    monthly_df["Inventory Level"] < monthly_df["Reorder_Point"],
    "⚠️ Reorder Now",
    "✅ Safe"
)

# ------------------------------
# KPI SECTION
# ------------------------------
k1, k2, k3, k4 = st.columns(4)

k1.metric("📦 Total Products", df["Product ID"].nunique())
k2.metric("📈 Total Units Sold", f"{int(df['Units Sold'].sum()):,}")
k3.metric("⚠️ Low Stock Alerts",
          int((monthly_df["Inventory_Status"] == "⚠️ Reorder Now").sum()))
k4.metric("💰 Avg Monthly Demand",
          f"{int(monthly_df['Units Sold'].mean()):,}")

# ------------------------------
# FILTERS
# ------------------------------
st.sidebar.header("🔎 Filters")

selected_category = st.sidebar.selectbox(
    "Category",
    ["All"] + sorted(df["Category"].unique())
)

selected_product = st.sidebar.selectbox(
    "Product",
    ["All"] + sorted(df["Product ID"].unique())
)

filtered_df = monthly_df.copy()

if selected_category != "All":
    filtered_df = filtered_df[
        filtered_df["Category"] ==
        encoders["Category"].transform([selected_category])[0]
    ]

if selected_product != "All":
    filtered_df = filtered_df[
        filtered_df["Product ID"] ==
        encoders["Product ID"].transform([selected_product])[0]
    ]

# ------------------------------
# DEMAND TREND
# ------------------------------
st.subheader("📊 Demand Forecast Trend")

trend_df = filtered_df.sort_values("YearMonth")

st.line_chart(
    trend_df.set_index("YearMonth")[["Units Sold", "Predicted_Demand"]]
)

# ------------------------------
# CATEGORY WISE DEMAND
# ------------------------------
st.subheader("🗂 Category-Wise Demand")

cat_df = df.groupby("Category")["Units Sold"].sum().sort_values(ascending=False)
st.bar_chart(cat_df)

# ------------------------------
# INVENTORY ALERTS TABLE
# ------------------------------
st.subheader("🚨 Inventory Shortage Alerts")

alert_df = filtered_df[
    filtered_df["Inventory_Status"] == "⚠️ Reorder Now"
][[
    "Product ID",
    "Inventory Level",
    "Reorder_Point",
    "Safety_Stock",
    "Inventory_Status"
]]

st.dataframe(alert_df, use_container_width=True)

# ------------------------------
# PROFIT INSIGHTS
# ------------------------------
st.subheader("💰 Profit Optimization Insight")

profit_df = df.groupby("Category")["Profit"].sum()
st.bar_chart(profit_df)

# ------------------------------
# FOOTER
# ------------------------------
st.markdown("---")
st.caption("🚀 Built with Machine Learning • Inventory Science • Streamlit")
