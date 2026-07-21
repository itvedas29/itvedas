#!/usr/bin/env python3
"""
PHASE 5: Enhance category overview pages with content listings.
Automatically generate article listings and category descriptions.
"""

import pathlib
import re
from datetime import datetime

ROOT = pathlib.Path(".")

CATEGORY_DESCRIPTIONS = {
    'cloud': 'Explore cloud computing fundamentals, architecture patterns, and deployment strategies across major cloud providers.',
    'networking': 'Master networking concepts, protocols, infrastructure design, and troubleshooting techniques.',
    'security': 'Comprehensive security knowledge covering threats, defense strategies, compliance, and incident response.',
    'devops': 'Learn DevOps practices, CI/CD automation, infrastructure as code, and containerization technologies.',
    'databases': 'Database design, optimization, administration, and best practices for relational and NoSQL systems.',
    'linux': 'Linux system administration, command-line proficiency, kernel concepts, and server management.',
    'hardware': 'Computer hardware components, server architecture, performance optimization, and capacity planning.',
    'compliance': 'Regulatory compliance frameworks, data protection, audit procedures, and security standards.',
    'powershell': 'PowerShell scripting, automation, system administration, and enterprise management.',
    'azure': 'Microsoft Azure platform services, architecture, migration strategies, and certification guidance.',
    'servers': 'Server technologies, management, optimization, and enterprise infrastructure patterns.',
    'iis': 'Internet Information Services configuration, security, and hosting best practices.',
    'sql-server': 'SQL Server database administration, optimization, security, and high availability solutions.',
    'cve': 'Security vulnerability analysis, CVE research, threat assessment, and remediation strategies.',
    'aiml-operations': 'AI/ML operations, model deployment, MLOps infrastructure, and production machine learning.',
    'azure-certifications': 'Azure certification preparation, study guides, and career development resources.',
    'cloud-security': 'Cloud security architecture, compliance, data protection, and threat mitigation.',
    'hybrid-multicloud': 'Hybrid cloud solutions, multi-cloud strategies, and cross-platform integration patterns.',
    'microsoft-365': 'Microsoft 365 services, SharePoint, Teams, Exchange, and enterprise collaboration.',
    'api': 'API design, development, security, and integration best practices.'
}

def get_category_pages(category_path):
    """Get all pages in a category."""
    pages = []
    if category_path.is_dir():
        for page_file in sorted(category_path.glob("*.html")):
            if page_file.name != "index.html":
                try:
                    content = page_file.read_text(encoding='utf-8')
                    title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
                    title = title_match.group(1).replace(' — ITVedas', '') if title_match else page_file.stem

                    pages.append({
                        'path': page_file,
                        'url': f"/{category_path.relative_to(ROOT).as_posix()}/{page_file.name}",
                        'title': title
                    })
                except Exception:
                    pass

    return pages

def generate_category_listing(category_name, category_path):
    """Generate HTML listing of category pages."""
    pages = get_category_pages(category_path)

    if not pages:
        return ""

    listing = '\n<!-- Category Content Listing -->\n'
    listing += '<div style="margin-top:3rem;padding:1.5rem;background:#f9f9f9;border-radius:0.5rem;">\n'
    listing += f'<h2>Articles in {category_name.replace("-", " ").title()}</h2>\n'
    listing += '<ul style="list-style:none;padding:0;">\n'

    for page in pages[:10]:  # Limit to first 10
        title = page['title'].replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        listing += f'<li style="margin:0.75rem 0;"><a href="{page["url"]}">{title}</a></li>\n'

    if len(pages) > 10:
        listing += f'<li style="margin-top:1rem;font-style:italic;">... and {len(pages) - 10} more articles</li>\n'

    listing += '</ul>\n</div>\n'

    return listing

def enhance_category_index(file_path, category_name):
    """Enhance category index page with content listing."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # Check if already has listing
        if '<!-- Category Content Listing -->' in content:
            return False

        # Get category description
        description = CATEGORY_DESCRIPTIONS.get(category_name, "")

        # Add description if missing
        if description and f"<p>{description}" not in content:
            desc_html = f'<p>{description}</p>\n\n'
            # Insert after H1
            h1_match = re.search(r'(</h1>)', content, re.IGNORECASE)
            if h1_match:
                insert_pos = h1_match.end()
                content = content[:insert_pos] + desc_html + content[insert_pos:]

        # Add content listing
        category_path = file_path.parent
        listing = generate_category_listing(category_name, category_path)
        if listing:
            # Insert before </article> or </body>
            article_match = re.search(r'(</article>)', content, re.IGNORECASE)
            if article_match:
                insert_pos = article_match.start(1)
            else:
                body_match = re.search(r'(</body>)', content, re.IGNORECASE)
                insert_pos = body_match.start(1) if body_match else len(content)

            content = content[:insert_pos] + listing + content[insert_pos:]

        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True

        return False
    except Exception as e:
        return False

def main():
    """Enhance category index pages."""
    enhanced_count = 0

    # Enhance article category pages
    for category_dir in (ROOT / "articles").iterdir():
        if category_dir.is_dir():
            index_file = category_dir / "index.html"
            if index_file.exists():
                if enhance_category_index(index_file, category_dir.name):
                    enhanced_count += 1

    # Enhance chapter category pages
    for category_dir in (ROOT / "chapters").iterdir():
        if category_dir.is_dir():
            index_file = category_dir / "index.html"
            if index_file.exists():
                if enhance_category_index(index_file, category_dir.name):
                    enhanced_count += 1

    print(f"✓ Category pages enhanced: {enhanced_count} pages")
    return enhanced_count

if __name__ == "__main__":
    count = main()
    exit(0)
