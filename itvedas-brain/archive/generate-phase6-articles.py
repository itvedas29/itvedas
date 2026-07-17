#!/usr/bin/env python3
"""
Phase 6 Comprehensive Article Generator
Generates 11 articles for Microsoft 365, Azure Certifications, Cloud Security, Hybrid/Multi-Cloud, AI/ML
Uses Claude API with optimized prompts and structured output
"""

import os
import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
import anthropic

# Configuration
ARTICLE_DIRECTORY = Path("chapters")
MIN_WORD_COUNT = 2500
MAX_WORD_COUNT = 4500
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable not set")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Article configuration from Phase 6 content calendar
ARTICLES_TO_GENERATE = [
    {
        "id": "m365_teams_governance",
        "chapter": "microsoft-365",
        "title": "Microsoft Teams Governance, Security & Compliance",
        "difficulty": "Advanced",
        "reading_time": 14,
        "date": "2026-07-05",
        "outline": [
            "Teams Architecture: Channels, Conversations, Teams Across Organization",
            "Governance Framework: Naming Policies, Approval Workflows, Access Control",
            "Security: Encryption, Data Loss Prevention (DLP), Conditional Access",
            "Compliance: Retention Policies, Legal Hold, eDiscovery",
            "Best Practices: Lifecycle Management, Archiving, Team Health",
            "Troubleshooting: Common Issues, Monitoring, Performance Tuning"
        ],
        "topics": ["Teams", "Microsoft 365", "Governance", "Security", "Compliance"],
    },
    {
        "id": "m365_sharepoint_governance",
        "chapter": "microsoft-365",
        "title": "SharePoint Online Architecture & Governance at Scale",
        "difficulty": "Advanced",
        "reading_time": 15,
        "date": "2026-07-05",
        "outline": [
            "SharePoint Architecture: Hub Sites, Site Collections, Tenant Structure",
            "Site Governance: Naming Conventions, Approval Workflows, Lifecycle",
            "Information Architecture: Taxonomy, Metadata, Navigation",
            "Security & Permissions: Sites, Lists, Item-Level Permissions",
            "Data Management: Retention, Classification, Compliance",
            "Modern vs. Classic: Migration Strategy, Feature Parity",
            "Performance & Optimization: CDN, Caching, Query Tuning"
        ],
        "topics": ["SharePoint", "Microsoft 365", "Information Architecture", "Governance"],
    },
    {
        "id": "m365_exchange_hybrid",
        "chapter": "microsoft-365",
        "title": "Exchange Online & Hybrid Architecture Patterns",
        "difficulty": "Advanced",
        "reading_time": 13,
        "date": "2026-07-06",
        "outline": [
            "Exchange Online Architecture: Mailboxes, Routing, Federation",
            "Hybrid Deployments: Synchronization, Routing, Coexistence",
            "Migration Strategies: Staged, Cutover, Hybrid Migration Wizard",
            "Security: Encryption, DLP, Advanced Threat Protection",
            "Compliance: Retention, Hold, eDiscovery",
            "Monitoring & Troubleshooting: Health Dashboard, Message Tracking",
            "Performance Tuning: Connection Health, Mailbox Quotas"
        ],
        "topics": ["Exchange", "Hybrid", "Email", "Migration"],
    },
    {
        "id": "azure_fundamentals_az900",
        "chapter": "azure-certifications",
        "title": "Azure Fundamentals (AZ-900) Complete Study Guide",
        "difficulty": "Beginner",
        "reading_time": 12,
        "date": "2026-07-06",
        "outline": [
            "Cloud Concepts: What is Cloud, Benefits, Types of Cloud Services",
            "Azure Services: Compute, Storage, Database, Network, Analytics",
            "Azure Pricing & Support: Cost Management, Support Plans, SLA",
            "Exam Structure: Question Types, Time Management, Passing Score",
            "Study Tips: Best Resources, Practice Tests, Time Investment",
            "Key Concepts for Success: Terminology, Common Pitfalls",
            "Practice Questions & Answers: 30+ sample questions"
        ],
        "topics": ["Azure", "Certification", "AZ-900", "Exam Prep"],
    },
    {
        "id": "azure_admin_az104",
        "chapter": "azure-certifications",
        "title": "Azure Administrator (AZ-104) Study Path",
        "difficulty": "Intermediate",
        "reading_time": 16,
        "date": "2026-07-07",
        "outline": [
            "Virtual Machines: Creation, Sizing, Networking, Storage",
            "Azure Networking: VNets, Subnets, Route Tables, Load Balancers",
            "Storage: Blobs, Files, Queues, Table Storage, Accounts",
            "Identity & Access: Azure AD, RBAC, Managed Identities",
            "Compute Services: App Service, Function Apps, Container Instances",
            "Monitoring & Backup: Monitor, Log Analytics, Backup, Recovery",
            "Governance & Compliance: Policies, Subscriptions, Resource Groups",
            "Exam Strategy: Time Management, Difficult Topics, Lab Practice"
        ],
        "topics": ["Azure", "Certification", "AZ-104", "Administration"],
    },
    {
        "id": "azure_architect_az305",
        "chapter": "azure-certifications",
        "title": "Azure Solutions Architect (AZ-305) Deep Dive",
        "difficulty": "Advanced",
        "reading_time": 17,
        "date": "2026-07-08",
        "outline": [
            "Design Principles: Scalability, Availability, Security, Cost Optimization",
            "Compute Architecture: VMs vs. App Service vs. Serverless Patterns",
            "Data Architecture: Database Selection, Data Lake, Data Warehouse",
            "Network Design: Hub-Spoke, Multi-Region, Disaster Recovery",
            "Security Architecture: Defense in Depth, Encryption, Identity",
            "Migration Patterns: Lift-and-Shift, Refactor, Rearchitect, Rebuild",
            "Case Studies: E-Commerce Platform, Healthcare System, Financial Services",
            "Exam Strategy: Scenario Analysis, Design Thinking, Trade-offs"
        ],
        "topics": ["Azure", "Certification", "AZ-305", "Solution Architecture"],
    },
    {
        "id": "cloud_security_framework",
        "chapter": "cloud-security",
        "title": "Cloud Security Framework: Defense in Depth Strategy",
        "difficulty": "Advanced",
        "reading_time": 14,
        "date": "2026-07-05",
        "outline": [
            "Security Layers: Perimeter, Network, Compute, Data, Application, Identity",
            "Threat Modeling: STRIDE, Attack Trees, Common Attack Patterns",
            "Defense in Depth: Multiple Controls, Redundancy, Resilience",
            "Network Security: NACLs, Security Groups, DDoS Protection, WAF",
            "Application Security: OWASP Top 10, Secure Coding, SAST/DAST",
            "Data Security: Encryption at Rest/Transit, Tokenization, Masking",
            "Identity & Access: MFA, RBAC, Privileged Access, Just-in-Time",
            "Incident Response: Detection, Containment, Eradication, Recovery",
            "Best Practices: Least Privilege, Separation of Duties, Monitoring"
        ],
        "topics": ["Security", "Cloud", "Architecture", "Defense"],
    },
    {
        "id": "compliance_frameworks",
        "chapter": "cloud-security",
        "title": "Compliance Frameworks: HIPAA, GDPR, SOC 2, PCI-DSS",
        "difficulty": "Advanced",
        "reading_time": 13,
        "date": "2026-07-08",
        "outline": [
            "Compliance Overview: Regulatory Requirements, Standards, Certifications",
            "HIPAA: Protected Health Information (PHI), HITRUST, Audit Requirements",
            "GDPR: Data Protection, Privacy by Design, Data Subject Rights",
            "SOC 2: Trust Service Criteria, Audit Process, Attestation",
            "PCI-DSS: Payment Card Security, Requirements, Validation",
            "Cloud Compliance: Shared Responsibility, Assessment, Monitoring",
            "Compliance Automation: Policy as Code, Continuous Compliance",
            "Case Studies: Compliance in Cloud Migration, Multi-Region Deployment",
            "Tools & Resources: Compliance Dashboards, Assessment Tools"
        ],
        "topics": ["Compliance", "Regulations", "Security", "Governance"],
    },
    {
        "id": "hybrid_architecture",
        "chapter": "hybrid-multicloud",
        "title": "Hybrid Cloud Architecture: On-Premises to Azure Integration",
        "difficulty": "Advanced",
        "reading_time": 14,
        "date": "2026-07-09",
        "outline": [
            "Hybrid Architecture Patterns: Hub-Spoke, Mesh, Islands",
            "Connectivity: Site-to-Site VPN, ExpressRoute, Hybrid Runbook Worker",
            "Identity Hybrid: Azure AD Connect, Pass-Through Auth, Federation",
            "Data Synchronization: Azure AD Sync, DFS, Hybrid File Sync",
            "Application Integration: Service Bus, Event Grid, Logic Apps",
            "Disaster Recovery: Failover Scenarios, RTO/RPO Targets",
            "Monitoring Across Environments: Unified Monitoring, Dashboards",
            "Best Practices: Network Design, Security, Performance",
            "Migration Path: Step-by-Step Transition Strategy"
        ],
        "topics": ["Hybrid", "Azure", "On-Premises", "Integration"],
    },
    {
        "id": "multicloud_strategy",
        "chapter": "hybrid-multicloud",
        "title": "Multi-Cloud Strategy: Azure, AWS, GCP Interoperability",
        "difficulty": "Advanced",
        "reading_time": 13,
        "date": "2026-07-09",
        "outline": [
            "Multi-Cloud Overview: Benefits, Challenges, Use Cases",
            "Azure-AWS Interoperability: Networking, Identity, Data Transfer",
            "Azure-GCP Patterns: Workload Distribution, Vendor Lock-In Prevention",
            "Cost Optimization Across Clouds: Reserved Instances, Committed Use",
            "Unified Monitoring: Cross-Cloud Dashboards, Alerting",
            "Application Portability: Containers, Kubernetes, Microservices",
            "Data Strategy: Multi-Cloud Data Lakes, Replication",
            "Governance: Policy Enforcement, Compliance Across Providers",
            "Case Studies: Real-World Multi-Cloud Deployments"
        ],
        "topics": ["Multi-Cloud", "Cloud Strategy", "Architecture", "Interoperability"],
    },
    {
        "id": "mlops_fundamentals",
        "chapter": "aiml-operations",
        "title": "MLOps Fundamentals: ML Pipeline Automation & Governance",
        "difficulty": "Advanced",
        "reading_time": 14,
        "date": "2026-07-10",
        "outline": [
            "MLOps Concepts: ML Lifecycle, Automation, Reproducibility",
            "ML Pipeline: Data Preparation, Model Training, Validation, Deployment",
            "Model Registry: Version Control, Metadata, Experiment Tracking",
            "CI/CD for ML: Automated Testing, Retraining, Deployment Automation",
            "Monitoring ML Models: Accuracy Drift, Data Drift, Performance",
            "Responsible AI: Fairness, Interpretability, Transparency, Bias Detection",
            "Tools & Platforms: Azure ML, MLflow, Kubeflow, DVC",
            "Best Practices: Reproducibility, Governance, Collaboration",
            "Case Studies: Production ML Systems at Scale"
        ],
        "topics": ["MLOps", "AI/ML", "Automation", "DevOps"],
    },
]

def generate_article_content(article_info: dict) -> str:
    """Generate comprehensive article content using Claude API"""

    outline_text = "\n".join([f"- {point}" for point in article_info["outline"]])

    prompt = f"""You are a senior IT architect and technical writer. Write a comprehensive, production-quality technical article.

Title: {article_info['title']}
Difficulty Level: {article_info['difficulty']}
Target Word Count: {MIN_WORD_COUNT}-{MAX_WORD_COUNT} words

Article Outline:
{outline_text}

Requirements:
1. Write in professional, educational tone similar to Microsoft Learn, AWS Documentation, or Cisco Learn
2. Include practical examples and real-world scenarios
3. Use technical accuracy and vendor-neutral language where appropriate
4. Include at least 3 detailed code examples or configuration snippets where relevant
5. Include enterprise best practices and common mistakes to avoid
6. Provide at least 2 reference tables or checklists
7. End with a comprehensive summary and learning path recommendations
8. Make content evergreen and not time-dependent

Structure your response as follows:

## Introduction
[2-3 paragraphs introducing the topic, its importance, and what readers will learn]

## Core Concepts
[Deep dive into fundamental concepts, with clear explanations]

## Architecture & Design
[Detailed architecture patterns and design principles]

## Implementation
[Step-by-step implementation guidance with examples]

## Best Practices
[Industry best practices and lessons learned]

## Common Mistakes
[Frequent errors and how to avoid them]

## Enterprise Scenarios
[Real-world use cases and case studies]

## Troubleshooting & Monitoring
[Operational considerations and monitoring strategies]

## FAQ & Glossary
[Frequently asked questions and key terminology]

## Summary & Next Steps
[Recap and recommended learning paths]

Write the full article now, ensuring it meets the word count requirement and covers all outline points thoroughly."""

    print(f"Generating: {article_info['title']}...")

    message = client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=6000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text

def create_html_file(article_info: dict, content: str, word_count: int) -> str:
    """Create a production-ready HTML file for the article"""

    date_obj = datetime.strptime(article_info["date"], "%Y-%m-%d")
    formatted_date = date_obj.strftime("%B %d, %Y")

    # Create filename
    slug = re.sub(r'[^a-z0-9-]+', '-', article_info['title'].lower()).strip('-')
    filename = f"{article_info['date']}-{slug}.html"

    # Convert markdown-style content to HTML
    html_content = convert_content_to_html(content, article_info, word_count, formatted_date)

    # Create chapter directory if needed
    chapter_dir = ARTICLE_DIRECTORY / article_info["chapter"]
    chapter_dir.mkdir(parents=True, exist_ok=True)

    filepath = chapter_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ Created: {filepath}")
    return str(filepath)

def convert_content_to_html(content: str, article_info: dict, word_count: int, formatted_date: str) -> str:
    """Convert article content to production HTML"""

    # Clean and format content
    content_html = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
    content_html = f"<p>{content_html}</p>"

    # Build metadata
    topics_meta = ", ".join(article_info["topics"])

    # HTML template
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{article_info['title']} — ITVedas</title>
<meta name="description" content="Comprehensive guide on {article_info['title']}. Learn enterprise best practices, architecture patterns, and real-world implementation strategies.">
<meta name="keywords" content="{topics_meta}, IT knowledge, enterprise architecture, technical guide">
<meta property="og:title" content="{article_info['title']} — ITVedas">
<meta property="og:description" content="Master {article_info['title']} with professional-grade documentation.">
<meta property="og:type" content="article">
<meta property="og:url" content="https://itvedas.com/chapters/{article_info['chapter']}/{article_info['date']}-{re.sub(r'[^a-z0-9-]+', '-', article_info['title'].lower()).strip('-')}.html">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://itvedas.com/chapters/{article_info['chapter']}/{article_info['date']}-{re.sub(r'[^a-z0-9-]+', '-', article_info['title'].lower()).strip('-')}.html">
<link rel="alternate" hreflang="x-default" href="https://itvedas.com/chapters/{article_info['chapter']}/index.html">
<link rel="alternate" hreflang="en" href="https://itvedas.com/chapters/{article_info['chapter']}/index.html">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{article_info['title']}",
  "description": "Professional guide on {article_info['title']}",
  "datePublished": "{article_info['date']}",
  "dateModified": "{article_info['date']}",
  "author": {{
    "@type": "Organization",
    "name": "ITVedas"
  }},
  "keywords": "{topics_meta}"
}}
</script>

<script async src="https://www.googletagmanager.com/gtag/js?id=G-D98BFZSJYP"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-D98BFZSJYP');</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#07070C; --bg2:#0E0E17; --bg3:#161624;
  --text:#F2F2FA; --sub:#C8C8E0; --muted:#9C9CBE;
  --accent:#FF6B35; --accent2:#8B5CF6; --cyan:#06B6D4; --green:#10B981;
  --border:rgba(255,255,255,0.09); --radius:16px;
  --font-display:'Space Grotesk',sans-serif; --font-body:'Inter',sans-serif;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}
body {{ background:var(--bg); color:var(--text); font-family:var(--font-body); font-size:16px; line-height:1.7; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.article-container {{ max-width:860px; margin:0 auto; padding:3rem 2rem; }}
.article-header {{ margin-bottom:3rem; }}
.article-title {{ font-size:2.2rem; font-weight:800; margin-bottom:1rem; color:var(--text); }}
.article-meta {{ display:flex; gap:1.5rem; margin-bottom:1rem; font-size:0.9rem; color:var(--muted); flex-wrap:wrap; }}
.meta-badge {{ background:rgba(255,107,53,0.1); color:var(--accent); padding:0.4rem 0.8rem; border-radius:20px; }}
.article-content {{ font-size:1.05rem; line-height:1.8; color:var(--sub); }}
.article-content p {{ margin-bottom:1.5rem; }}
.article-content h2 {{ font-size:1.8rem; font-weight:700; margin:2rem 0 1rem; color:var(--text); }}
.article-content h3 {{ font-size:1.3rem; font-weight:600; margin:1.5rem 0 0.75rem; color:var(--accent2); }}
.article-content code {{ background:var(--bg3); color:var(--cyan); padding:0.2rem 0.5rem; border-radius:4px; font-family:monospace; }}
.article-content pre {{ background:var(--bg3); border:1px solid var(--border); padding:1.5rem; border-radius:8px; overflow-x:auto; margin:1.5rem 0; }}
.article-content pre code {{ background:none; color:var(--cyan); padding:0; }}
.article-content ul, .article-content ol {{ margin:1rem 0 1.5rem 2rem; }}
.article-content li {{ margin-bottom:0.5rem; }}
.table-wrap {{ overflow-x:auto; margin:1.5rem 0; }}
.article-content table {{ width:100%; border-collapse:collapse; margin:1.5rem 0; }}
.article-content th {{ background:var(--bg3); color:var(--text); padding:0.75rem; text-align:left; font-weight:600; }}
.article-content td {{ border-bottom:1px solid var(--border); padding:0.75rem; }}
.reading-time {{ color:var(--muted); font-size:0.95rem; }}
footer {{ border-top:1px solid var(--border); margin-top:3rem; padding-top:2rem; text-align:center; color:var(--muted); }}
</style>
</head>
<body>
<article class="article-container">
  <header class="article-header">
    <h1 class="article-title">{article_info['title']}</h1>
    <div class="article-meta">
      <span class="meta-badge">{article_info['difficulty']}</span>
      <span class="reading-time">{article_info['reading_time']} min read</span>
      <span class="reading-time">{word_count} words</span>
      <span class="reading-time">{formatted_date}</span>
    </div>
  </header>

  <div class="article-content">
{content_html}
  </div>
</article>

<footer>
  <p>&copy; 2026 <a href="/">ITVedas</a> — IT Education for Everyone</p>
  <p><a href="/chapters/{article_info['chapter']}/">← Back to {article_info['chapter'].replace('-', ' ').title()}</a></p>
</footer>
</body>
</html>"""

    return html

def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())

def main():
    """Main generation pipeline"""
    print("=" * 60)
    print("ITVedas Phase 6 Article Generator")
    print("=" * 60)
    print()

    generated_articles = []
    failed_articles = []

    for i, article_info in enumerate(ARTICLES_TO_GENERATE, 1):
        try:
            print(f"\n[{i}/{len(ARTICLES_TO_GENERATE)}] {article_info['title']}")

            # Generate content
            content = generate_article_content(article_info)
            word_count = count_words(content)

            if word_count < MIN_WORD_COUNT:
                print(f"  ⚠ Warning: Word count {word_count} is below target {MIN_WORD_COUNT}")

            # Create HTML file
            filepath = create_html_file(article_info, content, word_count)

            generated_articles.append({
                "id": article_info["id"],
                "title": article_info["title"],
                "chapter": article_info["chapter"],
                "filepath": filepath,
                "word_count": word_count,
                "reading_time": article_info["reading_time"]
            })

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            failed_articles.append(article_info["title"])

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)
    print(f"Successfully generated: {len(generated_articles)}/{len(ARTICLES_TO_GENERATE)}")
    print(f"Failed: {len(failed_articles)}")

    if generated_articles:
        total_words = sum(a["word_count"] for a in generated_articles)
        print(f"Total words: {total_words}")
        print("\nGenerated articles:")
        for article in generated_articles:
            print(f"  ✓ {article['title']} ({article['word_count']} words)")

    if failed_articles:
        print("\nFailed articles:")
        for title in failed_articles:
            print(f"  ✗ {title}")

    return len(failed_articles) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
