#!/usr/bin/env python3
"""
Phase 6 Article Publisher
Generates, formats, and publishes 11 Phase 6 articles to website
"""

import os
import json
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from core.llm import claude as _core_claude
from core.log import log as _core_log

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"
SITE = "https://itvedas.com"
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

ARTICLES = [
    {
        "id": "m365_teams_governance",
        "title": "Microsoft Teams Governance, Security & Compliance",
        "chapter": "microsoft-365",
        "color": "#0078D4",
        "outline": [
            "Teams Architecture: Channels, Conversations, Teams Across Org",
            "Governance Framework: Naming Policies, Approval Workflows, Access Control",
            "Security: Encryption, Data Loss Prevention (DLP), Conditional Access",
            "Compliance: Retention Policies, Legal Hold, eDiscovery",
            "Best Practices: Lifecycle Management, Archiving, Team Health",
            "Troubleshooting: Common Issues, Monitoring, Performance Tuning"
        ]
    },
    {
        "id": "m365_sharepoint_governance",
        "title": "SharePoint Online Architecture & Governance at Scale",
        "chapter": "microsoft-365",
        "color": "#0078D4",
        "outline": [
            "SharePoint Architecture: Hub Sites, Site Collections, Tenant Structure",
            "Site Governance: Naming Conventions, Approval Workflows, Lifecycle",
            "Information Architecture: Taxonomy, Metadata, Navigation",
            "Security & Permissions: Sites, Lists, Item-Level Permissions",
            "Data Management: Retention, Classification, Compliance",
            "Modern vs. Classic: Migration Strategy, Feature Parity",
            "Performance & Optimization: CDN, Caching, Query Tuning"
        ]
    },
    {
        "id": "m365_exchange_hybrid",
        "title": "Exchange Online & Hybrid Architecture Patterns",
        "chapter": "microsoft-365",
        "color": "#0078D4",
        "outline": [
            "Exchange Online Architecture: Mailboxes, Routing, Federation",
            "Hybrid Deployments: Synchronization, Routing, Coexistence",
            "Migration Strategies: Staged, Cutover, Hybrid Migration Wizard",
            "Security: Encryption, DLP, Advanced Threat Protection",
            "Compliance: Retention, Hold, eDiscovery",
            "Monitoring & Troubleshooting: Health Dashboard, Message Tracking",
            "Performance Tuning: Connection Health, Mailbox Quotas"
        ]
    },
    {
        "id": "azure_fundamentals_az900",
        "title": "Azure Fundamentals (AZ-900) Complete Study Guide",
        "chapter": "azure-certifications",
        "color": "#0078D4",
        "outline": [
            "Cloud Concepts: What is Cloud, Benefits, Types of Cloud Services",
            "Azure Services: Compute, Storage, Database, Network, Analytics",
            "Azure Pricing & Support: Cost Management, Support Plans, SLA",
            "Exam Structure: Question Types, Time Management, Passing Score",
            "Study Tips: Best Resources, Practice Tests, Time Investment",
            "Key Concepts for Success: Terminology, Common Pitfalls",
            "Practice Questions & Answers: 30+ sample questions"
        ]
    },
    {
        "id": "azure_admin_az104",
        "title": "Azure Administrator (AZ-104) Study Path",
        "chapter": "azure-certifications",
        "color": "#0078D4",
        "outline": [
            "Virtual Machines: Creation, Sizing, Networking, Storage",
            "Azure Networking: VNets, Subnets, Route Tables, Load Balancers",
            "Storage: Blobs, Files, Queues, Table Storage, Accounts",
            "Identity & Access: Azure AD, RBAC, Managed Identities",
            "Compute Services: App Service, Function Apps, Container Instances",
            "Monitoring & Backup: Monitor, Log Analytics, Backup, Recovery",
            "Governance & Compliance: Policies, Subscriptions, Resource Groups",
            "Exam Strategy: Time Management, Difficult Topics, Lab Practice"
        ]
    },
    {
        "id": "azure_architect_az305",
        "title": "Azure Solutions Architect (AZ-305) Deep Dive",
        "chapter": "azure-certifications",
        "color": "#0078D4",
        "outline": [
            "Design Principles: Scalability, Availability, Security, Cost Optimization",
            "Compute Architecture: VMs vs. App Service vs. Serverless Patterns",
            "Data Architecture: Database Selection, Data Lake, Data Warehouse",
            "Network Design: Hub-Spoke, Multi-Region, Disaster Recovery",
            "Security Architecture: Defense in Depth, Encryption, Identity",
            "Migration Patterns: Lift-and-Shift, Refactor, Rearchitect, Rebuild",
            "Case Studies: E-Commerce Platform, Healthcare System, Financial Services",
            "Exam Strategy: Scenario Analysis, Design Thinking, Trade-offs"
        ]
    },
    {
        "id": "cloud_security_framework",
        "title": "Cloud Security Framework: Defense in Depth Strategy",
        "chapter": "cloud-security",
        "color": "#C5192D",
        "outline": [
            "Security Layers: Perimeter, Network, Compute, Data, Application",
            "Threat Modeling: STRIDE, Attack Trees, Common Attack Patterns",
            "Defense in Depth: Multiple Controls, Redundancy, Resilience",
            "Network Security: NACLs, Security Groups, DDoS Protection, WAF",
            "Application Security: OWASP Top 10, Secure Coding, SAST/DAST",
            "Data Security: Encryption at Rest/Transit, Tokenization, Masking",
            "Identity & Access: MFA, RBAC, Privileged Access, Just-in-Time",
            "Incident Response: Detection, Containment, Eradication, Recovery",
            "Best Practices: Least Privilege, Separation of Duties, Monitoring"
        ]
    },
    {
        "id": "compliance_frameworks",
        "title": "Compliance Frameworks: HIPAA, GDPR, SOC 2, PCI-DSS",
        "chapter": "cloud-security",
        "color": "#C5192D",
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
        ]
    },
    {
        "id": "hybrid_architecture",
        "title": "Hybrid Cloud Architecture: On-Premises to Azure Integration",
        "chapter": "hybrid-multicloud",
        "color": "#7B2CBF",
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
        ]
    },
    {
        "id": "multicloud_strategy",
        "title": "Multi-Cloud Strategy: Azure, AWS, GCP Interoperability",
        "chapter": "hybrid-multicloud",
        "color": "#7B2CBF",
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
        ]
    },
    {
        "id": "mlops_fundamentals",
        "title": "MLOps Fundamentals: ML Pipeline Automation & Governance",
        "chapter": "aiml-operations",
        "color": "#FF6B35",
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
        ]
    }
]

def log(msg):
    _core_log("phase6-publisher", msg)

def generate_article_content(title, outline):
    """Generate article content using Claude"""
    prompt = f"""Write a comprehensive IT infrastructure article titled "{title}".

Section Outline:
{chr(10).join(f'- {s}' for s in outline)}

Guidelines:
- Write in plain English (no jargon without explanation)
- Include 30+ interview Q&A
- Include 45+ FAQ items
- Include 24+ troubleshooting scenarios
- Include real-world examples and diagrams descriptions
- Professional, enterprise-focused tone
- 2000-3000 words
- Include introduction, detailed sections, and conclusion
- Add practical tips and best practices

Return ONLY the article body. No title, no HTML tags."""

    return _core_claude(prompt, max_tokens=4000, api_key=API_KEY, model=MODEL, log_fn=log)

def format_article_html(article, content):
    """Format article content as proper HTML"""
    title = article['title']
    article_id = article['id']
    chapter = article['chapter']
    color = article['color']

    description = f"Enterprise-grade guide to {title.lower()}. Complete with Q&A, FAQs, and troubleshooting scenarios."
    keywords = ", ".join([t.strip() for t in title.split("&")] + [article['chapter'].replace("-", " ").title()])

    url = f"{SITE}/chapters/{chapter}/articles/{article_id}.html"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | IT Vedas</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{url}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <link rel="canonical" href="{url}">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "description": "{description}",
      "datePublished": "2026-07-04",
      "author": {{
        "@type": "Organization",
        "name": "IT Vedas",
        "url": "https://itvedas.com"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "IT Vedas"
      }}
    }}
    </script>

    <style>
        :root {{ --primary: {color}; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0A0A0F;
            color: #F0F0F8;
            line-height: 1.7;
        }}
        nav {{
            position: fixed; top: 0; left: 0; right: 0; z-index: 100;
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 2rem; height: 64px;
            background: rgba(10,10,15,0.92);
            backdrop-filter: blur(32px);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .nav-logo {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.35rem; }}
        article {{ position: relative; z-index: 1; margin-top: 64px; }}
        .article-header {{
            border-left: 4px solid var(--primary);
            padding: 3rem 2rem;
            max-width: 900px;
            margin: 2rem auto 0;
        }}
        .article-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}
        .article-meta {{
            color: #8888A8;
            font-size: 0.9rem;
        }}
        main {{
            max-width: 900px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}
        main h2 {{
            font-size: 1.5rem;
            margin: 2rem 0 1rem 0;
            color: var(--primary);
        }}
        main h3 {{
            font-size: 1.2rem;
            margin: 1.5rem 0 0.8rem 0;
        }}
        main p {{
            margin-bottom: 1rem;
            color: #D0D0E8;
        }}
        .qa-section, .faq-section, .troubleshooting {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid var(--primary);
            padding: 2rem;
            border-radius: 8px;
            margin: 2rem 0;
        }}
        .qa-section h3, .faq-section h3, .troubleshooting h3 {{
            margin-top: 0;
            color: var(--primary);
        }}
        .qa-item, .faq-item, .troubleshooting-item {{
            margin-bottom: 1.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .qa-item:last-child, .faq-item:last-child, .troubleshooting-item:last-child {{
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }}
        .qa-q, .faq-q, .troubleshooting-scenario {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        code {{
            background: rgba(0,0,0,0.3);
            padding: 0.2em 0.4em;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background: rgba(0,0,0,0.5);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        ul, ol {{
            margin: 1rem 0 1rem 2rem;
        }}
        li {{
            margin-bottom: 0.5rem;
        }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: #8888A8;
            font-size: 0.9rem;
            border-top: 1px solid rgba(255,255,255,0.08);
            margin-top: 3rem;
        }}
    </style>
</head>
<body>
    <nav>
        <a href="/" class="nav-logo">IT<span style="color: #FF6B35;">Vedas</span></a>
        <a href="/" style="color: #8888A8; text-decoration: none;">← Back to Home</a>
    </nav>

    <article>
        <div class="article-header">
            <h1>{title}</h1>
            <p class="article-meta">Published: 2026-07-04 | Chapter: {chapter.replace('-', ' ').title()}</p>
        </div>

        <main>
            {content}

            <section class="qa-section">
                <h3>🎯 Interview Q&A</h3>
                <div class="qa-item">
                    <div class="qa-q">Q: What are the key differences between the concepts discussed?</div>
                    <p>A: Review the detailed sections above for comprehensive comparisons.</p>
                </div>
                <div class="qa-item">
                    <div class="qa-q">Q: How can these concepts be implemented in production?</div>
                    <p>A: See the best practices and real-world examples throughout this article.</p>
                </div>
            </section>

            <section class="faq-section">
                <h3>❓ Frequently Asked Questions</h3>
                <div class="faq-item">
                    <div class="faq-q">What is the best approach for implementation?</div>
                    <p>Start with the foundational concepts, understand the architecture, and follow the best practices outlined in each section.</p>
                </div>
                <div class="faq-item">
                    <div class="faq-q">How do I troubleshoot common issues?</div>
                    <p>Refer to the troubleshooting scenarios section below for detailed diagnosis and resolution steps.</p>
                </div>
            </section>

            <section class="troubleshooting">
                <h3>🔧 Troubleshooting Scenarios</h3>
                <div class="troubleshooting-item">
                    <div class="troubleshooting-scenario">Scenario: Common Issue Detection</div>
                    <p><strong>Problem:</strong> Systems not responding as expected.</p>
                    <p><strong>Root Cause:</strong> Configuration mismatch or missing prerequisites.</p>
                    <p><strong>Solution:</strong> Verify all settings against documentation and enable comprehensive logging.</p>
                </div>
                <div class="troubleshooting-item">
                    <div class="troubleshooting-scenario">Scenario: Performance Degradation</div>
                    <p><strong>Problem:</strong> Slow response times or high resource utilization.</p>
                    <p><strong>Root Cause:</strong> Insufficient capacity or suboptimal configuration.</p>
                    <p><strong>Solution:</strong> Review capacity planning and implement performance optimization techniques.</p>
                </div>
            </section>
        </main>

        <footer>
            <p>© 2026 IT Vedas. All rights reserved. | <a href="/" style="color: inherit;">Home</a></p>
        </footer>
    </article>
</body>
</html>"""

    return html

def main():
    if not API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return False

    log(f"Starting Phase 6 article publishing ({len(ARTICLES)} articles)")

    # Create articles directory structure
    for article in ARTICLES:
        chapter = article['chapter']
        articles_dir = BASE_DIR / "chapters" / chapter / "articles"
        articles_dir.mkdir(parents=True, exist_ok=True)

    published = 0
    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}] Publishing: {article['title']}")

        # Generate content
        content = generate_article_content(article['title'], article['outline'])
        if not content:
            print(f"  ERROR: Failed to generate content")
            continue

        # Format as HTML
        html = format_article_html(article, content)

        # Save to file
        chapter = article['chapter']
        article_id = article['id']
        file_path = BASE_DIR / "chapters" / chapter / "articles" / f"{article_id}.html"

        with open(file_path, 'w') as f:
            f.write(html)

        print(f"  ✓ Published {len(content)} chars → {file_path.relative_to(BASE_DIR)}")
        published += 1

    log(f"Completed: {published}/{len(ARTICLES)} articles published")
    print(f"\n✓ Phase 6 publishing complete: {published} articles")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
