import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Smart Inventory Forecast Dashboard",
    page_icon="📦",
    layout="wide"
)

# -------------------- BACKGROUND & STYLE --------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #cce7ff, #f5fbff);
}
.card {
    padding: 20px;
    border-radius: 18px;
    background: white;
    box-shadow: 0px 8px 25px rgba(0,0,0,0.1);
    text-align: center;
}
.metric-title {
    font-size: 16px;
    color: gray;
}
.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: #0077b6;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.markdown("""
<h1 style='text-align:center; color:#023e8a;'>📊 Smart Demand Forecast & Inventory Dashboard</h1>
<p style='text-align:center; color:gray;'>
Upload your sales dataset to analyze demand, trends, and inventory needs
</p>
""", unsafe_allow_html=True)

# -------------------- FILE UPLOAD --------------------
uploaded_file = st.file_uploader(
    "📂 Upload CSV File",
    type=["csv"]
)

if uploaded_file is None:
    st.info("""
### 📌 Required Columns (Minimum)
- Product / Category
- Date
- Units Sold or Demand
- Price / Discount (optional)
- Region (optional)

Once uploaded, dashboards will appear automatically.
""")
    st.stop()

# -------------------- LOAD DATA --------------------
df = pd.read_csv(uploaded_file)

# -------------------- DATE HANDLING --------------------
date_col = None
for col in df.columns:
    if "date" in col.lower():
        date_col = col
        df[col] = pd.to_datetime(df[col])
        break

# -------------------- BASIC COLUMN DETECTION --------------------
demand_col = None
for col in df.columns:
    if "sold" in col.lower() or "demand" in col.lower():
        demand_col = col
        break

product_col = None
for col in df.columns:
    if "product" in col.lower() or "sub" in col.lower():
        product_col = col
        break

category_col = None
for col in df.columns:
    if "category" in col.lower():
        category_col = col
        break

# -------------------- SIDEBAR FILTERS --------------------
st.sidebar.header("🎛 Filters")

if category_col:
    categories = st.sidebar.multiselect(
        "Select Category",
        df[category_col].unique(),
        default=df[category_col].unique()
    )
    df = df[df[category_col].isin(categories)]

if product_col:
    products = st.sidebar.multiselect(
        "Select Product",
        df[product_col].unique(),
        default=df[product_col].unique()
    )
    df = df[df[product_col].isin(products)]

# -------------------- KPI METRICS --------------------
total_demand = int(df[demand_col].sum())
avg_demand = int(df[demand_col].mean())
max_demand = int(df[demand_col].max())

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="metric-title">Total Demand</div>
        <div class="metric-value">{total_demand}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="metric-title">Average Demand</div>
        <div class="metric-value">{avg_demand}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="metric-title">Peak Demand</div>
        <div class="metric-value">{max_demand}</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- TABS --------------------
tab1, tab2, tab3 = st.tabs(["📈 Demand Trends", "📊 Product Comparison", "📦 Inventory Planning"])

# -------------------- TAB 1: LINE CHART --------------------
with tab1:
    st.subheader("Demand Over Time")
    if date_col:
        trend = df.groupby(date_col)[demand_col].sum().reset_index()
        fig = px.line(
            trend,
            x=date_col,
            y=demand_col,
            markers=True,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No Date column found")

# -------------------- TAB 2: BAR + PIE --------------------
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Demand by Product")
        prod_summary = df.groupby(product_col)[demand_col].sum().reset_index()
        fig = px.bar(
            prod_summary,
            x=product_col,
            y=demand_col,
            color=demand_col,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Category Contribution")
        if category_col:
            cat_summary = df.groupby(category_col)[demand_col].sum().reset_index()
            fig = px.pie(
                cat_summary,
                names=category_col,
                values=demand_col,
                hole=0.45
            )
            st.plotly_chart(fig, use_container_width=True)

# -------------------- TAB 3: INVENTORY FORECAST --------------------
with tab3:
    st.subheader("Inventory Recommendation")

    # Simple forecast logic
    df["Predicted_Demand"] = df[demand_col].rolling(3).mean().fillna(df[demand_col])
    df["Safety_Stock"] = df["Predicted_Demand"] * 0.2
    df["Reorder_Point"] = df["Predicted_Demand"] + df["Safety_Stock"]

    st.dataframe(
        df[[product_col, demand_col, "Predicted_Demand", "Reorder_Point"]]
        .sort_values("Reorder_Point", ascending=False)
        .head(20),
        use_container_width=True
    )

# -------------------- DOWNLOAD --------------------
st.download_button(
    "⬇ Download Forecast Results",
    df.to_csv(index=False),
    "inventory_forecast.csv",
    "text/csv"
)

# -------------------- FOOTER --------------------
st.markdown("""
<hr>
<p style='text-align:center; color:gray;'>
Built with ❤️ using AI-powered demand forecasting
</p>
""", unsafe_allow_html=True)
