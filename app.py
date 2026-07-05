import streamlit as st
from utils.data_loader import load_data
from utils.branding import show_logo

st.set_page_config(page_title="Stoneland Supply Chain Intelligence", layout="wide", initial_sidebar_state="expanded")
show_logo()

data = load_data()

st.title("Stoneland supply chain intelligence")
st.caption("AI-powered supply chain and procurement dashboard - granite, marble, quartzite, and quartz slab distribution across 4 warehouses")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Warehouses", len(data["Warehouses"]))
col2.metric("Active quarries", len(data["Quarries"]))
col3.metric("Slabs tracked", f"{len(data['Slab_Inventory']):,}")
col4.metric("Customers", len(data["Customers"]))

st.divider()
st.markdown("""
Use the sidebar to navigate:

- **Executive overview** - inventory value, margin, revenue trends
- **Inventory & warehouse ops** - aging, capacity, transfers, damage
- **Procurement & supplier performance** - open POs, quarry reliability, spend
- **Sales & customers** - top accounts, rep performance, order trends
- **AI recommendation center** - reorder suggestions, risk summaries, week-over-week deltas

Data covers 2023-01-01 through 2025-12-31 across the 15-table schema (Warehouses, Quarries, Materials,
Customers, Employees, Purchase Orders, PO Lines, Containers, Receiving Log, Slab Inventory, Sales Orders,
SO Lines, Transfers, Damage Log, and the Monthly Inventory Snapshot).
""")
