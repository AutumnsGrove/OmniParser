# AI-Powered Features

OmniParser includes optional AI-powered features for document enhancement, including auto-tagging, summarization, quality scoring, and image analysis.

## Features Overview

- **Auto-Tagging**: Generate relevant tags/keywords for documents
- **Summarization**: Create concise, detailed, or bullet-point summaries
- **Quality Scoring**: Assess document quality across multiple dimensions
- **Image Description**: Generate accessibility alt text for images
- **Image Analysis**: Comprehensive image analysis (OCR, classification, object detection)

## Installation

Install OmniParser with AI features:

```bash
pip install 'omniparser[ai]'
```

This installs the required dependencies:
- `anthropic` - Anthropic Claude API
- `openai` - OpenAI and OpenAI-compatible APIs (OpenRouter, Ollama, LM Studio)

## Configuration

### API Keys

Set API keys via environment variables:

```bash
# Cloud Providers
export ANTHROPIC_API_KEY='sk-ant-...'
export OPENAI_API_KEY='sk-...'
export OPENROUTER_API_KEY='sk-or-...'

# Local Providers (optional)
export OLLAMA_BASE_URL='http://localhost:11434/v1'
export LMSTUDIO_BASE_URL='http://localhost:1234/v1'
```

**Security Warning**: Never hardcode API keys in source code! Always use environment variables or secure secret management.

### Provider Selection

OmniParser supports multiple AI providers:

| Provider | Type | Models | API Key Required |
|----------|------|--------|------------------|
| **Anthropic** | Cloud | Claude 3 (Opus, Sonnet, Haiku) | Yes |
| **OpenAI** | Cloud | GPT-3.5, GPT-4, GPT-4o | Yes |
| **OpenRouter** | Cloud | 200+ models (Meta, Google, etc.) | Yes |
| **Ollama** | Local | Llama, Mistral, etc. | No |
| **LM Studio** | Local | Any GGUF model | No |

## Usage

### Auto-Tagging

Generate relevant tags/keywords for documents:

```python
from omniparser import parse_document
from omniparser.processors.ai_tagger import generate_tags

# Parse document
doc = parse_document("article.pdf")

# Generate tags (default: Anthropic Claude)
tags = generate_tags(doc, max_tags=10)
print(tags)
# ['machine learning', 'neural networks', 'deep learning', ...]

# Use specific provider
tags = generate_tags(
    doc,
    max_tags=5,
    ai_options={
        'ai_provider': 'openai',
        'ai_model': 'gpt-4o'
    }
)

# Use local model via Ollama
tags = generate_tags(
    doc,
    ai_options={
        'ai_provider': 'ollama',
        'ai_model': 'llama3.2:latest'
    }
)
```

**Parameters**:
- `max_tags` (int): Maximum number of tags (1-100, default: 10)
- `ai_options` (dict): AI configuration options

### Summarization

Generate summaries in different styles:

```python
from omniparser import parse_document
from omniparser.processors.ai_summarizer import summarize_document, summarize_chapter

doc = parse_document("book.epub")

# Concise summary (2-3 sentences)
summary = summarize_document(doc, style="concise")
print(summary)

# Detailed summary (up to 1000 words)
summary = summarize_document(doc, max_length=1000, style="detailed")

# Bullet-point summary
summary = summarize_document(doc, style="bullet")
print(summary)
# - Main theme: ...
# - Key argument: ...
# - Conclusion: ...

# Summarize specific chapter
chapter_summary = summarize_chapter(doc, chapter_id=3, style="concise")
```

**Parameters**:
- `max_length` (int): Maximum length in words (1-10000, default: 500)
- `style` (str): Summary style - "concise", "detailed", or "bullet"
- `ai_options` (dict): AI configuration options

**Styles**:
- **concise**: 2-3 sentence overview
- **detailed**: Comprehensive summary up to max_length words
- **bullet**: 5-7 key points in bullet-point format

### Quality Scoring

Assess document quality across multiple dimensions:

```python
from omniparser import parse_document
from omniparser.processors.ai_quality import score_quality, compare_quality

doc = parse_document("technical_doc.md")

# Score quality
quality = score_quality(doc)

print(f"Overall Quality: {quality['overall_score']}/100")
print(f"Readability: {quality['readability']}/100")
print(f"Structure: {quality['structure']}/100")
print(f"Completeness: {quality['completeness']}/100")
print(f"Coherence: {quality['coherence']}/100")

print("\nStrengths:")
for strength in quality['strengths']:
    print(f"  - {strength}")

print("\nSuggestions:")
for suggestion in quality['suggestions']:
    print(f"  - {suggestion}")

# Compare two documents
doc1 = parse_document("draft_v1.md")
doc2 = parse_document("draft_v2.md")
comparison = compare_quality(doc1, doc2)
print(f"Winner: {comparison['winner']}")
print(f"Comparison: {comparison['comparison']}")
```

**Quality Dimensions**:
- **Overall Score**: Weighted average of all dimensions (0-100)
- **Readability**: Clarity, sentence structure, word choice (0-100)
- **Structure**: Organization, headings, logical flow (0-100)
- **Completeness**: Depth, coverage, thoroughness (0-100)
- **Coherence**: Consistency, transitions, unity (0-100)

### Image Description

Generate accessibility alt text for images:

```python
from omniparser import parse_document
from omniparser.processors.ai_image_describer import (
    describe_image,
    describe_document_images,
    update_image_descriptions
)

doc = parse_document("illustrated_book.epub")

# Describe single image
if doc.images:
    img = doc.images[0]
    description = describe_image(img)
    print(description)
    # "A vibrant illustration showing a medieval castle..."

# Describe all images in document
descriptions = describe_document_images(doc)
for img_id, desc in descriptions.items():
    print(f"{img_id}: {desc}")

# Update document with AI-generated alt text
doc = update_image_descriptions(doc)
# All images now have AI-generated alt text in img.alt_text

# Use vision-capable model
description = describe_image(
    img,
    ai_options={
        'ai_provider': 'anthropic',
        'ai_model': 'claude-3-opus-20240229'
    }
)
```

**Supported Vision Models**:
- **Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **OpenAI**: gpt-4o, gpt-4-vision-preview
- **Ollama**: llava, bakllava (vision models)

**Image Requirements**:
- **Formats**: .jpg, .jpeg, .png, .gif, .webp
- **Max Size**: 10MB per image
- Images are base64-encoded for API transmission (~33% size increase)

### Image Analysis

Comprehensive image analysis pipeline:

```python
from omniparser.processors.ai_image_analyzer import (
    analyze_image,
    analyze_images_batch,
    analyze_image_reference
)

# Analyze single image
analysis = analyze_image("/path/to/diagram.png")

print(f"Type: {analysis.image_type}")  # diagram, chart, photo, etc.
print(f"Text Content: {analysis.text_content}")  # Extracted text (OCR)
print(f"Description: {analysis.description}")  # Detailed description
print(f"Objects: {', '.join(analysis.objects)}")  # Detected objects
print(f"Alt Text: {analysis.alt_text}")  # Accessibility text
print(f"Confidence: {analysis.confidence}")  # 0.0-1.0

# Batch analysis
image_paths = ["fig1.png", "fig2.png", "fig3.png"]
analyses = analyze_images_batch(image_paths)
for analysis in analyses:
    print(f"{analysis.image_path}: {analysis.image_type}")

# Analyze images from parsed document
doc = parse_document("technical_report.pdf")
for img in doc.images:
    analysis = analyze_image_reference(img)
    print(f"{img.image_id}: {analysis.image_type} - {analysis.alt_text}")
```

**Analysis Results**:
- **image_type**: Classification (diagram, flowchart, chart, graph, table, screenshot, photo, illustration, map, icon, other)
- **text_content**: Text extracted from image (OCR)
- **description**: Detailed description of image content
- **objects**: List of detected objects/elements
- **alt_text**: Concise accessibility text (<150 chars)
- **confidence**: Analysis confidence (0.0-1.0)

## Provider-Specific Configuration

### Anthropic Claude

```python
ai_options = {
    'ai_provider': 'anthropic',
    'ai_model': 'claude-3-haiku-20240307',  # Fast, cost-effective
    'max_tokens': 1024,
    'temperature': 0.3,
    'timeout': 60,
    'max_retries': 3,
    'retry_delay': 1.0
}
```

**Available Models**:
- `claude-3-opus-20240229` - Most capable (vision)
- `claude-3-sonnet-20240229` - Balanced (vision)
- `claude-3-haiku-20240307` - Fast and affordable (vision)

### OpenAI GPT

```python
ai_options = {
    'ai_provider': 'openai',
    'ai_model': 'gpt-4o',  # GPT-4 Omni (vision)
    'max_tokens': 1024,
    'temperature': 0.3,
    'timeout': 60
}
```

**Available Models**:
- `gpt-4o` - Multimodal (text + vision)
- `gpt-4-turbo` - Fast GPT-4
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Fast and affordable

### OpenRouter

```python
ai_options = {
    'ai_provider': 'openrouter',
    'ai_model': 'meta-llama/llama-3.2-3b-instruct:free',  # Free tier
    'max_tokens': 1024,
    'temperature': 0.3
}
```

**Popular Models**:
- `meta-llama/llama-3.2-3b-instruct:free` - Free tier
- `google/gemini-pro` - Google's model
- `anthropic/claude-3-sonnet` - Claude via OpenRouter

Browse models: https://openrouter.ai/models

### Ollama (Local)

```python
ai_options = {
    'ai_provider': 'ollama',
    'ai_model': 'llama3.2:latest',
    'base_url': 'http://localhost:11434/v1'  # Optional, uses default
}
```

**Setup**:
1. Install Ollama: https://ollama.ai
2. Pull model: `ollama pull llama3.2`
3. No API key required

**Popular Models**:
- `llama3.2:latest` - Meta Llama 3.2
- `mistral:latest` - Mistral 7B
- `llava:latest` - Vision model for image analysis

### LM Studio (Local)

```python
ai_options = {
    'ai_provider': 'lmstudio',
    'ai_model': 'local-model',
    'base_url': 'http://localhost:1234/v1'  # Optional, uses default
}
```

**Setup**:
1. Install LM Studio: https://lmstudio.ai
2. Download GGUF model
3. Start local server
4. No API key required

## Error Handling

The AI processors include automatic retry logic with exponential backoff:

```python
from omniparser.processors.ai_tagger import generate_tags

try:
    tags = generate_tags(doc, max_tags=10)
except ValueError as e:
    # Input validation errors
    print(f"Invalid input: {e}")
except Exception as e:
    # API errors after retries
    print(f"API error: {e}")
```

**Retry Behavior**:
- **Retriable Errors**: Rate limits (429), server errors (500, 502, 503, 504), timeouts, network errors
- **Non-Retriable Errors**: Authentication (401, 403), bad requests (400), not found (404)
- **Retry Schedule**: Exponential backoff (1s → 2s → 4s with default max_retries=3)

**Common Errors**:

```python
# Missing API key
# ValueError: ANTHROPIC_API_KEY environment variable not set

# Invalid input
# ValueError: max_tags must be positive

# Document has no content
# ValueError: Document has no content to analyze

# Unsupported image format
# ValueError: Unsupported image format: .bmp. Supported formats: .jpg, .jpeg, .png, .gif, .webp

# Image too large
# ValueError: Image file too large: 15.2MB. Maximum size: 10MB
```

## Memory Usage

**Image Processing**:
- Images are loaded into memory and base64-encoded (~33% size increase)
- **10MB limit per image** to prevent memory issues
- For large documents with many images, consider processing in batches

**Document Processing**:
- Content is sampled to reduce API costs and memory:
  - **Tagging**: First 2000 characters
  - **Quality Scoring**: First 3000 characters
  - **Summarization**: First 5000 characters
- Full chapter content used for chapter-specific operations

## Best Practices

### 1. Choose the Right Provider

- **Cloud providers** (Anthropic, OpenAI): Best quality, requires API key and costs money
- **OpenRouter**: Access to 200+ models, flexible pricing
- **Local models** (Ollama, LM Studio): Free, private, no API key, but slower and lower quality

### 2. Use Appropriate Models

- **Fast tasks** (tagging, concise summaries): Use haiku/gpt-3.5-turbo
- **Quality-critical tasks** (detailed analysis): Use opus/gpt-4
- **Vision tasks**: Use vision-capable models (Claude 3, GPT-4o, llava)

### 3. Optimize Costs

```python
# Use smaller, faster models for initial processing
tags = generate_tags(doc, ai_options={'ai_model': 'claude-3-haiku-20240307'})

# Use free tier models via OpenRouter
summary = summarize_document(
    doc,
    ai_options={
        'ai_provider': 'openrouter',
        'ai_model': 'meta-llama/llama-3.2-3b-instruct:free'
    }
)

# Use local models for privacy/cost savings
quality = score_quality(
    doc,
    ai_options={
        'ai_provider': 'ollama',
        'ai_model': 'llama3.2:latest'
    }
)
```

### 4. Handle Errors Gracefully

```python
from omniparser.processors.ai_tagger import generate_tags

# Validate inputs before processing
if not doc.content:
    print("Document is empty, skipping AI processing")
else:
    try:
        tags = generate_tags(doc, max_tags=10)
        print(f"Generated tags: {tags}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"API error (will be logged): {e}")
```

### 5. Monitor Parsing Warnings

AI responses are parsed using regex patterns. Check logs for parsing warnings:

```python
import logging

# Enable logging to see parsing warnings
logging.basicConfig(level=logging.WARNING)

# If parsing fails, warnings will be logged:
# "Failed to extract image type from response. Response preview: ..."
```

## Examples

### Complete Document Enhancement Pipeline

```python
from omniparser import parse_document
from omniparser.processors.ai_tagger import generate_tags
from omniparser.processors.ai_summarizer import summarize_document
from omniparser.processors.ai_quality import score_quality
from omniparser.processors.ai_image_describer import update_image_descriptions

# Parse document
doc = parse_document("research_paper.pdf")

# Generate tags
tags = generate_tags(doc, max_tags=8)
doc.metadata.tags = tags

# Generate summary
summary = summarize_document(doc, style="detailed", max_length=500)
print(f"Summary: {summary}")

# Score quality
quality = score_quality(doc)
print(f"\nQuality Score: {quality['overall_score']}/100")
print(f"Strengths: {', '.join(quality['strengths'])}")
print(f"Suggestions: {', '.join(quality['suggestions'])}")

# Update image descriptions
doc = update_image_descriptions(doc)

# Save enhanced document
doc.save_json("enhanced_document.json")
```

### Multi-Provider Comparison

```python
from omniparser import parse_document
from omniparser.processors.ai_summarizer import summarize_document

doc = parse_document("article.md")

providers = [
    {'ai_provider': 'anthropic', 'ai_model': 'claude-3-haiku-20240307'},
    {'ai_provider': 'openai', 'ai_model': 'gpt-3.5-turbo'},
    {'ai_provider': 'ollama', 'ai_model': 'llama3.2:latest'},
]

for provider in providers:
    try:
        summary = summarize_document(doc, style="concise", ai_options=provider)
        print(f"\n{provider['ai_provider']}:")
        print(summary)
    except Exception as e:
        print(f"\n{provider['ai_provider']}: Error - {e}")
```

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY environment variable not set"

**Solution**: Set API key in environment:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
# Or add to .bashrc / .zshrc for persistence
```

### Issue: "Image file too large: 15.2MB. Maximum size: 10MB"

**Solution**: Compress image before processing:

```bash
# Using ImageMagick
convert large_image.png -quality 85 -resize 2048x2048\> compressed.png

# Using Python PIL
from PIL import Image
img = Image.open("large_image.png")
img.thumbnail((2048, 2048))
img.save("compressed.png", optimize=True, quality=85)
```

### Issue: API timeouts with local models

**Solution**: Increase timeout in ai_options:

```python
ai_options = {
    'ai_provider': 'ollama',
    'ai_model': 'llama3.2:latest',
    'timeout': 120  # Increase to 120 seconds
}
```

### Issue: Parsing warnings in logs

**Solution**: This indicates AI response format varied from expected. Check raw responses:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Raw responses will be logged for debugging
```

## API Reference

See module docstrings for detailed API documentation:

- `omniparser.ai_config.AIConfig` - AI configuration and client management
- `omniparser.processors.ai_tagger` - Auto-tagging
- `omniparser.processors.ai_summarizer` - Summarization
- `omniparser.processors.ai_quality` - Quality scoring
- `omniparser.processors.ai_image_describer` - Image description
- `omniparser.processors.ai_image_analyzer` - Image analysis pipeline

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to OmniParser's AI features.

## License

OmniParser is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
