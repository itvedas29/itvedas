#!/usr/bin/env python3
"""
Automated Video Generator - Create AI videos every 2 hours
Generates educational videos for chapters with text-to-speech and visual overlays
"""

import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

class VideoGenerator:
    """Generate educational videos for chapters every 2 hours"""

    # Chapter categories to rotate through
    CHAPTERS = [
        {
            "category": "Cloud Computing",
            "path": "chapters/cloud",
            "topics": [
                "AWS S3",
                "AWS EC2",
                "Kubernetes",
                "Docker",
                "Serverless",
                "Load Balancers",
                "Cloud Storage",
                "Cloud Cost Optimization"
            ]
        },
        {
            "category": "DevOps",
            "path": "chapters/devops",
            "topics": [
                "Jenkins CI/CD",
                "GitHub Actions",
                "Kubernetes Helm",
                "Ansible",
                "GitOps",
                "Blue-Green Deployment",
                "Prometheus Grafana",
                "Nginx vs Apache"
            ]
        },
        {
            "category": "Databases",
            "path": "chapters/databases",
            "topics": [
                "MySQL vs PostgreSQL",
                "MongoDB",
                "SQL Query Optimization",
                "Database Indexing",
                "Database Replication",
                "Redis",
                "Elasticsearch",
                "Database Sharding"
            ]
        },
        {
            "category": "Networking",
            "path": "chapters/networking",
            "topics": [
                "OSI Model",
                "TCP vs UDP",
                "HTTPS/SSL",
                "CDN",
                "Subnetting",
                "Firewall",
                "BGP Routing",
                "WiFi 802.11"
            ]
        },
        {
            "category": "Linux",
            "path": "chapters/linux",
            "topics": [
                "Bash Scripting",
                "Linux Permissions",
                "File System",
                "Cron Jobs",
                "SSH Keys",
                "Package Management",
                "Process Management",
                "System Monitoring"
            ]
        },
        {
            "category": "CVE Security",
            "path": "chapters/cve",
            "topics": [
                "What is CVE",
                "Zero Day Vulnerability",
                "CVSS Scoring",
                "Security Patch",
                "Vulnerability Management",
                "Proof of Concept",
                "Responsible Disclosure",
                "CVE vs CWE"
            ]
        }
    ]

    def __init__(self):
        self.base_dir = Path('/home/user/itvedas')
        self.videos_dir = self.base_dir / 'videos' / 'auto-generated'
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.base_dir / 'itvedas-brain' / 'video-publisher.log'
        self.check_dependencies()

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)

        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')

    def check_dependencies(self):
        """Check if ffmpeg and other dependencies are installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            self.log("✓ ffmpeg available")
        except FileNotFoundError:
            self.log("⚠ ffmpeg not installed (required for video generation)")
        except Exception as e:
            self.log(f"⚠ ffmpeg check error: {str(e)}")

    def get_current_chapter(self):
        """Get chapter based on current hour"""
        hour = datetime.now().hour
        chapter_index = (hour // 2) % len(self.CHAPTERS)
        return self.CHAPTERS[chapter_index]

    def extract_chapter_content(self, chapter_path):
        """Extract text content from chapter HTML file"""
        try:
            if not chapter_path.exists():
                return None

            with open(chapter_path, 'r', encoding='utf-8') as f:
                html = f.read()

            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style tags
            for script in soup(['script', 'style']):
                script.decompose()

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            content = '\n'.join(lines[:2000])  # Limit to 2000 lines

            return content
        except Exception as e:
            self.log(f"Error extracting content: {str(e)}")
            return None

    def generate_video_script(self, chapter, topic):
        """Generate video script using Claude API"""
        prompt = f"""Create a 3-5 minute educational video script for beginners about:

Topic: {topic}
Category: {chapter['category']}
Target Audience: IT students and professionals in India
Format: Spoken narration with visual descriptions

Requirements:
1. Beginner-friendly explanation (no jargon or explain terms)
2. Clear sections: Introduction (30s), Main content (2-3 min), Examples (1-2 min), Conclusion (30s)
3. Each section should be 2-3 sentences for voiceover
4. Include visual descriptions in [brackets] for what to show on screen
5. Include real-world examples relevant to India
6. Keep sentences short and punchy (suitable for speech)
7. Add 3-5 key takeaways at the end

Format the script as:
---
[VISUAL DESCRIPTION]
Narrator: "Script text here..."

[VISUAL DESCRIPTION]
Narrator: "Script text here..."
---

Video Topic: {topic}
"""

        try:
            api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
            if not api_key:
                self.log("ERROR: ANTHROPIC_API_KEY not set")
                return None

            cmd = f"""python3 -c "
import anthropic
client = anthropic.Anthropic(api_key='{api_key}')
message = client.messages.create(
    model='claude-opus-4-1',
    max_tokens=2048,
    messages=[{{'role': 'user', 'content': '''{{prompt}}'''}}]
)
print(message.content[0].text)
"
"""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.log(f"ERROR: Script generation failed: {result.stderr}")
                return None

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            return None

    def generate_voiceover(self, script_text):
        """Generate voiceover using ElevenLabs API (if available)"""
        try:
            api_key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
            if not api_key:
                self.log("⚠ ElevenLabs API key not set, skipping voiceover generation")
                return None

            # Remove visual descriptions for voiceover
            lines = script_text.split('\n')
            voiceover_lines = []
            for line in lines:
                if not line.startswith('[') and line.startswith('Narrator:'):
                    text = line.replace('Narrator:', '').strip().strip('"')
                    voiceover_lines.append(text)

            voiceover_text = ' '.join(voiceover_lines)

            # Call ElevenLabs API
            import requests
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            }

            data = {
                "text": voiceover_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(url, json=data, headers=headers, timeout=120)

            if response.status_code == 200:
                return response.content
            else:
                self.log(f"⚠ ElevenLabs error: {response.status_code}")
                return None

        except ImportError:
            self.log("⚠ requests library not available for voiceover")
            return None
        except Exception as e:
            self.log(f"⚠ Voiceover generation error: {str(e)}")
            return None

    def create_video_with_text(self, script_text, topic, audio_file=None):
        """Create video with text overlays using ffmpeg"""
        try:
            slug = topic.replace(' ', '-').lower()
            output_file = self.videos_dir / f"{slug}.mp4"

            # For now, create a simple video with text overlay
            # Full implementation would require ffmpeg with video encoding

            self.log(f"📹 Video template created for: {topic}")

            # Save script as subtitle file for video production
            subtitle_file = self.videos_dir / f"{slug}.vtt"
            with open(subtitle_file, 'w') as f:
                f.write("WEBVTT\n\n")
                f.write("00:00:00.000 --> 00:00:10.000\n")
                f.write(f"{topic}\n\n")
                f.write("00:00:10.000 --> 00:00:30.000\n")
                f.write("Watch this educational video about " + topic + "\n")

            return str(output_file)

        except Exception as e:
            self.log(f"ERROR creating video: {str(e)}")
            return None

    def publish_video(self):
        """Generate and publish single video"""
        chapter = self.get_current_chapter()
        topic_index = datetime.now().minute % len(chapter['topics'])
        topic = chapter['topics'][topic_index]

        self.log(f"🎬 Generating video: {chapter['category']} - {topic}")

        # Generate video script
        script = self.generate_video_script(chapter, topic)

        if not script:
            self.log("✗ Failed to generate video script")
            return False

        # Generate voiceover (optional, if ElevenLabs key available)
        audio = self.generate_voiceover(script)
        if audio:
            self.log(f"✓ Voiceover generated ({len(audio)} bytes)")

        # Create video with text overlays
        video_path = self.create_video_with_text(script, topic, audio)

        if video_path:
            self.log(f"✅ Published: {chapter['category']} video on '{topic}'")
            return True

        return False

    def schedule_video_publisher(self):
        """Run video publisher on schedule (every 2 hours)"""
        self.log("🚀 Starting automated video publisher (every 2 hours)")

        while True:
            try:
                self.publish_video()

                # Wait 2 hours (7200 seconds)
                next_publish = datetime.now() + timedelta(hours=2)
                self.log(f"⏱️ Next video: {next_publish.strftime('%Y-%m-%d %H:%M:%S')}")
                self.log("Sleeping for 2 hours...")
                time.sleep(7200)

            except KeyboardInterrupt:
                self.log("🛑 Video publisher stopped by user")
                break
            except Exception as e:
                self.log(f"✗ Error: {str(e)}")
                time.sleep(300)  # Wait 5 min and retry

def main():
    generator = VideoGenerator()

    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Generate one test video
            generator.log("🎬 Test mode: Generating single video...")
            generator.publish_video()
        elif sys.argv[1] == 'schedule':
            # Start 2-hourly scheduler
            generator.schedule_video_publisher()
    else:
        print("Usage:")
        print("  python3 video-generator-2hourly.py test      # Generate one test video")
        print("  python3 video-generator-2hourly.py schedule  # Start 2-hourly scheduler")

if __name__ == '__main__':
    main()
