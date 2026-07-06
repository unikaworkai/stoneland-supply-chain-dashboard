import pandas as pd
from utils.data_loader import AVG_SQFT


def inventory_value_trend(data):
    snap = data["Monthly_Inventory_Snapshot"]
    return snap.groupby("snapshot_date")["inventory_value"].sum().reset_index()


def current_inventory_value(data):
    snap = data["Monthly_Inventory_Snapshot"]
    latest = snap.snapshot_date.max()
    return snap[snap.snapshot_date == latest]["inventory_value"].sum(), latest


def margin_by_material(data):
    sol = data["SO_Lines"]
    slabs = data["Slab_Inventory"]
    mat = data["Materials"]
    df = sol.merge(slabs[["slab_id", "material_id", "landed_unit_cost_sqft"]], on="slab_id")
    df = df.merge(mat[["material_id", "material_type"]], on="material_id")
    df["sqft"] = df["sale_price_total"] / df["sale_price_sqft"]
    df["cost_total"] = df["landed_unit_cost_sqft"] * df["sqft"]
    g = df.groupby("material_type").agg(revenue=("sale_price_total", "sum"), cost=("cost_total", "sum")).reset_index()
    g["margin_pct"] = (g.revenue - g.cost) / g.revenue * 100
    return g


def revenue_by_warehouse(data):
    so = data["Sales_Orders"]
    sol = data["SO_Lines"]
    wh = data["Warehouses"]
    df = so.merge(sol[["sales_order_id", "sale_price_total"]], on="sales_order_id")
    g = df.groupby("fulfillment_warehouse_id")["sale_price_total"].sum().reset_index()
    g = g.merge(wh[["warehouse_id", "name"]], left_on="fulfillment_warehouse_id", right_on="warehouse_id")
    return g.sort_values("sale_price_total", ascending=False)


def aging_distribution(data, as_of):
    slabs = data["Slab_Inventory"]
    instock = slabs[slabs.status == "in_stock"].copy()
    instock["age_days"] = (as_of - instock.received_date).dt.days
    bins = [0, 30, 90, 180, 999999]
    labels = ["0-30", "30-90", "90-180", "180+"]
    instock["bucket"] = pd.cut(instock.age_days, bins=bins, labels=labels)
    return instock.bucket.value_counts().reindex(labels).reset_index()


def dead_stock_candidates(data, as_of, min_age_days=90):
    slabs = data["Slab_Inventory"]
    mat = data["Materials"]
    instock = slabs[slabs.status == "in_stock"].copy()
    instock["age_days"] = (as_of - instock.received_date).dt.days
    old = instock[instock.age_days >= min_age_days]
    df = old.merge(mat[["material_id", "color_name", "material_type"]], on="material_id")
    g = df.groupby(["color_name", "material_type"]).agg(
        slab_count=("slab_id", "count"), avg_age=("age_days", "mean")
    ).reset_index().sort_values("slab_count", ascending=False)
    return g


def warehouse_utilization(data):
    slabs = data["Slab_Inventory"]
    mat = data["Materials"]
    wh = data["Warehouses"]
    instock = slabs[slabs.status == "in_stock"].merge(mat[["material_id", "material_type"]], on="material_id")
    instock["sqft"] = instock.material_type.map(AVG_SQFT)
    util = instock.groupby("warehouse_id")["sqft"].sum().reindex(wh.warehouse_id).fillna(0)
    out = wh[["warehouse_id", "name", "sq_ft_capacity"]].copy()
    out["sqft_on_hand"] = out.warehouse_id.map(util)
    out["utilization_pct"] = out.sqft_on_hand / out.sq_ft_capacity * 100
    return out


def quarry_leadtime_reliability(data):
    cont = data["Containers"].dropna(subset=["actual_arrival_date"])
    po = data["Purchase_Orders"]
    qr = data["Quarries"]
    df = cont.merge(po[["po_id", "quarry_id"]], on="po_id").merge(qr[["quarry_id", "quarry_name", "country"]], on="quarry_id")
    df["delay_days"] = (df.actual_arrival_date - df.eta).dt.days
    g = df.groupby(["quarry_name", "country"]).agg(
        avg_delay=("delay_days", "mean"), delay_std=("delay_days", "std"), shipments=("delay_days", "count")
    ).reset_index()
    return g.sort_values("avg_delay", ascending=False)


def damage_rate_by_quarry(data):
    slabs = data["Slab_Inventory"]
    qr = data["Quarries"]
    df = slabs.merge(qr[["quarry_id", "quarry_name"]], on="quarry_id")
    g = df.groupby("quarry_name").agg(
        total_slabs=("slab_id", "count"),
        damaged=("status", lambda s: (s == "damaged").sum()),
    ).reset_index()
    g["damage_pct"] = g.damaged / g.total_slabs * 100
    return g.sort_values("damage_pct", ascending=False)


def open_purchase_orders(data):
    po = data["Purchase_Orders"]
    pol = data["PO_Lines"]
    qr = data["Quarries"]
    df = po[po.status != "Completed"].merge(qr[["quarry_id", "quarry_name"]], on="quarry_id")
    spend = pol.merge(po[["po_id", "quarry_id", "status"]], on="po_id")
    spend["line_cost"] = spend.qty_ordered_sqft * spend.unit_cost
    open_spend = spend[spend.status != "Completed"].groupby("po_id")["line_cost"].sum().reset_index()
    df = df.merge(open_spend, on="po_id", how="left")
    return df[["po_id", "quarry_name", "order_date", "expected_ship_date", "status", "line_cost"]]


def reorder_candidates(data, as_of, lookback_days=90):
    slabs = data["Slab_Inventory"]
    mat = data["Materials"]
    qr = data["Quarries"]
    sol = data["SO_Lines"]
    so = data["Sales_Orders"]

    sold = sol.merge(so[["sales_order_id", "order_date"]], on="sales_order_id").merge(
        slabs[["slab_id", "material_id"]], on="slab_id"
    )
    recent = sold[sold.order_date >= as_of - pd.Timedelta(days=lookback_days)]
    velocity = recent.groupby("material_id").size().rename("sold_last_90d")

    instock = slabs[slabs.status == "in_stock"].groupby("material_id").size().rename("in_stock_count")

    lead = slabs.merge(qr[["quarry_id", "transit_days_min", "transit_days_max"]] if "transit_days_min" in qr.columns else qr[["quarry_id"]], on="quarry_id", how="left")

    df = pd.concat([velocity, instock], axis=1).fillna(0).reset_index().rename(columns={"index": "material_id"})
    df = df.merge(mat[["material_id", "color_name", "material_type"]], on="material_id")
    df["daily_velocity"] = df.sold_last_90d / lookback_days
    df["days_of_supply"] = df.apply(lambda r: (r.in_stock_count / r.daily_velocity) if r.daily_velocity > 0 else 999, axis=1)
    return df.sort_values("days_of_supply").reset_index(drop=True)


def top_customers(data, n=10):
    so = data["Sales_Orders"]
    sol = data["SO_Lines"]
    cust = data["Customers"]
    df = so.merge(sol[["sales_order_id", "sale_price_total"]], on="sales_order_id").merge(
        cust[["customer_id", "company_name", "customer_type"]], on="customer_id"
    )
    g = df.groupby(["company_name", "customer_type"])["sale_price_total"].sum().reset_index()
    return g.sort_values("sale_price_total", ascending=False).head(n)


def revenue_concentration(data, top_n=10):
    so = data["Sales_Orders"]
    sol = data["SO_Lines"]
    cust = data["Customers"]
    df = so.merge(sol[["sales_order_id", "sale_price_total"]], on="sales_order_id").merge(
        cust[["customer_id", "company_name"]], on="customer_id"
    )
    g = df.groupby("company_name")["sale_price_total"].sum().sort_values(ascending=False)
    return g.head(top_n).sum() / g.sum() * 100


def rep_leaderboard(data, n=10):
    so = data["Sales_Orders"]
    sol = data["SO_Lines"]
    emp = data["Employees"]
    df = so.merge(sol[["sales_order_id", "sale_price_total"]], on="sales_order_id").merge(
        emp[["employee_id", "warehouse_id"]], on="employee_id"
    )
    g = df.groupby("employee_id").agg(revenue=("sale_price_total", "sum"), orders=("sales_order_id", "nunique")).reset_index()
    return g.sort_values("revenue", ascending=False).head(n)


def monthly_order_volume(data):
    so = data["Sales_Orders"]
    so2 = so.copy()
    so2["month"] = so2.order_date.dt.to_period("M").dt.to_timestamp()
    return so2.groupby("month").size().reset_index(name="order_count")


def overdue_containers(data, as_of):
    cont = data["Containers"]
    return cont[cont.actual_arrival_date.isna() & (cont.eta < as_of)]


def demand_trend_by_material(data, as_of, recent_months=3, prior_months=3):
    """
    Lightweight trend CLASSIFIER (not a statistical forecast) - compares recent sell-through
    velocity to the prior period per material/color and labels it accelerating/stable/declining.
    Framed honestly: with ~3 years of monthly data, a full time-series forecast model would
    overclaim; a trend signal is what the data actually supports.
    """
    sol = data["SO_Lines"]
    so = data["Sales_Orders"]
    slabs = data["Slab_Inventory"]
    mat = data["Materials"]

    sold = sol.merge(so[["sales_order_id", "order_date"]], on="sales_order_id").merge(
        slabs[["slab_id", "material_id"]], on="slab_id"
    )

    recent_start = as_of - pd.DateOffset(months=recent_months)
    prior_start = as_of - pd.DateOffset(months=recent_months + prior_months)

    recent = sold[sold.order_date >= recent_start].groupby("material_id").size().rename("recent_sold")
    prior = sold[(sold.order_date >= prior_start) & (sold.order_date < recent_start)].groupby("material_id").size().rename("prior_sold")

    df = pd.concat([recent, prior], axis=1).fillna(0).reset_index().rename(columns={"index": "material_id"})
    df = df.merge(mat[["material_id", "color_name", "material_type"]], on="material_id")

    def classify(row):
        if row.prior_sold == 0 and row.recent_sold == 0:
            return "No activity"
        if row.prior_sold == 0:
            return "Accelerating"
        change = (row.recent_sold - row.prior_sold) / row.prior_sold
        if change > 0.20:
            return "Accelerating"
        if change < -0.20:
            return "Declining"
        return "Stable"

    df["trend"] = df.apply(classify, axis=1)
    df["change_pct"] = df.apply(
        lambda r: ((r.recent_sold - r.prior_sold) / r.prior_sold * 100) if r.prior_sold > 0 else None, axis=1
    )
    return df.sort_values("recent_sold", ascending=False)


def monthly_sales_by_material_type(data):
    sol = data["SO_Lines"]
    so = data["Sales_Orders"]
    slabs = data["Slab_Inventory"]
    mat = data["Materials"]
    df = sol.merge(so[["sales_order_id", "order_date"]], on="sales_order_id").merge(
        slabs[["slab_id", "material_id"]], on="slab_id"
    ).merge(mat[["material_id", "material_type"]], on="material_id")
    df["month"] = df.order_date.dt.to_period("M").dt.to_timestamp()
    return df.groupby(["month", "material_type"]).size().reset_index(name="slabs_sold")


def week_over_week_delta(data, as_of):
    snap = data["Monthly_Inventory_Snapshot"]
    dates = sorted(snap.snapshot_date.unique())
    if len(dates) < 2:
        return None
    latest, prev = dates[-1], dates[-2]
    cur = snap[snap.snapshot_date == latest].inventory_value.sum()
    prior = snap[snap.snapshot_date == prev].inventory_value.sum()
    return dict(latest_period=latest, prior_period=prev, current_value=cur, prior_value=prior, delta=cur - prior)
