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


def generate_insight(facts: dict, instruction: str) -> str:
    """
    facts: a JSON-serializable dict of pre-computed numbers (the ONLY numbers Claude may use)
    instruction: what kind of insight to write (e.g. "top 3 supply chain risks today")
    Falls back to a deterministic templated summary if no API key is configured,
    so the dashboard is always demoable without exposing credentials.
    """
    client = _client()
    if client is None:
        return _fallback(facts, instruction)

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
    except Exception as e:
        return _fallback(facts, instruction, error=str(e))


def _fallback(facts: dict, instruction: str, error: str = None) -> str:
    note = "[Offline mode - set ANTHROPIC_API_KEY to enable live AI narration]\n\n" if error is None else \
           f"[AI call failed ({error}) - showing computed facts directly]\n\n"
    return note + json.dumps(facts, default=str, indent=2)
