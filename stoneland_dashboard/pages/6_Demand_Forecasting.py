import streamlit as st
import plotly.express as px
from utils.data_loader import load_data
from utils.branding import NAVY, GREEN, CATEGORICAL
from utils.styling import section
from utils.metrics import demand_trend_by_material, monthly_sales_by_material_type

data = load_data()

st.title("Demand forecasting")
st.caption(
    "This is a trend signal, not a statistical forecast. With about 3 years of monthly data, "
    "a full time-series forecasting model would overclaim precision it can't support. Instead, "
    "this compares recent sell-through velocity to the prior period per color/material and "
    "classifies the direction - which is what design-trend tracking in this industry actually looks like."
)

as_of = data["Monthly_Inventory_Snapshot"].snapshot_date.max()
trend = demand_trend_by_material(data, as_of)

c1, c2, c3 = st.columns(3)
c1.metric("Accelerating", int((trend.trend == "Accelerating").sum()))
c2.metric("Stable", int((trend.trend == "Stable").sum()))
c3.metric("Declining", int((trend.trend == "Declining").sum()))

st.divider()
section("Sales by material type over time", "📈")
monthly = monthly_sales_by_material_type(data)
fig = px.line(monthly, x="month", y="slabs_sold", color="material_type",
              color_discrete_sequence=CATEGORICAL, markers=True)
fig.update_layout(yaxis_title="Slabs sold", xaxis_title=None, height=380)
st.plotly_chart(fig, use_container_width=True)

st.divider()
section("Trending colors and materials", "🎨")
active = trend[trend.trend != "No activity"].copy()
active["change_pct"] = active["change_pct"].map(lambda x: f"{x:+.0f}%" if x is not None else "new")

def trend_badge(t):
    color = {"Accelerating": "🟢", "Stable": "🔵", "Declining": "🟠"}.get(t, "⚪")
    return f"{color} {t}"

active["trend_display"] = active["trend"].map(trend_badge)

st.dataframe(
    active[["color_name", "material_type", "recent_sold", "prior_sold", "change_pct", "trend_display"]].rename(columns={
        "color_name": "Color", "material_type": "Material type",
        "recent_sold": "Sold (last 3mo)", "prior_sold": "Sold (prior 3mo)",
        "change_pct": "Change", "trend_display": "Trend"
    }),
    use_container_width=True, hide_index=True, height=450
)
