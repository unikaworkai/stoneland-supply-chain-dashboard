import streamlit as st
from utils.data_loader import load_data
from utils.branding import show_logo
from utils.styling import inject_css, banner, section

st.set_page_config(page_title="Stoneland Supply Chain Intelligence", layout="wide", initial_sidebar_state="expanded")
inject_css()
show_logo()


def home():
    data = load_data()

    banner(
        "Stoneland supply chain intelligence",
        "AI-powered supply chain and procurement dashboard &mdash; granite, marble, quartzite, "
        "and quartz slab distribution across 4 warehouses"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏭 Warehouses", len(data["Warehouses"]))
    col2.metric("⛰️ Active quarries", len(data["Quarries"]))
    col3.metric("🧱 Slabs tracked", f"{len(data['Slab_Inventory']):,}")
    col4.metric("🤝 Customers", len(data["Customers"]))

    st.divider()
    section("What's inside", "🧭")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
- **📊 Executive overview** — inventory value, margin, revenue trends
- **📦 Inventory & warehouse ops** — aging, capacity, transfers, damage
- **🚚 Procurement & suppliers** — open POs, quarry reliability, spend
""")
    with c2:
        st.markdown("""
- **💰 Sales & customers** — top accounts, rep performance, order trends
- **📈 Demand forecasting** — sell-through trend signal by color/material
- **🤖 AI recommendation center** — reorder suggestions, risk summaries, weekly deltas
""")

    st.divider()
    st.caption(
        "Data covers 2023-01-01 through 2025-12-31 across a 15-table schema (Warehouses, Quarries, "
        "Materials, Customers, Employees, Purchase Orders, PO Lines, Containers, Receiving Log, "
        "Slab Inventory, Sales Orders, SO Lines, Transfers, Damage Log, and the Monthly Inventory Snapshot)."
    )


pages = [
    st.Page(home, title="Home", icon="🏠", default=True),
    st.Page("pages/1_Executive_Overview.py", title="Executive overview", icon="📊"),
    st.Page("pages/2_Inventory_Warehouse_Ops.py", title="Inventory & warehouse ops", icon="📦"),
    st.Page("pages/3_Procurement_Supplier_Performance.py", title="Procurement & suppliers", icon="🚚"),
    st.Page("pages/4_Sales_Customers.py", title="Sales & customers", icon="💰"),
    st.Page("pages/6_Demand_Forecasting.py", title="Demand forecasting", icon="📈"),
    st.Page("pages/5_AI_Recommendation_Center.py", title="AI recommendation center", icon="🤖"),
]

pg = st.navigation(pages)
pg.run()
