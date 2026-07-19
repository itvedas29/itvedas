#!/usr/bin/env python3
"""
PHASE 1: Generate AI tool profile pages
Creates detailed HTML pages for each tool with schema markup and affiliate links
"""

import json
import pathlib
from datetime import datetime
import re

ROOT = pathlib.Path(".")
DATA_PATH = ROOT / "data" / "ai-tools-db.json"
TOOLS_DIR = ROOT / "ai-tools" / "tools"

def slugify(text):
    """Convert text to URL-safe slug."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def generate_schema_markup(tool, category_name):
    """Generate JSON-LD schema for tool."""
    schema = {
        "@context": "https://schema.org/",
        "@type": "SoftwareApplication",
        "name": tool["name"],
        "description": tool["description"],
        "applicationCategory": "Utility",
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": tool["pricing"].split()[0] if tool["pricing"] else "Contact for pricing"
        },
        "url": tool["url"],
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(tool["rating"]),
            "ratingCount": str(tool["reviews"])
        }
    }
    return json.dumps(schema, indent=2)

def generate_tool_profile_html(tool, category_name, category_slug):
    """Generate HTML page for a single tool."""
    title = f"{tool['name']} - AI Tool Review & Guide"
    description = f"Complete review and guide for {tool['name']}. Learn features, pricing, use cases, pros/cons, and alternatives."

    # Build capabilities section
    capabilities_html = "\n".join([
        f'                <div class="use-case-tag">{cap}</div>'
        for cap in tool.get("capabilities", [])
    ])

    # Build use cases section
    use_cases_html = "\n".join([
        f'                <div class="use-case-tag">{case}</div>'
        for case in tool.get("use_cases", [])
    ])

    # Build pros list
    pros_html = "\n".join([
        f'                    <li>{pro}</li>'
        for pro in tool.get("pros", [])
    ])

    # Build cons list
    cons_html = "\n".join([
        f'                    <li>{con}</li>'
        for con in tool.get("cons", [])
    ])

    # Build alternatives list
    alts_html = "\n".join([
        f'                <li><a href="#{slugify(alt)}">{alt}</a></li>'
        for alt in tool.get("alternatives", [])
    ])

    schema_markup = generate_schema_markup(tool, category_name)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — ITVedas</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{tool['name']},AI tool,review,comparison,pricing,features">

    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://itvedas.com/ai-tools/tools/{category_slug}/{tool['slug']}/"/>

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">

    <!-- Canonical -->
    <link rel="canonical" href="https://itvedas.com/ai-tools/tools/{category_slug}/{tool['slug']}/"/>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f9f9f9; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}
        header {{ background: white; border-bottom: 1px solid #eee; margin-bottom: 2rem; padding: 2rem 0; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .meta {{ color: #666; font-size: 0.95rem; }}
        .breadcrumb {{ margin-bottom: 1rem; font-size: 0.9rem; }}
        .breadcrumb a {{ color: #0066cc; text-decoration: none; }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        .rating {{ display: inline-block; background: #fff3cd; padding: 0.5rem 1rem; border-radius: 0.25rem; margin: 1rem 0; font-weight: 500; }}
        .cta-button {{ display: inline-block; background: #0066cc; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; margin: 1rem 0; font-weight: 500; }}
        .cta-button:hover {{ background: #0052a3; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin: 2rem 0; }}
        .info-card {{ background: white; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #0066cc; }}
        .info-card h3 {{ margin-bottom: 0.5rem; font-size: 1rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }}
        .info-card p {{ font-size: 1.1rem; font-weight: 500; }}
        .section {{ background: white; padding: 2rem; margin: 2rem 0; border-radius: 0.5rem; }}
        .section h2 {{ font-size: 1.8rem; margin-bottom: 1rem; border-bottom: 2px solid #0066cc; padding-bottom: 0.5rem; }}
        .pros {{ list-style: none; padding: 0; }}
        .pros li {{ padding: 0.5rem 0 0.5rem 2rem; position: relative; }}
        .pros li:before {{ content: "✓"; position: absolute; left: 0; color: #28a745; font-weight: bold; }}
        .cons {{ list-style: none; padding: 0; }}
        .cons li {{ padding: 0.5rem 0 0.5rem 2rem; position: relative; }}
        .cons li:before {{ content: "✗"; position: absolute; left: 0; color: #dc3545; font-weight: bold; }}
        .use-cases {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
        .use-case-tag {{ background: #e7f3ff; color: #0066cc; padding: 0.5rem 1rem; border-radius: 0.25rem; font-size: 0.9rem; }}
        @media (max-width: 768px) {{
            h1 {{ font-size: 1.8rem; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .section {{ padding: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav class="breadcrumb">
                <a href="/">Home</a> / <a href="/ai-tools/">AI Tools</a> / <a href="/ai-tools/tools/{category_slug}/">{category_name}</a> / {tool['name']}
            </nav>
            <h1>{tool['name']}</h1>
            <p class="meta">By {tool['provider']} • Founded {tool['founded']}</p>
            <div class="rating">
                ⭐ {tool['rating']}/5 ({tool['reviews']:,} reviews)
            </div>
            <a href="{tool['affiliate_url']}" class="cta-button" target="_blank" rel="noopener noreferrer">Try {tool['name']} →</a>
        </div>
    </header>

    <main class="container">
        <!-- Overview -->
        <section class="section">
            <h2>Overview</h2>
            <p>{tool['description']}</p>
        </section>

        <!-- Key Information -->
        <div class="info-grid">
            <div class="info-card">
                <h3>Pricing Model</h3>
                <p>{tool['pricing_model']}</p>
            </div>
            <div class="info-card">
                <h3>Price Range</h3>
                <p>{tool['pricing']}</p>
            </div>
            <div class="info-card">
                <h3>Provider</h3>
                <p>{tool['provider']}</p>
            </div>
        </div>

        <!-- Capabilities -->
        <section class="section">
            <h2>Key Capabilities</h2>
            <div class="use-cases">
{capabilities_html}
            </div>
        </section>

        <!-- Use Cases -->
        <section class="section">
            <h2>Best For</h2>
            <div class="use-cases">
{use_cases_html}
            </div>
        </section>

        <!-- Pros & Cons -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0;">
            <section class="section">
                <h2 style="color: #28a745;">Pros</h2>
                <ul class="pros">
{pros_html}
                </ul>
            </section>

            <section class="section">
                <h2 style="color: #dc3545;">Cons</h2>
                <ul class="cons">
{cons_html}
                </ul>
            </section>
        </div>

        <!-- Alternatives -->
        <section class="section">
            <h2>Alternatives</h2>
            <p>Comparing {tool['name']} to similar tools?</p>
            <ul style="margin-left: 2rem; margin-top: 1rem;">
{alts_html}
            </ul>
        </section>

        <!-- CTA -->
        <section class="section" style="background: #f0f7ff; text-align: center;">
            <h2>Ready to Get Started?</h2>
            <p>Try {tool['name']} today and see if it's the right fit for your needs.</p>
            <a href="{tool['affiliate_url']}" class="cta-button" target="_blank" rel="noopener noreferrer">Visit {tool['name']} →</a>
        </section>
    </main>

    <!-- JSON-LD Schema -->
    <script type="application/ld+json">
{schema_markup}
    </script>

    <footer style="background: #f5f5f5; padding: 2rem; margin-top: 3rem; text-align: center; color: #666; font-size: 0.9rem;">
        <p>&copy; 2026 ITVedas. All rights reserved.</p>
        <p><a href="/" style="color: #0066cc; text-decoration: none;">Home</a> | <a href="/ai-tools/" style="color: #0066cc; text-decoration: none;">AI Tools</a> | <a href="/about" style="color: #0066cc; text-decoration: none;">About</a></p>
    </footer>
</body>
</html>
"""
    return html

def generate_category_landing_page(category_name, category_slug, tools):
    """Generate category landing page with tool listings."""
    tools_html = ""
    for tool in tools:
        tools_html += f"""        <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #0066cc; margin-bottom: 1.5rem;">
            <h3><a href="/ai-tools/tools/{category_slug}/{tool['slug']}/">{tool['name']}</a></h3>
            <p style="color: #666; margin-bottom: 0.5rem;">{tool['description']}</p>
            <p style="font-size: 0.9rem;"><strong>Provider:</strong> {tool['provider']} | <strong>Pricing:</strong> {tool['pricing_model']} | ⭐ {tool['rating']}/5</p>
            <a href="/ai-tools/tools/{category_slug}/{tool['slug']}/" style="color: #0066cc; text-decoration: none; font-weight: 500;">View Full Review →</a>
        </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category_name} — AI Tools — ITVedas</title>
    <meta name="description" content="Comprehensive guide to {category_name.lower()}. Compare features, pricing, and find the best tool for your needs.">
    <meta name="keywords" content="AI tools,{category_slug},comparison,reviews,guide">
    <meta property="og:title" content="{category_name} — AI Tools">
    <meta property="og:description" content="Comprehensive guide to {category_name.lower()}.">
    <meta property="og:type" content="article">
    <link rel="canonical" href="https://itvedas.com/ai-tools/tools/{category_slug}/"/>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f9f9f9; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}
        header {{ background: white; border-bottom: 1px solid #eee; margin-bottom: 2rem; padding: 2rem 0; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .breadcrumb {{ font-size: 0.9rem; margin-bottom: 1rem; }}
        .breadcrumb a {{ color: #0066cc; text-decoration: none; }}
        h2 {{ font-size: 1.8rem; margin: 2rem 0 1rem 0; }}
        .section {{ background: white; padding: 2rem; margin: 2rem 0; border-radius: 0.5rem; }}
        @media (max-width: 768px) {{
            h1 {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav class="breadcrumb">
                <a href="/">Home</a> / <a href="/ai-tools/">AI Tools</a> / {category_name}
            </nav>
            <h1>{category_name}</h1>
        </div>
    </header>

    <main class="container">
        <section class="section">
            <h2>Featured Tools</h2>
            <p>Explore our comprehensive reviews of {len(tools)} tools in this category:</p>
{tools_html}
        </section>

        <section class="section">
            <h2>How to Choose</h2>
            <p>When selecting an AI tool, consider your specific needs, budget, and use case. Each tool has different strengths—review detailed comparisons on individual tool pages to find the best fit.</p>
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
    """Generate tool profile pages."""
    print("PHASE 1: Generating AI Tool Profile Pages\n")

    # Load database
    with open(DATA_PATH, 'r') as f:
        db = json.load(f)

    # Create tools directory
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Tools directory: {TOOLS_DIR}\n")

    total_tools = 0
    category_pages = 0

    # Generate category directories and tool pages
    for category_key, category_data in db["tools"].items():
        category_name = category_data["category_name"]
        category_slug = category_data["category_slug"]
        tools = category_data.get("tools", [])

        # Create category directory
        category_dir = TOOLS_DIR / category_slug
        category_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 {category_name} ({len(tools)} tools)")

        # Generate tool pages
        for tool in tools:
            tool_slug = tool["slug"]
            tool_file = category_dir / f"{tool_slug}.html"

            html = generate_tool_profile_html(tool, category_name, category_slug)

            with open(tool_file, 'w') as f:
                f.write(html)

            total_tools += 1

        # Generate category landing page
        category_landing = generate_category_landing_page(category_name, category_slug, tools)
        category_index = category_dir / "index.html"

        with open(category_index, 'w') as f:
            f.write(category_landing)

        category_pages += 1
        print(f"   ✓ Generated {len(tools)} tool pages + category landing\n")

    print(f"✓ Phase 1 Complete:")
    print(f"   - {total_tools} tool profile pages")
    print(f"   - {category_pages} category landing pages")
    print(f"   - Total pages: {total_tools + category_pages}")
    print(f"   - Location: {TOOLS_DIR}")

if __name__ == "__main__":
    main()
