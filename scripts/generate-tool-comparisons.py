#!/usr/bin/env python3
"""
Generate AI tool comparison pages - side-by-side reviews of popular tool pairs
"""

import json
import pathlib

ROOT = pathlib.Path(".")
COMPARISONS_DIR = ROOT / "ai-tools" / "comparisons"
DATA_PATH = ROOT / "data" / "ai-tools-db.json"

# Load tool database
with open(DATA_PATH, 'r') as f:
    db = json.load(f)

# Build lookup for quick access
tools_lookup = {}
for category in db["tools"].values():
    for tool in category.get("tools", []):
        tools_lookup[tool["slug"]] = tool

# Popular comparisons to create
COMPARISONS = [
    {
        "title": "ChatGPT vs Claude",
        "description": "Compare OpenAI's ChatGPT with Anthropic's Claude",
        "slug": "chatgpt-vs-claude",
        "tool1_slug": "chatgpt",
        "tool2_slug": "claude"
    },
    {
        "title": "DALL-E vs Midjourney",
        "description": "Compare image generation capabilities",
        "slug": "dalle-vs-midjourney",
        "tool1_slug": "dall-e-3",
        "tool2_slug": "midjourney"
    },
    {
        "title": "GitHub Copilot vs Codeium",
        "description": "Compare AI coding assistants",
        "slug": "copilot-vs-codeium",
        "tool1_slug": "github-copilot",
        "tool2_slug": "codeium"
    },
    {
        "title": "Zapier vs Make",
        "description": "Compare workflow automation platforms",
        "slug": "zapier-vs-make",
        "tool1_slug": "zapier",
        "tool2_slug": "make-com"
    },
    {
        "title": "TensorFlow vs PyTorch",
        "description": "Compare deep learning frameworks",
        "slug": "tensorflow-vs-pytorch",
        "tool1_slug": "tensorflow",
        "tool2_slug": "pytorch"
    },
    {
        "title": "Synthesia vs HeyGen",
        "description": "Compare AI video generation platforms",
        "slug": "synthesia-vs-heygen",
        "tool1_slug": "synthesia",
        "tool2_slug": "heygen"
    },
    {
        "title": "Jasper vs Copy.ai",
        "description": "Compare AI writing assistants",
        "slug": "jasper-vs-copyai",
        "tool1_slug": "jasper",
        "tool2_slug": "copy-ai"
    },
    {
        "title": "Perplexity vs ChatGPT",
        "description": "Compare AI search capabilities",
        "slug": "perplexity-vs-chatgpt",
        "tool1_slug": "perplexity",
        "tool2_slug": "chatgpt"
    }
]

def generate_comparison_page(comp):
    """Generate a comparison page HTML."""
    tool1 = tools_lookup.get(comp["tool1_slug"])
    tool2 = tools_lookup.get(comp["tool2_slug"])

    if not tool1 or not tool2:
        return None

    title = comp["title"]
    slug = comp["slug"]

    # Build capabilities comparison
    caps1_html = "".join([f"<li>{c}</li>" for c in tool1.get("capabilities", [])])
    caps2_html = "".join([f"<li>{c}</li>" for c in tool2.get("capabilities", [])])

    # Build pros/cons
    pros1_html = "".join([f"<li>{p}</li>" for p in tool1.get("pros", [])])
    pros2_html = "".join([f"<li>{p}</li>" for p in tool2.get("pros", [])])
    cons1_html = "".join([f"<li>{c}</li>" for c in tool1.get("cons", [])])
    cons2_html = "".join([f"<li>{c}</li>" for c in tool2.get("cons", [])])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — ITVedas</title>
    <meta name="description" content="{comp['description']}. Detailed comparison of features, pricing, pros, cons, and use cases.">
    <meta name="keywords" content="{tool1['name']},{tool2['name']},comparison,review,vs">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{comp['description']}">
    <meta property="og:type" content="article">
    <link rel="canonical" href="https://itvedas.com/ai-tools/comparisons/{slug}/"/>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f9f9f9; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 2rem 1rem; }}
        header {{ background: #0066cc; color: white; padding: 2rem 0; margin-bottom: 2rem; }}
        header .container {{ padding: 2rem 1rem; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .breadcrumb {{ font-size: 0.9rem; opacity: 0.9; }}
        .breadcrumb a {{ color: rgba(255,255,255,0.8); text-decoration: none; }}
        .comparison-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0; }}
        .tool-card {{ background: white; padding: 1.5rem; border-radius: 0.5rem; }}
        .tool-header {{ margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid #0066cc; }}
        .tool-name {{ font-size: 1.4rem; font-weight: bold; margin-bottom: 0.25rem; }}
        .rating {{ color: #ffc107; font-weight: 500; margin: 0.5rem 0; }}
        .pricing {{ background: #f0f7ff; padding: 1rem; border-radius: 0.25rem; margin: 1rem 0; }}
        .section {{ margin: 1.5rem 0; }}
        .section h3 {{ font-size: 1.1rem; margin-bottom: 0.5rem; color: #0066cc; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 0.35rem 0 0.35rem 1.5rem; position: relative; }}
        li:before {{ content: "•"; position: absolute; left: 0; color: #0066cc; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 2rem 0; background: white; }}
        .comparison-table th, .comparison-table td {{ padding: 1rem; border: 1px solid #eee; text-align: left; }}
        .comparison-table th {{ background: #f5f5f5; font-weight: 600; }}
        .verdict {{ background: #f0f7ff; padding: 2rem; border-radius: 0.5rem; margin: 2rem 0; }}
        @media (max-width: 768px) {{
            .comparison-grid {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav class="breadcrumb">
                <a href="/">Home</a> / <a href="/ai-tools/">AI Tools</a> / Comparisons / {title}
            </nav>
            <h1>{title}</h1>
            <p>{comp['description']}</p>
        </div>
    </header>

    <main class="container">
        <div class="comparison-grid">
            <!-- Tool 1 -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-name">{tool1['name']}</div>
                    <p style="color: #666; margin: 0.25rem 0;">By {tool1['provider']}</p>
                    <div class="rating">⭐ {tool1['rating']}/5 ({tool1['reviews']:,} reviews)</div>
                </div>

                <div class="pricing">
                    <strong>Pricing:</strong> {tool1['pricing_model']}<br/>
                    {tool1['pricing']}
                </div>

                <div class="section">
                    <h3>Capabilities</h3>
                    <ul>{caps1_html}</ul>
                </div>

                <div class="section">
                    <h3>Pros</h3>
                    <ul>{pros1_html}</ul>
                </div>

                <div class="section">
                    <h3>Cons</h3>
                    <ul>{cons1_html}</ul>
                </div>

                <a href="/ai-tools/tools/{tool1['slug']}/" style="display: inline-block; background: #0066cc; color: white; padding: 0.75rem 1.5rem; border-radius: 0.25rem; text-decoration: none; margin-top: 1rem;">Full Review →</a>
            </div>

            <!-- Tool 2 -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-name">{tool2['name']}</div>
                    <p style="color: #666; margin: 0.25rem 0;">By {tool2['provider']}</p>
                    <div class="rating">⭐ {tool2['rating']}/5 ({tool2['reviews']:,} reviews)</div>
                </div>

                <div class="pricing">
                    <strong>Pricing:</strong> {tool2['pricing_model']}<br/>
                    {tool2['pricing']}
                </div>

                <div class="section">
                    <h3>Capabilities</h3>
                    <ul>{caps2_html}</ul>
                </div>

                <div class="section">
                    <h3>Pros</h3>
                    <ul>{pros2_html}</ul>
                </div>

                <div class="section">
                    <h3>Cons</h3>
                    <ul>{cons2_html}</ul>
                </div>

                <a href="/ai-tools/tools/{tool2['slug']}/" style="display: inline-block; background: #0066cc; color: white; padding: 0.75rem 1.5rem; border-radius: 0.25rem; text-decoration: none; margin-top: 1rem;">Full Review →</a>
            </div>
        </div>

        <!-- Verdict -->
        <div class="verdict">
            <h2>Verdict</h2>
            <p><strong>{tool1['name']}</strong> is best if you need {tool1.get('pros', [''])[0].lower()}</p>
            <p><strong>{tool2['name']}</strong> is best if you need {tool2.get('pros', [''])[0].lower()}</p>
        </div>

        <!-- Related Comparisons -->
        <section style="background: white; padding: 2rem; border-radius: 0.5rem; margin-top: 2rem;">
            <h2>Related Comparisons</h2>
            <p>Check out other AI tool comparisons in our guide:</p>
            <ul style="list-style: none; padding: 0; margin-top: 1rem;">
                <li><a href="/ai-tools/comparisons/">Browse all comparisons →</a></li>
            </ul>
        </section>
    </main>

    <footer style="background: #f5f5f5; padding: 2rem; margin-top: 3rem; text-align: center; color: #666; font-size: 0.9rem;">
        <p>&copy; 2026 ITVedas. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    return html

def main():
    """Generate all comparison pages."""
    COMPARISONS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating AI Tool Comparison Pages\n")

    generated = 0
    for comp in COMPARISONS:
        html = generate_comparison_page(comp)
        if html:
            comp_file = COMPARISONS_DIR / f"{comp['slug']}.html"
            with open(comp_file, 'w') as f:
                f.write(html)
            generated += 1
            print(f"✓ {comp['title']}")

    # Create comparison index
    comparisons_index = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tools Comparisons — ITVedas</title>
    <meta name="description" content="Side-by-side comparisons of popular AI tools. Compare features, pricing, pros and cons.">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f9f9f9; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}
        header {{ background: #0066cc; color: white; padding: 2rem 0; margin-bottom: 2rem; }}
        h1 {{ font-size: 2rem; }}
        .comparisons-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin: 2rem 0; }}
        .comparison-card {{ background: white; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #0066cc; }}
        .comparison-card a {{ color: #0066cc; text-decoration: none; font-weight: 500; }}
        .comparison-card a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav style="margin-bottom: 1rem; font-size: 0.9rem; color: rgba(255,255,255,0.8);">
                <a href="/" style="color: rgba(255,255,255,0.8); text-decoration: none;">Home</a> / AI Tools / Comparisons
            </nav>
            <h1>AI Tool Comparisons</h1>
            <p>Side-by-side comparisons of the most popular AI tools.</p>
        </div>
    </header>

    <main class="container">
        <div class="comparisons-grid">
"""

    for comp in COMPARISONS:
        comparisons_index += f"""        <div class="comparison-card">
            <h3><a href="/ai-tools/comparisons/{comp['slug']}/">{comp['title']}</a></h3>
            <p>{comp['description']}</p>
        </div>
"""

    comparisons_index += """        </div>
    </main>

    <footer style="background: #f5f5f5; padding: 2rem; margin-top: 3rem; text-align: center; color: #666; font-size: 0.9rem;">
        <p>&copy; 2026 ITVedas. All rights reserved.</p>
    </footer>
</body>
</html>
"""

    with open(COMPARISONS_DIR / "index.html", 'w') as f:
        f.write(comparisons_index)

    print(f"\n✓ Comparison pages generated: {generated}")
    print(f"✓ Index page created: /ai-tools/comparisons/")

if __name__ == "__main__":
    main()
