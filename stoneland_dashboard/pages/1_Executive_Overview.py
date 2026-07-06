import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_data
from utils.branding import NAVY, GREEN, CATEGORICAL
from utils.metrics import (
    inventory_value_trend, current_inventory_value, margin_by_material,
    revenue_by_warehouse, aging_distribution
)

data = load_data()

st.title("Executive overview")

as_of = data["Monthly_Inventory_Snapshot"].snapshot_date.max()

warehouses = ["All"] + data["Warehouses"].name.tolist()
sel_wh = st.selectbox("Warehouse", warehouses)

cur_value, latest_period = current_inventory_value(data)
margin_df = margin_by_material(data)
overall_margin = (margin_df.revenue.sum() - margin_df.cost.sum()) / margin_df.revenue.sum() * 100
aging = aging_distribution(data, as_of)
aged_180 = int(aging.loc[aging["bucket"] == "180+", "count"].values[0])

sold_slabs = data["Slab_Inventory"][data["Slab_Inventory"].status == "sold"]
sol = data["SO_Lines"].merge(sold_slabs[["slab_id", "received_date"]], on="slab_id")
sol = sol.merge(data["Sales_Orders"][["sales_order_id", "order_date"]], on="sales_order_id")
avg_dwell = (sol.order_date - sol.received_date).dt.days.mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Inventory value", f"${cur_value:,.0f}", help=f"As of {latest_period.date()}")
c2.metric("Gross margin", f"{overall_margin:.1f}%")
c3.metric("Avg dwell time", f"{avg_dwell:.0f} days")
c4.metric("Aged 180+ days", f"{aged_180:,} slabs")

st.divider()

left, right = st.columns([1.4, 1])

wh_id_map = dict(zip(data["Warehouses"].name, data["Warehouses"].warehouse_id))

with left:
    st.subheader("Inventory value trend")
    snap = data["Monthly_Inventory_Snapshot"]
    if sel_wh != "All":
        snap = snap[snap.warehouse_id == wh_id_map[sel_wh]]
    trend = snap.groupby("snapshot_date")["inventory_value"].sum().reset_index()
    fig = px.line(trend, x="snapshot_date", y="inventory_value", markers=True,
                  color_discrete_sequence=[NAVY])
    fig.update_layout(yaxis_title="Inventory value ($)", xaxis_title=None, height=350)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by warehouse")
    rev = revenue_by_warehouse(data)
    if sel_wh != "All":
        rev = rev[rev.name == sel_wh]
    fig2 = px.bar(rev, x="name", y="sale_price_total", color_discrete_sequence=[GREEN])
    fig2.update_layout(yaxis_title="Revenue ($)", xaxis_title=None, height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Margin by material type")
mdf = margin_by_material(data)
mdf_display = mdf.copy()
mdf_display["revenue"] = mdf_display["revenue"].map(lambda x: f"${x:,.0f}")
mdf_display["cost"] = mdf_display["cost"].map(lambda x: f"${x:,.0f}")
mdf_display["margin_pct"] = mdf_display["margin_pct"].map(lambda x: f"{x:.1f}%")
st.dataframe(mdf_display.rename(columns={
    "material_type": "Material", "revenue": "Revenue", "cost": "Cost", "margin_pct": "Margin"
}), use_container_width=True, hide_index=True)
