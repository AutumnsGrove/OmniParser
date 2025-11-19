# OmniParser - Universal Document Parser

**Status:** Phase 2.8 Complete ✅ | 6 Parsers + AI Features Production-Ready
**Version:** 0.3.0 (Development)
**License:** MIT

---

> **Any file format → clean markdown.**
>
> OmniParser is a universal document parser that transforms documents, web pages, and structured data into standardized markdown with comprehensive metadata. Connect it to your pipelines, tools, or workflows—anywhere you need intelligent document ingestion.

---

## Parser Implementation Status

| Format | Status | Features |
|--------|--------|----------|
| 📖 EPUB | ✅ **Production** | TOC chapters, images, metadata extraction |
| 🌐 HTML/URL | ✅ **Production** | Semantic parsing, URL support, images |
| 📄 PDF | ✅ **Production** | Multi-column layout, images, tables |
| 📝 DOCX | ✅ **Production** | Text extraction, tables, lists, hyperlinks, images |
| 📋 Markdown | ✅ **Production** | Frontmatter, code blocks, link preservation |
| 📃 Text | ✅ **Production** | Auto chapter detection, encoding handling |

**QR Code Support:** ✅ Detect QR codes in PDFs and images, fetch URL content (optional, requires `pyzbar`)

**AI Features:** ✅ Auto-tagging, summarization, image analysis, quality scoring (optional, requires `ai` extra)

---

## Quick Navigation

### 📋 Planning Documents (Start Here)

1. **[RESEARCH_SYNTHESIS_SUMMARY.md](docs/RESEARCH_SYNTHESIS_SUMMARY.md)** - Executive summary of architecture planning
   - 16,000 words | Read time: 20 minutes
   - Overview of all design decisions and implementation strategy

2. **[ARCHITECTURE_PLAN.md](docs/ARCHITECTURE_PLAN.md)** - Complete implementation blueprint
   - 40,000 words | Read time: 60 minutes
   - Phase-by-phase implementation guide (16 phases)
   - epub2tts migration strategy
   - Risk assessment

3. **[IMPLEMENTATION_REFERENCE.md](docs/IMPLEMENTATION_REFERENCE.md)** - Developer quick reference
   - 16,000 words | Read time: 20 minutes
   - API contracts
   - Code patterns
   - Command reference
   - Troubleshooting guide

4. **[ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md)** - Visual architecture reference
   - 37,000 words | Read time: 30 minutes
   - System diagrams
   - Data flow diagrams
   - Component structure
   - Package layout

5. **[OMNIPARSER_PROJECT_SPEC.md](docs/OMNIPARSER_PROJECT_SPEC.md)** - Original project specification
   - 36,000 words | Read time: 45 minutes
   - Complete technical specification
   - API reference
   - Usage examples

---

## Project Overview

OmniParser is a **universal content ingestion platform** that transforms any document, web page, social media post, feed, or structured data into clean, standardized markdown with comprehensive metadata extraction.

### Vision: Parse Anything, Output Consistency

From books and PDFs to blog posts and tweets, from research papers to Reddit threads - OmniParser provides a **single unified API** that handles 20+ input formats and delivers consistent, structured output every time.

### Primary Goals

1. Extract epub2tts's production-tested EPUB processing into a reusable library ✅ **COMPLETE**
2. Create unified interface for parsing **any content source** regardless of format ✅ **Architecture Complete**
3. Provide consistent data models across all parsers ✅ **Implemented**
4. Enable epub2tts, RAG systems, content platforms, and other projects to consume document parsing as a service 🚧 **In Progress**

---

## What Works Today (v0.3.0)

### 6 Production-Ready Parsers

**EPUB Parser** - Digital books and ebooks
```python
from omniparser import parse_document

doc = parse_document("alice-in-wonderland.epub")
# TOC-based chapters, metadata, images
# 357 tests passing | 5MB in ~0.25 seconds
```

**HTML/URL Parser** - Web pages and articles
```python
doc = parse_document("https://example.com/article.html", {
    "extract_images": True,
    "max_image_workers": 10,  # Parallel downloads
    "rate_limit_delay": 0.5   # Rate limiting
})
# Semantic parsing, OpenGraph metadata
# 105 tests passing | <0.2 seconds
```

**PDF Parser** - Documents and reports
```python
doc = parse_document("research-paper.pdf", {
    "extract_images": True,
    "ocr_enabled": False  # Enable for scanned PDFs
})
# Multi-column layout, images, tables
# 89 tests passing | Handles complex layouts
```

**PDF with QR Code Detection** - Extract and fetch QR code content
```python
doc = parse_document("document-with-qr.pdf", {
    "detect_qr_codes": True,      # Enable QR detection
    "qr_fetch_urls": True,        # Fetch content from URL QR codes
    "qr_timeout": 15,             # URL fetch timeout (seconds)
    "qr_dpi": 150                 # DPI for page rendering
})
# Detected QR codes available in doc.qr_codes
# Fetched URL content merged into document
for qr in doc.qr_codes:
    print(f"QR {qr.qr_id}: {qr.data_type} - {qr.raw_data}")
    if qr.fetched_content:
        print(f"  Content: {qr.fetched_content[:100]}...")
```

**DOCX Parser** - Microsoft Word documents (Beta)
```python
doc = parse_document("report.docx")
# Text extraction, tables, basic images
# 67 tests passing | Production-ready for text-heavy docs
```

**Markdown Parser** - Parse and normalize Markdown
```python
doc = parse_document("README.md")
# Frontmatter, code blocks, links preserved
# 45 tests passing | Fast and lightweight
```

**Text Parser** - Plain text files
```python
doc = parse_document("notes.txt")
# Auto chapter detection, encoding handling
# 33 tests passing | Smart formatting
```

### QR Code Detection (Optional)

**Detect and extract content from QR codes in PDFs and images:**

```python
from omniparser import parse_document

# Parse PDF with QR code detection enabled
doc = parse_document("document.pdf", {
    "detect_qr_codes": True,
    "qr_fetch_urls": True,
})

# Access detected QR codes
print(f"Found {len(doc.qr_codes)} QR codes")

for qr in doc.qr_codes:
    print(f"QR {qr.qr_id}: {qr.data_type}")
    print(f"  Data: {qr.raw_data}")
    if qr.fetched_content:
        print(f"  Fetched: {len(qr.fetched_content)} characters")
```

**QR Code Features:**
- ✅ **Multi-format detection** - URL, Email, Phone, WiFi, vCard, Geo, SMS, Text
- ✅ **Automatic URL fetching** - Retrieve content from URL QR codes
- ✅ **Wayback Machine fallback** - Access archived content for dead links
- ✅ **Document integration** - Merge fetched content into document
- ✅ **Position tracking** - Track QR code location and page number

**Standalone Image Scanning:**
```python
from omniparser.processors.qr_detector import scan_image_for_qr_and_fetch

# Scan any image file for QR codes
qr_codes, warnings = scan_image_for_qr_and_fetch("image.png", fetch_urls=True)

for qr in qr_codes:
    print(f"{qr.data_type}: {qr.raw_data}")
```

**Requirements:** Requires `pyzbar` library and system `zbar` library:
```bash
# Install pyzbar
pip install pyzbar

# On Ubuntu/Debian
apt-get install libzbar0

# On macOS
brew install zbar
```

---

### AI-Powered Features (Optional)

**Enhanced document understanding with multiple AI providers:**

```python
from omniparser import parse_document
from omniparser.processors.ai_tagger import generate_tags
from omniparser.processors.ai_summarizer import summarize_document
from omniparser.processors.ai_quality_scorer import score_quality
from omniparser.utils.config import get_ai_options, load_config

# Parse any document
doc = parse_document("book.epub")

# Configure AI provider
config = load_config()
ai_options = get_ai_options("anthropic", config)  # or "openai", "ollama", etc.

# Generate tags
tags = generate_tags(doc, max_tags=10, ai_options=ai_options)
print(f"Tags: {', '.join(tags)}")

# Summarize content
summary = summarize_document(doc, style="concise", ai_options=ai_options)
print(f"Summary: {summary}")

# Score quality
quality = score_quality(doc, ai_options=ai_options)
print(f"Readability: {quality['readability_score']}/10")
```

**Available AI Features:**
- ✅ **Auto-Tagging** - Generate relevant tags from content
- ✅ **Summarization** - Concise, detailed, or bullet-point summaries
- ✅ **Image Analysis** - Vision models for alt text and descriptions
- ✅ **Quality Scoring** - Readability, structure, completeness assessment
- ✅ **Multi-Provider Support** - Anthropic, OpenAI, OpenRouter, Ollama, LM Studio

**Performance:**
- 1070+ tests (100% success rate)
- All parsers production-ready except DOCX (beta)
- AI features and QR detection fully optional (no dependency overhead)

---

## Future Features

### Future Expansion (v0.4+)
- **Web & Social:** Twitter/X, Reddit, LinkedIn, Medium, RSS/Atom feeds
- **Cloud Platforms:** Google Docs, Notion, Confluence, Dropbox Paper
- **Structured Data:** JSON, XML, CSV, YAML parsing with schema detection
- **Archives:** ZIP/TAR support with batch processing
- **Technical:** Jupyter notebooks, code documentation, API specs
- **Advanced AI:** Semantic analysis, question answering, content classification (v1.0+)

**📖 See [Diagrams/comprehensive-workflow.md](docs/Diagrams/comprehensive-workflow.md) for the complete vision**

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│              parse_document(file_path)                  │
│                  Main Entry Point                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  EPUBParser │ PDFParser │ DOCXParser │ HTMLParser       │
│  All inherit from BaseParser                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  chapter_detector │ metadata_extractor │ text_cleaner   │
│  Shared Processing Components                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Document(content, chapters, images, metadata)          │
│  Universal Data Model                                   │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Installation (Development)

**Note:** OmniParser v0.1.0 is currently in development. Install from source:

```bash
# Clone repository
git clone https://github.com/AutumnsGrove/omniparser.git
cd omniparser

# Install with UV (recommended)
uv sync

# Or with pip
pip install -e .
```

**Lightweight Installation** (without 25MB of example EPUB files):
```bash
# Clone without large files
git clone --filter=blob:none --no-checkout https://github.com/AutumnsGrove/omniparser.git
cd omniparser
git sparse-checkout init --cone
git sparse-checkout set '/*' '!tests/fixtures/epub/*.epub'
git checkout
uv sync
```

### Basic Usage (All 6 Parsers - v0.3.0)

```python
from omniparser import parse_document

# Parse any supported format - automatic detection
doc = parse_document("book.epub")           # EPUB
doc = parse_document("report.pdf")          # PDF
doc = parse_document("document.docx")       # DOCX
doc = parse_document("article.html")        # HTML
doc = parse_document("README.md")           # Markdown
doc = parse_document("notes.txt")           # Text
doc = parse_document("https://example.com") # URL

# Access metadata
print(f"Title: {doc.metadata.title}")
print(f"Author: {doc.metadata.author}")
print(f"Language: {doc.metadata.language}")

# Access content
print(f"Chapters: {len(doc.chapters)}")
print(f"Word count: {doc.word_count}")
print(f"Reading time: {doc.reading_time_minutes} minutes")

# Iterate chapters
for chapter in doc.chapters:
    print(f"Chapter {chapter.chapter_id}: {chapter.title}")
    print(f"  Words: {chapter.word_count}")
    print(f"  Start: position {chapter.start_position}")

# Access images
for image in doc.images:
    print(f"Image: {image.filename} ({image.format})")
```

### EPUB to Markdown Conversion

See the complete working example in `examples/epub_to_markdown.py`:

```python
# Converts EPUB to Obsidian-compatible Markdown
# with YAML frontmatter, TOC, and image embedding
python examples/epub_to_markdown.py book.epub output/
```

---

## AI-Powered Features (Optional)

OmniParser includes **optional AI-powered features** for enhanced document understanding and processing. These features require the `ai` extra dependencies.

### Supported AI Providers

| Provider | Cloud/Local | API Key Required | Best For |
|----------|-------------|------------------|----------|
| **Anthropic Claude** | ☁️ Cloud | ✅ Yes | Vision tasks, high-quality analysis |
| **OpenAI GPT** | ☁️ Cloud | ✅ Yes | General purpose, good performance |
| **OpenRouter** | ☁️ Cloud | ✅ Yes | Access to multiple models via one API |
| **Ollama** | 🏠 Local | ❌ No | Privacy, no API costs, offline |
| **LM Studio** | 🏠 Local | ❌ No | Privacy, no API costs, offline |

### AI Features Available

1. **Auto-Tagging** - Generate relevant tags based on content
2. **Summarization** - Create concise, detailed, or bullet-point summaries
3. **Image Description** - Generate alt text and descriptions using vision models
4. **Quality Scoring** - Assess readability, structure, completeness, and coherence
5. **Image Analysis** - Extract text (OCR), classify image types, detect objects

### Quick Start with AI

**1. Install AI dependencies:**
```bash
uv sync --extra ai
```

**2. Set up your secrets:**
```bash
# Copy the template
cp secrets_template.json secrets.json

# Edit secrets.json and add your API keys:
{
  "anthropic_api_key": "sk-ant-...",
  "openai_api_key": "sk-...",
  "ollama_base_url": "http://localhost:11434/v1",
  "lmstudio_base_url": "http://localhost:1234/v1"
}
```

**3. (Optional) Customize configuration:**
```bash
# Copy the config template
cp config_template.json config.json

# Edit config.json to customize models, timeouts, etc.
```

**4. Use AI features in your code:**
```python
from omniparser import parse_document
from omniparser.processors.ai_tagger import generate_tags
from omniparser.processors.ai_summarizer import summarize_document
from omniparser.utils.config import get_ai_options, load_config

# Parse document
doc = parse_document("book.epub")

# Get AI configuration for your provider
config = load_config()
ai_options = get_ai_options("anthropic", config)  # or "openai", "ollama", etc.

# Generate tags
tags = generate_tags(doc, max_tags=10, ai_options=ai_options)
print(f"Tags: {', '.join(tags)}")

# Generate summary
summary = summarize_document(doc, style="concise", ai_options=ai_options)
print(f"Summary: {summary}")
```

### Complete AI Example

See `examples/ai_usage_example.py` for comprehensive examples of all AI features:

```bash
# Use Anthropic Claude
python examples/ai_usage_example.py --file book.epub --provider anthropic --all-features

# Use local Ollama
python examples/ai_usage_example.py --file book.epub --provider ollama --summarize

# Compare different providers
python examples/ai_usage_example.py --file book.epub --compare
```

**Important Note:** If your file path contains spaces, you must quote it in your shell command:

```bash
# ✅ Correct - with quotes
python examples/ai_usage_example.py --file "My Book With Spaces.epub" --provider anthropic --all-features

# ❌ Incorrect - without quotes (will fail)
python examples/ai_usage_example.py --file My Book With Spaces.epub --provider anthropic --all-features
```

This is standard shell behavior and applies to all command-line tools, not just OmniParser.

### Configuration Files

**`secrets.json` (gitignored)** - API keys and endpoints
```json
{
  "anthropic_api_key": "sk-ant-...",
  "openai_api_key": "sk-...",
  "ollama_base_url": "http://localhost:11434/v1"
}
```

**`config.json` (optional)** - AI models and parsing settings
```json
{
  "ai": {
    "default_provider": "anthropic",
    "anthropic": {
      "model": "claude-3-haiku-20240307",
      "max_tokens": 1024,
      "temperature": 0.3
    }
  },
  "parsing": {
    "extract_images": true,
    "clean_text": true
  }
}
```

**Priority order:** `user_options` → `config_local.json` → `config.json` → `defaults`

### Environment Variables (Alternative)

You can also use environment variables instead of `secrets.json`:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export OLLAMA_BASE_URL="http://localhost:11434/v1"
```

**Note:** `secrets.json` takes precedence over environment variables.

---

## Implementation Roadmap

### Phase 1-5: Foundation (18 hours)
- Repository setup
- Data models
- Base parser interface
- Utilities and exceptions

### Phase 6-7: Core Parsers (12 hours)
- EPUB parser (port from epub2tts)
- PDF parser (PyMuPDF + OCR)

### Phase 8-10: Additional Parsers (9 hours)
- DOCX parser
- HTML/URL parser
- Markdown & Text parsers

### Phase 11-14: Integration (17 hours)
- Post-processors
- Main parser function
- Package exports
- Integration tests

### Phase 15-16: Polish (8 hours)
- Documentation
- Final validation

**Total Estimated Time:** 64 hours (8 working days)

---

## Current Status

### ✅ Phase 1: Planning & Research (COMPLETE - Oct 16, 2025)
- [x] Project specification (36,000 words)
- [x] Architecture planning (40,000 words, 16-phase plan)
- [x] Implementation reference (16,000 words)
- [x] Architecture diagrams (37,000 words, 14 diagrams)
- [x] epub2tts migration strategy
- [x] Risk assessment

### ✅ Phase 2.1: Foundation (COMPLETE - Oct 16, 2025)
- [x] Universal data models (Document, Chapter, Metadata, ImageReference, ProcessingInfo)
- [x] Exception hierarchy (6 custom exception classes)
- [x] BaseParser abstract interface
- [x] Utility modules (format_detector, encoding, validators)
- [x] Package configuration (pyproject.toml with UV/hatchling)
- [x] 171 comprehensive unit tests (100% passing)

### ✅ Phase 2.2: EPUB Parser (COMPLETE - Oct 20, 2025)
- [x] Complete EPUBParser implementation (~1,030 lines)
- [x] TOC-based chapter detection (with spine-based fallback)
- [x] Metadata extraction from OPF (Dublin Core fields)
- [x] HTML to Markdown text extraction
- [x] Image extraction with persistent/temporary directory support
- [x] Text cleaning processor (no TTS-specific features)
- [x] Main parse_document() API integration
- [x] 342 tests passing (141 new EPUB tests)
- [x] All code Black formatted and type-hinted

### ✅ Phase 2.3: Integration Testing (COMPLETE - Oct 20, 2025)
- [x] 5 Project Gutenberg EPUBs added (26MB test fixtures)
- [x] 15 integration tests with real EPUB files (221 lines)
- [x] EPUB to Markdown demo application (213 lines)
- [x] Persistent image extraction feature added
- [x] Obsidian-compatible markdown output
- [x] Performance validated: 0.25s for 5MB EPUB (20x faster than 5s target!)
- [x] **357 total tests passing (100% success rate)**

### ✅ Phase 2.5: HTML/URL Parser (COMPLETE - Oct 29, 2025)
- [x] Complete HTMLParser implementation (~650 lines)
- [x] Live URL fetching with configurable timeout
- [x] Parallel image downloads using ThreadPoolExecutor
- [x] Configurable rate limiting for requests
- [x] Custom User-Agent support
- [x] Comprehensive image extraction with metadata
- [x] OpenGraph/Dublin Core metadata extraction
- [x] Heading-based chapter detection
- [x] Shared processor utilities (markdown_converter, chapter_detector, metadata_extractor)
- [x] 105 tests passing (74 unit + 31 integration)
- [x] All code Black formatted and type-hinted
- [x] **468 total tests passing (100% success rate)**

### ✅ Phase 2.6: PDF Parser (COMPLETE - Oct 29, 2025)
- [x] Complete PDFParser implementation with PyMuPDF
- [x] Multi-column layout detection
- [x] Image extraction from PDF
- [x] Table detection and preservation
- [x] 89 tests passing (58 unit + 31 integration)
- [x] **557 total tests passing (100% success rate)**

### ✅ Phase 2.7: DOCX, Markdown, Text Parsers (COMPLETE - Oct 29, 2025)
- [x] DOCXParser implementation (Beta - text and tables)
- [x] MarkdownParser implementation (frontmatter, code blocks)
- [x] TextParser implementation (auto chapter detection)
- [x] 145 additional tests (67 DOCX, 45 Markdown, 33 Text)
- [x] **696 total tests passing (100% success rate)**

### ✅ Phase 2.8: AI Features (COMPLETE - Oct 29, 2025)
- [x] AI configuration system (secrets, config files)
- [x] Multi-provider support (Anthropic, OpenAI, OpenRouter, Ollama, LM Studio)
- [x] Auto-tagging processor
- [x] Document summarization (concise, detailed, bullet-point)
- [x] Image analysis and description
- [x] Quality scoring system
- [x] Comprehensive AI tests and examples
- [x] **Phase 2.8 Complete - 6 Parsers + AI Features**

### 📋 Next Steps

**Option A: Phase 3 - Package Release** (Recommended)
- [ ] Update documentation for v0.3.0
- [ ] Set up CI/CD pipeline
- [ ] Publish to PyPI as multi-format parser
- [ ] Create demo repository
- [ ] User onboarding guide

**Option B: Phase 4 - epub2tts Integration**
- [ ] Integrate OmniParser into epub2tts
- [ ] Validate TTS pipeline works
- [ ] Performance testing

**Future Phases:**
- [ ] Additional parsers (social media, cloud platforms)
- [ ] Advanced AI features (semantic analysis, Q&A)
- [ ] Web API/service deployment

---

## Documentation Index

### Planning Documents
- **[docs/RESEARCH_SYNTHESIS_SUMMARY.md](docs/RESEARCH_SYNTHESIS_SUMMARY.md)** - High-level overview
- **[docs/ARCHITECTURE_PLAN.md](docs/ARCHITECTURE_PLAN.md)** - Detailed implementation plan
- **[docs/IMPLEMENTATION_REFERENCE.md](docs/IMPLEMENTATION_REFERENCE.md)** - Developer quick reference
- **[docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md)** - Visual architecture
- **[docs/OMNIPARSER_PROJECT_SPEC.md](docs/OMNIPARSER_PROJECT_SPEC.md)** - Technical specification

### Visual Workflows
- **[docs/Diagrams/comprehensive-workflow.md](docs/Diagrams/comprehensive-workflow.md)** - 🆕 **Comprehensive workflow vision**
  - Universal content ingestion platform
  - 20+ input sources (documents, web, social, feeds, cloud, code)
  - Complete parser routing and processing pipeline
  - Integration patterns and consumers
  - Future roadmap and expansion phases
  - **Start here to see the full scope of OmniParser's potential**

### Source Materials (Reference)
- **epub2tts:** Original EPUB processing implementation
  - `METAPROMPT_1_OMNIPARSER_EXTRACTION.md`
  - `src/core/ebooklib_processor.py` (963 lines)
  - `src/core/text_cleaner.py` (522 lines)

---

## Key Design Decisions

### 1. Universal Data Model
All parsers return the same `Document` structure:
- `content`: Full text as markdown
- `chapters`: List of Chapter objects with boundaries
- `images`: List of ImageReference objects
- `metadata`: Title, author, publisher, etc.
- `processing_info`: Parser execution metadata

### 2. Options-Based Configuration
No Config object dependency - everything via options dict:
```python
parser = EPUBParser({
    'extract_images': True,
    'detect_chapters': True,
    'clean_text': True
})
```

### 3. Clean Separation from epub2tts
- **OmniParser:** Document parsing, format handling
- **epub2tts:** TTS processing, audio generation
- No TTS-specific features in OmniParser
- epub2tts applies TTS processing after parsing

### 4. BaseParser Interface
All parsers inherit from abstract base class:
```python
class BaseParser(ABC):
    def parse(self, file_path: Path) -> Document
    def supports_format(self, file_path: Path) -> bool
    def extract_images(self, file_path: Path) -> List[ImageReference]
    def clean_text(self, text: str) -> str
```

---

## Dependencies

### Currently Active (v0.2.1 - EPUB & HTML Parsers)
- **Core Processing:**
  - pyyaml>=6.0 - Configuration and data serialization
  - beautifulsoup4>=4.12.0 - HTML parsing
  - lxml>=5.0.0 - XML/HTML processing
  - ftfy>=6.1.0 - Text encoding fixes
  - python-magic>=0.4.27 - Format detection

- **EPUB Parser:**
  - ebooklib>=0.18 - EPUB file handling
  - Pillow>=10.0.0 - Image extraction
  - chardet>=5.2.0 - Character encoding detection
  - regex>=2023.0.0 - Pattern matching

- **HTML/URL Parser:**
  - requests>=2.31.0 - HTTP requests for URL fetching
  - trafilatura>=1.6.0 - Main HTML content extraction
  - readability-lxml>=0.8.0 - Fallback content extraction

- **QR Code Detection:**
  - pyzbar>=0.1.9 - QR code detection library
  - Requires system library: `libzbar0` (Linux) or `zbar` (macOS)

### Installed but Not Yet Used (Future Parsers)
- **PDF (Phase 2.4):** PyMuPDF>=1.23.0, pytesseract>=0.3.10
- **DOCX (Phase 2.6):** python-docx>=1.0.0

### Development
- pytest>=8.4.2, pytest-cov>=7.0.0
- black>=25.9.0, mypy>=1.18.2

---

## Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/AutumnsGrove/omniparser.git
cd omniparser

# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/
```

### Adding a New Parser
1. Create `parsers/new_format_parser.py`
2. Inherit from `BaseParser`
3. Implement `parse()` and `supports_format()`
4. Add tests in `tests/unit/test_new_format_parser.py`
5. Update documentation

---

## Testing Strategy

### Coverage Goals
- Overall: >80%
- Data models: 100%
- Parsers: >90%
- Utilities: >85%

### Test Structure
```
tests/
├── unit/                # Fast, isolated tests
├── integration/         # End-to-end tests
└── fixtures/            # Test data files
```

---

## Success Metrics

### v0.3.0 - 6 Parsers + AI Features (Current)
- [x] 6 parsers implemented (EPUB, HTML, PDF, DOCX, Markdown, Text)
- [x] AI features with multi-provider support
- [x] >90% test coverage for all components (696 tests passing)
- [x] Package builds successfully: `uv build`
- [x] Can install from source: `uv sync` or `pip install -e .`
- [x] Examples run successfully (epub_to_markdown.py, ai_usage_example.py)
- [x] Performance exceeds targets (all parsers optimized)
- [x] Real-world validation (multiple test fixtures, live URL testing)
- [ ] PyPI publication (pending Phase 3)

### v1.0.0 - Public Release (Next Target)
- [x] 6+ parsers implemented (EPUB ✅, HTML ✅, PDF ✅, DOCX ✅, Markdown ✅, Text ✅)
- [x] >80% overall test coverage (achieved with 696 tests)
- [x] >500 total tests (696 currently passing)
- [ ] Published to PyPI: `pip install omniparser`
- [ ] CI/CD pipeline operational
- [ ] Complete API documentation
- [ ] epub2tts integration validated

### epub2tts Integration (Phase 4)
- [ ] epub2tts uses OmniParser dependency
- [ ] All epub2tts tests pass
- [ ] Audio generation works with OmniParser
- [ ] No performance regression >20%

---

## Timeline

**Week 1-2:** Foundation + EPUB parser (30 hours)
**Week 3:** Additional parsers (9 hours)
**Week 4:** Integration + tests (17 hours)
**Week 5:** Documentation + validation (8 hours)
**Week 6:** epub2tts migration (16 hours)

**Total:** 80 hours over 6 weeks

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

- **epub2tts** - Original EPUB processing logic
- **EbookLib** - EPUB parsing
- **PyMuPDF** - PDF parsing
- **python-docx** - DOCX parsing
- **Trafilatura** - HTML content extraction

---

## Contact

**Project:** https://github.com/AutumnsGrove/omniparser
**Issues:** https://github.com/AutumnsGrove/omniparser/issues
**Documentation:** (Coming soon)

---

**Status:** Phase 2.8 Complete ✅ | 6 Parsers + AI Features Production-Ready
**Version:** v0.3.0 (Development)
**Next Action:** Phase 3 (PyPI Release) or Phase 4 (epub2tts Integration)
**Last Updated:** October 29, 2025
