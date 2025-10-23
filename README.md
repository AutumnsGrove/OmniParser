# OmniParser - Universal Document Parser

**Status:** Phase 2.3 Complete ✅ | EPUB Parser Production-Ready
**Version:** 0.1.0 (Development)
**License:** MIT

## Parser Implementation Status

| Format | Status | Tests | Notes |
|--------|--------|-------|-------|
| 📖 EPUB | ✅ **Implemented** | 357 passing | Production-ready, full TOC/metadata support |
| 📄 PDF | 📋 Planned | - | Phase 2.4 (Estimated: 2-3 weeks) |
| 📝 DOCX | 📋 Planned | - | Phase 2.5 (Estimated: 1 week) |
| 🌐 HTML/URL | 📋 Planned | - | Phase 2.5 (Estimated: 1-2 weeks) |
| 📋 Markdown | 📋 Planned | - | Phase 2.6 (Estimated: 3-5 days) |
| 📃 Text | 📋 Planned | - | Phase 2.6 (Estimated: 3-5 days) |

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

1. Extract epub2tts's production-tested EPUB processing into a reusable library ✅ **COMPLETE**
2. Create unified interface for parsing **any content source** regardless of format ✅ **Architecture Complete**
3. Provide consistent data models across all parsers ✅ **Implemented**
4. Enable epub2tts, RAG systems, content platforms, and other projects to consume document parsing as a service 🚧 **In Progress**

---

## What Works Today (v0.1.0)

**Production-Ready EPUB Parser** with:
- ✅ **TOC-based chapter detection** (with spine-based fallback)
- ✅ **Complete metadata extraction** (Dublin Core: title, author, publisher, language, etc.)
- ✅ **HTML to Markdown conversion** with clean text extraction
- ✅ **Image extraction** (temporary or persistent directories, Obsidian-compatible)
- ✅ **Text cleaning** (encoding fixes, normalization, whitespace handling)
- ✅ **Position tracking** for content structure
- ✅ **Word count & reading time** estimation
- ✅ **357 comprehensive tests** (100% passing)
- ✅ **Performance**: Parses 5MB EPUB in ~0.25 seconds (20x faster than initial target!)

**Example Output:**
```python
from omniparser import parse_document

doc = parse_document("alice-in-wonderland.epub")
# Returns Document with 12 chapters, full metadata, 11 images
# Processed in 0.25 seconds
```

**Real-World Testing:**
- ✅ Validated with 5 Project Gutenberg classics (Alice, Frankenstein, Jekyll & Hyde, Moby-Dick, Pride & Prejudice)
- ✅ Handles EPUBs from 189KB to 24MB
- ✅ Integration tests with real-world files
- ✅ Demo converter: EPUB → Obsidian-compatible Markdown

---

## Future Features

### Planned Parsers (v0.2 - v1.0)
- **PDF Parser** (Phase 2.4): PyMuPDF-based with OCR support
- **DOCX Parser** (Phase 2.5): Microsoft Word document parsing
- **HTML/URL Parser** (Phase 2.5): Web content extraction
- **Markdown Parser** (Phase 2.6): Parse and normalize existing Markdown
- **Text Parser** (Phase 2.6): Plain text with smart formatting

### Future Expansion (v1.1+)
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

### Basic Usage (EPUB Only - v0.1.0)

```python
from omniparser import parse_document

# Parse EPUB files (only supported format currently)
doc = parse_document("book.epub")

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

### 📋 Next Steps

**Option A: Phase 3 - Package Release** (Recommended)
- [ ] Update documentation for v0.1.0
- [ ] Set up CI/CD pipeline
- [ ] Publish to PyPI as EPUB-focused parser
- [ ] Create demo repository
- [ ] User onboarding guide

**Option B: Phase 2.4 - PDF Parser** (Add second format first)
- [ ] Implement PDFParser with PyMuPDF
- [ ] Add OCR support for scanned PDFs
- [ ] Heading-based chapter detection
- [ ] Comprehensive PDF testing
- [ ] Estimated: 2-3 weeks

**Future Phases:**
- [ ] Additional parsers (DOCX, HTML, Markdown, Text)
- [ ] epub2tts integration
- [ ] Advanced features (NLP chapter detection, semantic analysis)

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

### Currently Active (v0.1.0 - EPUB Parser)
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

### Installed but Not Yet Used (Future Parsers)
- **PDF (Phase 2.4):** PyMuPDF>=1.23.0, pytesseract>=0.3.10
- **DOCX (Phase 2.5):** python-docx>=1.0.0
- **HTML/URL (Phase 2.5):** trafilatura>=1.6.0, readability-lxml>=0.8.0, requests>=2.31.0

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

### v0.1.0 - EPUB Parser (Current)
- [x] EPUB parser fully implemented and tested
- [x] >90% test coverage for EPUB components (357 tests passing)
- [x] Package builds successfully: `uv build`
- [x] Can install from source: `uv sync` or `pip install -e .`
- [x] Examples run successfully (epub_to_markdown.py)
- [x] Performance exceeds targets (0.25s vs 5s goal)
- [x] Real-world validation (5 Project Gutenberg EPUBs)
- [ ] PyPI publication (pending Phase 3)

### v1.0.0 - Multi-Format Parser (Future Target)
- [ ] 3+ parsers implemented (EPUB ✅, PDF, DOCX minimum)
- [ ] >80% overall test coverage
- [ ] >500 total tests
- [ ] Published to PyPI: `pip install omniparser`
- [ ] CI/CD pipeline operational
- [ ] Complete API documentation

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

**Status:** Phase 2.3 Complete ✅ | EPUB Parser Production-Ready
**Version:** v0.1.0 (Development)
**Next Action:** Choose Phase 3 (PyPI Release) or Phase 2.4 (PDF Parser)
**Last Updated:** October 23, 2025
