import os, json, urllib.request, datetime, pathlib

KEY = os.environ["ANTHROPIC_API_KEY"]

TOPICS = [
    "Networking", "Cloud", "Security",
    "DevOps", "Databases", "Linux", "Hardware"
]

today = datetime.date.today()
topic = TOPICS[today.toordinal() % len(TOPICS)]

prompt = f"""Write a 1200-word beginner-friendly IT tutorial
about a specific, useful {topic} topic that is trending in 2026.
Include:
- A clear SEO-friendly title
- Short introduction (2 paragraphs)
- 3-4 sections with h2 headings
- Practical step-by-step examples
- A summary section
Write in simple, helpful language for IT beginners and professionals.
Mark TWO spots where an affiliate link fits naturally by writing [AFFILIATE].
Output as clean HTML using only h1, h2, h3, p, ul, li, code, pre tags."""

body = json.dumps({
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 4000,
    "messages": [{"role": "user", "content": prompt}]
}).encode()

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=body,
    headers={
        "x-api-key": KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
)

response = json.load(urllib.request.urlopen(req))
article = response["content"][0]["text"]

pathlib.Path("drafts").mkdir(exist_ok=True)
filename = f"drafts/{today}-{topic.lower()}.html"
pathlib.Path(filename).write_text(article, encoding="utf-8")
print(f"Article written: {filename}")
