import streamlit as st
import plotly.express as px
from utils.data_loader import load_data
from utils.branding import show_logo, NAVY, GREEN, SEQUENTIAL_BLUE
from utils.metrics import aging_distribution, dead_stock_candidates, warehouse_utilization

st.set_page_config(page_title="Inventory & warehouse ops", layout="wide")
show_logo()
data = load_data()

st.title("Inventory & warehouse operations")

as_of = data["Monthly_Inventory_Snapshot"].snapshot_date.max()

slabs = data["Slab_Inventory"]
total_instock = (slabs.status == "in_stock").sum()
total_damaged = (slabs.status == "damaged").sum()

util = warehouse_utilization(data)

c1, c2, c3 = st.columns(3)
c1.metric("Slabs in stock", f"{total_instock:,}")
c2.metric("Avg capacity utilization", f"{util.utilization_pct.mean():.1f}%")
c3.metric("Damaged slabs (lifetime)", f"{total_damaged:,}")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Inventory aging distribution")
    aging = aging_distribution(data, as_of)
    fig = px.bar(aging, x="bucket", y="count", color="bucket",
                 color_discrete_sequence=SEQUENTIAL_BLUE)
    fig.update_layout(showlegend=False, xaxis_title="Days in stock", yaxis_title="Slab count", height=350)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Warehouse capacity utilization")
    fig2 = px.bar(util, x="name", y="utilization_pct", color_discrete_sequence=[GREEN])
    fig2.update_layout(yaxis_title="Utilization (%)", xaxis_title=None, height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Dead-stock candidates (90+ days, no sale)")
dead = dead_stock_candidates(data, as_of)
dead_display = dead.copy()
dead_display["avg_age"] = dead_display["avg_age"].round(0).astype(int)
st.dataframe(dead_display.rename(columns={
    "color_name": "Color", "material_type": "Material type",
    "slab_count": "Slabs on hand", "avg_age": "Avg days on hand"
}).head(15), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Transfers between warehouses")
trf = data["Transfers"]
wh = data["Warehouses"][["warehouse_id", "name"]]
trf_summary = trf.groupby("to_warehouse_id").size().reset_index(name="transfers_in").merge(
    wh, left_on="to_warehouse_id", right_on="warehouse_id"
)[["name", "transfers_in"]]
trf_out = trf.groupby("from_warehouse_id").size().reset_index(name="transfers_out").merge(
    wh, left_on="from_warehouse_id", right_on="warehouse_id"
)[["name", "transfers_out"]]
trf_full = trf_summary.merge(trf_out, on="name", how="outer").fillna(0)
st.dataframe(trf_full.rename(columns={"name": "Warehouse"}), use_container_width=True, hide_index=True)
