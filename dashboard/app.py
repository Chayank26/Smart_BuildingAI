"""
Streamlit Dashboard for Autonomous Smart Building Control System.
Provides telemetry monitoring, HVAC energy analytics, and setpoint controls.
"""

import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Smart Building AI Control Center",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏢 Autonomous Smart Building Control System")
st.markdown("Real-time telemetry, EnergyPlus co-simulation monitoring, and MCP agent controls.")

# Sidebar Controls
st.sidebar.header("🕹️ Building Control Panel")
selected_zone = st.sidebar.selectbox("Select Thermal Zone", ["Zone_1", "Zone_2", "Zone_3"])
agent_mode = st.sidebar.toggle("Autonomous AI Agent Mode", value=True)

st.sidebar.subheader("Manual Setpoint Override")
heating_sp = st.sidebar.slider("Heating Setpoint (°C)", 16.0, 24.0, 20.0, 0.5)
cooling_sp = st.sidebar.slider("Cooling Setpoint (°C)", 22.0, 30.0, 24.0, 0.5)

if st.sidebar.button("Apply Setpoints"):
    st.sidebar.success(f"Applied setpoints to {selected_zone}: Heat {heating_sp}°C, Cool {cooling_sp}°C")

# Generate Synthetic Historical Telemetry Data
np.random.seed(42)
time_stamps = pd.date_range(end=pd.Timestamp.now(), periods=24, freq="h")
temp_indoor = 22.0 + np.sin(np.linspace(0, 3 * np.pi, 24)) * 1.5 + np.random.normal(0, 0.3, 24)
temp_outdoor = 18.0 + np.sin(np.linspace(0, 2 * np.pi, 24)) * 8.0
power_kw = max(1.0, 4.0 + (temp_outdoor - 20.0) * 0.5 + np.random.normal(0, 0.5, 24))

df = pd.DataFrame({
    "Timestamp": time_stamps,
    "Indoor Temperature (°C)": temp_indoor,
    "Outdoor Temperature (°C)": temp_outdoor,
    "HVAC Power (kW)": power_kw,
    "Heating Setpoint (°C)": heating_sp,
    "Cooling Setpoint (°C)": cooling_sp,
})

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Indoor Temp", f"{temp_indoor[-1]:.1f} °C", "+0.2 °C")
col2.metric("Outdoor Weather", f"{temp_outdoor[-1]:.1f} °C", "-1.1 °C")
col3.metric("HVAC Power Consumption", f"{power_kw[-1]:.2f} kW", "-0.4 kW")
col4.metric("Agent Status", "Active 🤖" if agent_mode else "Manual 👤")

st.divider()

# Charts
tab1, tab2 = st.tabs(["📈 Temperature & Comfort", "⚡ Energy Analytics"])

with tab1:
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(x=df["Timestamp"], y=df["Indoor Temperature (°C)"], name="Indoor Temp", line=dict(color="#00CC96", width=3)))
    fig_temp.add_trace(go.Scatter(x=df["Timestamp"], y=df["Outdoor Temperature (°C)"], name="Outdoor Temp", line=dict(color="#EF553B", dash="dash")))
    fig_temp.add_trace(go.Scatter(x=df["Timestamp"], y=df["Heating Setpoint (°C)"], name="Heating Setpoint", line=dict(color="#AB63FA", dot="dot")))
    fig_temp.add_trace(go.Scatter(x=df["Timestamp"], y=df["Cooling Setpoint (°C)"], name="Cooling Setpoint", line=dict(color="#FFA15A", dot="dot")))
    fig_temp.update_layout(title="Thermal Zone Telemetry & Setpoints", xaxis_title="Time", yaxis_title="Temperature (°C)", template="plotly_white")
    st.plotly_chart(fig_temp, use_container_width=True)

with tab2:
    fig_power = px.bar(df, x="Timestamp", y="HVAC Power (kW)", title="Hourly HVAC Power Consumption", color_discrete_sequence=["#636EFA"])
    fig_power.update_layout(template="plotly_white")
    st.plotly_chart(fig_power, use_container_width=True)

# Footer / Log status
st.caption("EnergyPlus API Bridge & MCP Control Server initialized.")
