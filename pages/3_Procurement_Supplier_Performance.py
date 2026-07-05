import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_data
from utils.branding import show_logo
from utils.metrics import open_purchase_orders, quarry_leadtime_reliability, damage_rate_by_quarry, reorder_candidates

st.set_page_config(page_title="Procurement & supplier performance", layout="wide")
show_logo()
data = load_data()

st.title("Procurement & supplier performance")

as_of = data["Monthly_Inventory_Snapshot"].snapshot_date.max()
open_pos = open_purchase_orders(data)
lead = quarry_leadtime_reliability(data)
dmg = damage_rate_by_quarry(data)

c1, c2, c3 = st.columns(3)
c1.metric("Open purchase orders", len(open_pos))
c2.metric("Committed open spend", f"${open_pos.line_cost.sum():,.0f}")
c3.metric("Avg lead-time delay (all quarries)", f"{lead.avg_delay.mean():.1f} days")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Quarry lead-time reliability")
    fig = px.bar(lead.head(10), x="quarry_name", y="avg_delay", color="avg_delay",
                 color_continuous_scale="Oranges")
    fig.update_layout(yaxis_title="Avg delay vs ETA (days)", xaxis_title=None, height=380, coloraxis_showscale=False)
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Damage rate by quarry")
    fig2 = px.bar(dmg.head(10), x="quarry_name", y="damage_pct", color="damage_pct",
                  color_continuous_scale="Reds")
    fig2.update_layout(yaxis_title="Damage rate (%)", xaxis_title=None, height=380, coloraxis_showscale=False)
    fig2.update_xaxes(tickangle=-35)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Reorder candidates (lowest days-of-supply first)")
reorder = reorder_candidates(data, as_of)
reorder_display = reorder[reorder.days_of_supply < 999].copy()
reorder_display["days_of_supply"] = reorder_display["days_of_supply"].round(0).astype(int)
st.dataframe(reorder_display[["color_name", "material_type", "in_stock_count", "sold_last_90d", "days_of_supply"]].rename(columns={
    "color_name": "Color", "material_type": "Material type", "in_stock_count": "In stock (slabs)",
    "sold_last_90d": "Sold last 90 days", "days_of_supply": "Days of supply"
}).head(15), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Open purchase orders")
st.dataframe(open_pos.rename(columns={
    "po_id": "PO", "quarry_name": "Quarry", "order_date": "Order date",
    "expected_ship_date": "Expected ship", "status": "Status", "line_cost": "Committed spend"
}), use_container_width=True, hide_index=True)
