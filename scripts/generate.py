import os, json, urllib.request, pathlib, datetime, random

KEY = os.environ["ANTHROPIC_API_KEY"]

def claude(prompt, max_tokens=4000):
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
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
    res = json.load(urllib.request.urlopen(req, timeout=30))
    return res["content"][0]["text"].strip()

# High-traffic IT keywords mapped to topics
KEYWORD_POOL = [
    # Networking
    {"keyword": "what is DNS and how does it work", "topic": "Networking", "intent": "beginner"},
    {"keyword": "how does a VPN work explained simply", "topic": "Networking", "intent": "beginner"},
    {"keyword": "TCP IP model explained for beginners", "topic": "Networking", "intent": "beginner"},
    {"keyword": "what is a firewall and why do you need one", "topic": "Networking", "intent": "beginner"},
    {"keyword": "difference between HTTP and HTTPS", "topic": "Networking", "intent": "beginner"},
    # Cloud
    {"keyword": "what is cloud computing explained simply", "topic": "Cloud", "intent": "beginner"},
    {"keyword": "AWS vs Azure vs Google Cloud comparison 2026", "topic": "Cloud", "intent": "comparison"},
    {"keyword": "what is serverless computing beginner guide", "topic": "Cloud", "intent": "beginner"},
    {"keyword": "how to deploy website on AWS for free", "topic": "Cloud", "intent": "howto"},
    {"keyword": "what is Kubernetes and why use it", "topic": "Cloud", "intent": "beginner"},
    # Security
    {"keyword": "how to protect your website from hackers", "topic": "Security", "intent": "howto"},
    {"keyword": "what is two factor authentication and how it works", "topic": "Security", "intent": "beginner"},
    {"keyword": "difference between encryption and hashing", "topic": "Security", "intent": "beginner"},
    {"keyword": "what is zero trust security model", "topic": "Security", "intent": "beginner"},
    {"keyword": "how SSL certificates work explained simply", "topic": "Security", "intent": "beginner"},
    # DevOps
    {"keyword": "what is DevOps explained for beginners", "topic": "DevOps", "intent": "beginner"},
    {"keyword": "Docker tutorial for absolute beginners 2026", "topic": "DevOps", "intent": "tutorial"},
    {"keyword": "what is CI CD pipeline explained simply", "topic": "DevOps", "intent": "beginner"},
    {"keyword": "Git commands every developer should know", "topic": "DevOps", "intent": "tutorial"},
    {"keyword": "Kubernetes vs Docker what is the difference", "topic": "DevOps", "intent": "comparison"},
    # Databases
    {"keyword": "SQL vs NoSQL which database to choose", "topic": "Databases", "intent": "comparison"},
    {"keyword": "what is PostgreSQL beginner tutorial", "topic": "Databases", "intent": "tutorial"},
    {"keyword": "how does database indexing work simply explained", "topic": "Databases", "intent": "beginner"},
    {"keyword": "what is Redis and when to use it", "topic": "Databases", "intent": "beginner"},
    {"keyword": "MySQL vs PostgreSQL difference explained", "topic": "Databases", "intent": "comparison"},
    # Linux
    {"keyword": "Linux commands every beginner must know", "topic": "Linux", "intent": "tutorial"},
    {"keyword": "what is Linux and why developers use it", "topic": "Linux", "intent": "beginner"},
    {"keyword": "how to install Ubuntu step by step 2026", "topic": "Linux", "intent": "howto"},
    {"keyword": "Bash scripting for beginners complete guide", "topic": "Linux", "intent": "tutorial"},
    {"keyword": "what is SSH and how does it work", "topic": "Linux", "intent": "beginner"},
    # Hardware
    {"keyword": "how does a CPU work explained simply", "topic": "Hardware", "intent": "beginner"},
    {"keyword": "SSD vs HDD which is better 2026", "topic": "Hardware", "intent": "comparison"},
    {"keyword": "what is RAM and how much do you need", "topic": "Hardware", "intent": "beginner"},
    {"keyword": "how does a data center work explained", "topic": "Hardware", "intent": "beginner"},
    {"keyword": "difference between 32 bit and 64 bit processor", "topic": "Hardware", "intent": "beginner"},
]

def pick_keyword():
    # Avoid repeating recently used keywords
    used_file = pathlib.Path("drafts/.used_keywords.json")
    used = []
    if used_file.exists():
        try:
            used = json.loads(used_file.read_text())[-20:]  # last 20
        except Exception as e:
            print(f"Used keywords file corrupt, resetting: {e}")
            used = []

    available = [k for k in KEYWORD_POOL if k["keyword"] not in used]
    if not available:
        available = KEYWORD_POOL  # reset if all used

    chosen = random.choice(available)
    used.append(chosen["keyword"])
    pathlib.Path("drafts").mkdir(exist_ok=True)
    used_file.write_text(json.dumps(used))
    return chosen

def generate_article(kw):
    prompt = f"""You are an expert IT writer for ITVedas.com — a knowledge hub for people who know NOTHING about technology.

Your job: Write a COMPLETE, DETAILED article targeting this exact Google search keyword:
"{kw['keyword']}"

STRICT WRITING RULES:
1. Write like you are explaining to a 12-year-old or someone's grandmother — zero tech jargon without explanation
2. Every technical term MUST be explained with a real-world analogy (like "A DNS is like a phone book for the internet")
3. Use short sentences. Never write a sentence longer than 20 words.
4. Use "you" and "your" — make it personal and conversational
5. Include real examples people can relate to (Netflix, WhatsApp, Google, YouTube)

CONTENT STRUCTURE (follow exactly):
- One H1 title (include the keyword naturally, make it compelling)
- Meta description (160 chars max, include keyword, add to a comment at top)
- Introduction (2 paragraphs, hook the reader, explain WHY this matters to them personally)
- "What is [topic]?" section with H2 — use a simple real-world analogy
- "How does it work?" section with H2 — step by step, numbered list, simple language
- "Why does this matter to you?" section with H2 — real benefits for normal people
- "Real world example" section with H2 — walk through a specific scenario
- "Common questions answered" section with H2 — 3 FAQ items
- "Key takeaways" section with H2 — bullet points, 5 max
- Conclusion (1 paragraph, encouraging, tell them what to explore next on ITVedas)

SEO REQUIREMENTS:
- Use the keyword "{kw['keyword']}" in H1, first paragraph, and one H2
- Use related keywords naturally throughout
- Add schema markup hints as HTML comments
- Target word count: 1500-2000 words
- Use power words: "exactly", "simple", "proven", "complete", "step-by-step"

OUTPUT FORMAT:
Return ONLY clean HTML. Start with a comment containing meta data:
<!-- META
title: [your H1 title]
description: [160 char meta description]
keyword: {kw['keyword']}
topic: {kw['topic']}
-->

Then the full article HTML using: h1, h2, h3, p, ul, ol, li, strong, code, pre, blockquote tags only.
No html/head/body tags. Just the article content."""

    return claude(prompt, max_tokens=4000)

def main():
    kw = pick_keyword()
    print(f"Keyword: {kw['keyword']}")
    print(f"Topic: {kw['topic']}")

    content = generate_article(kw)

    pathlib.Path("drafts").mkdir(exist_ok=True)
    today = datetime.date.today()
    filename = f"drafts/{today}-{kw['topic'].lower()}.html"
    pathlib.Path(filename).write_text(content, encoding="utf-8")
    print(f"Draft saved: {filename}")

if __name__ == "__main__":
    main()
