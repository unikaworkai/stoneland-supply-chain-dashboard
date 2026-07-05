# Stoneland supply chain intelligence dashboard

An AI-powered supply chain and procurement dashboard built for Stoneland Inc,
a B2B granite/marble/quartzite/quartz slab distributor with 4 warehouses
(St. Louis, Springfield, Winchester, Nashville).

Portfolio project: internship-scoped enterprise-style dashboard demonstrating
supply chain analytics, procurement, inventory optimization, and AI-generated
insights on realistic synthetic data.

## Structure

```
app.py                          Home page
pages/
  1_Executive_Overview.py       Inventory value, margin, revenue trends
  2_Inventory_Warehouse_Ops.py  Aging, capacity, transfers, damage
  3_Procurement_Supplier_Performance.py   Open POs, quarry reliability, spend
  4_Sales_Customers.py          Top accounts, rep leaderboard, order trends
  5_AI_Recommendation_Center.py Reorder suggestions, risk summary, week-over-week delta
utils/
  data_loader.py                Cached load of the 15-sheet workbook
  metrics.py                    All deterministic pandas calculations
  ai_insights.py                Claude API narration layer with offline fallback
data/
  Stoneland_Supply_Chain_Data.xlsx   15-table synthetic dataset (3 years, ~9,400 slabs)
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Enabling live AI insights

The AI Recommendation Center works out of the box in "offline mode" (shows the
computed facts directly) so the dashboard is always demoable without a key.

To enable live narrated insights, set your own Anthropic API key before launching:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run app.py
```

Every AI panel follows the same pattern: Python computes the actual numbers first
(pandas, deterministic, no LLM involved), then Claude is given only that
pre-computed JSON and asked to narrate/reason over it - never given raw table
rows, so it cannot invent a number that isn't already correct.

## Data model

15 tables covering master data (warehouses, quarries, materials, customers,
employees), the procurement/import chain (purchase orders, PO lines, containers,
receiving log), physical inventory (slab-level, not SKU-quantity - each slab is
a unique physical unit), sales (orders and slab-specific line items), movement/
exceptions (transfers, damage log), and an analytics layer (monthly inventory
snapshot for aging/valuation). See the ERD from project planning for full
column-level detail.
