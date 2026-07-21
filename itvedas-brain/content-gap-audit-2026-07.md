# ITVedas content completeness audit — 2026-07-21

Scope: every topic/chapter the site currently covers, cross-referenced against
the site's own published skill roadmap (`career-paths.html`, which already
defines Foundation → Intermediate → Advanced → Expert/Professional tiers for
8 core topics) plus the additional topic areas the site covers outside that
roadmap (PowerShell, Azure, IIS, SQL Server, CVE Analysis, APIs, AI Tools).

Method: enumerated every file under `chapters/*/` and `articles/*/` (and the
loose dated files directly under `articles/`, which is where the live
`itvedas-brain/content-writer.py` pipeline actually publishes), read every
title, and mapped them against `career-paths.html`'s stated skill list per
tier. Two independent content taxonomies exist on the site today:

- `chapters/<topic>/*.html` — deeper reference-style pages, populated by a
  series of one-time "PHASE" scripts, not by any currently-scheduled
  GitHub Action.
- `articles/*.html` (loose, dated) — the output of `content-writer.py`,
  which runs 3x/week via `.github/workflows/write-article.yml` and is the
  only part of this content actively growing on autopilot.

## 8 core topics (have a `career-paths.html` roadmap)

For each: what's covered today, and the specific Advanced/Expert-tier gap.
✅ = filled in this pass with one new advanced-tier article (see below).

### Networking — ✅ partially filled
Covered: OSI model, subnetting, DHCP, NAT, TCP vs UDP, CDN, IPv4/IPv6,
Wi-Fi standards, PKI basics, SSL/TLS handshake, firewall setup (iptables/UFW),
and a beginner-level BGP intro. 12 chapter pages + several beginner articles.
**Gap (Advanced/Expert):** no OSPF coverage at all; BGP coverage was
intro-only (no path selection, route reflectors); no MPLS/SD-WAN; no network
automation (Python/Ansible for network config); no NetFlow/sFlow; no
large-scale network architecture or service-provider-scale routing design.
**Filled:** "BGP and OSPF Explained: Advanced Routing Protocols for Network
Engineers" — multi-area OSPF/LSA types, full BGP best-path algorithm, route
reflectors/confederations, MPLS L3VPN + SD-WAN.
**Still open:** network automation (Python/Ansible), NetFlow/sFlow analysis,
data-center/cloud networking fabrics, large-scale/service-provider routing
design, network security architecture as its own topic.

### Cloud — ✅ partially filled
Covered: EC2, S3, load balancers, Docker vs Kubernetes basics, Terraform
intro, serverless (Lambda vs Azure Functions), cost optimization, SRE vs
DevOps. 12 chapter pages.
**Gap (Advanced/Expert):** no multi-account/multi-region architecture; no
DR/HA design; no EKS/AKS/GKE specifics; no FinOps depth; no enterprise
cloud governance/landing zones; no cloud security architecture; no
policy-as-code (OPA/Sentinel).
**Filled:** "Multi-Region Cloud Architecture: Designing for High Availability
and Disaster Recovery" — AZ vs region failure domains, the DR spectrum
(backup/restore → pilot light → warm standby → active-active), replication
tradeoffs, failover mechanics, split-brain.
**Still open:** landing zones/multi-cloud governance, policy-as-code, FinOps
in depth, EKS/AKS/GKE-specific operations, advanced Terraform module design.

### Security — ✅ partially filled
Covered: OWASP Top 10, SIEM basics, pentest methodology (intro), DDoS,
social engineering, incident response, OAuth 2.0, Linux hardening. Plus a
beginner-level Zero Trust article and a cloud-security sub-chapter
(defense-in-depth + compliance frameworks). 8 chapter pages.
**Gap (Advanced/Expert):** zero coverage of threat hunting or digital
forensics; pentest coverage stops at methodology, no red-teaming depth; no
SOAR/security automation; no enterprise security architecture; no
purple-team practice; no board-level risk communication.
**Filled:** "Threat Hunting and Digital Forensics: A Practical Guide for
Security Analysts" — hunting loop methodology, MITRE ATT&CK mapping, key
Windows event IDs, chain of custody, order of volatility, live response vs
imaging.
**Still open:** red-teaming/purple-team practice in depth, SOAR playbooks,
enterprise security architecture, zero-trust *implementation* (the existing
zero-trust piece is explicitly beginner-level).

### DevOps — ✅ partially filled
Covered: GitHub Actions, Jenkins CI/CD, Ansible, GitOps, Helm, blue-green
deployment, Prometheus/Grafana setup, Nginx vs Apache. 8 chapter pages.
**Gap (Advanced/Expert):** zero coverage of service mesh (Istio/Linkerd);
no platform engineering / internal developer platforms; no multi-cluster
architecture; no SRE on-call practice; no distributed tracing depth (only
metrics via Prometheus/Grafana are covered).
**Filled:** "Service Mesh Explained: Istio vs Linkerd for Kubernetes
Microservices" — sidecar pattern, mTLS, Istio vs Linkerd architecture
tradeoffs, when you don't need a mesh yet.
**Still open:** platform engineering / IDPs, multi-cluster/multi-region
Kubernetes, SRE practices and on-call ownership, distributed tracing.

### Databases — ✅ partially filled
Covered: ACID, replication (master-slave), indexing, SQL optimization,
sharding, MongoDB, Redis, MySQL vs PostgreSQL, Elasticsearch. 10 chapter
pages.
**Gap (Advanced/Expert):** no HA/DR architecture as its own topic; no
managed cloud database services (RDS/Aurora, DynamoDB, Cassandra); no
distributed databases (Spanner, CockroachDB); no enterprise data
governance.
**Filled:** "Database High Availability and Disaster Recovery: Architecture
Patterns Explained" — HA vs DR distinction, replication topologies
(async/sync/multi-primary/quorum), failover mechanics, split-brain, what
managed services do and don't cover.
**Still open:** distributed/multi-region databases (Spanner, CockroachDB),
enterprise data governance and multi-model strategy.

### Linux & OS — ✅ partially filled
Covered: permissions, systemd, package management, cron, SSH keys, process
management, file hierarchy, grep/awk/sed, performance-monitoring tools. 10
chapter pages.
**Gap (Advanced/Expert):** no kernel tuning/sysctl coverage; no cgroups;
no HA clustering (Pacemaker/Corosync); no fleet-scale automation
(Puppet/Chef beyond a passing Ansible mention); no virtualization deep dive
(KVM/Proxmox); no kernel internals.
**Filled:** "Linux Kernel Tuning and Performance: sysctl, cgroups, and
Fleet-Scale Automation" — profiling discipline, key sysctl parameters,
cgroups v2 (the primitive containers/Kubernetes sit on), fleet automation
and drift detection.
**Still open:** HA clustering, KVM/Proxmox virtualization, kernel internals
and custom builds, enterprise config management at fleet scale.

### Hardware — ✅ partially filled
Covered: CPU/GPU architecture, RAM, SSD/HDD/NVMe, motherboards, server
hardware types, overclocking, BIOS/UEFI, CPU generations, data-center
power/cooling basics. 10 chapter pages.
**Gap (Advanced/Expert):** zero coverage of SAN/NAS or hyperconverged
infrastructure; no hardware lifecycle/capacity planning; no enterprise
data-center architecture or vendor strategy; no sustainability/power
efficiency strategy.
**Filled:** "SAN vs NAS: Enterprise Storage Architecture Explained" —
block vs file storage, Fibre Channel/iSCSI, NAS protocols, where HCI fits
and its tradeoffs.
**Still open:** hardware lifecycle/capacity planning, enterprise DC
architecture and vendor/procurement strategy, sustainability/power
efficiency.

### Compliance — ✅ partially filled
Covered: GDPR, HIPAA, PCI-DSS, ISO 27001 (foundation level), plus an
overlapping "Compliance Frameworks" page under the cloud-security
sub-chapter. 4 chapter pages + 1 overlap.
**Gap (Advanced/Expert):** no standalone SOC 2 article anywhere on the
site (a real gap given how often it's the actual sales blocker for SaaS
companies); no NIST CSF; no audit-leadership process; no enterprise
GRC/policy-as-code; no multi-jurisdiction compliance.
**Filled:** "SOC 2 Audit Process Explained: Type I vs Type II and How to
Prepare" — the 5 Trust Services Criteria, Type I vs II, the full audit
process step by step, what auditors actually ask for.
**Still open:** NIST CSF, audit-leadership practice (SOC 2/ISO 27001 run
end-to-end by the practitioner rather than experienced as a vendor),
enterprise GRC/policy-as-code, multi-jurisdiction programs.

## Topics without a career-paths.html roadmap (not filled this pass)

These don't have the same Foundation→Expert framework published, but the
same "thin/beginner-only" pattern shows up. Flagged here, not filled, so
scope stayed achievable — see "Why these weren't filled" below.

### PowerShell — thin-to-intermediate
5 articles: fundamentals, functions/modules, AD automation, server admin,
best practices. Reasonable beginner→intermediate spread, but nothing on
**DSC (Desired State Configuration)**, **PowerShell remoting/JEA (Just
Enough Administration)**, module publishing/packaging, or Pester testing.

### Azure — thin
4 articles (AD/Entra ID, networking/VNets, SQL DB vs SQL Server, VM
deployment) + 3 AZ-900/104/305 study guides. No **Azure governance/Policy**,
no **landing zones**, no Azure Monitor/Log Analytics depth, no Azure DevOps
pipelines, no Azure-specific cost management.

### IIS Server — thin
3 articles: install, app-pool management, SSL/TLS. No **URL
Rewrite/ARR reverse-proxy setup**, no load balancing across multiple IIS
servers, no logging/performance tuning, no troubleshooting common IIS
error codes (500/502/503).

### SQL Server — thin
3 articles: editions/licensing, install/config, Always-On AG. No **backup/
restore strategy**, no SQL-Server-specific performance tuning/indexing, no
other replication types (transactional/merge/snapshot), no TDE/row-level
security, no deadlock/blocking troubleshooting.

### APIs — the thinnest topic on the site
**1 article total** ("What is an API? REST, HTTP Methods and JSON"). No
REST vs GraphQL vs gRPC comparison, no API authentication patterns
(OAuth2/API keys/JWT), no rate limiting/throttling, no versioning
strategy, no API gateway patterns, no OWASP API Top 10. Given this is the
single thinnest topic on the whole site by page count, it's the strongest
candidate for the *next* gap-filling pass.

### CVE Analysis — well covered, no action needed
22 pages total (11 conceptual chapter pages: what is a CVE, CVSS scoring,
responsible disclosure, etc. + 11 real-world case studies: Log4Shell,
EternalBlue, Heartbleed, Shellshock, Zerologon, ProxyLogon, PrintNightmare,
Spectre/Meltdown, plus 2026 CVEs). This is genuinely the deepest topic on
the site already; flagged only as "no gap found," not as a candidate for
more content right now.

### Career Paths — not a content gap
`career-paths.html`/`career-navigator.html` are roadmap/tool pages, not
article content, and are already the most structured thing on the site
(they're what this whole audit used as its rubric). No gap to fill here.

## Why 8 topics were filled and 5 weren't

`content-writer.py`'s live pipeline (the "same pipeline" this pass reused,
per the request) only knows 8 topics — its `CHAPTERS` dict and 3x/week
content calendar cover exactly Networking, Cloud, Security, DevOps,
Databases, Linux, Hardware, Compliance. Publishing through that pipeline for
those 8 gets full integration for free: the article lands in the right
chapter hub's article list, in the homepage's "Latest Articles" section, in
`build_chapter_pages()`'s per-topic listing, and in state tracking used for
"refresh oldest article" logic.

PowerShell/Azure/IIS/SQL Server/APIs live in a *different* taxonomy
(`articles/<category>/index.html` hub pages populated by older one-time
scripts, not by `content-writer.py`). Publishing into those via the same
pipeline would have meant either extending `content-writer.py`'s `CHAPTERS`
dict and calendar (a bigger, more permanent pipeline change than one gap-fill
pass warranted) or hand-writing a page that "reuses the format" without the
hub-page integration actually working — i.e., an orphaned article nobody
could browse to. Flagging these 5 clearly here, rather than half-filling
them, was the more honest option.

## Pipeline issues found along the way (unrelated to content, worth a look)

- `content-writer.py`'s `build_sitemap()` used to hand-roll a ~24-URL
  sitemap and overwrite the full one on every publish (3x/week) — fixed in
  the companion canonical-URL commit to delegate to
  `scripts/generate-sitemap.py` instead.
- `update_homepage(state)` silently no-ops: it looks for either a
  `<!-- LATEST_ARTICLES_START -->` marker or a
  `<div style="padding:5rem 0;" id="newsletter">` anchor in `index.html`,
  and neither currently exists in the live homepage. This means the
  "Latest Articles" section on the homepage may not be getting refreshed by
  the automated pipeline at all right now — worth a look independent of
  this content pass.
- `scripts/generate-search-index.py` built URLs with `str(path)` instead of
  `path.as_posix()`, so running it on Windows corrupts every URL with
  backslashes (harmless on the Ubuntu GitHub Actions runner, but broke
  immediately when run locally to reindex the new articles here) — fixed
  as part of regenerating the search index for this pass.
