"""Small regression checks for traffic-safe sitemap discovery rules."""
from pathlib import Path
from traffic_recovery_sitemap import is_indexable_html, iter_ai_tools

ROOT = Path(__file__).resolve().parents[1]

assert is_indexable_html(ROOT / "tools" / "index.html")
ai_tools = list(iter_ai_tools(ROOT) or [])
assert ai_tools, "Expected AI tools to be discoverable"
print(f"Indexable AI-tool pages discovered: {len(ai_tools)}")
