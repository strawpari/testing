import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration and theme
st.set_page_config(layout="wide", page_title="GPU TCO Calculator", page_icon="💰")

st.title("💰 GPU TCO Calculator")

# Load example GPU data
@st.cache_data
def load_gpu_data():
    data = {
        'Card': ['NVIDIA H100 NVL', 'H100 SXM', 'H100 PCIe', 'L40S', 'L4', 'A100', 'A40', 'RTX 6000 Ada', 'RTX A6000', 'RTX A5000', 'RTX 4000 Ada', 'RTX A4000', 'RTX 4090', 'RTX 3090'],
        'Cost': [26000, 30000, 26000, 12000, 3300, 15000, 6000, 6350, 3200, 1000, 1250, 700, 1650, 700],
        'Power_Active': [350, 700, 350, 350, 72, 350, 300, 300, 300, 230, 130, 140, 450, 350],
        'Power_Idle': [25, 25, 25, 10, 10, 25, 10, 15, 15, 15, 10, 10, 19, 25],
        'Spot_Price': [1.65, 2.00, 1.65, 0.50, 0.22, 0.85, 0.28, 0.52, 0.38, 0.22, 0.19, 0.16, 0.35, 0.22],
        'OnDemand_Price': [2.79, 3.99, 3.29, 0.99, 0.43, 1.69, 0.35, 1.03, 0.76, 0.43, 0.38, 0.32, 0.69, 0.43]
    }
    return pd.DataFrame(data)

# Initialize session state
if 'gpu_data' not in st.session_state:
    st.session_state.gpu_data = load_gpu_data()

# Sidebar inputs with enhanced styling
with st.sidebar:
    st.header("📊 Input Parameters")

    # GPU Selection
    selected_gpu = st.selectbox("🎯 Select GPU", st.session_state.gpu_data['Card'])
    gpu_info = st.session_state.gpu_data[st.session_state.gpu_data['Card'] == selected_gpu].iloc[0]

# Main content area
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎮 GPU Attributes")
    st.info(f"**Selected GPU:** {selected_gpu}")
    st.metric("GPU Cost", f"${gpu_info['Cost']:,.2f}")
    st.metric("Active Power", f"{gpu_info['Power_Active']}W")
    st.metric("Idle Power", f"{gpu_info['Power_Idle']}W")
    duty_cycle = st.slider("⚡ Duty Cycle (%)", 0, 100, 80)

with col2:
    st.subheader("🏢 Rack and System Attributes")
    deployment_term = st.number_input("📅 Deployment Term (years)", value=5, min_value=1, max_value=10)
    dc_cost_per_rack = st.number_input("💵 Data Center Cost/Rack Space per month ($)", value=200)
    server_cost = st.number_input("🖥️ Server Cost ($)", value=21000)
    gpus_per_server = st.number_input("🔢 GPUs per Server", value=8, min_value=1)
    servers_per_rack = st.number_input("📦 Servers per Rack", value=3, min_value=1)

# Calculations
total_gpus = gpus_per_server * servers_per_rack
gpu_capex = gpu_info['Cost'] * total_gpus
rack_capex = server_cost * servers_per_rack + 2000
total_capex = gpu_capex + rack_capex
capex_per_month = total_capex / (deployment_term * 12)

power_per_gpu = (gpu_info['Power_Active'] * (duty_cycle/100) +
                 gpu_info['Power_Idle'] * (1-duty_cycle/100))
total_power = power_per_gpu * total_gpus
power_cost_monthly = total_power * 24 * 30 * 0.24 / 1000

opex_monthly = power_cost_monthly + dc_cost_per_rack
opex_per_gpu = opex_monthly / total_gpus

hours_per_month = 30 * 24
revenue_per_gpu = (gpu_info['OnDemand_Price'] * duty_cycle/100 +
                  gpu_info['Spot_Price'] * (1-duty_cycle/100)) * hours_per_month
total_revenue = revenue_per_gpu * total_gpus
revenue_after_cut = total_revenue * 0.8

# Enhanced Results Display
st.markdown("---")
st.header("💰 Financial Analysis")
col3, col4, col5 = st.columns(3)

with col3:
    st.subheader("💵 CapEx")
    st.success(f"**Total CapEx:** ${total_capex:,.2f}")
    st.success(f"**Monthly CapEx:** ${capex_per_month:,.2f}")
    st.success(f"**CapEx per GPU:** ${total_capex/total_gpus:,.2f}")

with col4:
    st.subheader("💸 OpEx")
    st.warning(f"**Monthly Power Cost:** ${power_cost_monthly:,.2f}")
    st.warning(f"**Total Monthly OpEx:** ${opex_monthly:,.2f}")
    st.warning(f"**OpEx per GPU:** ${opex_per_gpu:,.2f}")

with col5:
    st.subheader("📈 Revenue & ROI")
    st.info(f"**Monthly Revenue:** ${revenue_after_cut:,.2f}")
    monthly_profit = revenue_after_cut - opex_monthly - capex_per_month
    st.info(f"**Monthly Profit:** ${monthly_profit:,.2f}")
    payback_months = total_capex / (revenue_after_cut - opex_monthly)
    st.info(f"**Payback Period:** {payback_months:.1f} months")

# Enhanced Visualizations
st.markdown("---")
st.header("📊 Visualizations")
col6, col7 = st.columns(2)

with col6:
    st.subheader("📈 Monthly Financial Breakdown")
    monthly_data = pd.DataFrame({
        'Category': ['Costs', 'Revenue'],
        'CapEx': [capex_per_month, 0],
        'OpEx': [opex_monthly, 0],
        'Revenue': [0, revenue_after_cut]
    })
    st.bar_chart(monthly_data.set_index('Category'), use_container_width=True)

with col7:
    st.subheader("💹 Cumulative Cash Flow")
    months = range(0, 37)
    cash_flow = [-total_capex]
    for _ in range(1, 37):
        cash_flow.append(cash_flow[-1] + revenue_after_cut - opex_monthly)

    cash_flow_df = pd.DataFrame({
        'Month': months,
        'Cash Flow': cash_flow
    })
    st.line_chart(cash_flow_df.set_index('Month'), use_container_width=True)
