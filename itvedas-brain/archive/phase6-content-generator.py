#!/usr/bin/env python3
"""
Phase 6 Autonomous Content Generator
Generates all 11 Phase 6 articles using Claude API only
"""

import os
import json
import re
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from core.llm import claude as _core_claude
from core.log import log as _core_log

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MODEL = "claude-haiku-4-5-20251001"
SITE = "https://itvedas.com"

ARTICLES = [
    {
        "id": "m365_teams_governance",
        "title": "Microsoft Teams Governance, Security & Compliance",
        "chapter": "microsoft-365",
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
    _core_log("phase6-generator", msg)

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

def main():
    if not API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return False

    log(f"Starting Phase 6 autonomous content generation ({len(ARTICLES)} articles)")

    generated = 0
    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}] Generating: {article['title']}")

        # Generate content
        content = generate_article_content(article['title'], article['outline'])
        if not content:
            print(f"  ERROR: Failed to generate content")
            continue

        print(f"  ✓ Generated {len(content)} characters")
        generated += 1

    log(f"Completed: {generated}/{len(ARTICLES)} articles generated")
    print(f"\n✓ Phase 6 autonomous generation complete: {generated} articles")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
