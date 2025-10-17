# OmniParser - Universal Document Parser

**Status:** Planning Phase Complete ✅
**Version:** 1.0.0 (Target)
**License:** MIT

---

## Quick Navigation

### 📋 Planning Documents (Start Here)

1. **[RESEARCH_SYNTHESIS_SUMMARY.md](RESEARCH_SYNTHESIS_SUMMARY.md)** - Executive summary of architecture planning
   - 16,000 words | Read time: 20 minutes
   - Overview of all design decisions and implementation strategy

2. **[ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md)** - Complete implementation blueprint
   - 40,000 words | Read time: 60 minutes
   - Phase-by-phase implementation guide (16 phases)
   - epub2tts migration strategy
   - Risk assessment

3. **[IMPLEMENTATION_REFERENCE.md](IMPLEMENTATION_REFERENCE.md)** - Developer quick reference
   - 16,000 words | Read time: 20 minutes
   - API contracts
   - Code patterns
   - Command reference
   - Troubleshooting guide

4. **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - Visual architecture reference
   - 37,000 words | Read time: 30 minutes
   - System diagrams
   - Data flow diagrams
   - Component structure
   - Package layout

5. **[OMNIPARSER_PROJECT_SPEC.md](OMNIPARSER_PROJECT_SPEC.md)** - Original project specification
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

1. Extract epub2tts's production-tested EPUB processing into a reusable library
2. Create unified interface for parsing **any content source** regardless of format
3. Provide consistent data models across all parsers
4. Enable epub2tts, RAG systems, content platforms, and other projects to consume document parsing as a service

### Key Features

#### v1.0-1.2 (Core Foundation)
- **6 Format Parsers:** EPUB, PDF, DOCX, HTML/URL, Markdown, Text
- **Universal Output:** All parsers return same Document structure
- **Chapter Detection:** Intelligent heading-based chapter boundaries
- **Metadata Extraction:** Author, title, publisher, etc.
- **Image Handling:** Extract and catalog images with position tracking
- **Text Cleaning:** Encoding fixes, normalization, whitespace handling
- **PyPI Ready:** Professional package for `pip install omniparser`

#### Future Expansion (v1.3+)
- **Web & Social:** Twitter/X, Reddit, LinkedIn, Medium, RSS/Atom feeds
- **Cloud Platforms:** Google Docs, Notion, Confluence, Dropbox Paper
- **Structured Data:** JSON, XML, CSV, YAML parsing with schema detection
- **Archives:** ZIP/TAR support with batch processing
- **Technical:** Jupyter notebooks, code documentation, API specs
- **AI-Powered:** Semantic analysis, auto-tagging, summarization (v2.0+)

**📖 See [Diagrams/comprehensive-workflow.md](Diagrams/comprehensive-workflow.md) for the complete vision**

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

## Quick Start (Future)

### Installation
```bash
pip install omniparser
# or
uv add omniparser
```

### Basic Usage
```python
from omniparser import parse_document

# Parse any supported format
doc = parse_document("book.epub")

# Access data
print(f"Title: {doc.metadata.title}")
print(f"Chapters: {len(doc.chapters)}")
print(f"Word count: {doc.word_count}")

# Iterate chapters
for chapter in doc.chapters:
    print(f"Chapter {chapter.chapter_id}: {chapter.title}")
    print(f"Words: {chapter.word_count}")
```

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

### ✅ Completed
- [x] Project specification written
- [x] Architecture planning complete
- [x] Implementation strategy documented
- [x] epub2tts migration plan created
- [x] Risk assessment completed
- [x] Visual diagrams created

### 🚧 In Progress
- [ ] Phase 1: Repository setup
- [ ] Phase 2: Core data models
- [ ] Phase 3: Base parser interface

### 📋 Planned
- [ ] Phases 4-16: Implementation
- [ ] PyPI publication
- [ ] epub2tts integration
- [ ] v1.1+ features

---

## Documentation Index

### Planning Documents
- **RESEARCH_SYNTHESIS_SUMMARY.md** - High-level overview
- **ARCHITECTURE_PLAN.md** - Detailed implementation plan
- **IMPLEMENTATION_REFERENCE.md** - Developer quick reference
- **ARCHITECTURE_DIAGRAMS.md** - Visual architecture
- **OMNIPARSER_PROJECT_SPEC.md** - Technical specification

### Visual Workflows
- **[Diagrams/comprehensive-workflow.md](Diagrams/comprehensive-workflow.md)** - 🆕 **Comprehensive workflow vision**
  - Universal content ingestion platform
  - 20+ input sources (documents, web, social, feeds, cloud, code)
  - Complete parser routing and processing pipeline
  - Integration patterns and consumers
  - Future roadmap and expansion phases
  - **Start here to see the full scope of OmniParser's potential**

### Source Materials (Reference)
- `/Users/autumn/Documents/Projects/epub2tts/METAPROMPT_1_OMNIPARSER_EXTRACTION.md`
- `/Users/autumn/Documents/Projects/epub2tts/src/core/ebooklib_processor.py` (963 lines)
- `/Users/autumn/Documents/Projects/epub2tts/src/core/text_cleaner.py` (522 lines)

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

### Core
- pyyaml>=6.0
- beautifulsoup4>=4.12.0
- lxml>=5.0.0
- ftfy>=6.1.0
- python-magic>=0.4.27

### Parser-Specific
- ebooklib>=0.19 (EPUB)
- PyMuPDF>=1.23.0 (PDF)
- pytesseract>=0.3.10 (PDF OCR)
- python-docx>=1.0.0 (DOCX)
- trafilatura>=1.6.0 (HTML)
- chardet>=5.2.0 (Text)
- Pillow>=10.0.0 (Images)

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

### Package Quality
- [ ] All 6 parsers implemented
- [ ] >80% test coverage
- [ ] Package builds: `uv build`
- [ ] Can install: `uv add omniparser`
- [ ] Examples run successfully

### epub2tts Integration
- [ ] epub2tts uses OmniParser
- [ ] All epub2tts tests pass
- [ ] Audio generation works
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

**Status:** Planning Phase Complete ✅
**Next Action:** Begin Phase 1 (Repository Setup)
**Last Updated:** October 16, 2025
