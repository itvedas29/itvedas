#!/usr/bin/env python3
"""
Generate a complete sitemap.xml from all HTML files in the repository.
Scans articles/, news/, and root HTML files.
Intended to run as part of CI/CD to keep sitemap up-to-date.
"""

import pathlib
import datetime
import xml.etree.ElementTree as ET

SITE_URL = "https://itvedas.com"
ROOT = pathlib.Path(".")

def get_html_files():
    """Recursively find all HTML files and categorize them."""
    files = {
        "main": [],      # Root HTML files
        "chapters": [],  # Article category index pages
        "articles": [], # Individual article files
        "news": [],     # Individual news files
    }

    # Root HTML files (home, about, faq, etc.)
    for f in ROOT.glob("*.html"):
        if f.name not in ["cve-database.html", "cve-database-complete.html"]:
            files["main"].append(f)

    # Article category index pages (articles/networking/, articles/cloud/, etc.)
    for category_dir in (ROOT / "articles").glob("*/"):
        if category_dir.is_dir():
            index_file = category_dir / "index.html"
            if index_file.exists():
                files["chapters"].append(index_file)

    # Individual article files
    for article_file in (ROOT / "articles").rglob("*.html"):
        if article_file.name != "index.html":
            files["articles"].append(article_file)

    # Individual news files
    for news_file in (ROOT / "news").rglob("*.html"):
        if news_file.name != "index.html":
            files["news"].append(news_file)

    return files

def file_to_url(file_path):
    """Convert file path to URL."""
    rel_path = file_path.relative_to(ROOT)
    return f"{SITE_URL}/{rel_path.as_posix()}"

def get_file_modified_date(file_path):
    """Get file modification date in ISO format."""
    mtime = file_path.stat().st_mtime
    return datetime.datetime.fromtimestamp(mtime).date().isoformat()

def build_sitemap():
    """Build and write sitemap.xml."""
    today = datetime.date.today().isoformat()
    files = get_html_files()

    # Create root element
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Helper to add URL entry
    def add_url(loc, lastmod, changefreq, priority):
        url_elem = ET.SubElement(urlset, "url")
        loc_elem = ET.SubElement(url_elem, "loc")
        loc_elem.text = loc
        lastmod_elem = ET.SubElement(url_elem, "lastmod")
        lastmod_elem.text = lastmod
        freq_elem = ET.SubElement(url_elem, "changefreq")
        freq_elem.text = changefreq
        prio_elem = ET.SubElement(url_elem, "priority")
        prio_elem.text = str(priority)

    # Add homepage
    add_url(SITE_URL, today, "weekly", 1.0)

    # Add main pages (highest priority after homepage)
    priority_map = {
        "news.html": (0.9, "daily"),
        "security-news.html": (0.9, "daily"),
        "career-paths.html": (0.8, "monthly"),
        "career-navigator.html": (0.8, "monthly"),
        "chapters.html": (0.8, "weekly"),
        "quiz.html": (0.7, "monthly"),
        "faq.html": (0.7, "weekly"),
        "problems-solutions.html": (0.7, "monthly"),
        "about.html": (0.6, "monthly"),
        "privacy-policy.html": (0.5, "yearly"),
        "terms-of-service.html": (0.5, "yearly"),
    }

    for f in sorted(files["main"]):
        prio, freq = priority_map.get(f.name, (0.6, "monthly"))
        lastmod = get_file_modified_date(f)
        add_url(file_to_url(f), lastmod, freq, prio)

    # Add chapter/category index pages
    for f in sorted(files["chapters"]):
        lastmod = get_file_modified_date(f)
        add_url(file_to_url(f), lastmod, "weekly", 0.7)

    # Add individual articles (high priority but lower than categories)
    for f in sorted(files["articles"]):
        lastmod = get_file_modified_date(f)
        add_url(file_to_url(f), lastmod, "monthly", 0.8)

    # Add news articles (medium-high priority, updated frequently)
    for f in sorted(files["news"]):
        lastmod = get_file_modified_date(f)
        add_url(file_to_url(f), lastmod, "weekly", 0.7)

    # Write sitemap
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    sitemap_path = ROOT / "sitemap.xml"
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)

    total_urls = (len(files["main"]) + len(files["chapters"]) +
                  len(files["articles"]) + len(files["news"]))
    print(f"✓ Sitemap generated: {total_urls} URLs")
    print(f"  - Main pages: {len(files['main'])}")
    print(f"  - Categories: {len(files['chapters'])}")
    print(f"  - Articles: {len(files['articles'])}")
    print(f"  - News: {len(files['news'])}")

    return total_urls

if __name__ == "__main__":
    try:
        total = build_sitemap()
        print(f"Sitemap written to sitemap.xml")
        exit(0)
    except Exception as e:
        print(f"Error generating sitemap: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
