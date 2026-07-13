#!/usr/bin/env python3
"""
PHASE 6: Create AI tool comparison frameworks.
Generate comparison tables and decision matrices.
"""

import pathlib
import json

ROOT = pathlib.Path(".")

COMPARISON_FRAMEWORKS = {
    "ml-frameworks-comparison": {
        "title": "ML Frameworks Comparison",
        "description": "Compare popular machine learning frameworks",
        "frameworks": [
            {
                "name": "TensorFlow",
                "language": "Python",
                "learning_curve": "Moderate",
                "performance": "High",
                "community": "Large",
                "use_cases": "Deep Learning, Production Systems",
                "pros": "Flexible, production-ready, extensive ecosystem",
                "cons": "Steep learning curve for beginners"
            },
            {
                "name": "PyTorch",
                "language": "Python",
                "learning_curve": "Easy",
                "performance": "High",
                "community": "Large",
                "use_cases": "Research, Deep Learning",
                "pros": "Intuitive, strong research community, dynamic graphs",
                "cons": "Fewer production tools compared to TensorFlow"
            },
            {
                "name": "Scikit-learn",
                "language": "Python",
                "learning_curve": "Easy",
                "performance": "Moderate",
                "community": "Large",
                "use_cases": "Classical ML, Data Science",
                "pros": "Easy to learn, great documentation, good for beginners",
                "cons": "Limited to classical ML, not for deep learning"
            }
        ]
    },
    "cloud-ai-platforms": {
        "title": "Cloud AI Platforms Comparison",
        "description": "Compare major cloud AI and ML platforms",
        "platforms": [
            {
                "name": "Google Cloud AI",
                "pricing_model": "Pay-per-use",
                "ml_services": "Comprehensive",
                "ease_of_use": "Moderate",
                "best_for": "Research, AutoML, Big Data",
                "pros": "Advanced ML services, strong data capabilities",
                "cons": "Complex pricing, steep learning curve"
            },
            {
                "name": "AWS AI",
                "pricing_model": "Pay-per-use",
                "ml_services": "Comprehensive",
                "ease_of_use": "Moderate",
                "best_for": "Enterprise, Production systems",
                "pros": "Extensive services, market leader, wide adoption",
                "cons": "Large service portfolio can be overwhelming"
            },
            {
                "name": "Azure AI",
                "pricing_model": "Subscription/Pay-per-use",
                "ml_services": "Comprehensive",
                "ease_of_use": "Easy",
                "best_for": "Microsoft ecosystem, Enterprise",
                "pros": "Good integration with Microsoft services, Azure ML",
                "cons": "Best suited for Microsoft-centric organizations"
            }
        ]
    }
}

def generate_comparison_page(comp_key, comp_data):
    """Generate comparison page HTML."""
    title = comp_data['title']
    description = comp_data['description']

    # Determine which type of data we have
    if 'frameworks' in comp_data:
        items = comp_data['frameworks']
        item_type = 'Framework'
    else:
        items = comp_data['platforms']
        item_type = 'Platform'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — ITVedas</title>
    <meta name="description" content="{description}">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        h1 {{ font-size: 2rem; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 2rem 0; }}
        .comparison-table th, .comparison-table td {{ padding: 1rem; border: 1px solid #ddd; text-align: left; }}
        .comparison-table th {{ background: #f5f5f5; font-weight: 600; }}
        .comparison-table tbody tr:nth-child(even) {{ background: #fafafa; }}
        .comparison-table tbody tr:hover {{ background: #f0f0f0; }}
        .pros {{ color: #28a745; font-weight: 500; }}
        .cons {{ color: #dc3545; font-weight: 500; }}
        nav {{ margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <a href="/">Home</a> / <a href="/ai-tools/">AI Tools</a> / {title}
        </nav>

        <h1>{title}</h1>
        <p>{description}</p>

        <table class="comparison-table">
            <thead>
                <tr>
                    <th>{item_type} Name</th>
"""

    # Get all unique keys from first item
    first_item = items[0]
    keys = [k for k in first_item.keys()]

    for key in keys:
        if key != 'name' and key != 'pros' and key != 'cons':
            display_key = key.replace('_', ' ').title()
            html += f"                    <th>{display_key}</th>\n"

    html += """                </tr>
            </thead>
            <tbody>
"""

    for item in items:
        html += "                <tr>\n"
        html += f"                    <td><strong>{item.get('name', '')}</strong></td>\n"

        for key in keys:
            if key != 'name' and key != 'pros' and key != 'cons':
                value = item.get(key, '')
                html += f"                    <td>{value}</td>\n"

        html += "                </tr>\n"

    html += """            </tbody>
        </table>

        <h2>Detailed Analysis</h2>

"""

    for item in items:
        html += f"        <div style='margin: 2rem 0; padding: 1.5rem; border-left: 4px solid #0066cc;'>\n"
        html += f"            <h3>{item.get('name', '')}</h3>\n"

        if 'pros' in item:
            html += f"            <p><span class='pros'>✓ Pros:</span> {item.get('pros', '')}</p>\n"

        if 'cons' in item:
            html += f"            <p><span class='cons'>✗ Cons:</span> {item.get('cons', '')}</p>\n"

        html += "        </div>\n\n"

    html += """    </div>
</body>
</html>
"""

    return html

def main():
    """Create AI tool comparison pages."""
    print("✓ Creating AI tool comparison frameworks...\n")

    comparisons_dir = ROOT / "ai-tools" / "comparisons"
    comparisons_dir.mkdir(parents=True, exist_ok=True)

    comparison_count = 0

    for comp_key, comp_data in COMPARISON_FRAMEWORKS.items():
        comp_html = generate_comparison_page(comp_key, comp_data)
        comp_path = comparisons_dir / f"{comp_key}.html"

        with open(comp_path, 'w') as f:
            f.write(comp_html)

        comparison_count += 1
        title = comp_data['title']
        print(f"  ✓ Comparison page created: {title}")

    print(f"\n✓ AI tool comparison frameworks complete: {comparison_count} pages")

    return comparison_count

if __name__ == "__main__":
    count = main()
    exit(0)
