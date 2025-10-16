# OmniParser Architecture Diagrams
**Visual reference for OmniParser architecture**

---

## System Context Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                         External Systems                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ epub2tts│  │  CLI    │  │   Web   │  │  Other  │            │
│  │ (Audio) │  │  Tools  │  │  Apps   │  │  Apps   │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │             │            │                  │
│       └────────────┴─────────────┴────────────┘                  │
│                          │                                        │
└──────────────────────────┼────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                        OmniParser                                 │
│                  Universal Document Parser                        │
│                                                                   │
│  Input: File path (EPUB/PDF/DOCX/HTML/URL/MD/TXT)               │
│  Output: Document object (markdown + metadata + structure)       │
└───────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                    External Libraries                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ebooklib  PyMuPDF  python-docx  trafilatura  beautifulsoup4     │
│  tesseract  chardet  python-magic  ftfy  readability-lxml        │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                           │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  parse_document(file_path, options...) -> Document           │ │
│  │  - Entry point for all parsing operations                    │ │
│  │  - Format detection, validation, error handling              │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PARSER LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  EPUB    │  │   PDF    │  │   DOCX   │  │   HTML   │          │
│  │ Parser   │  │  Parser  │  │  Parser  │  │  Parser  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │             │              │             │                 │
│  ┌────┴─────┐  ┌───┴──────┐                                       │
│  │ Markdown │  │   Text   │                                       │
│  │  Parser  │  │  Parser  │                                       │
│  └────┬─────┘  └────┬─────┘                                       │
│       │             │              │             │                 │
│       └─────────────┴──────────────┴─────────────┘                │
│                           │                                        │
│                     All inherit from                               │
│                   ┌──────▼────────┐                               │
│                   │  BaseParser   │                               │
│                   │  (Abstract)   │                               │
│                   └───────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       PROCESSOR LAYER                               │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────┐      │
│  │    Chapter     │  │    Metadata      │  │     Text     │      │
│  │   Detector     │  │    Extractor     │  │   Cleaner    │      │
│  └────────────────┘  └──────────────────┘  └──────────────┘      │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │           Markdown Converter (HTML → MD)                   │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BASE LAYER                                 │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Data Models: Document, Chapter, Metadata, ImageReference    │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐         │
│  │ Exceptions │  │   Utilities  │  │ Format Detection  │         │
│  └────────────┘  └──────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Parser Flow Diagram

```
┌──────────────┐
│  User calls  │
│parse_document│
│  (file.epub) │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Validate File   │
│  - Exists?       │
│  - Readable?     │
│  - Size OK?      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Detect Format   │
│  - Magic bytes   │
│  - Extension     │
│  Result: "epub"  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Select Parser   │
│  EPUBParser      │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────┐
│  EPUBParser.parse()              │
│  ┌────────────────────────────┐  │
│  │ 1. Load with ebooklib      │  │
│  └────────┬───────────────────┘  │
│           │                      │
│  ┌────────▼───────────────────┐  │
│  │ 2. Extract metadata        │  │
│  │    (title, author, etc)    │  │
│  └────────┬───────────────────┘  │
│           │                      │
│  ┌────────▼───────────────────┐  │
│  │ 3. Parse TOC structure     │  │
│  │    (chapter boundaries)    │  │
│  └────────┬───────────────────┘  │
│           │                      │
│  ┌────────▼───────────────────┐  │
│  │ 4. Extract chapter content │  │
│  │    (HTML → text)           │  │
│  └────────┬───────────────────┘  │
│           │                      │
│  ┌────────▼───────────────────┐  │
│  │ 5. Extract images          │  │
│  │    (if enabled)            │  │
│  └────────┬───────────────────┘  │
│           │                      │
│  ┌────────▼───────────────────┐  │
│  │ 6. Clean text              │  │
│  │    (if enabled)            │  │
│  └────────┬───────────────────┘  │
│           │                      │
│  ┌────────▼───────────────────┐  │
│  │ 7. Build Document object   │  │
│  └────────┬───────────────────┘  │
└───────────┼──────────────────────┘
            │
            ▼
┌───────────────────────────┐
│  Return Document          │
│  - content (markdown)     │
│  - chapters (List)        │
│  - images (List)          │
│  - metadata (Metadata)    │
│  - processing_info        │
└───────────────────────────┘
```

---

## Document Object Structure

```
Document
├── document_id: "uuid-1234-5678"
├── content: "Full text as markdown..."
├── word_count: 50000
├── estimated_reading_time: 250  # minutes
│
├── chapters: List[Chapter]
│   ├── Chapter 0
│   │   ├── chapter_id: 0
│   │   ├── title: "Prologue"
│   │   ├── content: "Chapter text..."
│   │   ├── start_position: 0
│   │   ├── end_position: 500
│   │   ├── word_count: 100
│   │   ├── level: 1
│   │   └── metadata: {}
│   │
│   ├── Chapter 1
│   │   ├── chapter_id: 1
│   │   ├── title: "Chapter 1: The Beginning"
│   │   └── ...
│   │
│   └── Chapter N...
│
├── images: List[ImageReference]
│   ├── ImageReference 0
│   │   ├── image_id: "img_001"
│   │   ├── position: 1500
│   │   ├── file_path: "/path/to/image.jpg"
│   │   ├── alt_text: "Description"
│   │   ├── size: (800, 600)
│   │   └── format: "jpg"
│   │
│   └── ImageReference N...
│
├── metadata: Metadata
│   ├── title: "Book Title"
│   ├── author: "Author Name"
│   ├── authors: ["Author 1", "Author 2"]
│   ├── publisher: "Publisher Inc."
│   ├── publication_date: datetime(2024, 1, 1)
│   ├── language: "en"
│   ├── isbn: "978-0-123456-78-9"
│   ├── description: "Book description..."
│   ├── tags: ["fiction", "fantasy"]
│   ├── original_format: "epub"
│   ├── file_size: 2048000
│   └── custom_fields: {}
│
└── processing_info: ProcessingInfo
    ├── parser_used: "epub"
    ├── parser_version: "1.0.0"
    ├── processing_time: 2.5  # seconds
    ├── timestamp: datetime(2025, 10, 16, 12, 0, 0)
    ├── warnings: []
    └── options_used: {"extract_images": true, ...}
```

---

## EPUB Parser Internal Flow

```
EPUBParser.parse(book.epub)
│
├─► Load EPUB
│   └─► ebooklib.read_epub()
│
├─► Extract Metadata
│   ├─► book.get_metadata('DC', 'title')
│   ├─► book.get_metadata('DC', 'creator')
│   ├─► book.get_metadata('DC', 'publisher')
│   └─► Return Metadata object
│
├─► Extract TOC Structure
│   ├─► book.toc (Table of Contents)
│   ├─► Recursive processing
│   │   ├─► epub.Link → TocEntry
│   │   ├─► epub.Section → TocEntry with children
│   │   └─► Build hierarchy
│   └─► Return List[TocEntry]
│
├─► Extract Chapters
│   ├─► For each TOC entry:
│   │   ├─► Find item by href
│   │   ├─► Extract HTML content
│   │   ├─► Parse with BeautifulSoup
│   │   ├─► Extract text
│   │   └─► Create Chapter object
│   │
│   ├─► Fallback (no TOC):
│   │   ├─► Iterate spine items
│   │   └─► Each spine item = chapter
│   │
│   └─► Return List[Chapter]
│
├─► Extract Images (optional)
│   ├─► For each ITEM_IMAGE:
│   │   ├─► Extract binary data
│   │   ├─► Save to temp location
│   │   └─► Create ImageReference
│   │
│   └─► Return List[ImageReference]
│
├─► Build Full Content
│   ├─► Join chapter.content
│   └─► Markdown format
│
├─► Clean Text (optional)
│   ├─► Fix encoding (ftfy)
│   ├─► Normalize whitespace
│   └─► Normalize quotes
│
└─► Return Document
    └─► Document(content, chapters, images, metadata, ...)
```

---

## Parser Inheritance Hierarchy

```
BaseParser (ABC)
├── parse() [abstract]
├── supports_format() [abstract]
├── extract_images() [optional override]
└── clean_text() [optional override]
    │
    ├─► EPUBParser
    │   ├── Uses: ebooklib, BeautifulSoup
    │   ├── Supports: .epub
    │   └── Features: TOC-based chapters, images, metadata
    │
    ├─► PDFParser
    │   ├── Uses: PyMuPDF, Tesseract
    │   ├── Supports: .pdf
    │   └── Features: OCR, table extraction, font-based headings
    │
    ├─► DOCXParser
    │   ├── Uses: python-docx
    │   ├── Supports: .docx, .doc
    │   └── Features: Style-based headings, images, tables
    │
    ├─► HTMLParser
    │   ├── Uses: Trafilatura, Readability, requests
    │   ├── Supports: .html, .htm, URLs
    │   └── Features: Main content extraction, URL fetching
    │
    ├─► MarkdownParser
    │   ├── Uses: PyYAML
    │   ├── Supports: .md, .markdown
    │   └── Features: Frontmatter, heading detection
    │
    └─► TextParser
        ├── Uses: chardet
        ├── Supports: .txt
        └── Features: Encoding detection, normalization
```

---

## Data Flow: epub2tts Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    epub2tts Application                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ user uploads book.epub
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              epub2tts.core.epub_processor.py                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  def process_epub(epub_path):                          │ │
│  │      # Parse with OmniParser                           │ │
│  │      doc = parse_document(epub_path)                   │ │
│  │                                                         │ │
│  │      # Convert to epub2tts format                      │ │
│  │      result = ProcessingResult(                        │ │
│  │          text_content=doc.content,                     │ │
│  │          chapters=_convert_chapters(doc.chapters),     │ │
│  │          metadata=_convert_metadata(doc.metadata),     │ │
│  │          ...                                            │ │
│  │      )                                                  │ │
│  │                                                         │ │
│  │      # Apply TTS-specific processing                   │ │
│  │      result.text_content = tts_cleaner.add_pauses(     │ │
│  │          result.text_content                           │ │
│  │      )                                                  │ │
│  │                                                         │ │
│  │      return result                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      OmniParser                             │
│                  (External Package)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  parse_document(epub_path) -> Document                 │ │
│  │      - Format detection                                │ │
│  │      - EPUBParser selected                             │ │
│  │      - Parse EPUB structure                            │ │
│  │      - Extract chapters, metadata, images              │ │
│  │      - Return Document object                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ returns Document
┌─────────────────────────────────────────────────────────────┐
│                    Back to epub2tts                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   TTS Pipeline                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  - Text chunking (respects chapters)                   │ │
│  │  - Voice synthesis (Kokoro TTS)                        │ │
│  │  - Audio stitching                                     │ │
│  │  - M4B/M4A output                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   Audiobook Output
```

---

## Error Handling Flow

```
┌──────────────────────────┐
│  parse_document(path)    │
└────────┬─────────────────┘
         │
         ▼
┌────────────────────────────┐
│  Validate Input            │
│  ┌──────────────────────┐  │
│  │ File exists?         │  │─── No ──► FileReadError
│  │ File readable?       │  │─── No ──► FileReadError
│  │ File size OK?        │  │─── No ──► ValidationError
│  └──────────┬───────────┘  │
└─────────────┼───────────────┘
              │ Yes
              ▼
┌────────────────────────────┐
│  Detect Format             │
│  ┌──────────────────────┐  │
│  │ Magic bytes check    │  │
│  │ Extension fallback   │  │
│  └──────────┬───────────┘  │
└─────────────┼───────────────┘
              │
              ├─► Supported ──► Continue
              │
              └─► Unsupported ──► UnsupportedFormatError
                                  "Format not supported: ..."

┌────────────────────────────┐
│  Create Parser             │
│  ┌──────────────────────┐  │
│  │ EPUBParser()         │  │
│  └──────────┬───────────┘  │
└─────────────┼───────────────┘
              │
              ▼
┌────────────────────────────┐
│  Parser.parse()            │
│  ┌──────────────────────┐  │
│  │ Try parsing          │  │
│  │ Handle errors        │  │
│  └──────────┬───────────┘  │
└─────────────┼───────────────┘
              │
              ├─► Success ──► Return Document
              │
              └─► Error ──┬─► ParsingError
                          │   (with original_error preserved)
                          │
                          ├─► NetworkError (if URL)
                          │
                          └─► FileReadError (if IO issue)
```

---

## Testing Structure

```
tests/
├── unit/                           # Unit tests (fast, isolated)
│   ├── test_models.py              # Data model tests
│   │   ├── test_document_creation
│   │   ├── test_document_serialization
│   │   ├── test_chapter_helpers
│   │   └── test_metadata_fields
│   │
│   ├── test_epub_parser.py         # EPUB parser tests
│   │   ├── test_parse_valid_epub
│   │   ├── test_parse_no_toc
│   │   ├── test_metadata_extraction
│   │   ├── test_chapter_detection
│   │   └── test_image_extraction
│   │
│   ├── test_pdf_parser.py          # PDF parser tests
│   ├── test_docx_parser.py         # DOCX parser tests
│   ├── test_html_parser.py         # HTML parser tests
│   ├── test_markdown_parser.py     # Markdown parser tests
│   ├── test_text_parser.py         # Text parser tests
│   │
│   ├── test_format_detector.py     # Format detection tests
│   ├── test_text_cleaner.py        # Text cleaning tests
│   ├── test_chapter_detector.py    # Chapter detection tests
│   └── test_exceptions.py          # Exception tests
│
├── integration/                    # Integration tests (slower, end-to-end)
│   ├── test_full_pipeline.py       # parse_document() with all formats
│   ├── test_format_detection.py    # Format detection integration
│   ├── test_error_handling.py      # Error scenarios
│   └── test_serialization.py       # JSON save/load tests
│
└── fixtures/                       # Test data
    ├── sample.epub                 # Valid EPUB
    ├── no_toc.epub                 # EPUB without TOC
    ├── images.epub                 # EPUB with images
    ├── sample.pdf                  # Text-based PDF
    ├── scanned.pdf                 # OCR PDF
    ├── sample.docx                 # DOCX with formatting
    ├── sample.html                 # HTML article
    ├── sample.md                   # Markdown with frontmatter
    └── sample.txt                  # Plain text
```

---

## Package Structure

```
omniparser/
├── pyproject.toml              # UV package configuration
├── README.md                   # User-facing documentation
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── .gitignore                  # Git ignore rules
│
├── src/
│   └── omniparser/
│       ├── __init__.py         # Package exports
│       │   └── Exports: parse_document, Document, exceptions
│       │
│       ├── parser.py           # Main parse_document() function
│       │   └── Entry point, format detection, parser selection
│       │
│       ├── models.py           # Data models
│       │   └── Document, Chapter, Metadata, ImageReference, ProcessingInfo
│       │
│       ├── exceptions.py       # Custom exceptions
│       │   └── OmniparserError, ParsingError, etc.
│       │
│       ├── base/               # Abstract base classes
│       │   ├── __init__.py
│       │   └── base_parser.py  # BaseParser ABC
│       │
│       ├── parsers/            # Format-specific parsers
│       │   ├── __init__.py
│       │   ├── epub_parser.py  # EPUBParser (ported from epub2tts)
│       │   ├── pdf_parser.py   # PDFParser (PyMuPDF + OCR)
│       │   ├── docx_parser.py  # DOCXParser (python-docx)
│       │   ├── html_parser.py  # HTMLParser (Trafilatura)
│       │   ├── markdown_parser.py  # MarkdownParser
│       │   └── text_parser.py  # TextParser (chardet)
│       │
│       ├── processors/         # Post-processing components
│       │   ├── __init__.py
│       │   ├── chapter_detector.py     # Heading-based detection
│       │   ├── metadata_extractor.py   # Metadata extraction
│       │   ├── markdown_converter.py   # HTML → Markdown
│       │   └── text_cleaner.py         # Text normalization
│       │
│       └── utils/              # Utility functions
│           ├── __init__.py
│           ├── format_detector.py  # Magic bytes detection
│           ├── encoding.py         # Encoding utilities
│           └── validators.py       # Input validation
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data files
│
├── docs/                       # Documentation
│   ├── index.md                # Main docs
│   ├── api.md                  # API reference
│   ├── parsers.md              # Parser implementation guide
│   └── contributing.md         # Contribution guide
│
└── examples/                   # Usage examples
    ├── basic_usage.py          # Simple example
    ├── batch_processing.py     # Process directory
    └── custom_parser.py        # Custom parser implementation
```

---

## Version 1.0 Scope

```
Included in v1.0:
✅ EPUB parser (ported from epub2tts)
✅ PDF parser (PyMuPDF + Tesseract OCR)
✅ DOCX parser (python-docx)
✅ HTML/URL parser (Trafilatura + Readability)
✅ Markdown parser (frontmatter + headings)
✅ Text parser (chardet + encoding)
✅ Chapter detection (heading-based)
✅ Metadata extraction (format-agnostic)
✅ Image extraction (all formats)
✅ Text cleaning (basic, non-TTS)
✅ Comprehensive tests (>80% coverage)
✅ Professional documentation
✅ PyPI package

Not included in v1.0 (future):
❌ RTF parser
❌ ODT parser
❌ AI-powered chapter detection
❌ JavaScript rendering for URLs
❌ Plugin system
❌ Streaming API
❌ Multi-document archives
```

---

## Deployment Pipeline

```
Development
    │
    ├─► Write code
    │   └─► src/omniparser/
    │
    ├─► Write tests
    │   └─► tests/
    │
    ├─► Run tests locally
    │   └─► uv run pytest
    │
    ├─► Format code
    │   └─► uv run black .
    │
    └─► Type check
        └─► uv run mypy src/
            │
            ▼
        All pass?
            │
            ├─► No ──► Fix issues, repeat
            │
            └─► Yes
                │
                ▼
┌───────────────────────────────────┐
│  Pre-release Validation           │
│  ├─► All tests pass                │
│  ├─► Coverage >80%                │
│  ├─► Documentation complete       │
│  ├─► Examples work                │
│  └─► CHANGELOG updated            │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Build Package                    │
│  └─► uv build                     │
│      ├─► Creates .tar.gz          │
│      └─► Creates .whl             │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Test Local Install               │
│  └─► uv add ./dist/...            │
│      └─► Import works?            │
└───────────────┬───────────────────┘
                │
                ▼
            Success?
                │
                ├─► No ──► Debug, repeat
                │
                └─► Yes
                    │
                    ▼
┌───────────────────────────────────┐
│  Publish to PyPI                  │
│  └─► uv publish                   │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Tag Release                      │
│  └─► git tag v1.0.0               │
│      git push --tags              │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  Update epub2tts                  │
│  └─► Add omniparser dependency    │
│      Test integration             │
│      Deploy                       │
└───────────────────────────────────┘
```

---

**Last Updated:** October 16, 2025
**Status:** Ready for Reference
**Companion Documents:**
- ARCHITECTURE_PLAN.md (detailed implementation plan)
- IMPLEMENTATION_REFERENCE.md (quick reference)
