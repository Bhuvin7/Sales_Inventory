import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. PAGE CONFIG (Always at the top)
st.set_page_config(page_title="AI Inventory Dashboard", page_icon="📦", layout="wide")

# 2. CUSTOM CSS FOR CARDS AND THEME
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    h1 {
        color: #023e8a;
    }
</style>
""", unsafe_allow_html=True)

# 3. HEADER (Visible immediately)
st.title("📊 Smart Demand Forecast & Inventory Control")
st.write("Welcome! Please upload your AI-processed CSV in the sidebar to generate the intelligence report.")
st.markdown("---")

# 4. SIDEBAR SETUP
st.sidebar.header("📂 Data Management")
uploaded_file = st.sidebar.file_uploader("Upload Processed CSV", type=["csv"])

# 5. MAIN LOGIC
if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file)
    
    # --- ROBUST DATE HANDLING ---
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)

    # --- AUTOMATIC COLUMN DETECTION ---
    demand_col = next((c for c in df.columns if any(x in c.lower() for x in ["actual", "demand", "sold"])), None)
    pred_col = next((c for c in df.columns if any(x in c.lower() for x in ["pred", "forecast"])), None)
    cat_col = next((c for c in df.columns if "category" in c.lower()), None)
    region_col = next((c for c in df.columns if "region" in c.lower()), None)
    stock_col = next((c for c in df.columns if any(x in c.lower() for x in ["inventory", "stock"])), "Inventory Level")

    # --- SIDEBAR FILTERS (Now Dynamic) ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filter View")
    
    filtered_df = df.copy()
    if cat_col:
        selected_cat = st.sidebar.multiselect("Select Category", df[cat_col].unique(), default=df[cat_col].unique())
        filtered_df = filtered_df[filtered_df[cat_col].isin(selected_cat)]
    
    if region_col:
        selected_region = st.sidebar.multiselect("Select Region", df[region_col].unique(), default=df[region_col].unique())
        filtered_df = filtered_df[filtered_df[region_col].isin(selected_region)]

    # --- TOP KPI METRICS ---
    st.subheader("📌 Executive Summary")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Total Actual Demand", f"{int(filtered_df[demand_col].sum()):,}")
    with kpi2:
        if pred_col:
            # Accuracy Calculation
            mae = abs(filtered_df[demand_col] - filtered_df[pred_col]).mean()
            acc = max(0, 100 - (mae / filtered_df[demand_col].mean() * 100))
            st.metric("Model Accuracy", f"{acc:.1f}%")
    with kpi3:
        st.metric("Peak Daily Demand", f"{int(filtered_df[demand_col].max()):,}")
    with kpi4:
        # Check for Stock Status or simulate based on demand
        if 'Stock_Status' in filtered_df.columns:
            critical = len(filtered_df[filtered_df['Stock_Status'] == 'Critical Low'])
            st.metric("Critical Items", critical, delta="Alert", delta_color="inverse")
        else:
            st.metric("Total Rows", len(filtered_df))

    st.markdown("---")

    # --- TABS FOR PROFESSIONAL LAYOUT ---
    tab1, tab2, tab3 = st.tabs(["📈 Forecasting Trends", "📊 Product Insights", "🚨 Inventory Planning"])

    with tab1:
        st.subheader("Demand Trend Analysis (Last 100 Records)")
        # Interactive Line Chart
        fig_trend = px.line(filtered_df.tail(100), x=date_col, y=[demand_col, pred_col] if pred_col else [demand_col],
                            labels={"value": "Units", "variable": "Metric"},
                            color_discrete_map={demand_col: "#0077b6", pred_col: "#fb8500"},
                            template="plotly_white")
        fig_trend.update_layout(hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Demand Distribution by Category")
            if cat_col:
                cat_sum = filtered_df.groupby(cat_col)[demand_col].sum().reset_index()
                fig_bar = px.bar(cat_sum, x=cat_col, y=demand_col, color=demand_col, color_continuous_scale="Blues")
                st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("Regional Market Share")
            if region_col:
                region_sum = filtered_df.groupby(region_col)[demand_col].sum().reset_index()
                fig_pie = px.pie(region_sum, names=region_col, values=demand_col, hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.subheader("🚨 Stock Reorder Recommendation")
        st.markdown("The following items have high predicted demand and require stock verification.")
        
        # Select and show relevant columns
        cols_to_show = [c for c in [date_col, 'Product ID', cat_col, region_col, stock_col, pred_col, 'Suggested_Order'] if c in filtered_df.columns]
        st.dataframe(filtered_df[cols_to_show].sort_values(by=pred_col, ascending=False).head(25), use_container_width=True)

        # DOWNLOAD BUTTON
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download This Analysis", csv, "inventory_analysis.csv", "text/csv")

else:
    # This shows when the app is "Waiting" for data
    st.info("### 👈 Get Started")
    st.write("Use the sidebar on the left to upload your `final_dashboard_data.csv`. Once uploaded, the AI will generate your trends and inventory alerts.")
    
    # Optional: Display a small diagram of the system logic
    st.markdown("---")
    st.write("#### How the AI Intelligence Works")
    st.write("1. **Data Ingestion:** Loads your 70,000 sales records.")
    st.write("2. **Demand Prediction:** Uses Random Forest to predict future needs.")
    st.write("3. **Stock Optimization:** Compares prediction vs current inventory to suggest orders.")

    

[Image of an inventory management system architecture]
