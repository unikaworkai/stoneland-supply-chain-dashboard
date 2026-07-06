import streamlit as st
import plotly.express as px
from utils.data_loader import load_data
from utils.branding import CATEGORICAL, NAVY
from utils.metrics import top_customers, revenue_concentration, rep_leaderboard, monthly_order_volume

data = load_data()

st.title("Sales & customers")

so = data["Sales_Orders"]
sol = data["SO_Lines"]
total_revenue = sol.sale_price_total.sum()
avg_order_value = sol.merge(so[["sales_order_id"]], on="sales_order_id").groupby("sales_order_id").sale_price_total.sum().mean()
concentration = revenue_concentration(data, top_n=10)

c1, c2, c3 = st.columns(3)
c1.metric("Total revenue", f"${total_revenue:,.0f}")
c2.metric("Avg order value", f"${avg_order_value:,.0f}")
c3.metric("Top-10 customer concentration", f"{concentration:.1f}%")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Top 10 customers by revenue")
    top10 = top_customers(data, 10)
    fig = px.bar(top10, x="sale_price_total", y="company_name", orientation="h", color="customer_type",
                 color_discrete_sequence=CATEGORICAL)
    fig.update_layout(yaxis_title=None, xaxis_title="Revenue ($)", height=400, yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Sales rep leaderboard")
    reps = rep_leaderboard(data, 10)
    fig2 = px.bar(reps, x="employee_id", y="revenue", color_discrete_sequence=[NAVY])
    fig2.update_layout(xaxis_title=None, yaxis_title="Revenue ($)", height=400)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Monthly order volume")
vol = monthly_order_volume(data)
fig3 = px.line(vol, x="month", y="order_count", markers=True, color_discrete_sequence=[NAVY])
fig3.update_layout(xaxis_title=None, yaxis_title="Orders", height=320)
st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.subheader("Customers with no order in 180+ days")
cust = data["Customers"]
last_order = so.merge(sol[["sales_order_id"]].drop_duplicates(), on="sales_order_id").groupby("customer_id").order_date.max()
as_of = so.order_date.max()
inactive = (as_of - last_order).dt.days
inactive_df = inactive[inactive >= 180].reset_index()
inactive_df.columns = ["customer_id", "days_since_last_order"]
inactive_df = inactive_df.merge(cust[["customer_id", "company_name", "customer_type"]], on="customer_id")
st.dataframe(inactive_df[["company_name", "customer_type", "days_since_last_order"]].sort_values(
    "days_since_last_order", ascending=False
).rename(columns={"company_name": "Customer", "customer_type": "Type", "days_since_last_order": "Days inactive"}),
    use_container_width=True, hide_index=True)
