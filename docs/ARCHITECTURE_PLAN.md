# OmniParser Architecture Plan
**Version:** 1.0
**Date:** October 16, 2025
**Status:** Blueprint for Implementation
**Based on:** METAPROMPT_1 (16 Phases) + OMNIPARSER_PROJECT_SPEC.md

---

## 1. Executive Summary

### 1.1 Project Goals
OmniParser is a standalone, PyPI-published universal document parser that converts multiple file formats (EPUB, PDF, DOCX, HTML, URLs, Markdown, Text) into clean, structured markdown with comprehensive metadata extraction.

**Primary Objectives:**
- Extract epub2tts's production-tested EPUB processing logic into a reusable library
- Create a unified interface for parsing documents regardless of source format
- Provide consistent data models and error handling across all parsers
- Enable epub2tts and other projects to consume document parsing as a service

### 1.2 Relationship to epub2tts
OmniParser will serve as the document ingestion layer for epub2tts:

```
epub2tts Pipeline:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Input     │────>│  OmniParser  │────>│ Text Clean  │────>│   TTS    │
│  (various)  │     │  (external)  │     │  & Process  │     │ Pipeline │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
```

**Separation of Concerns:**
- **OmniParser:** Document format handling, content extraction, structure detection
- **epub2tts:** Audio generation, TTS processing, voice synthesis, web interface

### 1.3 Success Criteria
- All 6 parsers implemented and tested (EPUB, PDF, DOCX, HTML, Markdown, Text)
- Test coverage >80%
- Package builds and installs via `uv add omniparser`
- epub2tts successfully migrates to use OmniParser
- API matches spec exactly
- Professional documentation

---

## 2. Architecture Overview

### 2.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                               │
│  parse_document() - Main entry point                        │
│  Format detection, parser selection, error handling         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Parser Layer                              │
│  EPUBParser │ PDFParser │ DOCXParser │ HTMLParser │ etc.    │
│  All inherit from BaseParser interface                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Processor Layer                             │
│  chapter_detector │ metadata_extractor │ text_cleaner       │
│  markdown_converter - Shared utilities                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Base Layer                                │
│  Data Models (Document, Chapter, Metadata, etc.)            │
│  Exceptions, Utilities, Format Detection                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
omniparser/
├── parser.py              # Main parse_document() function
│   └── Uses: format_detector, all parsers, exceptions
│
├── models.py              # Data models
│   └── Document, Chapter, Metadata, ImageReference, ProcessingInfo
│
├── base/
│   └── base_parser.py     # Abstract BaseParser class
│
├── parsers/               # Format-specific implementations
│   ├── epub_parser.py     # Port from epub2tts (EbookLib)
│   ├── pdf_parser.py      # PyMuPDF + Tesseract OCR
│   ├── docx_parser.py     # python-docx
│   ├── html_parser.py     # Trafilatura + Readability
│   ├── markdown_parser.py # Minimal processing + frontmatter
│   └── text_parser.py     # Chardet + encoding normalization
│
├── processors/            # Post-processing components
│   ├── chapter_detector.py     # Heading-based chapter detection
│   ├── metadata_extractor.py   # Format-agnostic metadata
│   ├── markdown_converter.py   # HTML → Markdown
│   └── text_cleaner.py         # Port subset from epub2tts
│
├── utils/                 # Utility functions
│   ├── format_detector.py # Magic bytes + extension fallback
│   ├── encoding.py        # Chardet, UTF-8 normalization
│   └── validators.py      # Input validation
│
└── exceptions.py          # Custom exception hierarchy
```

### 2.3 Data Flow

**Example: Processing an EPUB file**
```
1. parse_document("book.epub")
   └─> Validates file exists
   └─> Detects format: "epub" (via magic bytes)

2. Creates EPUBParser(options)
   └─> Inherits from BaseParser

3. EPUBParser.parse()
   └─> Uses ebooklib to read EPUB structure
   └─> Extracts metadata from OPF
   └─> Processes TOC for chapter boundaries
   └─> Converts HTML to text using BeautifulSoup
   └─> Extracts images with base64 handling
   └─> Applies text_cleaner for normalization

4. Returns Document object
   └─> content: Full markdown text
   └─> chapters: List[Chapter] with boundaries
   └─> images: List[ImageReference] with positions
   └─> metadata: Comprehensive book info
   └─> processing_info: Parser metadata
```

---

## 3. Data Model Design

### 3.1 Core Models (from OMNIPARSER_PROJECT_SPEC.md)

**Models to Implement:**
1. `ImageReference` - Image metadata and position tracking
2. `Chapter` - Chapter content with word counts and boundaries
3. `Metadata` - Document-level metadata (author, title, etc.)
4. `ProcessingInfo` - Parser execution metadata
5. `Document` - Main container object

### 3.2 Mapping from epub2tts to OmniParser

**epub2tts Structure:**
```python
# ebooklib_processor.py
@dataclass
class EbookMetadata:
    title, authors, publisher, publication_date,
    language, identifier, description, subjects,
    rights, spine_length, has_toc, epub_version

@dataclass
class Chapter:
    chapter_num, title, content, word_count,
    estimated_duration, confidence
```

**OmniParser Structure (Generalized):**
```python
@dataclass
class Metadata:
    # Superset that works for all formats
    title: Optional[str]
    author: Optional[str]  # Single author (or primary)
    authors: Optional[List[str]]  # EPUB supports multiple
    publisher: Optional[str]
    publication_date: Optional[datetime]
    language: Optional[str]
    isbn: Optional[str]  # identifier
    description: Optional[str]
    tags: Optional[List[str]]  # subjects
    original_format: str  # "epub", "pdf", etc.
    file_size: int
    custom_fields: Optional[Dict]  # Format-specific extras

@dataclass
class Chapter:
    chapter_id: int  # Renamed from chapter_num for clarity
    title: str
    content: str  # Markdown formatted
    start_position: int  # New: character position in full text
    end_position: int    # New: character position in full text
    word_count: int
    level: int  # New: heading level (1=main, 2=sub, etc.)
    metadata: Optional[Dict]  # New: chapter-specific metadata

    # Remove TTS-specific fields:
    # - estimated_duration (TTS concern)
    # - confidence (internal to detection)
```

### 3.3 Key Differences and Rationale

**Why remove `estimated_duration` from Chapter?**
- This is a TTS-specific calculation (words per minute)
- OmniParser should be TTS-agnostic
- epub2tts can calculate this when consuming the data

**Why add `start_position` and `end_position`?**
- Enables precise text range extraction
- Supports image position tracking
- Allows chapter reconstruction without reparsing

**Why add `level` to Chapter?**
- Preserves heading hierarchy (H1, H2, H3, etc.)
- Useful for generating nested TOCs
- Helps distinguish main chapters from subsections

**Why generalize Metadata?**
- Different formats have different metadata schemas
- `custom_fields` dict allows format-specific extras
- Core fields work across all document types

---

## 4. EPUB Parser Port Strategy

### 4.1 Source Analysis: ebooklib_processor.py (963 lines)

**Core Components to Port:**

1. **Metadata Extraction (lines 245-324):**
   - Uses ebooklib's `get_metadata('DC', ...)` API
   - Extracts: title, authors, publisher, date, language, identifier, description, subjects, rights
   - **Port Strategy:** Adapt to return OmniParser's `Metadata` model

2. **TOC Structure Extraction (lines 326-386):**
   - Recursive processing of ebooklib TOC structure
   - Handles nested sections and hierarchies
   - **Port Strategy:** Keep similar structure, use for chapter detection

3. **Content Extraction (lines 388-440):**
   - TOC-based chapter boundary detection
   - Fallback to spine-based processing
   - HTML text extraction with BeautifulSoup
   - **Port Strategy:** Core logic stays the same, return `Chapter` objects

4. **HTMLTextExtractor (lines 66-100):**
   - Custom HTML parser for clean text extraction
   - Handles block elements, whitespace normalization
   - **Port Strategy:** Move to `processors/markdown_converter.py`

5. **Image Extraction (lines 629-678):**
   - Extracts all ITEM_IMAGE objects from EPUB
   - Saves to temp directory
   - Tracks file paths and metadata
   - **Port Strategy:** Adapt to return `ImageReference` objects

6. **Chapter Post-Processing (lines 680-760):**
   - Filters short chapters (min_words_per_chapter)
   - Splits long chapters (max_words_per_chunk)
   - **Port Strategy:** Make configurable via options, but simplify for OmniParser

### 4.2 What Stays the Same

✅ **Core ebooklib API usage:**
```python
import ebooklib
from ebooklib import epub

book = epub.read_epub(str(epub_path))
book.get_metadata('DC', 'title')
book.toc  # Table of contents
book.spine  # Reading order
book.get_items()  # All items
item.get_type()  # ITEM_DOCUMENT, ITEM_IMAGE, etc.
```

✅ **TOC-based chapter detection logic:**
- Recursive TOC traversal
- href mapping to spine items
- Hierarchical section handling

✅ **HTML text extraction:**
- BeautifulSoup for parsing
- Block element handling
- Whitespace normalization

### 4.3 What Changes

🔄 **Configuration System:**
```python
# epub2tts (coupled to Config object)
def __init__(self, config: Config, progress_tracker=None):
    self.config = config
    self.cleaner = TextCleaner()
    min_words = self.config.chapters.min_words_per_chapter

# OmniParser (options dict)
def __init__(self, options: dict = None):
    self.options = options or {}
    min_words = self.options.get('min_words_per_chapter', 100)
```

🔄 **Return Types:**
```python
# epub2tts returns ProcessingResult
return ProcessingResult(
    success=True,
    text_content=cleaned_text,
    chapters=processed_chapters,
    metadata=asdict(metadata),
    ...
)

# OmniParser returns Document
return Document(
    document_id=str(uuid.uuid4()),
    content=full_markdown,
    chapters=chapters,
    images=images,
    metadata=metadata,
    processing_info=processing_info,
    ...
)
```

🔄 **TextCleaner Integration:**
```python
# epub2tts: Tight integration with TextCleaner
from core.text_cleaner import TextCleaner
self.cleaner = TextCleaner()
cleaned_text = self.cleaner.clean_text(text_content)

# OmniParser: Optional via BaseParser method
def clean_text(self, text: str) -> str:
    """Optional override by parsers"""
    if self.options.get('clean_text', True):
        from .processors.text_cleaner import clean_text
        return clean_text(text)
    return text
```

### 4.4 TextCleaner Extraction Strategy

**epub2tts TextCleaner Features:**
- ftfy for encoding fixes
- Regex pattern-based cleaning (removal + transformation)
- TTS-specific replacements (pause markers)
- Whitespace normalization
- Chapter segmentation (detect chapters by patterns)

**What to Port to OmniParser:**
```python
# processors/text_cleaner.py
def clean_text(
    text: str,
    remove_extra_whitespace: bool = True,
    fix_encoding: bool = True,
    normalize_quotes: bool = True
) -> str:
    """Basic text cleaning - NO TTS-specific features"""

    if fix_encoding:
        text = ftfy.fix_text(text)

    if normalize_quotes:
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

    if remove_extra_whitespace:
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
```

**What to EXCLUDE:**
- ❌ Pause markers ([PAUSE: 2.0])
- ❌ TTS-specific replacements
- ❌ Regex pattern loading from YAML (too epub2tts-specific)
- ❌ CleaningStats tracking (internal concern)
- ❌ Chapter detection by patterns (use processors/chapter_detector.py)

**Rationale:** OmniParser should provide universal text cleaning, not TTS-optimized cleaning. epub2tts can apply its own TTS-specific cleaning after getting the Document.

---

## 5. Phase-by-Phase Implementation Plan

### Phase 1: Repository Setup & Structure (2 hours)

**Tasks:**
1. Create new OmniParser repository
2. Initialize with UV: `uv init`
3. Create directory structure (see spec section 2.2)
4. Setup pyproject.toml with dependencies (see spec section 9.1)
5. Create README.md, LICENSE (MIT), .gitignore, CHANGELOG.md
6. Initialize git repository

**Files to Create:**
- `/pyproject.toml` - UV package configuration
- `/README.md` - Package overview
- `/LICENSE` - MIT License
- `/.gitignore` - Python gitignore
- `/CHANGELOG.md` - Version 1.0.0

**Validation:**
```bash
uv sync
git init
git add .
git status
```

**Dependencies Checklist:**
```toml
[project.dependencies]
# Core
pyyaml>=6.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# EPUB
ebooklib>=0.19

# PDF
PyMuPDF>=1.23.0
pytesseract>=0.3.10

# DOCX
python-docx>=1.0.0

# HTML/URLs
trafilatura>=1.6.0
readability-lxml>=0.8.0
requests>=2.31.0

# Text processing
ftfy>=6.1.0
chardet>=5.2.0
python-magic>=0.4.27

# Utilities
Pillow>=10.0.0
dataclasses-json>=0.6.0
```

---

### Phase 2: Core Data Models (3 hours)

**Tasks:**
1. Implement `src/omniparser/models.py`
2. Create all dataclasses with type hints
3. Implement helper methods (to_dict, from_dict, save_json, load_json)
4. Add comprehensive docstrings
5. Write unit tests

**Models to Implement:**
```python
@dataclass
class ImageReference:
    image_id: str
    position: int
    file_path: Optional[str]
    alt_text: Optional[str]
    size: Optional[tuple]
    format: str

@dataclass
class Chapter:
    chapter_id: int
    title: str
    content: str
    start_position: int
    end_position: int
    word_count: int
    level: int
    metadata: Optional[Dict] = None

@dataclass
class Metadata:
    title: Optional[str] = None
    author: Optional[str] = None
    # ... (see spec section 3.2)

@dataclass
class ProcessingInfo:
    parser_used: str
    parser_version: str
    processing_time: float
    timestamp: datetime
    warnings: List[str]
    options_used: Dict

@dataclass
class Document:
    document_id: str
    content: str
    chapters: List[Chapter]
    images: List[ImageReference]
    metadata: Metadata
    processing_info: ProcessingInfo
    word_count: int
    estimated_reading_time: int

    def get_chapter(self, chapter_id: int) -> Optional[Chapter]
    def get_text_range(self, start: int, end: int) -> str
    def to_dict(self) -> dict
    @classmethod
    def from_dict(cls, data: dict) -> 'Document'
    def save_json(self, path: str)
    @classmethod
    def load_json(cls, path: str) -> 'Document'
```

**Test File:** `tests/unit/test_models.py`

**Test Cases:**
- Create each model with valid data
- Serialize to dict and back
- Save to JSON and load
- Test helper methods
- Test edge cases (empty chapters, missing metadata)

**Validation:**
```bash
uv run pytest tests/unit/test_models.py -v
```

---

### Phase 3: Base Parser Interface (2 hours)

**Task:** Implement `src/omniparser/base/base_parser.py`

**Implementation:**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ..models import Document, ImageReference

class BaseParser(ABC):
    """Abstract base class for all parsers"""

    def __init__(self, options: dict = None):
        self.options = options or {}

    @abstractmethod
    def parse(self, file_path: Path) -> Document:
        """Parse document and return Document object"""
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if this parser supports the file format"""
        pass

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """Extract images (optional override)"""
        return []

    def clean_text(self, text: str) -> str:
        """Apply text cleaning (optional override)"""
        if self.options.get('clean_text', True):
            from ..processors.text_cleaner import clean_text
            return clean_text(text)
        return text
```

**Validation:**
- Code is syntactically correct
- Imports resolve properly
- Abstract methods properly decorated

---

### Phase 4: Utility Functions (4 hours)

**4a. Format Detection (`utils/format_detector.py`):**
```python
import magic
from pathlib import Path

def detect_format(file_path: Path) -> str:
    """
    Detect file format using magic bytes.

    Returns: "epub", "pdf", "docx", "html", "markdown", or "text"
    Raises: UnsupportedFormatError if format not supported
    """
    mime = magic.from_file(str(file_path), mime=True)

    format_map = {
        'application/epub+zip': 'epub',
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'text/html': 'html',
        'text/plain': 'text',
        'text/markdown': 'markdown'
    }

    detected = format_map.get(mime)

    if not detected:
        # Fallback to extension
        ext = file_path.suffix.lower()
        if ext in ['.md', '.markdown']:
            return 'markdown'
        elif ext in ['.txt']:
            return 'text'
        else:
            raise UnsupportedFormatError(f"Unsupported format: {mime}")

    return detected
```

**4b. Encoding Utilities (`utils/encoding.py`):**
```python
import chardet

def detect_encoding(file_path: Path) -> str:
    """Detect file encoding using chardet"""
    with open(file_path, 'rb') as f:
        raw = f.read()
        result = chardet.detect(raw)
        return result['encoding']

def normalize_to_utf8(text: str) -> str:
    """Normalize text to UTF-8"""
    return text.encode('utf-8', errors='ignore').decode('utf-8')
```

**4c. Validators (`utils/validators.py`):**
```python
def validate_file_exists(file_path: Path) -> None:
    """Raise FileReadError if file doesn't exist"""
    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")

def validate_file_size(file_path: Path, max_size_mb: int = 500) -> None:
    """Raise ValidationError if file too large"""
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValidationError(f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)")
```

**Test Files:**
- `tests/unit/test_format_detector.py`
- `tests/unit/test_encoding.py`
- `tests/unit/test_validators.py`

---

### Phase 5: Exception Classes (1 hour)

**Task:** Implement `src/omniparser/exceptions.py`

```python
class OmniparserError(Exception):
    """Base exception for Omniparser"""
    pass

class UnsupportedFormatError(OmniparserError):
    """Raised when file format is not supported"""
    pass

class ParsingError(OmniparserError):
    """Raised when parsing fails"""
    def __init__(self, message: str, parser: str = None, original_error: Exception = None):
        super().__init__(message)
        self.parser = parser
        self.original_error = original_error

class FileReadError(OmniparserError):
    """Raised when file cannot be read"""
    pass

class NetworkError(OmniparserError):
    """Raised when URL fetch fails"""
    pass

class ValidationError(OmniparserError):
    """Raised when input validation fails"""
    pass
```

**Validation:**
- Can raise and catch each exception type
- Error messages are clear
- Inheritance hierarchy correct

---

### Phase 6: EPUB Parser (Port from epub2tts) (8 hours)

**Source:** epub2tts `src/core/ebooklib_processor.py`

**Task:** Create `src/omniparser/parsers/epub_parser.py`

**Implementation Strategy:**

1. **Copy core methods from ebooklib_processor.py:**
   - `_extract_metadata()` → adapt to return OmniParser Metadata
   - `_extract_toc_structure()` → keep as-is
   - `_extract_content_with_chapters()` → adapt to return Document
   - `_extract_chapters_from_toc()` → adapt to return Chapter objects
   - `_extract_text_from_item()` → keep as-is
   - `_extract_images()` → adapt to return ImageReference objects

2. **Adapt to BaseParser interface:**
```python
class EPUBParser(BaseParser):
    """Parser for EPUB files using EbookLib"""

    def parse(self, file_path: Path) -> Document:
        """Parse EPUB file"""
        import ebooklib
        from ebooklib import epub
        import uuid
        import time

        start_time = time.time()

        # Load EPUB
        book = epub.read_epub(str(file_path))

        # Extract metadata
        metadata = self._extract_metadata(book)

        # Extract TOC
        toc_structure = self._extract_toc_structure(book)

        # Extract content and chapters
        chapters = self._extract_chapters_from_toc(book, toc_structure)

        # Extract images if enabled
        images = []
        if self.options.get('extract_images', True):
            images = self._extract_images(book)

        # Build full content
        full_content = self._build_full_content(chapters)

        # Apply text cleaning if enabled
        if self.options.get('clean_text', True):
            full_content = self.clean_text(full_content)

        # Calculate positions
        chapters = self._calculate_chapter_positions(chapters, full_content)

        # Build Document object
        document = Document(
            document_id=str(uuid.uuid4()),
            content=full_content,
            chapters=chapters,
            images=images,
            metadata=metadata,
            processing_info=ProcessingInfo(
                parser_used="epub",
                parser_version="1.0.0",
                processing_time=time.time() - start_time,
                timestamp=datetime.now(),
                warnings=[],
                options_used=self.options
            ),
            word_count=len(full_content.split()),
            estimated_reading_time=len(full_content.split()) // 200
        )

        return document

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.epub'

    def _extract_metadata(self, book) -> Metadata:
        """Port from ebooklib_processor.py (lines 245-324)"""
        # ... implementation ...

    def _extract_toc_structure(self, book) -> List[TocEntry]:
        """Port from ebooklib_processor.py (lines 326-386)"""
        # ... implementation ...

    # ... other methods ...
```

3. **Key Adaptations:**
   - Remove Config dependency
   - Use options dict instead
   - Return Document instead of ProcessingResult
   - Remove progress_tracker references
   - Simplify chapter post-processing (no TTS-specific logic)
   - Remove temp directory management (caller handles this)

**Test File:** `tests/unit/test_epub_parser.py`

**Test Cases:**
- Parse valid EPUB with TOC
- Parse EPUB without TOC (spine fallback)
- Extract metadata correctly
- Detect chapters with hierarchy
- Extract images
- Handle corrupted EPUB gracefully

**Validation:**
```bash
uv run pytest tests/unit/test_epub_parser.py -v
```

---

### Phase 7-10: Other Parsers (16 hours total)

**Phase 7: PDF Parser (4 hours)**
- Use PyMuPDF for text extraction
- Font-based heading detection
- Tesseract OCR for scanned PDFs
- Test with text PDF and scanned PDF

**Phase 8: DOCX Parser (3 hours)**
- Use python-docx
- Style-based heading detection
- Image extraction from relationships
- Test with formatted DOCX

**Phase 9: HTML/URL Parser (4 hours)**
- Use Trafilatura for content extraction
- Readability fallback
- URL fetching with timeout
- Test with HTML file and mock URL

**Phase 10: Markdown & Text Parsers (2 hours each)**
- Markdown: YAML frontmatter, heading detection
- Text: Chardet encoding detection, normalization
- Test with various encodings

---

### Phase 11: Post-Processing Components (6 hours)

**11a. Chapter Detector (`processors/chapter_detector.py`):**
```python
def detect_chapters(
    content: str,
    format_type: str = "markdown",
    min_confidence: float = 0.5
) -> List[Chapter]:
    """
    Detect chapter boundaries based on headings.

    Strategies:
    - Markdown: Detect # headings
    - HTML: Detect <h1>-<h6> tags
    - Plain text: Heuristic patterns
    """
    if format_type == "markdown":
        return _detect_markdown_chapters(content)
    elif format_type == "html":
        return _detect_html_chapters(content)
    else:
        return _detect_plain_chapters(content)
```

**11b. Metadata Extractor (`processors/metadata_extractor.py`):**
```python
def extract_metadata(
    file_path: Path,
    format_type: str,
    content: str = None
) -> Metadata:
    """Extract metadata from document"""
    # Format-specific extraction logic
```

**11c. Markdown Converter (`processors/markdown_converter.py`):**
```python
def html_to_markdown(html: str) -> str:
    """Convert HTML to clean markdown"""
    # Use BeautifulSoup + custom logic
```

**11d. Text Cleaner (`processors/text_cleaner.py`):**
```python
def clean_text(
    text: str,
    remove_extra_whitespace: bool = True,
    fix_encoding: bool = True,
    normalize_quotes: bool = True
) -> str:
    """Clean and normalize text (NO TTS features)"""
    # Port subset from epub2tts TextCleaner
```

---

### Phase 12: Main Parser Function (4 hours)

**Task:** Implement `src/omniparser/parser.py`

```python
def parse_document(
    file_path: Union[str, Path],
    extract_images: bool = True,
    detect_chapters: bool = True,
    clean_text: bool = True,
    ocr_enabled: bool = True,
    custom_options: dict = None
) -> Document:
    """
    Parse a document and return structured output.

    Main entry point for Omniparser.
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path

    # Validate file
    validate_file_exists(file_path)
    validate_file_size(file_path)

    # Detect format
    if str(file_path).startswith('http'):
        format_type = 'html'
    else:
        format_type = detect_format(file_path)

    # Select parser
    parser_map = {
        'epub': EPUBParser,
        'pdf': PDFParser,
        'docx': DOCXParser,
        'html': HTMLParser,
        'markdown': MarkdownParser,
        'text': TextParser
    }

    parser_class = parser_map.get(format_type)
    if not parser_class:
        raise UnsupportedFormatError(f"Format not supported: {format_type}")

    # Configure parser
    options = custom_options or {}
    options.update({
        'extract_images': extract_images,
        'detect_chapters': detect_chapters,
        'clean_text': clean_text,
        'ocr_enabled': ocr_enabled
    })

    parser = parser_class(options)

    # Parse document
    try:
        document = parser.parse(file_path)
        return document
    except Exception as e:
        raise ParsingError(
            f"Failed to parse {file_path}",
            parser=format_type,
            original_error=e
        )
```

**Test File:** `tests/integration/test_full_pipeline.py`

---

### Phase 13: Package Exports (1 hour)

**Task:** Configure `src/omniparser/__init__.py`

```python
"""
Omniparser - Universal Document Parser

Parse documents from multiple formats into clean, structured markdown.
"""

__version__ = "1.0.0"

from .parser import parse_document
from .models import Document, Chapter, Metadata, ImageReference
from .exceptions import (
    OmniparserError,
    UnsupportedFormatError,
    ParsingError,
    FileReadError,
    NetworkError,
    ValidationError
)

__all__ = [
    'parse_document',
    'Document',
    'Chapter',
    'Metadata',
    'ImageReference',
    'OmniparserError',
    'UnsupportedFormatError',
    'ParsingError',
    'FileReadError',
    'NetworkError',
    'ValidationError'
]
```

**Validation:**
```bash
uv run python -c "from omniparser import parse_document; print('Import successful')"
```

---

### Phase 14: Integration Tests (6 hours)

**Tests to Create:**

1. **`test_full_pipeline.py`:**
   - Test parse_document() with all formats
   - Verify Document structure consistency
   - Test error handling

2. **`test_format_detection.py`:**
   - Test magic bytes detection
   - Test extension fallback
   - Test unsupported format error

3. **`test_error_handling.py`:**
   - Missing files
   - Corrupted files
   - Empty files
   - Large files

4. **`test_serialization.py`:**
   - Document.to_dict()
   - Document.from_dict()
   - Document.save_json()
   - Document.load_json()

**Fixtures:**
- Create small test files for each format
- Store in `tests/fixtures/`

---

### Phase 15: Documentation (4 hours)

**15a. README.md:**
- Project overview
- Installation
- Quickstart examples
- API reference (brief)
- Contributing

**15b. docs/api.md:**
- Full API documentation
- All functions and classes
- Parameters and returns
- Examples

**15c. docs/parsers.md:**
- How each parser works
- Supported features
- Limitations
- Custom parser guide

**15d. examples/:**
- `basic_usage.py`
- `batch_processing.py`
- `custom_parser.py`

---

### Phase 16: Final Validation & Testing (4 hours)

**Validation Checklist:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage >80%
- [ ] Code formatted with Black
- [ ] No type errors (mypy)
- [ ] Package builds: `uv build`
- [ ] Package installs locally
- [ ] Can import and use parse_document()
- [ ] All examples run
- [ ] Documentation complete
- [ ] CHANGELOG.md updated

**Commands:**
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=omniparser --cov-report=html

# Format code
uv run black src/ tests/

# Build package
uv build

# Test local install
uv add ./dist/omniparser-1.0.0.tar.gz
```

---

## 6. epub2tts Migration Strategy

### 6.1 How epub2tts Will Consume OmniParser

**Before (current):**
```python
# epub2tts/src/core/epub_processor.py
from core.ebooklib_processor import EbookLibProcessor

processor = EbookLibProcessor(config)
result = processor.process_epub(epub_path, output_dir)

# result.text_content → full text
# result.chapters → List[Chapter]
# result.metadata → dict
```

**After (with OmniParser):**
```python
# epub2tts/src/core/epub_processor.py
from omniparser import parse_document

# Parse EPUB using OmniParser
doc = parse_document(epub_path, extract_images=True, detect_chapters=True)

# Convert to epub2tts format
result = ProcessingResult(
    success=True,
    text_content=doc.content,
    chapters=[_convert_chapter(ch) for ch in doc.chapters],
    metadata=_convert_metadata(doc.metadata),
    image_info=[_convert_image(img) for img in doc.images],
    ...
)

def _convert_chapter(omni_chapter) -> Chapter:
    """Convert OmniParser Chapter to epub2tts Chapter"""
    return Chapter(
        chapter_num=omni_chapter.chapter_id,
        title=omni_chapter.title,
        content=omni_chapter.content,
        word_count=omni_chapter.word_count,
        estimated_duration=omni_chapter.word_count / 200.0,  # TTS-specific
        confidence=1.0  # Default high confidence
    )
```

### 6.2 Import Changes Needed

**Update `pyproject.toml`:**
```toml
[project.dependencies]
# Add OmniParser
omniparser>=1.0.0

# Keep these (still needed for TTS):
kokoro>=0.9.2
pydub>=0.25.0
# etc.

# Can remove these (now in OmniParser):
# ebooklib>=0.19  # ❌ Remove
# beautifulsoup4  # ❌ Remove (unless used elsewhere)
```

**Update imports:**
```python
# OLD
from core.ebooklib_processor import EbookLibProcessor

# NEW
from omniparser import parse_document, Document
```

### 6.3 What Code Gets Removed

**Files to DELETE:**
- ❌ `src/core/ebooklib_processor.py` (963 lines) → Now in OmniParser
- ❌ Parts of `src/core/text_cleaner.py` → Basic cleaning in OmniParser, keep TTS-specific

**Files to KEEP:**
- ✅ `src/core/epub_processor.py` → Wrapper that calls OmniParser + TTS pipeline
- ✅ `src/core/text_cleaner.py` → Keep TTS-specific cleaning (pause markers, etc.)
- ✅ All TTS, audio, web, orchestration code

**Estimated LOC Reduction:** ~1000 lines removed from epub2tts

### 6.4 Testing Strategy

**Phase 1: Parallel Testing**
```python
# In epub2tts, temporarily support both paths
if config.use_omniparser:
    doc = parse_document(epub_path)
    result = _convert_omniparser_result(doc)
else:
    processor = EbookLibProcessor(config)
    result = processor.process_epub(epub_path)
```

**Phase 2: Validation**
- Run full epub2tts test suite with OmniParser
- Compare outputs byte-by-byte
- Verify audio generation still works
- Test web interface

**Phase 3: Cleanup**
- Remove old code paths
- Update documentation
- Update tests

---

## 7. Risk Assessment

### 7.1 Potential Issues

**Risk 1: API Incompatibility**
- **Issue:** OmniParser Document structure doesn't match epub2tts needs
- **Mitigation:** Design Document model upfront, validate with epub2tts team
- **Severity:** HIGH
- **Status:** Addressed in Section 3.2 (careful mapping)

**Risk 2: Performance Regression**
- **Issue:** OmniParser slower than current ebooklib_processor
- **Mitigation:** Profile both implementations, optimize hot paths
- **Severity:** MEDIUM
- **Status:** Acceptable trade-off for abstraction (can optimize later)

**Risk 3: Loss of epub2tts-Specific Features**
- **Issue:** Some epub2tts features not preserved in OmniParser
- **Mitigation:** Identify must-have features upfront, add to OmniParser spec
- **Severity:** MEDIUM
- **Status:** TTS-specific features kept in epub2tts (pause markers, etc.)

**Risk 4: Dependency Hell**
- **Issue:** OmniParser dependencies conflict with epub2tts
- **Mitigation:** Careful dependency versioning, test in isolation
- **Severity:** LOW
- **Status:** Use UV for clean dependency resolution

**Risk 5: Incomplete Test Coverage**
- **Issue:** Edge cases not covered by tests
- **Mitigation:** Target >80% coverage, comprehensive integration tests
- **Severity:** MEDIUM
- **Status:** Phase 14 dedicated to testing

### 7.2 Mitigation Strategies

**Strategy 1: Incremental Migration**
- Don't replace epub2tts code all at once
- Support both paths temporarily
- Validate output equivalence before cutover

**Strategy 2: Feature Parity Matrix**
```
Feature                     | ebooklib_processor | OmniParser | Status
----------------------------|--------------------|-----------|---------
TOC-based chapter detection | ✅                 | ✅        | Ported
Metadata extraction         | ✅                 | ✅        | Ported
Image extraction            | ✅                 | ✅        | Ported
HTML text extraction        | ✅                 | ✅        | Ported
TTS pause markers           | ✅                 | ❌        | Kept in epub2tts
Chapter splitting           | ✅                 | ⚠️        | Configurable in options
Progress tracking           | ✅                 | ❌        | epub2tts responsibility
```

**Strategy 3: Backward Compatibility**
- OmniParser provides everything epub2tts needs
- epub2tts adds TTS-specific processing on top
- Clean separation of concerns

---

## 8. Implementation Timeline

**Total Estimated Time:** 60-70 hours

**Week 1: Foundation (Phases 1-5)**
- Day 1-2: Setup, models, base classes (10 hours)
- Day 3-4: Utilities, exceptions, tests (8 hours)

**Week 2: Core Parsers (Phases 6-7)**
- Day 5-7: EPUB parser port (8 hours)
- Day 8-9: PDF parser (4 hours)

**Week 3: Remaining Parsers (Phases 8-10)**
- Day 10: DOCX parser (3 hours)
- Day 11: HTML/URL parser (4 hours)
- Day 12: Markdown & Text parsers (4 hours)

**Week 4: Integration (Phases 11-14)**
- Day 13: Post-processors (6 hours)
- Day 14: Main parser function (4 hours)
- Day 15: Package exports (1 hour)
- Day 16-17: Integration tests (6 hours)

**Week 5: Polish (Phases 15-16)**
- Day 18-19: Documentation (4 hours)
- Day 20: Final validation (4 hours)
- Day 21: Buffer for issues (4 hours)

**Week 6: epub2tts Migration**
- Day 22-23: Update epub2tts integration (8 hours)
- Day 24: Testing and validation (4 hours)
- Day 25: Cleanup and documentation (4 hours)

---

## 9. Success Metrics

**Code Quality:**
- [ ] All parsers implement BaseParser interface
- [ ] Type hints on all public APIs
- [ ] Docstrings on all public functions/classes
- [ ] Black formatting applied
- [ ] No mypy errors

**Test Coverage:**
- [ ] >80% code coverage overall
- [ ] 100% coverage on data models
- [ ] All parsers have unit tests
- [ ] Integration tests for all formats
- [ ] Error handling tested

**Functionality:**
- [ ] All 6 parsers working
- [ ] Format detection accurate
- [ ] Chapter detection working
- [ ] Metadata extraction complete
- [ ] Image extraction functional

**Package Quality:**
- [ ] Builds without errors: `uv build`
- [ ] Installs cleanly: `uv add omniparser`
- [ ] Imports work: `from omniparser import parse_document`
- [ ] Examples run successfully
- [ ] README is clear and helpful

**epub2tts Integration:**
- [ ] epub2tts successfully uses OmniParser
- [ ] All epub2tts tests pass
- [ ] Audio generation still works
- [ ] No performance regression >20%
- [ ] Documentation updated

---

## 10. Next Steps After Completion

**Immediate (v1.0):**
1. Publish to PyPI: `uv publish`
2. Update epub2tts to use OmniParser
3. Remove old epub processing code from epub2tts
4. Write blog post announcing OmniParser

**Short-term (v1.1):**
1. Add RTF parser
2. Add ODT parser (LibreOffice)
3. Improve OCR quality
4. Better table extraction

**Medium-term (v1.2):**
1. Plugin system for custom parsers
2. Advanced URL parsing (JavaScript rendering)
3. Better image handling (alt text generation)
4. Processing progress callbacks
5. Performance optimizations

**Long-term (v2.0):**
1. AI-powered chapter detection
2. Semantic content analysis
3. Multi-document parsing (archives)
4. Streaming API for large files
5. Internationalization support

---

## 11. Conclusion

This architecture plan provides a complete blueprint for implementing OmniParser following METAPROMPT_1's 16 phases. Key design decisions:

1. **Clean separation:** OmniParser handles parsing, epub2tts handles TTS
2. **Proven foundation:** Port production-tested EPUB code from epub2tts
3. **Universal interface:** All parsers inherit from BaseParser
4. **Consistent data:** Document model works for all formats
5. **Professional quality:** Tests, docs, proper packaging

**The path forward is clear:**
- Phases 1-16 build OmniParser from scratch
- epub2tts migration strategy preserves functionality
- Risk mitigation strategies address potential issues
- Success metrics ensure quality

**This is the blueprint. Let's build it.**

---

**Document Version:** 1.0
**Last Updated:** October 16, 2025
**Status:** Ready for Implementation
**Next Action:** Begin Phase 1 (Repository Setup)
