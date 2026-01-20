import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inventory Dashboard", layout="wide")

st.title("📊 Smart Inventory Control Center")

# --- SIDEBAR ---
st.sidebar.header("Settings")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # 1. Load Data
    df = pd.read_csv(uploaded_file)
    
    # 2. Show Raw Data Preview (To confirm it's NOT blank)
    with st.expander("👀 Preview Raw Data"):
        st.write(df.head(10))

    # 3. Robust Date Conversion
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)

    # 4. Column Detection
    demand_col = next((c for c in df.columns if any(x in c.lower() for x in ["actual", "demand", "sold"])), None)
    pred_col = next((c for c in df.columns if any(x in c.lower() for x in ["pred", "forecast"])), None)

    # 5. UI Layout
    if demand_col:
        st.success(f"Detected Demand Column: {demand_col}")
        
        # KPI Row
        k1, k2 = st.columns(2)
        k1.metric("Total Demand", f"{int(df[demand_col].sum()):,}")
        if pred_col:
            k2.metric("Predicted Demand", f"{int(df[pred_col].sum()):,}")

        # Charts
        st.subheader("📈 Demand Trend")
        fig = px.line(df.tail(100), x=date_col if date_col else df.index, 
                      y=[demand_col, pred_col] if pred_col else [demand_col])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Could not find a 'Demand' or 'Units Sold' column in your file.")

else:
    st.info("Please upload a CSV file to begin.")
