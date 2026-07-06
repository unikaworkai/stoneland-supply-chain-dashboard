import os
import json

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a supply chain analyst writing short, plain-language insights for Stoneland Inc, "
    "a B2B granite/marble/quartzite/quartz slab distributor. You are given a JSON block of "
    "PRE-COMPUTED facts (already correct, do not recompute or contradict them). Write a concise, "
    "specific insight grounded ONLY in the numbers provided. Never invent a number that is not in "
    "the facts. Keep it to 2-4 sentences per item. No preamble, no markdown headers."
)


def _client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not _HAS_ANTHROPIC:
        return None
    return anthropic.Anthropic(api_key=api_key)


def generate_insight(facts: dict, instruction: str, fallback_fn=None) -> str:
    """
    facts: a JSON-serializable dict of pre-computed numbers (the ONLY numbers Claude may use)
    instruction: what kind of insight to write
    fallback_fn: a function(facts) -> str that writes a real rule-based narrative when no
                 API key is configured, so the app never shows raw JSON to the user.
    """
    client = _client()
    if client is None:
        return _fallback(facts, fallback_fn)

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Instruction: {instruction}\n\nFacts (JSON):\n{json.dumps(facts, default=str, indent=2)}"
            }],
        )
        return "".join(b.text for b in msg.content if hasattr(b, "text"))
    except Exception:
        return _fallback(facts, fallback_fn)


def _fallback(facts: dict, fallback_fn) -> str:
    if fallback_fn is not None:
        return fallback_fn(facts)
    return json.dumps(facts, default=str, indent=2)


# ---------- Rule-based narrative generators (used when no API key is set) ----------

def narrate_top_risks(facts: dict) -> str:
    lines = []
    lead = facts.get("worst_leadtime_quarries", [])
    dmg = facts.get("worst_damage_quarries", [])
    overdue = facts.get("overdue_container_count", 0)
    dead = facts.get("dead_stock_top5", [])

    if lead:
        q = lead[0]
        lines.append(
            f"**Lead-time risk:** {q['quarry_name']} ({q['country']}) is running "
            f"{q['avg_delay']:.1f} days late on average across {q['shipments']} shipments — "
            f"the least reliable quarry in the network right now."
        )
    if dmg:
        q = dmg[0]
        lines.append(
            f"**Damage risk:** {q['quarry_name']} has a {q['damage_pct']:.1f}% damage rate "
            f"({q['damaged']} of {q['total_slabs']} slabs) — worth a quality conversation with this supplier."
        )
    if overdue:
        lines.append(f"**Logistics risk:** {overdue} container(s) are currently overdue (past their expected arrival date).")
    if dead:
        names = ", ".join(f"{d['color_name']} ({int(d['slab_count'])} slabs)" for d in dead[:3])
        lines.append(f"**Dead-stock risk:** {names} have been sitting unsold the longest — candidates for a markdown or discontinuation review.")

    return "\n\n".join(lines) if lines else "No significant risks detected in the current data."


def narrate_reorder(facts: dict) -> str:
    items = facts.get("reorder_candidates", [])
    if not items:
        return "No materials currently show a supply gap - inventory levels look healthy relative to demand."
    lines = []
    for r in items[:5]:
        lines.append(
            f"**{r['color_name']} ({r['material_type']})** — only {r['days_of_supply']:.0f} days of supply left "
            f"at the current sell-through rate ({r['sold_last_90d']:.0f} slabs sold in the last 90 days, "
            f"{r['in_stock_count']:.0f} left on hand). Recommend placing a reorder soon."
        )
    return "\n\n".join(lines)


def narrate_weekly_delta(facts: dict) -> str:
    if not facts:
        return "Not enough snapshot history to compute a week-over-week change yet."
    cur = facts.get("current_value", 0)
    prior = facts.get("prior_value", 0)
    delta = facts.get("delta", cur - prior)
    direction = "increased" if delta > 0 else "decreased"
    pct = (abs(delta) / prior * 100) if prior else 0
    return (
        f"Total inventory value {direction} by ${abs(delta):,.0f} ({pct:.1f}%) between "
        f"{facts.get('prior_period')} and {facts.get('latest_period')}, moving from "
        f"${prior:,.0f} to ${cur:,.0f}. This reflects the net effect of new receipts, sales, "
        f"transfers, and damage write-downs across all four warehouses in that period."
    )

