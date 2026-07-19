#!/usr/bin/env python3
"""
PHASE 6: Create AI Knowledge Hub infrastructure.
1. Design AI tool category pages
2. Create tool discovery mechanisms
3. Implement tool comparison frameworks
4. Build AI-specific metadata structure
"""

import pathlib
import json
import re

ROOT = pathlib.Path(".")

AI_TOOLS_METADATA = {
    "machine-learning": {
        "title": "Machine Learning Tools & Frameworks",
        "description": "Comprehensive guide to ML frameworks, tools, and platforms for building and deploying machine learning models.",
        "tools": [
            {"name": "TensorFlow", "category": "Deep Learning", "url": "#tensorflow", "description": "End-to-end open-source platform for machine learning"},
            {"name": "PyTorch", "category": "Deep Learning", "url": "#pytorch", "description": "Python-first deep learning framework"},
            {"name": "Scikit-learn", "category": "General ML", "url": "#sklearn", "description": "Machine learning library for Python"},
            {"name": "Keras", "category": "Neural Networks", "url": "#keras", "description": "High-level neural networks API"},
            {"name": "XGBoost", "category": "Gradient Boosting", "url": "#xgboost", "description": "Extreme Gradient Boosting for classification and regression"}
        ]
    },
    "ai-platforms": {
        "title": "AI Platforms & Cloud Services",
        "description": "Explore major AI platforms and cloud services for training, deploying, and managing AI models at scale.",
        "tools": [
            {"name": "Google Cloud AI", "category": "Cloud Platform", "url": "#gcp-ai", "description": "Google's comprehensive AI and machine learning services"},
            {"name": "AWS AI", "category": "Cloud Platform", "url": "#aws-ai", "description": "Amazon's AI and machine learning platform"},
            {"name": "Azure AI", "category": "Cloud Platform", "url": "#azure-ai", "description": "Microsoft Azure's AI and machine learning services"},
            {"name": "Hugging Face", "category": "Model Hub", "url": "#huggingface", "description": "Open-source models and tools for NLP"},
            {"name": "OpenAI API", "category": "LLM Platform", "url": "#openai", "description": "Access to advanced language models via API"}
        ]
    },
    "data-engineering": {
        "title": "Data Engineering & Processing Tools",
        "description": "Tools and frameworks for data pipeline creation, processing, and management.",
        "tools": [
            {"name": "Apache Spark", "category": "Big Data", "url": "#spark", "description": "Distributed computing framework for large-scale data processing"},
            {"name": "Airflow", "category": "Orchestration", "url": "#airflow", "description": "Workflow and pipeline orchestration tool"},
            {"name": "Kafka", "category": "Streaming", "url": "#kafka", "description": "Event streaming platform for real-time data pipelines"},
            {"name": "Pandas", "category": "Data Analysis", "url": "#pandas", "description": "Python data manipulation and analysis library"},
            {"name": "DBT", "category": "Analytics", "url": "#dbt", "description": "Data transformation and analytics platform"}
        ]
    },
    "nlp-tools": {
        "title": "Natural Language Processing Tools",
        "description": "Specialized tools and libraries for NLP, text analysis, and language understanding.",
        "tools": [
            {"name": "NLTK", "category": "NLP Library", "url": "#nltk", "description": "Natural Language Toolkit for Python"},
            {"name": "spaCy", "category": "NLP Library", "url": "#spacy", "description": "Industrial-strength NLP library"},
            {"name": "transformers", "category": "Pretrained Models", "url": "#transformers", "description": "State-of-the-art NLP models from Hugging Face"},
            {"name": "BERT", "category": "Language Models", "url": "#bert", "description": "Bidirectional Encoder Representations from Transformers"},
            {"name": "GPT", "category": "Language Models", "url": "#gpt", "description": "Generative Pre-trained Transformer models"}
        ]
    },
    "computer-vision": {
        "title": "Computer Vision & Image Processing",
        "description": "Tools and frameworks for image processing, object detection, and computer vision applications.",
        "tools": [
            {"name": "OpenCV", "category": "Image Processing", "url": "#opencv", "description": "Open-source computer vision library"},
            {"name": "YOLO", "category": "Object Detection", "url": "#yolo", "description": "Real-time object detection framework"},
            {"name": "PyTorch Vision", "category": "Vision Library", "url": "#torchvision", "description": "PyTorch's computer vision library"},
            {"name": "MediaPipe", "category": "Body/Hand Detection", "url": "#mediapipe", "description": "Framework for building perception pipelines"},
            {"name": "Detectron2", "category": "Object Detection", "url": "#detectron2", "description": "Facebook's detection framework"}
        ]
    }
}

def create_ai_hub_directory():
    """Create AI tools hub directory structure."""
    hub_dir = ROOT / "ai-tools"
    if not hub_dir.exists():
        hub_dir.mkdir(parents=True, exist_ok=True)

    return hub_dir

def generate_tool_category_page(category_key, category_data):
    """Generate HTML page for AI tool category."""
    title = category_data['title']
    description = category_data['description']
    tools = category_data['tools']

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — ITVedas</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="AI,tools,machine learning,data engineering,analytics">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .intro {{ font-size: 1.1rem; color: #666; margin-bottom: 2rem; }}
        .tools-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin: 2rem 0; }}
        .tool-card {{ border: 1px solid #ddd; padding: 1.5rem; border-radius: 0.5rem; }}
        .tool-card h3 {{ margin: 0 0 0.5rem 0; font-size: 1.2rem; }}
        .tool-category {{ font-size: 0.9rem; color: #0066cc; font-weight: 500; }}
        .tool-description {{ color: #666; font-size: 0.95rem; margin-top: 0.5rem; }}
        nav {{ margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <a href="/">Home</a> / <a href="/ai-tools/">AI Tools</a> / {title}
        </nav>

        <h1>{title}</h1>
        <p class="intro">{description}</p>

        <h2>Available Tools & Frameworks</h2>

        <div class="tools-grid">
"""

    for tool in tools:
        html += f"""        <div class="tool-card">
            <div class="tool-category">{tool['category']}</div>
            <h3 id="{tool['name'].lower().replace(' ', '-')}">{tool['name']}</h3>
            <p class="tool-description">{tool['description']}</p>
            <a href="#" style="color:#0066cc;">Learn more →</a>
        </div>
"""

    html += """        </div>

        <div style="margin-top: 3rem; padding: 1.5rem; background: #f5f5f5; border-radius: 0.5rem;">
            <h3>Getting Started with AI Tools</h3>
            <ul>
                <li>Choose the right tool based on your use case and experience level</li>
                <li>Review documentation and tutorials for each tool</li>
                <li>Start with simple examples to understand core concepts</li>
                <li>Join communities and forums for support and best practices</li>
                <li>Experiment and iterate on your AI/ML projects</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

    return html

def create_ai_tools_index():
    """Create main AI tools index page."""
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tools & Frameworks Index — ITVedas</title>
    <meta name="description" content="Comprehensive index of AI tools, machine learning frameworks, and data engineering platforms for modern development.">
    <meta name="keywords" content="AI,machine learning,tools,frameworks,data engineering">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 0; }
        .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
        h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        .intro { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
        .categories-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
        .category-card { border: 1px solid #ddd; padding: 1.5rem; border-radius: 0.5rem; }
        .category-card h2 { margin: 0 0 0.5rem 0; font-size: 1.3rem; }
        .category-card p { color: #666; margin: 0; }
        .category-card a { color: #0066cc; text-decoration: none; font-weight: 500; }
        .category-card a:hover { text-decoration: underline; }
        nav { margin-bottom: 2rem; }
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <a href="/">Home</a> / AI Tools
        </nav>

        <h1>AI Tools & Frameworks Index</h1>
        <p class="intro">Explore comprehensive resources on AI tools, machine learning frameworks, and data engineering platforms used in modern development.</p>

        <h2>Tool Categories</h2>

        <div class="categories-grid">
            <div class="category-card">
                <h2>Machine Learning</h2>
                <p>ML frameworks and libraries for building and training models.</p>
                <a href="/ai-tools/machine-learning/">Browse Tools →</a>
            </div>

            <div class="category-card">
                <h2>AI Platforms</h2>
                <p>Cloud platforms and services for AI/ML development and deployment.</p>
                <a href="/ai-tools/ai-platforms/">Browse Tools →</a>
            </div>

            <div class="category-card">
                <h2>Data Engineering</h2>
                <p>Tools for data pipelines, processing, and engineering.</p>
                <a href="/ai-tools/data-engineering/">Browse Tools →</a>
            </div>

            <div class="category-card">
                <h2>NLP Tools</h2>
                <p>Natural language processing libraries and models.</p>
                <a href="/ai-tools/nlp-tools/">Browse Tools →</a>
            </div>

            <div class="category-card">
                <h2>Computer Vision</h2>
                <p>Image processing and computer vision frameworks.</p>
                <a href="/ai-tools/computer-vision/">Browse Tools →</a>
            </div>
        </div>

        <div style="margin-top: 3rem; padding: 1.5rem; background: #f5f5f5; border-radius: 0.5rem;">
            <h3>Why Learn AI Tools?</h3>
            <ul>
                <li><strong>Career Growth:</strong> AI/ML skills are highly sought after in today's job market</li>
                <li><strong>Problem Solving:</strong> Build intelligent solutions to complex problems</li>
                <li><strong>Innovation:</strong> Leverage cutting-edge technologies in your projects</li>
                <li><strong>Automation:</strong> Automate complex tasks and improve efficiency</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

    return index_html

def main():
    """Create AI Knowledge Hub infrastructure."""
    print("PHASE 6: Creating AI Knowledge Hub Infrastructure\n")

    # Create hub directory
    hub_dir = create_ai_hub_directory()
    print(f"✓ AI Tools hub directory created: {hub_dir}")

    # Create main index
    index_path = hub_dir / "index.html"
    with open(index_path, 'w') as f:
        f.write(create_ai_tools_index())
    print(f"✓ Main AI tools index created")

    # Create category pages
    category_count = 0
    for category_key, category_data in AI_TOOLS_METADATA.items():
        category_html = generate_tool_category_page(category_key, category_data)
        category_path = hub_dir / f"{category_key}.html"

        with open(category_path, 'w') as f:
            f.write(category_html)

        category_count += 1
        print(f"✓ Category page created: {category_key}")

    print(f"\n✓ AI Knowledge Hub infrastructure complete: 1 index + {category_count} category pages")

    return 1 + category_count

if __name__ == "__main__":
    count = main()
    exit(0)
