#!/usr/bin/env python3
"""
PHASE 4: Expand short content pages (< 500 words).
Add comprehensive introductions and overview paragraphs to category pages.
"""

import pathlib
import re

ROOT = pathlib.Path(".")

CATEGORY_EXPANSIONS = {
    'cloud': """
Cloud computing has revolutionized the way organizations deploy and manage IT infrastructure. Rather than maintaining expensive on-premises data centers, businesses can leverage cloud providers' resources on a pay-as-you-go basis. This guide covers the essential concepts of cloud computing, including Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS).

Understanding cloud computing involves learning about different deployment models: public clouds (AWS, Azure, Google Cloud), private clouds (dedicated infrastructure), and hybrid clouds (combination of both). Each model offers distinct advantages depending on security requirements, compliance needs, and cost considerations. Major cloud providers offer services ranging from computing power and storage to databases and machine learning capabilities, enabling organizations to build sophisticated applications without significant upfront infrastructure investment.

Security in cloud environments requires a shared responsibility model. While cloud providers secure the underlying infrastructure, organizations must protect their data, applications, and access controls. Key concepts include identity and access management, encryption, network security, and regular security audits. Proper configuration of cloud resources and monitoring services help prevent misconfigurations and unauthorized access.

Cost optimization is critical in cloud deployments. Organizations must implement proper resource tagging, monitor usage patterns, and leverage reserved instances or savings plans. Regular cost analysis and optimization ensure cloud investments deliver maximum business value while controlling expenses.
""",

    'networking': """
Networking forms the foundation of modern IT infrastructure, enabling communication between computers and devices. Understanding networking concepts is essential for IT professionals, from configuring routers and switches to managing complex enterprise networks. This comprehensive guide covers the protocols, technologies, and best practices that enable reliable network communication.

The OSI (Open Systems Interconnection) model provides a framework for understanding network communications across seven layers. Physical layer deals with hardware and cables, while the data link layer manages switching and MAC addresses. The network layer, handled by protocols like IP, routes data across networks. Transport layer protocols (TCP and UDP) manage end-to-end communication. Upper layers handle application-level services like HTTP, DNS, and email.

IPv4 and IPv6 are fundamental to modern networking. IPv4 uses 32-bit addresses (192.168.1.1 format), while IPv6 uses 128-bit addresses to support the growing number of connected devices. Subnetting divides networks into smaller segments, improving performance and security. Network Address Translation (NAT) allows private networks to communicate with external networks.

Network security requires implementing firewalls, VPNs, and intrusion detection systems. Proper network segmentation isolates critical systems from general user networks. Regular monitoring and logging help detect unauthorized access and suspicious activities. Quality of Service (QoS) ensures critical applications receive adequate bandwidth.
""",

    'security': """
Security is paramount in modern IT operations. With cyber threats evolving constantly, organizations must implement comprehensive security strategies protecting data, applications, and infrastructure from unauthorized access, data breaches, and malicious attacks. This guide covers essential security concepts, best practices, and technologies.

Cybersecurity threats range from malware and ransomware to phishing and social engineering attacks. Malware includes viruses, trojans, and worms that compromise system integrity. Ransomware encrypts data and demands payment for decryption. Phishing attacks trick users into revealing credentials or downloading malicious files. Understanding these threats helps organizations implement appropriate defenses.

Defense-in-depth uses multiple security layers rather than relying on a single protection mechanism. This includes network firewalls, endpoint protection, data encryption, access controls, and security monitoring. Multi-factor authentication (MFA) adds additional protection by requiring multiple verification methods. Regular security awareness training helps employees recognize and avoid social engineering attacks.

Data protection requires encryption both in transit and at rest. Digital certificates enable secure communication over networks. Role-based access control (RBAC) ensures users access only necessary resources. Regular security audits, vulnerability scanning, and penetration testing identify weaknesses before attackers exploit them. Incident response plans enable quick recovery from security breaches.

Compliance frameworks like HIPAA, PCI-DSS, GDPR, and SOC 2 establish minimum security standards for specific industries and use cases.
""",

    'linux': """
Linux is a free, open-source operating system powering servers, cloud infrastructure, and IoT devices worldwide. Understanding Linux is essential for IT professionals managing modern infrastructure. This guide covers Linux fundamentals, command-line operations, system administration, and best practices.

Linux distributions like Ubuntu, CentOS, and Red Hat provide different flavors of the Linux operating system, each optimized for different use cases. Ubuntu focuses on ease of use, CentOS emphasizes stability, and Red Hat targets enterprise environments. The Linux kernel manages hardware resources and enables multi-tasking and multi-user capabilities.

The Linux file system organizes data hierarchically with "/" as the root directory. Common directories include "/home" for user files, "/etc" for configuration, "/var" for variable data, and "/usr" for user programs. Understanding file permissions (read, write, execute) and ownership is critical for security and system management.

Command-line proficiency is essential for Linux administration. The bash shell provides powerful scripting capabilities for automation. Common commands include grep for searching, sed for text manipulation, awk for data processing, and find for locating files. Piping allows chaining commands for complex operations.

System administration tasks include user management, package installation, service management, and log monitoring. The systemd init system manages services and system startup. Proper backups, security updates, and performance monitoring ensure reliable Linux systems.
""",

    'devops': """
DevOps combines development and operations practices to deliver software faster while maintaining quality and reliability. DevOps culture emphasizes collaboration, automation, and continuous improvement throughout the software lifecycle. This guide covers key DevOps concepts, tools, and methodologies.

Continuous Integration (CI) automates the process of integrating code changes from multiple developers. Automated testing runs on every commit, catching bugs early. Continuous Deployment (CD) automates the release process, enabling frequent production deployments. CI/CD pipelines reduce manual effort and improve deployment reliability.

Infrastructure as Code (IaC) treats infrastructure like software, using version control and automation. Tools like Terraform and CloudFormation define infrastructure as code, enabling reproducible deployments across environments. Configuration management tools like Ansible, Chef, and Puppet automate system configuration and maintenance.

Containerization with Docker and orchestration with Kubernetes revolutionized application deployment. Containers package applications with dependencies, ensuring consistency across development and production environments. Kubernetes automates container deployment, scaling, and management across clusters.

Monitoring and observability provide visibility into system behavior and performance. Tools like Prometheus, Grafana, and ELK stack collect and visualize metrics, logs, and traces. Proper alerting enables rapid response to issues. This data-driven approach enables continuous optimization.

DevOps practices reduce deployment risk, improve release frequency, and enhance system reliability. Organizations adopting DevOps see faster time-to-market and higher overall system stability.
""",

    'databases': """
Databases are critical components of modern applications, storing and retrieving data efficiently. Understanding database concepts, design principles, and management is essential for IT professionals. This guide covers relational databases, NoSQL systems, and best practices.

Relational databases use tables with rows and columns to organize data. SQL (Structured Query Language) enables querying and manipulating data. ACID properties (Atomicity, Consistency, Isolation, Durability) ensure data integrity and reliability. Popular relational databases include PostgreSQL, MySQL, and SQL Server.

Database normalization eliminates redundancy and improves data integrity. First normal form eliminates repeating groups, second normal form removes partial dependencies, and third normal form handles transitive dependencies. Proper normalization reduces storage requirements and prevents update anomalies.

Indexing improves query performance by creating efficient access paths to data. Primary keys uniquely identify records, while foreign keys establish relationships between tables. Joins combine data from multiple tables. Query optimization ensures efficient data retrieval even with large datasets.

NoSQL databases serve different needs than traditional relational databases. Document databases like MongoDB store flexible JSON-like structures. Key-value stores like Redis provide high-performance caching. Graph databases efficiently represent relationships between entities.

Database administration includes backup and recovery, performance tuning, security configuration, and capacity planning. Regular maintenance and monitoring ensure optimal database performance and reliability.
""",

    'compliance': """
Compliance ensures organizations meet legal, regulatory, and industry-specific requirements. Non-compliance can result in significant financial penalties, legal liability, and reputational damage. This guide covers major compliance frameworks and best practices.

GDPR (General Data Protection Regulation) governs how organizations collect, process, and store personal data of European residents. Requirements include obtaining explicit consent, enabling data subject rights, and reporting data breaches within specific timeframes. Non-compliance can result in fines up to 20 million euros or 4% of annual revenue.

HIPAA (Health Insurance Portability and Accountability Act) protects patient health information in the healthcare industry. HIPAA requires administrative, physical, and technical safeguards to protect patient privacy. Business associates handling patient data must maintain BAAs with healthcare entities.

PCI-DSS (Payment Card Industry Data Security Standard) applies to organizations processing credit card payments. Requirements include network security, data protection, vulnerability management, and access control. Merchants failing compliance risk fines and payment processing restrictions.

SOC 2 (Service Organization Control) provides a framework for service providers to demonstrate their security and control environment. Type I reports assess controls at a point in time, while Type II reports evaluate controls over an extended period.

ISO 27001 provides a general framework for information security management applicable across industries. It requires establishing information security policies, managing access controls, implementing security monitoring, and continually improving security practices. Organizations achieving ISO 27001 certification demonstrate commitment to information security.

Regular audits, documentation, staff training, and security monitoring ensure ongoing compliance with applicable requirements.
""",

    'hardware': """
Understanding computer hardware is essential for IT professionals responsible for system procurement, configuration, and maintenance. Modern computing relies on processors, memory, storage, and networking components working together. This guide covers hardware fundamentals and best practices.

Processors (CPUs) execute instructions and determine system performance. Modern CPUs include multiple cores for parallel processing. Clock speed (GHz) indicates how many operations per second a processor executes. Cache memory stores frequently accessed data for faster retrieval.

RAM (Random Access Memory) provides temporary storage for running programs and data. Sufficient RAM enables smooth multitasking and prevents excessive disk swapping. SSDs (Solid State Drives) provide faster storage than traditional mechanical hard drives. NVMe SSDs offer even higher performance for demanding applications.

Server hardware differs from workstations, optimized for reliability, performance, and scalability. Redundant components including power supplies and storage prevent single points of failure. RAID (Redundant Array of Independent Disks) technology protects against disk failures. Proper cooling and power management ensure reliable operation.

Graphics Processing Units (GPUs) accelerate computationally intensive tasks including graphics rendering, scientific computing, and artificial intelligence. Modern data centers increasingly use GPUs for machine learning workloads.

Network Interface Cards (NICs) enable system communication. Modern systems support gigabit or higher speeds. Proper network infrastructure design ensures adequate bandwidth for applications.

Regular hardware monitoring, maintenance, and timely upgrades ensure systems remain performant and reliable as technology evolves.
"""
}

def get_content_length(html):
    """Get word count of main content."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return len(text.split())

def expand_page_intro(content, expansion_text):
    """Add comprehensive introduction to pages with short content."""
    # Find the first <h2 or <p after the main H1 and insert expansion before it
    match = re.search(r'(<h2[^>]*>|<p[^>]*>)', content, re.IGNORECASE)
    if match:
        insert_pos = match.start()
        expansion_html = f'<p>{expansion_text.strip()}</p>\n\n'
        return content[:insert_pos] + expansion_html + content[insert_pos:]
    return content

def process_file(file_path, category_name):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        word_count = get_content_length(content)

        if word_count < 500 and category_name in CATEGORY_EXPANSIONS:
            content = expand_page_intro(content, CATEGORY_EXPANSIONS[category_name])

            if content != original:
                file_path.write_text(content, encoding='utf-8')
                return True
        return False
    except Exception as e:
        return False

def main():
    """Expand short content pages."""
    expanded_count = 0

    # Process category index pages
    categories = [d.name for d in (ROOT / "articles").iterdir() if d.is_dir()]

    for category in categories:
        index_file = ROOT / "articles" / category / "index.html"
        if index_file.exists():
            if process_file(index_file, category):
                expanded_count += 1

    # Process chapter category pages
    chapter_categories = [d.name for d in (ROOT / "chapters").iterdir() if d.is_dir()]
    for category in chapter_categories:
        index_file = ROOT / "chapters" / category / "index.html"
        if index_file.exists():
            if process_file(index_file, category):
                expanded_count += 1

    print(f"✓ Short content expanded: {expanded_count} pages")
    return expanded_count

if __name__ == "__main__":
    count = main()
    exit(0)
