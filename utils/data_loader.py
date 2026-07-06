import streamlit as st
import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Stoneland_Supply_Chain_Data.xlsx")

DATE_COLS = {
    "Quarries": ["relationship_start_date"],
    "Employees": ["hire_date"],
    "Purchase_Orders": ["order_date", "expected_ship_date"],
    "Containers": ["ship_date", "eta", "actual_arrival_date"],
    "Receiving_Log": ["received_date"],
    "Slab_Inventory": ["received_date"],
    "Sales_Orders": ["order_date"],
    "Transfers": ["transfer_date"],
    "Damage_Log": ["reported_date"],
    "Monthly_Inventory_Snapshot": ["snapshot_date"],
}


@st.cache_data
def load_data():
    sheets = pd.read_excel(DATA_PATH, sheet_name=None)
    for name, cols in DATE_COLS.items():
        for c in cols:
            if name in sheets and c in sheets[name].columns:
                sheets[name][c] = pd.to_datetime(sheets[name][c])
    return sheets


AVG_SQFT = {"Granite": 56, "Marble": 54, "Quartzite": 62, "Quartz": 48}
