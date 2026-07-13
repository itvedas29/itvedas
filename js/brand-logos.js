// Brand detection and logo generation system
const BrandLogos = {
  // Brand keyword mappings - detect brands in news headlines/summaries
  brandKeywords: {
    'Android': { name: 'Android', color: '#3DDC84', keywords: ['android', 'apk', 'play store'] },
    'Claude': { name: 'Claude', color: '#000000', keywords: ['claude', 'anthropic'] },
    'AWS': { name: 'AWS', color: '#FF9900', keywords: ['aws', 'amazon web services', 's3', 'ec2'] },
    'Google': { name: 'Google', color: '#4285F4', keywords: ['google', 'gcp', 'cloud platform'] },
    'Microsoft': { name: 'Microsoft', color: '#00A4EF', keywords: ['microsoft', 'azure', 'windows'] },
    'Apple': { name: 'Apple', color: '#555555', keywords: ['apple', 'ios', 'macos', 'iphone'] },
    'OpenAI': { name: 'OpenAI', color: '#10A37F', keywords: ['openai', 'gpt', 'chatgpt'] },
    'Meta': { name: 'Meta', color: '#0A66C2', keywords: ['meta', 'facebook', 'instagram', 'threads'] },
    'Linux': { name: 'Linux', color: '#FCC624', keywords: ['linux', 'kernel', 'ubuntu', 'debian'] },
    'Kubernetes': { name: 'Kubernetes', color: '#326CE5', keywords: ['kubernetes', 'k8s', 'docker'] },
    'Jenkins': { name: 'Jenkins', color: '#D33833', keywords: ['jenkins', 'ci/cd'] },
    'GitHub': { name: 'GitHub', color: '#333333', keywords: ['github', 'git', 'repository'] },
    'Docker': { name: 'Docker', color: '#2496ED', keywords: ['docker', 'container'] },
    'Slack': { name: 'Slack', color: '#E01E5A', keywords: ['slack', 'messaging'] },
    'Nvidia': { name: 'Nvidia', color: '#76B900', keywords: ['nvidia', 'cuda', 'gpu'] },
    'Intel': { name: 'Intel', color: '#0071C5', keywords: ['intel', 'processor'] },
    'Fortinet': { name: 'Fortinet', color: '#EE3124', keywords: ['fortinet', 'firewall'] },
    'Cisco': { name: 'Cisco', color: '#049FD9', keywords: ['cisco', 'network'] },
  },

  // Get SVG logo for a brand
  getSvgLogo(brandName) {
    const logos = {
      'Android': this.androidLogo(),
      'Claude': this.claudeLogo(),
      'AWS': this.awsLogo(),
      'Google': this.googleLogo(),
      'Microsoft': this.microsoftLogo(),
      'Apple': this.appleLogo(),
      'OpenAI': this.openaiLogo(),
      'Meta': this.metaLogo(),
      'Linux': this.linuxLogo(),
      'Kubernetes': this.kubernetesLogo(),
      'Jenkins': this.jenkinsLogo(),
      'GitHub': this.githubLogo(),
      'Docker': this.dockerLogo(),
      'Slack': this.slackLogo(),
      'Nvidia': this.nvidiaLogo(),
      'Intel': this.intelLogo(),
      'Fortinet': this.fortinetLogo(),
      'Cisco': this.ciscoLogo(),
    };
    return logos[brandName] || null;
  },

  // Detect brand from text
  detectBrand(text) {
    if (!text) return null;
    const lowerText = text.toLowerCase();
    for (const [brand, data] of Object.entries(this.brandKeywords)) {
      for (const keyword of data.keywords) {
        if (lowerText.includes(keyword)) {
          return brand;
        }
      }
    }
    return null;
  },

  // Get brand color
  getBrandColor(brandName) {
    return this.brandKeywords[brandName]?.color || '#8B5CF6';
  },

  // SVG Logo implementations
  androidLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#3DDC84" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <ellipse cx="0" cy="-8" rx="12" ry="16" fill="#3DDC84"/>
        <ellipse cx="-18" cy="-4" rx="8" ry="14" fill="#3DDC84"/>
        <ellipse cx="18" cy="-4" rx="8" ry="14" fill="#3DDC84"/>
        <rect x="-20" y="8" width="40" height="28" rx="4" fill="#3DDC84"/>
        <rect x="-26" y="12" width="8" height="16" fill="#3DDC84"/>
        <rect x="18" y="12" width="8" height="16" fill="#3DDC84"/>
        <circle cx="-8" cy="12" r="3" fill="white"/>
        <circle cx="8" cy="12" r="3" fill="white"/>
      </g>
    </svg>`;
  },

  claudeLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#000000" opacity="0.1"/>
      <g transform="translate(64, 64)">
        <circle cx="-12" cy="-8" r="14" fill="none" stroke="#000" stroke-width="3"/>
        <circle cx="0" cy="10" r="14" fill="none" stroke="#000" stroke-width="3"/>
        <circle cx="12" cy="-8" r="14" fill="none" stroke="#000" stroke-width="3"/>
      </g>
    </svg>`;
  },

  awsLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#FF9900" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <path d="M -20,-12 Q -20,-20 -12,-20 L 12,-20 Q 20,-20 20,-12 L 20,20 Q 20,28 12,28 L -12,28 Q -20,28 -20,20 Z" fill="none" stroke="#FF9900" stroke-width="2"/>
        <circle cx="-8" cy="2" r="3" fill="#FF9900"/>
        <circle cx="0" cy="2" r="3" fill="#FF9900"/>
        <circle cx="8" cy="2" r="3" fill="#FF9900"/>
        <line x1="-12" y1="12" x2="12" y2="12" stroke="#FF9900" stroke-width="2"/>
      </g>
    </svg>`;
  },

  googleLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#4285F4" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <circle cx="0" cy="0" r="16" fill="none" stroke="#4285F4" stroke-width="2"/>
        <circle cx="0" cy="0" r="10" fill="none" stroke="#EA4335" stroke-width="2"/>
        <circle cx="0" cy="0" r="4" fill="#FBBC04"/>
      </g>
    </svg>`;
  },

  microsoftLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#00A4EF" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <rect x="-14" y="-14" width="10" height="10" fill="#F25022"/>
        <rect x="-2" y="-14" width="10" height="10" fill="#7FBA00"/>
        <rect x="-14" y="-2" width="10" height="10" fill="#00A4EF"/>
        <rect x="-2" y="-2" width="10" height="10" fill="#FFB900"/>
      </g>
    </svg>`;
  },

  appleLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#555555" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <path d="M -2,-16 Q -8,-16 -8,-10 Q -8,-6 -4,-2 Q -2,0 0,2 Q 2,0 4,-2 Q 8,-6 8,-10 Q 8,-16 2,-16 Q -1,-16 -2,-16 Z" fill="#555"/>
        <ellipse cx="0" cy="8" rx="12" ry="14" fill="none" stroke="#555" stroke-width="2"/>
      </g>
    </svg>`;
  },

  openaiLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#10A37F" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <circle cx="0" cy="0" r="16" fill="none" stroke="#10A37F" stroke-width="2.5"/>
        <path d="M -8,0 A 8,8 0 0,1 8,0" fill="none" stroke="#10A37F" stroke-width="2.5"/>
      </g>
    </svg>`;
  },

  metaLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#0A66C2" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <path d="M -12,-8 Q -16,-14 -8,-18 Q -2,-20 2,-16 Q 8,-12 6,-4 Q 4,4 -2,6 Q -10,8 -12,-2 Z" fill="none" stroke="#0A66C2" stroke-width="2"/>
        <path d="M 6,-8 Q 10,-14 18,-18 Q 24,-20 28,-16 Q 34,-12 32,-4 Q 30,4 24,6 Q 16,8 14,-2 Z" fill="none" stroke="#0A66C2" stroke-width="2"/>
      </g>
    </svg>`;
  },

  linuxLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#FCC624" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <ellipse cx="0" cy="-4" rx="8" ry="6" fill="none" stroke="#FCC624" stroke-width="2"/>
        <path d="M -4,-4 L -6,4 M 4,-4 L 6,4 M 0,-4 L 0,10" stroke="#FCC624" stroke-width="2" fill="none"/>
        <path d="M -8,8 Q -8,14 0,16 Q 8,14 8,8" fill="none" stroke="#FCC624" stroke-width="2"/>
      </g>
    </svg>`;
  },

  kubernetesLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#326CE5" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <circle cx="0" cy="0" r="10" fill="none" stroke="#326CE5" stroke-width="2"/>
        <circle cx="-8" cy="-8" r="3" fill="#326CE5"/>
        <circle cx="8" cy="-8" r="3" fill="#326CE5"/>
        <circle cx="-8" cy="8" r="3" fill="#326CE5"/>
        <circle cx="8" cy="8" r="3" fill="#326CE5"/>
      </g>
    </svg>`;
  },

  jenkinsLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#D33833" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <rect x="-8" y="-12" width="6" height="8" fill="#D33833"/>
        <rect x="2" y="-12" width="6" height="8" fill="#D33833"/>
        <rect x="-12" y="-2" width="8" height="6" fill="#D33833"/>
        <rect x="4" y="-2" width="8" height="6" fill="#D33833"/>
        <rect x="-10" y="6" width="20" height="10" fill="none" stroke="#D33833" stroke-width="2"/>
      </g>
    </svg>`;
  },

  githubLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#333333" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <path d="M -6,-12 L 6,-12 L 10,0 L 10,12 Q 10,16 6,16 L -6,16 Q -10,16 -10,12 L -10,0 Z" fill="none" stroke="#333" stroke-width="2"/>
        <path d="M -6,-12 Q -10,-16 -2,-18 Q 6,-18 10,-12" fill="none" stroke="#333" stroke-width="2"/>
      </g>
    </svg>`;
  },

  dockerLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#2496ED" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <rect x="-10" y="0" width="6" height="6" fill="#2496ED"/>
        <rect x="0" y="0" width="6" height="6" fill="#2496ED"/>
        <rect x="10" y="0" width="6" height="6" fill="#2496ED"/>
        <rect x="-10" y="8" width="6" height="6" fill="#2496ED"/>
        <rect x="0" y="8" width="6" height="6" fill="#2496ED"/>
        <rect x="10" y="8" width="6" height="6" fill="#2496ED"/>
      </g>
    </svg>`;
  },

  slackLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#E01E5A" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <rect x="-12" y="-4" width="4" height="16" fill="#E01E5A"/>
        <rect x="-4" y="-12" width="16" height="4" fill="#E01E5A"/>
        <rect x="4" y="-4" width="4" height="16" fill="#E90064"/>
        <rect x="-4" y="4" width="16" height="4" fill="#E90064"/>
      </g>
    </svg>`;
  },

  nvidiaLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#76B900" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <polygon points="0,-14 12,-4 6,8 -6,8 -12,-4" fill="none" stroke="#76B900" stroke-width="2"/>
        <line x1="0" y1="-14" x2="0" y2="10" stroke="#76B900" stroke-width="2"/>
      </g>
    </svg>`;
  },

  intelLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#0071C5" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <rect x="-12" y="-12" width="8" height="8" fill="#0071C5"/>
        <rect x="-2" y="-12" width="8" height="8" fill="#0071C5"/>
        <rect x="8" y="-12" width="8" height="8" fill="#0071C5"/>
        <line x1="-8" y1="-4" x2="-8" y2="12" stroke="#0071C5" stroke-width="2"/>
        <line x1="2" y1="-4" x2="2" y2="12" stroke="#0071C5" stroke-width="2"/>
        <line x1="12" y1="-4" x2="12" y2="12" stroke="#0071C5" stroke-width="2"/>
      </g>
    </svg>`;
  },

  fortinetLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#EE3124" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <polygon points="-8,-10 0,-16 8,-10 6,-2 8,6 0,10 -8,6 -6,-2" fill="none" stroke="#EE3124" stroke-width="2"/>
      </g>
    </svg>`;
  },

  ciscoLogo() {
    return `<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="60" fill="#049FD9" opacity="0.15"/>
      <g transform="translate(64, 64)">
        <line x1="-10" y1="-10" x2="10" y2="10" stroke="#049FD9" stroke-width="2"/>
        <line x1="10" y1="-10" x2="-10" y2="10" stroke="#049FD9" stroke-width="2"/>
        <circle cx="0" cy="0" r="12" fill="none" stroke="#049FD9" stroke-width="1.5"/>
      </g>
    </svg>`;
  },
};

// Dynamic SVG generator for unknown brands
function generateDynamicImage(headline, topic, index) {
  const colors = {
    'AI': ['#F97316', '#8B5CF6', '#EC4899'],
    'Security': ['#10B981', '#06B6D4', '#0EA5E9'],
    'Cloud': ['#3B82F6', '#0EA5E9', '#06B6D4'],
    'DevOps': ['#8B5CF6', '#A78BFA', '#F97316'],
    'General': ['#64748B', '#94A3B8', '#CBD5E1'],
    'Hardware': ['#06B6D4', '#0EA5E9', '#3B82F6'],
  };

  const topicColors = colors[topic] || colors['General'];
  const color1 = topicColors[index % topicColors.length];
  const color2 = topicColors[(index + 1) % topicColors.length];

  // Extract main keywords from headline
  const words = headline.toLowerCase().split(/\s+/).filter(w => w.length > 4);
  const keyword = words[index % words.length] || 'tech';

  // Generate unique SVG based on keyword and topic
  const seed = keyword.charCodeAt(0) + (index * 7);
  const shapes = [
    `<circle cx="32" cy="32" r="${8 + (seed % 12)}" fill="${color1}" opacity="0.8"/>
     <polygon points="64,${10 + (seed % 20)} ${75 + (seed % 15)},${40 + (seed % 20)} ${53 - (seed % 15)},${50 + (seed % 20)}" fill="${color2}" opacity="0.7"/>
     <rect x="${20 + (seed % 30)}" y="${20 + (seed % 30)}" width="${16 + (seed % 10)}" height="${16 + (seed % 10)}" fill="${color1}" opacity="0.6"/>`,

    `<rect x="10" y="10" width="44" height="44" fill="${color1}" opacity="0.7"/>
     <circle cx="60" cy="60" r="${10 + (seed % 8)}" fill="${color2}" opacity="0.8"/>
     <polygon points="32,20 42,50 22,50" fill="${color2}" opacity="0.6"/>`,

    `<path d="M 20,20 Q 40,${10 + (seed % 30)} 60,20 L 60,60 Q 40,${70 - (seed % 20)} 20,60 Z" fill="${color1}" opacity="0.7"/>
     <circle cx="${32 + (seed % 20)}" cy="${32 + (seed % 20)}" r="6" fill="${color2}"/>
     <circle cx="${48 - (seed % 20)}" cy="${48 - (seed % 20)}" r="4" fill="${color2}" opacity="0.6"/>`,

    `<g transform="rotate(${seed % 360} 32 32)">
       <rect x="16" y="10" width="8" height="44" fill="${color1}" opacity="0.8"/>
       <rect x="26" y="16" width="8" height="32" fill="${color2}" opacity="0.7"/>
       <rect x="36" y="22" width="8" height="20" fill="${color1}" opacity="0.6"/>
       <rect x="46" y="28" width="8" height="8" fill="${color2}" opacity="0.5"/>
     </g>`,
  ];

  const shape = shapes[seed % shapes.length];

  return `<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="grad-${index}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${color1};stop-opacity:0.15" />
        <stop offset="100%" style="stop-color:${color2};stop-opacity:0.15" />
      </linearGradient>
    </defs>
    <rect width="80" height="80" fill="url(#grad-${index})"/>
    ${shape}
  </svg>`;
}

// Main function to get the right visual for a news item
function getNewsVisual(headline, summary, topic, index = 0) {
  const fullText = headline + ' ' + summary;
  const detectedBrand = BrandLogos.detectBrand(fullText);

  if (detectedBrand) {
    const logo = BrandLogos.getSvgLogo(detectedBrand);
    if (logo) {
      return {
        svg: logo,
        type: 'brand',
        brand: detectedBrand,
        color: BrandLogos.getBrandColor(detectedBrand),
      };
    }
  }

  // If no brand detected, generate dynamic image based on topic
  const svg = generateDynamicImage(headline, topic, index);
  return {
    svg: svg,
    type: 'dynamic',
    brand: null,
    color: topic === 'AI' ? '#F97316' :
           topic === 'Security' ? '#10B981' :
           topic === 'Cloud' ? '#3B82F6' :
           topic === 'DevOps' ? '#8B5CF6' :
           topic === 'Hardware' ? '#06B6D4' : '#64748B',
  };
}
