import streamlit as st
import pandas as pd
from utils.data_loader import load_data
from utils.branding import show_logo
from utils.metrics import (
    reorder_candidates, quarry_leadtime_reliability, damage_rate_by_quarry,
    dead_stock_candidates, overdue_containers, week_over_week_delta
)
from utils.ai_insights import generate_insight

st.set_page_config(page_title="AI recommendation center", layout="wide")
show_logo()
data = load_data()

st.title("AI recommendation center")
st.caption(
    "Every panel below is generated from pre-computed facts (pandas), never raw table rows. "
    "Claude's job is narration and reasoning over those facts, not arithmetic."
)

if not st.session_state.get("_ai_key_notice_shown"):
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.info("No ANTHROPIC_API_KEY found in environment - showing computed facts directly. "
                "Set the key to enable live narrated insights.")
    st.session_state["_ai_key_notice_shown"] = True

as_of = data["Monthly_Inventory_Snapshot"].snapshot_date.max()

tab1, tab2, tab3 = st.tabs(["Top risks today", "Reorder recommendations", "What changed since last week"])

with tab1:
    st.subheader("Top risks today")
    lead = quarry_leadtime_reliability(data).head(5)
    dmg = damage_rate_by_quarry(data).head(5)
    overdue = overdue_containers(data, as_of)
    dead = dead_stock_candidates(data, as_of).head(5)

    facts = {
        "worst_leadtime_quarries": lead.to_dict(orient="records"),
        "worst_damage_quarries": dmg.to_dict(orient="records"),
        "overdue_container_count": len(overdue),
        "dead_stock_top5": dead.to_dict(orient="records"),
    }
    with st.spinner("Generating insight..."):
        insight = generate_insight(facts, "Summarize the top 3 supply chain risks today, ranked by severity, in plain language for a COO.")
    st.markdown(insight)

    with st.expander("Underlying computed facts"):
        st.json(facts)

with tab2:
    st.subheader("Reorder recommendations")
    reorder = reorder_candidates(data, as_of)
    urgent = reorder[reorder.days_of_supply < 999].sort_values("days_of_supply").head(8)
    facts2 = {"reorder_candidates": urgent.to_dict(orient="records")}
    with st.spinner("Generating insight..."):
        insight2 = generate_insight(
            facts2,
            "For each material below, explain why it needs reordering and roughly how urgent it is, "
            "based only on days_of_supply and sold_last_90d."
        )
    st.markdown(insight2)

    with st.expander("Underlying computed facts"):
        st.json(facts2)

with tab3:
    st.subheader("What changed since last week")
    delta = week_over_week_delta(data, as_of)
    if delta is None:
        st.write("Not enough snapshot history to compute a delta.")
    else:
        facts3 = delta
        with st.spinner("Generating insight..."):
            insight3 = generate_insight(
                facts3,
                "Explain the change in total inventory value between the two periods, in plain language."
            )
        st.markdown(insight3)
        with st.expander("Underlying computed facts"):
            st.json({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in facts3.items()})
