/**
 * ITVedas Diagram Components
 * Mermaid-based diagrams for network, architecture, and process flows
 */

class DiagramComponents {
  static init() {
    // Load Mermaid if not already loaded
    if (typeof mermaid === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
      script.onload = () => {
        mermaid.initialize({ startOnLoad: true, theme: 'dark' });
        mermaid.contentLoaded();
      };
      document.head.appendChild(script);
    }

    // Process diagram elements
    this.processDiagrams();
  }

  static processDiagrams() {
    document.querySelectorAll('[data-diagram]').forEach(el => {
      const type = el.dataset.diagram;
      const config = JSON.parse(el.dataset.config || '{}');
      const diagram = this.createDiagram(type, config);
      if (diagram) {
        el.innerHTML = diagram;
      }
    });
  }

  static createDiagram(type, config) {
    switch (type) {
      case 'network':
        return this.networkDiagram(config);
      case 'architecture':
        return this.architectureDiagram(config);
      case 'flowchart':
        return this.flowchartDiagram(config);
      case 'sequence':
        return this.sequenceDiagram(config);
      case 'cicd':
        return this.cicdPipeline(config);
      case 'cloud-architecture':
        return this.cloudArchitecture(config);
      case 'kubernetes':
        return this.kubernetesArchitecture(config);
      case 'active-directory':
        return this.activeDirectoryFlow(config);
      case 'dns-resolution':
        return this.dnsResolution(config);
      case 'vpn-topology':
        return this.vpnTopology(config);
      default:
        return null;
    }
  }

  static networkDiagram(config = {}) {
    const {
      title = 'Network Topology',
      includeInternetGateway = true,
      includeLoadBalancer = true,
      includeSecurityGroups = true
    } = config;

    return `
      <div class="mermaid">
        graph TD
          ${includeInternetGateway ? 'IGW["🌐 Internet Gateway"]' : ''}
          LB["⚖️ Load Balancer"]
          SG1["🔒 Security Group"]
          SG2["🔒 Security Group"]
          VM1["🖥️ VM Instance 1<br/>Web Server"]
          VM2["🖥️ VM Instance 2<br/>App Server"]
          DB["🗄️ Database<br/>Primary"]
          DBR["🗄️ Database<br/>Replica"]

          ${includeInternetGateway ? 'IGW --> LB' : 'LB'}
          LB --> SG1
          LB --> SG2
          SG1 --> VM1
          SG2 --> VM2
          VM1 --> DB
          VM2 --> DB
          DB --> DBR

          style VM1 fill:#ff6b35
          style VM2 fill:#ff6b35
          style DB fill:#10b981
          style DBR fill:#10b981
          style LB fill:#8b5cf6
          style SG1 fill:#06b6d4
          style SG2 fill:#06b6d4
      </div>
    `;
  }

  static architectureDiagram(config = {}) {
    const { title = 'System Architecture' } = config;

    return `
      <div class="mermaid">
        graph LR
          subgraph "Client Layer"
            WEB["🌐 Web Browser<br/>Desktop App"]
            MOBILE["📱 Mobile App"]
          end

          subgraph "API Layer"
            LB["⚖️ Load Balancer"]
            API1["🔌 API Server 1"]
            API2["🔌 API Server 2"]
          end

          subgraph "Service Layer"
            AUTH["🔐 Auth Service"]
            USER["👥 User Service"]
            DATA["📊 Data Service"]
          end

          subgraph "Data Layer"
            DB["🗄️ PostgreSQL"]
            CACHE["⚡ Redis Cache"]
          end

          WEB --> LB
          MOBILE --> LB
          LB --> API1
          LB --> API2
          API1 --> AUTH
          API1 --> USER
          API1 --> DATA
          API2 --> AUTH
          API2 --> USER
          API2 --> DATA
          AUTH --> DB
          USER --> DB
          DATA --> DB
          AUTH --> CACHE
          USER --> CACHE

          style WEB fill:#ff6b35
          style MOBILE fill:#ff6b35
          style API1 fill:#8b5cf6
          style API2 fill:#8b5cf6
          style DB fill:#10b981
          style CACHE fill:#fbbf24
      </div>
    `;
  }

  static flowchartDiagram(config = {}) {
    const { title = 'Process Flow' } = config;

    return `
      <div class="mermaid">
        flowchart TD
          START([Start]) --> DECISION{Decision<br/>Point}
          DECISION -->|Yes| ACTION1["Execute Action 1"]
          DECISION -->|No| ACTION2["Execute Action 2"]
          ACTION1 --> RESULT1["Result 1"]
          ACTION2 --> RESULT2["Result 2"]
          RESULT1 --> END([End])
          RESULT2 --> END

          style START fill:#10b981
          style END fill:#ef4444
          style DECISION fill:#fbbf24
          style ACTION1 fill:#8b5cf6
          style ACTION2 fill:#8b5cf6
      </div>
    `;
  }

  static sequenceDiagram(config = {}) {
    return `
      <div class="mermaid">
        sequenceDiagram
          participant Client
          participant Server
          participant Database

          Client->>Server: Request Data
          activate Server
          Server->>Database: Query
          activate Database
          Database-->>Server: Result Set
          deactivate Database
          Server-->>Client: JSON Response
          deactivate Server
      </div>
    `;
  }

  static cicdPipeline(config = {}) {
    return `
      <div class="mermaid">
        graph LR
          GIT["📦 Git Push"]
          BUILD["🔨 Build"]
          TEST["✅ Test"]
          SCAN["🔍 Security Scan"]
          STAGE["🚀 Staging Deploy"]
          PROD["🌍 Production Deploy"]

          GIT --> BUILD
          BUILD --> TEST
          TEST --> SCAN
          SCAN --> STAGE
          STAGE --> PROD

          style GIT fill:#ff6b35
          style BUILD fill:#8b5cf6
          style TEST fill:#06b6d4
          style SCAN fill:#fbbf24
          style STAGE fill:#10b981
          style PROD fill:#10b981
      </div>
    `;
  }

  static cloudArchitecture(config = {}) {
    const { provider = 'aws' } = config;

    return `
      <div class="mermaid">
        graph TB
          subgraph "Internet"
            USER["👥 Users<br/>0.0.0.0/0"]
          end

          subgraph "AWS Account"
            subgraph "VPC"
              subgraph "Public Subnet"
                IGW["Internet<br/>Gateway"]
                ALB["Application<br/>Load Balancer"]
              end

              subgraph "Private Subnet"
                EC2_1["EC2<br/>Instance 1"]
                EC2_2["EC2<br/>Instance 2"]
              end

              subgraph "Database Subnet"
                RDS["RDS<br/>Multi-AZ"]
              end
            end

            S3["S3<br/>Storage"]
            CF["CloudFront<br/>CDN"]
          end

          USER --> CF
          CF --> ALB
          ALB --> EC2_1
          ALB --> EC2_2
          EC2_1 --> RDS
          EC2_2 --> RDS
          EC2_1 --> S3
          EC2_2 --> S3

          style IGW fill:#ff9900
          style ALB fill:#ff9900
          style EC2_1 fill:#ff9900
          style EC2_2 fill:#ff9900
          style RDS fill:#527fff
          style S3 fill:#527fff
          style CF fill:#f58536
      </div>
    `;
  }

  static kubernetesArchitecture(config = {}) {
    return `
      <div class="mermaid">
        graph TB
          subgraph "Kubernetes Cluster"
            subgraph "Control Plane"
              API["API Server"]
              SCHED["Scheduler"]
              CTRL["Controller Manager"]
              ETCD["etcd"]
            end

            subgraph "Worker Nodes"
              NODE1["Node 1"]
              NODE2["Node 2"]
              NODE3["Node 3"]
            end

            subgraph "Pods"
              P1["Pod - App"]
              P2["Pod - App"]
              P3["Pod - DB"]
            end

            subgraph "Services"
              SVC["Service<br/>Load Balancer"]
            end
          end

          API --> ETCD
          SCHED --> NODE1
          SCHED --> NODE2
          SCHED --> NODE3
          CTRL --> NODE1
          CTRL --> NODE2
          CTRL --> NODE3
          NODE1 --> P1
          NODE2 --> P2
          NODE3 --> P3
          SVC --> P1
          SVC --> P2

          style API fill:#326ce5
          style ETCD fill:#419eda
          style NODE1 fill:#419eda
          style NODE2 fill:#419eda
          style NODE3 fill:#419eda
          style P1 fill:#00a651
          style P2 fill:#00a651
          style P3 fill:#00a651
      </div>
    `;
  }

  static activeDirectoryFlow(config = {}) {
    return `
      <div class="mermaid">
        graph TD
          USER["👤 Domain User"]
          DC["Domain Controller<br/>AD DS"]
          KDC["Key Distribution<br/>Center"]
          TGT["Ticket Granting<br/>Ticket"]
          SP["Service Principal"]
          RESOURCE["Resource<br/>Computer"]

          USER -->|Logon Request| DC
          DC -->|Verify Credentials| KDC
          KDC -->|Issue TGT| TGT
          TGT -->|Request Service| SP
          SP -->|Grant Access| RESOURCE

          style USER fill:#ff6b35
          style DC fill:#8b5cf6
          style KDC fill:#06b6d4
          style TGT fill:#fbbf24
          style RESOURCE fill:#10b981
      </div>
    `;
  }

  static dnsResolution(config = {}) {
    return `
      <div class="mermaid">
        sequenceDiagram
          participant Client as User's Computer
          participant RR as Recursive Resolver
          participant RS as Root Server
          participant TLD as TLD Server
          participant NS as Nameserver

          Client->>RR: 1. What's the IP of example.com?
          RR->>RS: 2. Where's example.com?
          RS-->>RR: 3. Ask the .com TLD server
          RR->>TLD: 4. Where's example.com?
          TLD-->>RR: 5. Ask this nameserver
          RR->>NS: 6. Where's example.com?
          NS-->>RR: 7. 93.184.216.34
          RR-->>Client: 8. 93.184.216.34
      </div>
    `;
  }

  static vpnTopology(config = {}) {
    return `
      <div class="mermaid">
        graph TB
          subgraph "Office A"
            OFFICE_A["Office Network<br/>192.168.1.0/24"]
          end

          subgraph "VPN Connection"
            ENCRYPT["Encrypted Tunnel<br/>IPSec/OpenVPN"]
          end

          subgraph "Office B"
            OFFICE_B["Office Network<br/>192.168.2.0/24"]
          end

          subgraph "Internet"
            ISP["Public Internet"]
          end

          OFFICE_A -->|VPN Gateway| ENCRYPT
          ENCRYPT -->|VPN Gateway| OFFICE_B
          OFFICE_A -.->|Fallback| ISP
          OFFICE_B -.->|Fallback| ISP

          style OFFICE_A fill:#ff6b35
          style OFFICE_B fill:#ff6b35
          style ENCRYPT fill:#8b5cf6
          style ISP fill:#cccccc
      </div>
    `;
  }

  // Initialize on document ready
  static onReady(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback);
    } else {
      callback();
    }
  }
}

// Initialize on DOM ready
DiagramComponents.onReady(() => {
  DiagramComponents.init();
});

// Expose for use in templates
window.DiagramComponents = DiagramComponents;
