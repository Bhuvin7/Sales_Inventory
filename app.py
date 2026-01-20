import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. PAGE CONFIG
st.set_page_config(page_title="AI Inventory Dashboard", page_icon="📦", layout="wide")

# 2. THEME-AWARE CSS
# Using rgba(128,128,128,0.1) creates a subtle border that works in both modes
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 3. HEADER
st.title("📊 Smart Demand Forecast & Inventory Control")
st.write("Upload your AI-processed CSV in the sidebar to view trends and reorder points.")
st.markdown("---")

# 4. SIDEBAR
st.sidebar.header("📂 Data Management")
uploaded_file = st.sidebar.file_uploader("Upload Processed CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Date Handling
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[date_col]).sort_values(by=date_col)

    # Column Detection
    demand_col = next((c for c in df.columns if any(x in c.lower() for x in ["actual", "demand", "sold"])), None)
    pred_col = next((c for c in df.columns if any(x in c.lower() for x in ["pred", "forecast"])), None)
    cat_col = next((c for c in df.columns if "category" in c.lower()), None)
    region_col = next((c for c in df.columns if "region" in c.lower()), None)
    stock_col = next((c for c in df.columns if any(x in c.lower() for x in ["inventory", "stock"])), "Inventory Level")

    # Sidebar Filters
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filter View")
    filtered_df = df.copy()
    if cat_col:
        selected_cat = st.sidebar.multiselect("Category", df[cat_col].unique(), default=df[cat_col].unique())
        filtered_df = filtered_df[filtered_df[cat_col].isin(selected_cat)]
    
    if region_col:
        selected_region = st.sidebar.multiselect("Region", df[region_col].unique(), default=df[region_col].unique())
        filtered_df = filtered_df[filtered_df[region_col].isin(selected_region)]

    # Metrics Row
    st.subheader("📌 Executive Summary")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Actual Demand", f"{int(filtered_df[demand_col].sum()):,}")
    with k2:
        if pred_col:
            mae = abs(filtered_df[demand_col] - filtered_df[pred_col]).mean()
            # Safety check for division by zero
            mean_demand = filtered_df[demand_col].mean()
            acc = max(0, 100 - (mae / mean_demand * 100)) if mean_demand != 0 else 0
            st.metric("Model Accuracy", f"{acc:.1f}%")
    with k3:
        st.metric("Peak Daily Demand", f"{int(filtered_df[demand_col].max()):,}")
    with k4:
        st.metric("Total Records", f"{len(filtered_df):,}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Forecasting Trends", "📊 Product Insights", "🚨 Inventory Planning"])

    with tab1:
        st.subheader("Demand Trend Analysis")
        # Removing template="plotly_white" allows it to follow Streamlit's theme
        fig_trend = px.line(filtered_df.tail(100), x=date_col, 
                            y=[demand_col, pred_col] if pred_col else [demand_col],
                            color_discrete_map={demand_col: "#0077b6", pred_col: "#fb8500"})
        fig_trend.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig_trend, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            if cat_col:
                st.write("#### Demand by Category")
                cat_sum = filtered_df.groupby(cat_col)[demand_col].sum().reset_index()
                fig_bar = px.bar(cat_sum, x=cat_col, y=demand_col, color=demand_col, color_continuous_scale="Blues")
                st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            if region_col:
                st.write("#### Regional Market Share")
                region_sum = filtered_df.groupby(region_col)[demand_col].sum().reset_index()
                fig_pie = px.pie(region_sum, names=region_col, values=demand_col, hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.subheader("🚨 Stock Reorder Recommendations")
        cols_to_show = [c for c in [date_col, 'Product ID', cat_col, region_col, stock_col, pred_col, 'Suggested_Order'] if c in filtered_df.columns]
        st.dataframe(filtered_df[cols_to_show].sort_values(by=date_col, ascending=False).head(25), use_container_width=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Analysis", csv, "inventory_analysis.csv", "text/csv")

else:
    st.info("### 👈 Get Started: Upload your CSV in the sidebar.")
    st.write("If you switch to Dark Mode, the charts and text will now adapt automatically.")
