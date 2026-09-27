# ITVedas Enterprise Software Spec Database ("GSMArena for IT & DevOps")

## Overview
**ITVedas Spec Database** is a modern, high-density B2B technical specification engine designed for IT Directors, Systems Architects, DevOps Engineers, and Infrastructure Practitioners. Modeled after **GSMArena**, it prioritizes concrete, factual, and verified engineering telemetry over generic marketing blurbs.

---

## Key Features & Architectural Components

### 1. Core Brand & Header
- **Brand Identity**: ITVedas (*"The Unbiased Technical Spec Database for IT & DevOps Software"*)
- **Global Search Bar**: Instant client-side autocomplete search indexing enterprise software, vendors, tags, and categories. Supports keyboard navigation (`↑`, `↓`, `Enter`, `Esc`) and global shortcut `⌘K` / `Ctrl+K`.
- **Top Navigation**: Instant access to Categories, Side-by-Side Compare, Parametric Filter, Pricing Tracker, and "Suggest an Edit".

### 2. Featured Software Detail Page: ManageEngine Endpoint Central
- **Product Header & Verified Vendor**: Full attribution to Zoho Corporation with verified tier status, HQ location, and active LTS branch.
- **Spec Rating Score**: 9.4 / 10 Spec Index Score with category ranking badge (#1 in Hybrid UEM).
- **Category & Deployment Badges**: Unified Endpoint Management (UEM), Client Management, Patch Management, Hybrid (Cloud SaaS & On-Premise).
- **Quick Spec Summary Card (GSMArena Highlight Grid)**:
  - **OS Support**: 6 families (Windows, macOS, Linux, iOS, Android, ChromeOS)
  - **Min Server RAM**: 8 GB (On-Prem default)
  - **Directory Sync**: Active Directory, Microsoft Entra ID, OpenLDAP, Okta SCIM
  - **Max Tested Nodes**: 25,000+ per server (100,000+ in Enterprise WAN Mesh)
  - **Free Tier**: Yes (Permanent free edition for up to 25 endpoints)
  - **Agent Footprint & Ports**: ~45 MB RAM, HTTPS 8383 / WebSocket 8027

### 3. GSMArena-Style 7-Section Tabular Spec Sheet (Accordions / Structured Grid)
- **Section 01: General & Architecture**: Delivery model, transport protocols (TLS 1.3, WebSockets, WebRTC), multi-tenant MSP support, WAN distribution servers, active-passive failover clustering (<60s heartbeat), and secure DMZ gateway.
- **Section 02: Platform & OS Compatibility**: Windows 11/10/8.1/7, Windows Server 2025/2022/2019/2016/2012/2008, macOS 15 Sequoia down to Big Sur (Universal binary: native Apple Silicon M1-M4 & Intel), Linux (Ubuntu, RHEL, Debian, Rocky, SUSE), Mobile (iOS 14-18+, Android Enterprise 9-15), ChromeOS kiosk mode.
- **Section 03: Hardware & System Requirements**: Min vs Recommended CPU cores, RAM scaling tiers (8 GB, 16 GB, 32-64 GB), database engines (bundled PostgreSQL vs MS SQL Server), storage IOPS, and silent background agent resource limits.
- **Section 4: Core Capabilities**: 850+ third-party patch catalog, silent software deployment formats (MSI, EXE, PKG, DMG, DEB, RPM, PS1, Shell), HTML5 WebRTC remote control with session recording, bare-metal PXE imaging, and software metering.
- **Section 5: Identity, Security & Compliance**: SAML 2.0 IdP (Okta, Entra, Ping, JumpCloud), TOTP/RADIUS MFA, fine-grained RBAC, AES-256 + TLS 1.3, SOC 2 Type II, ISO 27001:2022, HIPAA, GDPR, FedRAMP Moderate.
- **Section 6: Integrations & API**: ServiceDesk Plus native sync, ServiceNow certified store app, Jira, Splunk, Log360, Datadog, OpenAPI 3.0 REST v2, and PowerShell SDK.
- **Section 7: Edition Comparison Matrix**: Interactive table comparing Professional vs. Enterprise vs. UEM Edition vs. Security Edition with feature checkmarks, add-on badges, and transparent annual pricing.

### 4. Interactive Tabs
- **Full Specs**: Tabular GSMArena accordion specifications with "Expand / Collapse All" toggle.
- **Editions & Pricing**: Detailed commercial cards breaking down Professional, Enterprise, UEM, and Security Editions.
- **Direct Competitor Diff**: Side-by-side comparison cards and full spec diff matrix comparing Endpoint Central against **Microsoft Intune**, **NinjaOne**, and **Ivanti Neurons**.

### 5. Parametric Faceted Filter Engine & Sidebar
- **Facet 1: Deployment Type**: Cloud SaaS, On-Premise, Air-Gapped / Isolated LAN.
- **Facet 2: Directory & Auth**: Active Directory, Microsoft Entra ID, SAML 2.0, OpenLDAP.
- **Facet 3: Free Tier**: Any, Permanent Free Tier (≤25 Nodes), Trial Only.
- **Facet 4: Minimum Node Scale Slider**: 100 to 50,000+ nodes.
- **Live Counter**: Dynamically calculates matching platforms and updates UI in real-time.

### 6. Interactive Floating Compare Drawer & Modals
- **Compare Queue**: Add/remove platforms with visual chip drawer at screen bottom.
- **Full Spec Diff Modal**: Multi-column comparison table comparing all 4 competitors across 10 critical enterprise criteria.
- **Report Outdated Spec Modal**: Community-driven audit submissions with citation links.
- **Suggest an Edit Modal**: Direct workflow for administrators to submit newly released tools or undocumented capabilities.

---

## File Deliverables
- `specs.html` — The main high-density web application.
- `js/specs-app.js` — Client-side search, filtering, accordion toggling, comparison queue, and modal logic.
- `data/software-catalog.json` — Structured JSON catalog containing technical profiles for enterprise tools.
- `SPECS_DATABASE_README.md` — Technical documentation and architecture map.
