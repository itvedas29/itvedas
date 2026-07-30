#!/usr/bin/env python3
"""
Automated Article Publisher - Publish every 2 hours
Generates and publishes trending IT/Security articles on schedule
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class AutoPublisher:
    """Publish articles every 2 hours on various IT topics"""

    # Topic rotation (every 2 hours, 12 articles per day) - INDIA OPTIMIZED
    TOPICS = [
        {
            "category": "CVE/Security",
            "keywords": [
                "how to protect from ransomware attack India",
                "critical vulnerability explained for beginners",
                "zero-day exploit analysis and prevention",
                "malware detection techniques for Windows Linux",
                "latest security patch installation guide",
                "cybersecurity threats India 2026",
                "data breach prevention tips",
                "antivirus software comparison India"
            ]
        },
        {
            "category": "Cloud Computing",
            "keywords": [
                "AWS pricing and cost optimization India",
                "Azure deployment guide for beginners",
                "cloud computing benefits for Indian startups",
                "serverless computing explained simply",
                "Google Cloud vs AWS vs Azure comparison",
                "cloud security best practices",
                "cloud storage solutions for small business India",
                "how to migrate to cloud from on-premise"
            ]
        },
        {
            "category": "DevOps/Automation",
            "keywords": [
                "Docker containerization tutorial for beginners",
                "Kubernetes orchestration step by step",
                "CI/CD pipeline setup with Jenkins",
                "infrastructure as code with Terraform",
                "DevOps tools comparison 2026",
                "continuous deployment best practices",
                "automation testing with Selenium",
                "GitLab vs GitHub for DevOps"
            ]
        },
        {
            "category": "Networking",
            "keywords": [
                "how does VPN work explained simply",
                "best VPN for India legal issues",
                "network security protocols explained",
                "how to use VPN on mobile India",
                "firewall configuration tutorial",
                "DNS security and DNS over HTTPS",
                "network troubleshooting commands",
                "how to secure home WiFi network"
            ]
        },
        {
            "category": "Linux/System Admin",
            "keywords": [
                "Linux commands every beginner should know",
                "how to install Linux on Windows",
                "Ubuntu vs CentOS which is better",
                "Linux system hardening security guide",
                "Linux performance tuning tips",
                "how to manage users and permissions Linux",
                "Linux system monitoring tools",
                "bash scripting tutorial for beginners"
            ]
        },
        {
            "category": "Databases",
            "keywords": [
                "MySQL vs PostgreSQL comparison 2026",
                "how to optimize slow SQL queries",
                "MongoDB tutorial for beginners",
                "database backup and recovery strategies",
                "database replication master slave setup",
                "database indexing explained simply",
                "NoSQL vs SQL when to use which",
                "database security best practices"
            ]
        },
        {
            "category": "Web Development",
            "keywords": [
                "REST API design best practices",
                "how to build secure web application",
                "API authentication OAuth vs JWT",
                "web server Apache vs Nginx comparison",
                "how to deploy web application to production",
                "HTTPS SSL certificate installation guide",
                "web performance optimization techniques",
                "web application firewall WAF explained"
            ]
        },
        {
            "category": "AI/Machine Learning",
            "keywords": [
                "machine learning for beginners explained",
                "artificial intelligence vs machine learning",
                "how to train machine learning model",
                "deep learning neural networks tutorial",
                "TensorFlow vs PyTorch comparison",
                "natural language processing NLP explained",
                "computer vision applications 2026",
                "machine learning ethics and bias"
            ]
        }
    ]

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.articles_dir = self.base_dir / 'articles' / 'auto-generated'
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.base_dir / 'itvedas-brain' / 'publisher.log'

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)

        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')

    def get_current_topic(self):
        """Get topic based on current hour"""
        hour = datetime.now().hour
        topic_index = (hour // 2) % len(self.TOPICS)
        return self.TOPICS[topic_index]

    def generate_article_prompt(self, topic, keyword):
        """Generate Claude prompt for article"""
        prompt = f"""
Generate a comprehensive IT education article for beginners:

Topic: {topic['category']}
Keyword: {keyword}
Target Audience: IT students and professionals in India
Length: 1500-2000 words
Format: HTML with proper structure

Requirements:
1. Clear, beginner-friendly explanation
2. Real-world examples relevant to India
3. Practical tips and best practices
4. Step-by-step guides where applicable
5. Common mistakes to avoid
6. Internal link opportunities (mention related topics)
7. SEO-optimized headings
8. Include FAQ section with 5-7 questions
9. All prices and money amounts must be in Indian Rupees (₹), never USD

Write the article in HTML format with:
- Proper semantic HTML5
- h2, h3, h4 headings
- Paragraphs and lists
- Code examples where relevant
- Strong, em tags for emphasis

Start with <article> tag and end with </article>

Article keyword: {keyword}
Article category: {topic['category']}
"""
        return prompt

    def call_claude_api(self, prompt):
        """Call Claude API via Anthropic SDK (in-process, no shell)"""
        try:
            api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
            if not api_key:
                self.log("ERROR: ANTHROPIC_API_KEY not set")
                return None

            import anthropic
            client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
            message = client.messages.create(
                model='claude-sonnet-5',
                max_tokens=8000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return message.content[0].text.strip()

        except Exception as e:
            self.log(f"ERROR: API call failed: {str(e)}")
            return None

    def create_html_article(self, article_content, topic, keyword):
        """Wrap article content in full HTML template"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        slug = keyword.replace(' ', '-').lower()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{keyword.title()} - Complete Guide 2026 | ITVedas</title>
<meta name="description" content="Learn {keyword} in plain English. Step-by-step guide with examples, best practices, and real-world applications. Updated {timestamp}.">
<meta name="keywords" content="{keyword}, IT education, {topic['category']}, beginner guide">
<link rel="icon" type="image/svg+xml" href="/assets/logo-mark.svg">
<link rel="canonical" href="https://itvedas.com/articles/auto-generated/{slug}.html">
<link rel="alternate" hreflang="x-default" href="https://itvedas.com/articles/auto-generated/{slug}.html">
<link rel="alternate" hreflang="en-US" href="https://itvedas.com/articles/auto-generated/{slug}.html">
<link rel="alternate" hreflang="en-GB" href="https://itvedas.com/articles/auto-generated/{slug}.html">
<link rel="alternate" hreflang="en-IN" href="https://itvedas.com/articles/auto-generated/{slug}.html">
<link rel="alternate" hreflang="en" href="https://itvedas.com/articles/auto-generated/{slug}.html">
<style>
:root{{--bg:#EEF3FC;--bg2:#FFFFFF;--bg3:#F7F9FD;--text:#182238;--muted:#6B7A94;--accent:#FF6B35;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;line-height:1.8;}}
article{{max-width:860px;margin:4rem auto;padding:2rem;}}
h2{{font-size:1.8rem;margin:2rem 0 1rem;color:var(--text);}}
h3{{font-size:1.4rem;margin:1.5rem 0 0.75rem;color:var(--text);}}
p{{margin:1rem 0;color:var(--text);}}
code{{background:var(--bg2);padding:0.2rem 0.5rem;border-radius:4px;font-family:monospace;}}
</style>
</head>
<body>
<article>
{article_content}
</article>
</body>
</html>
"""
        return html, slug

    def save_article(self, html_content, slug):
        """Save article to file"""
        filename = self.articles_dir / f"{slug}.html"

        try:
            with open(filename, 'w') as f:
                f.write(html_content)

            self.log(f"✓ Article saved: {filename}")
            return True
        except Exception as e:
            self.log(f"✗ Error saving article: {str(e)}")
            return False

    def publish_article(self):
        """Generate and publish single article"""
        topic = self.get_current_topic()
        keyword = topic['keywords'][datetime.now().minute % len(topic['keywords'])]

        self.log(f"📝 Generating article: {topic['category']} - {keyword}")

        # Generate article via Claude
        prompt = self.generate_article_prompt(topic, keyword)
        article_content = self.call_claude_api(prompt)

        if not article_content:
            self.log("✗ Failed to generate article content")
            return False

        # Create full HTML
        html, slug = self.create_html_article(article_content, topic, keyword)

        # Save to file
        if self.save_article(html, slug):
            self.log(f"✅ Published: {topic['category']} article on '{keyword}'")
            return True

        return False

    def schedule_publisher(self):
        """Run publisher on schedule (every 2 hours)"""
        self.log("🚀 Starting automated publisher (every 2 hours)")

        while True:
            try:
                self.publish_article()

                # Wait 2 hours (7200 seconds)
                next_publish = datetime.now() + timedelta(hours=2)
                self.log(f"⏱️ Next publish: {next_publish.strftime('%Y-%m-%d %H:%M:%S')}")
                self.log("Sleeping for 2 hours...")
                time.sleep(7200)

            except KeyboardInterrupt:
                self.log("🛑 Publisher stopped by user")
                break
            except Exception as e:
                self.log(f"✗ Error: {str(e)}")
                time.sleep(300)  # Wait 5 min and retry

def main():
    publisher = AutoPublisher()

    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Generate one test article
            publisher.log("📝 Test mode: Generating single article...")
            publisher.publish_article()
        elif sys.argv[1] == 'schedule':
            # Start 2-hourly scheduler
            publisher.schedule_publisher()
    else:
        print("Usage:")
        print("  python3 auto-publisher-2hourly.py test      # Generate one test article")
        print("  python3 auto-publisher-2hourly.py schedule  # Start 2-hourly scheduler")

if __name__ == '__main__':
    main()
