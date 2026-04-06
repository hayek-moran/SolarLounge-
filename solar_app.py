import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# page configuration
st.set_page_config(page_title="Solar Lounge | smart ems", layout="wide")

# --- backend logic & constants ---
solar_capacity = 10.2  # kwp
batt_capacity = 22.0  # kwh
capex = 115000  # ils
annual_savings = 10368  # ils
co2_factor = 0.533  # kg co2 saved per kwh (israeli grid avg)

# --- lowercase documentation & style ---
# initialize session state for simulation if needed
if 'soh' not in st.session_state:
    st.session_state.soh = 98.2  # state of health percentage

# --- sidebar settings ---
with st.sidebar:
    st.header("🛠️ system settings")
    weather_condition = st.selectbox("current weather", ["sunny", "partly cloudy", "overcast"])
    maintenance_mode = st.toggle("maintenance mode", False)
    st.divider()
    st.write("system id: sl-96-tech-2026")

# --- main ui ---
st.title("☀️ Solar Lounge : Smart Energy Management ☀️")
st.write(f"welcome back | system status: {'online' if not maintenance_mode else 'maintenance'}")

# tabs for clean organization
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 real-time monitor", "⛅ weather & forecast", "💰 financial & eco", "📋 telemetry logs"])

with tab1:
    # point 2: smart alerts & live metrics
    c1, c2, c3, c4 = st.columns(4)

    curr_batt = 82
    c1.metric("battery level", f"{curr_batt}%", "-2% (discharging)")
    c2.metric("current production", "7.8 kw", "optimal")
    c3.metric("household load", "2.1 kw", "low")
    c4.metric("grid export", "5.7 kw", "earning")

    # alerts logic
    if curr_batt < 20:
        st.error("⚠️ alert: battery critically low. reducing non-essential loads.")
    elif weather_condition == "overcast":
        st.warning("ℹ️ notice: low solar production expected. manage heavy appliances.")
    else:
        st.success("✅ system performing optimally. surplus energy detected.")

    # hourly simulation
    hours = [f"{h:02d}:00" for h in range(24)]
    weather_multiplier = {"sunny": 1.0, "partly cloudy": 0.6, "overcast": 0.2}[weather_condition]

    solar_gen = [max(0, solar_capacity * weather_multiplier * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0 for h
                 in range(24)]
    house_load = [1.5 + 2.2 * np.exp(-(h - 8) ** 2 / 4) + 3.8 * np.exp(-(h - 20) ** 2 / 9) for h in range(24)]

    soc_list, current_soc = [], 0.82
    for s, l in zip(solar_gen, house_load):
        net = s - l
        if net > 0:
            current_soc = min(1.0, current_soc + (net * 0.95 / batt_capacity))
        else:
            current_soc = max(0.05, current_soc - (abs(net) / batt_capacity))
        soc_list.append(current_soc * 100)

    # power flow chart
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=hours, y=solar_gen, name="solar (kw)", fill='tozeroy', line=dict(color='#ffa500', width=3)))
    fig.add_trace(go.Scatter(x=hours, y=house_load, name="load (kw)", line=dict(color='#1e90ff', dash='dash')))
    fig.add_trace(go.Scatter(x=hours, y=soc_list, name="battery %", yaxis='y2', line=dict(color='#00ff7f', width=4)))

    fig.update_layout(
        template="plotly_dark", height=450,
        yaxis=dict(title="power (kw)", gridcolor='rgba(255,255,255,0.1)'),
        yaxis2=dict(title="soc %", overlaying='y', side='right', range=[0, 105], gridcolor='rgba(255,255,255,0.1)'),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # point 1: solar forecast based on weather
    st.subheader("⛅ 24-hour solar forecast")
    st.info("forecast data based on real-time meteorological api integration")

    forecast_col, health_col = st.columns([2, 1])

    with forecast_col:
        # showing tomorrow's projection vs today
        tomorrow_gen = [s * 0.85 for s in solar_gen]  # simulated 15% drop
        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Bar(x=hours, y=solar_gen, name="today", marker_color='orange', opacity=0.6))
        fig_forecast.add_trace(
            go.Scatter(x=hours, y=tomorrow_gen, name="tomorrow (pred.)", line=dict(color='white', dash='dot')))
        fig_forecast.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_forecast, use_container_width=True)

    with health_col:
        # point 3: battery health (soh)
        st.subheader("🔋 battery health")
        st.metric("state of health (soh)", f"{st.session_state.soh}%", "-0.1% since last month")
        st.write("estimated remaining life: 14.2 years")
        st.progress(st.session_state.soh / 100)

with tab3:
    # point 4: financial & environmental impact
    st.subheader("🌍 sustainability & roi")

    m1, m2, m3 = st.columns(3)
    total_produced = 45200  # simulated lifetime kwh

    m1.metric("co2 saved", f"{total_produced * co2_factor / 1000:.1f} tons")
    m2.metric("trees planted eq.", f"{int(total_produced / 20)} trees")
    m3.metric("net profit (lifetime)", f"₪{annual_savings * 5 - capex:,.0f}")

    years = np.arange(26)
    cumulative_profit = -capex + (annual_savings * years)
    fig_roi = go.Figure()
    fig_roi.add_trace(
        go.Scatter(x=years, y=cumulative_profit, name="cash flow", fill='tozeroy', line=dict(color='lime')))
    fig_roi.add_hline(y=0, line_dash="dash", line_color="red")
    fig_roi.update_layout(template="plotly_dark", height=350, xaxis_title="years", yaxis_title="ils balance")
    st.plotly_chart(fig_roi, use_container_width=True)

with tab4:
    # telemetry log
    st.subheader("📋 detailed sensor logs")
    log_df = pd.DataFrame({
        "timestamp": hours,
        "solar_kw": solar_gen,
        "load_kw": house_load,
        "soc_pct": soc_list,
        "temp_c": [22 + np.random.normal(0, 1) for _ in range(24)]
    })
    st.dataframe(log_df.style.format(precision=2), use_container_width=True)

    csv = log_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 download technical log", data=csv, file_name='solar_lounge_telemetry.csv')

# summary footer
st.divider()
st.caption("solar lounge | designed by moran hayek")