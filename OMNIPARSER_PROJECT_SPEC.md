# Omniparser - Universal Document Parser

## Project Specification v1.0

**Last Updated:** October 16, 2025
**Status:** Planning Phase
**License:** MIT
**Target:** PyPI Package

---

## 1. Executive Summary

### 1.1 Project Overview
Omniparser is a universal document-to-markdown converter that extracts clean, structured text from multiple document formats. It serves as the parsing layer for epub2tts and other text processing applications, providing a consistent interface regardless of input format.

### 1.2 Core Value Proposition
- **Universal Interface**: Single API for all document formats
- **High-Quality Output**: Clean markdown with chapter detection and metadata
- **Format Agnostic**: EPUB, PDF, DOCX, HTML, URLs, TXT, Markdown
- **Image Handling**: Extract and catalog images with position tracking
- **Chapter Detection**: Intelligent heading-based chapter boundary identification
- **Metadata Extraction**: Author, title, word count, reading time estimates
- **PyPI Ready**: Professional package for easy installation

### 1.3 Use Cases
- **epub2tts**: Primary consumer for audiobook generation
- **Content Management**: Convert documents to uniform markdown format
- **Web Scrapers**: Extract main content from URLs
- **Document Pipelines**: Preprocessing for NLP/ML applications
- **Archive Tools**: Normalize document collections

---

## 2. Architecture Overview

### 2.1 Design Philosophy

**Abstract Base Parser:**
All format-specific parsers inherit from a common base class, ensuring consistent output structure and error handling.

**Pipeline Architecture:**
```
Input File → Format Detection → Specialized Parser → HTML Cleaner →
Markdown Converter → Chapter Detector → Metadata Extractor →
Output (Document object)
```

**Plugin System:**
New parsers can be added without modifying core logic by implementing the `BaseParser` interface.

### 2.2 Repository Structure

```
omniparser/
├── pyproject.toml              # UV package configuration
├── README.md                   # Package documentation
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── .gitignore
│
├── src/
│   └── omniparser/
│       ├── __init__.py         # Package exports
│       ├── parser.py           # Main parse_document() function
│       ├── models.py           # Data models (Document, Chapter, etc.)
│       │
│       ├── base/               # Abstract base classes
│       │   ├── __init__.py
│       │   └── base_parser.py  # BaseParser abstract class
│       │
│       ├── parsers/            # Format-specific parsers
│       │   ├── __init__.py
│       │   ├── epub_parser.py  # EPUB (EbookLib)
│       │   ├── pdf_parser.py   # PDF (PyMuPDF + OCR)
│       │   ├── docx_parser.py  # DOCX (python-docx)
│       │   ├── html_parser.py  # HTML/URLs (Trafilatura)
│       │   ├── markdown_parser.py  # Markdown (minimal)
│       │   └── text_parser.py  # Plain text (minimal)
│       │
│       ├── processors/         # Post-processing utilities
│       │   ├── __init__.py
│       │   ├── chapter_detector.py  # Heading-based chapter detection
│       │   ├── metadata_extractor.py  # Extract title, author, etc.
│       │   ├── markdown_converter.py  # HTML → Markdown conversion
│       │   └── text_cleaner.py  # Whitespace, encoding fixes
│       │
│       ├── utils/              # Utility functions
│       │   ├── __init__.py
│       │   ├── format_detector.py  # Detect file type (magic bytes)
│       │   ├── encoding.py     # Encoding detection and normalization
│       │   └── validators.py   # Input validation
│       │
│       └── exceptions.py       # Custom exceptions
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   │   ├── test_epub_parser.py
│   │   ├── test_pdf_parser.py
│   │   ├── test_docx_parser.py
│   │   └── ...
│   ├── integration/            # Integration tests
│   │   ├── test_full_pipeline.py
│   │   └── test_format_detection.py
│   └── fixtures/               # Test documents
│       ├── sample.epub
│       ├── sample.pdf
│       ├── sample.docx
│       └── ...
│
├── docs/                       # Documentation
│   ├── index.md                # Main documentation
│   ├── api.md                  # API reference
│   ├── parsers.md              # Parser implementation guide
│   └── contributing.md         # Contribution guidelines
│
└── examples/                   # Usage examples
    ├── basic_usage.py
    ├── custom_parser.py
    └── batch_processing.py
```

---

## 3. Core API

### 3.1 Main Function: `parse_document()`

```python
from omniparser import parse_document, Document

def parse_document(
    file_path: str,
    extract_images: bool = True,
    detect_chapters: bool = True,
    clean_text: bool = True,
    ocr_enabled: bool = True,
    custom_options: dict = None
) -> Document:
    """
    Parse a document and return structured output.

    Args:
        file_path: Path to document file or URL
        extract_images: Whether to extract and catalog images
        detect_chapters: Whether to detect chapter boundaries
        clean_text: Whether to apply text cleaning
        ocr_enabled: Whether to use OCR for image-based PDFs
        custom_options: Format-specific options

    Returns:
        Document object with parsed content and metadata

    Raises:
        UnsupportedFormatError: If file format is not supported
        ParsingError: If parsing fails
        FileNotFoundError: If file doesn't exist

    Examples:
        >>> # Parse an EPUB file
        >>> doc = parse_document("book.epub")
        >>> print(f"Title: {doc.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")

        >>> # Parse a PDF with OCR
        >>> doc = parse_document("scanned.pdf", ocr_enabled=True)

        >>> # Parse a URL
        >>> doc = parse_document("https://example.com/article")

        >>> # Custom options
        >>> doc = parse_document("document.pdf", custom_options={
        ...     "extract_tables": True,
        ...     "page_numbers": False
        ... })
    """
```

### 3.2 Data Models

```python
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class ImageReference:
    """Reference to an image within the document"""
    image_id: str
    position: int           # Character position in text
    file_path: Optional[str]  # Path to extracted image file
    alt_text: Optional[str]   # Alt text or caption
    size: Optional[tuple]     # (width, height) if available
    format: str             # "png", "jpg", etc.

@dataclass
class Chapter:
    """Represents a chapter or section"""
    chapter_id: int
    title: str
    content: str            # Markdown formatted
    start_position: int     # Character position in full text
    end_position: int       # Character position in full text
    word_count: int
    level: int              # Heading level (1=main chapter, 2=subsection, etc.)
    metadata: Optional[Dict] = None  # Chapter-specific metadata

@dataclass
class Metadata:
    """Document metadata"""
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[datetime] = None
    language: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    original_format: str = None
    file_size: int = 0
    custom_fields: Optional[Dict] = None

@dataclass
class ProcessingInfo:
    """Information about the parsing process"""
    parser_used: str        # "epub", "pdf", "docx", etc.
    parser_version: str
    processing_time: float  # Seconds
    timestamp: datetime
    warnings: List[str]     # Non-fatal issues encountered
    options_used: Dict      # Options passed to parser

@dataclass
class Document:
    """Main document object returned by parse_document()"""
    document_id: str        # UUID generated during parsing
    content: str            # Full document in markdown
    chapters: List[Chapter]
    images: List[ImageReference]
    metadata: Metadata
    processing_info: ProcessingInfo
    word_count: int
    estimated_reading_time: int  # Minutes

    def get_chapter(self, chapter_id: int) -> Optional[Chapter]:
        """Get chapter by ID"""
        return next((c for c in self.chapters if c.chapter_id == chapter_id), None)

    def get_text_range(self, start: int, end: int) -> str:
        """Extract text between character positions"""
        return self.content[start:end]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        # Implementation...

    @classmethod
    def from_dict(cls, data: dict) -> 'Document':
        """Create Document from dictionary"""
        # Implementation...

    def save_json(self, path: str):
        """Save to JSON file"""
        # Implementation...

    @classmethod
    def load_json(cls, path: str) -> 'Document':
        """Load from JSON file"""
        # Implementation...
```

---

## 4. Parser Implementations

### 4.1 Base Parser Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path
from .models import Document

class BaseParser(ABC):
    """Abstract base class for all parsers"""

    def __init__(self, options: dict = None):
        self.options = options or {}

    @abstractmethod
    def parse(self, file_path: Path) -> Document:
        """
        Parse the document and return a Document object.

        Args:
            file_path: Path to the file to parse

        Returns:
            Document object with parsed content

        Raises:
            ParsingError: If parsing fails
        """
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """
        Check if this parser supports the given file format.

        Args:
            file_path: Path to check

        Returns:
            True if format is supported
        """
        pass

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """
        Extract images from document (optional override).

        Returns:
            List of ImageReference objects
        """
        return []

    def clean_text(self, text: str) -> str:
        """
        Apply text cleaning (optional override).

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Default implementation
        from .processors.text_cleaner import clean_text
        return clean_text(text)
```

### 4.2 EPUB Parser (`parsers/epub_parser.py`)

**Port from epub2tts:**
- Use existing `src/core/ebooklib_processor.py` logic
- EbookLib for EPUB parsing
- BeautifulSoup for HTML processing
- TOC-based chapter detection
- Image extraction with base64 handling

**Key Features:**
```python
class EPUBParser(BaseParser):
    """Parser for EPUB files"""

    def parse(self, file_path: Path) -> Document:
        """
        Parse EPUB file using EbookLib.

        Features:
        - TOC-based chapter detection
        - Image extraction
        - Metadata from OPF
        - HTML to Markdown conversion
        """
        # Port logic from epub2tts/src/core/ebooklib_processor.py
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.epub']
```

**Dependencies:**
- `ebooklib>=0.19`
- `beautifulsoup4>=4.12.0`
- `lxml>=5.0.0`

### 4.3 PDF Parser (`parsers/pdf_parser.py`)

**Implementation:**
- PyMuPDF (fitz) for PDF parsing
- Tesseract OCR for image-based PDFs
- Table extraction support
- Font-based heading detection

**Key Features:**
```python
class PDFParser(BaseParser):
    """Parser for PDF files"""

    def parse(self, file_path: Path) -> Document:
        """
        Parse PDF file using PyMuPDF.

        Features:
        - Text extraction with font information
        - OCR fallback for scanned PDFs (Tesseract)
        - Table extraction
        - Image extraction
        - Font size-based heading detection
        """
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        text_blocks = []

        for page in doc:
            # Extract text with formatting info
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if block["type"] == 0:  # Text block
                    # Analyze font sizes for heading detection
                    # Extract text
                    pass
                elif block["type"] == 1:  # Image block
                    # Extract image
                    pass

        # If no text found, use OCR
        if not text_blocks and self.options.get("ocr_enabled", True):
            text_blocks = self._ocr_fallback(doc)

        return self._build_document(text_blocks)

    def _ocr_fallback(self, doc):
        """Use Tesseract OCR for image-based PDFs"""
        import pytesseract
        from PIL import Image

        # Implementation...
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'
```

**Dependencies:**
- `PyMuPDF>=1.23.0`
- `pytesseract>=0.3.10` (optional, for OCR)
- `Pillow>=10.0.0`

### 4.4 DOCX Parser (`parsers/docx_parser.py`)

**Implementation:**
- python-docx for DOCX parsing
- Heading styles for chapter detection
- Image extraction
- Preserve formatting markers

**Key Features:**
```python
class DOCXParser(BaseParser):
    """Parser for Microsoft Word DOCX files"""

    def parse(self, file_path: Path) -> Document:
        """
        Parse DOCX file using python-docx.

        Features:
        - Style-based heading detection
        - Image extraction
        - Table parsing
        - Footnote/endnote handling
        - Preserve bold/italic/emphasis
        """
        from docx import Document as DocxDocument

        docx = DocxDocument(file_path)

        # Extract metadata
        metadata = self._extract_metadata(docx.core_properties)

        # Process paragraphs
        markdown_content = []
        images = []

        for para in docx.paragraphs:
            # Check if heading
            if para.style.name.startswith('Heading'):
                level = int(para.style.name[-1])
                markdown_content.append('#' * level + ' ' + para.text)
            else:
                # Convert formatting to markdown
                md_text = self._format_to_markdown(para)
                markdown_content.append(md_text)

        # Extract images
        for rel in docx.part.rels.values():
            if "image" in rel.target_ref:
                images.append(self._extract_image(rel))

        return self._build_document(markdown_content, images, metadata)

    def _format_to_markdown(self, paragraph):
        """Convert DOCX formatting to Markdown"""
        # Implementation for bold, italic, etc.
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.docx', '.doc']
```

**Dependencies:**
- `python-docx>=1.0.0`
- `Pillow>=10.0.0`

### 4.5 HTML/URL Parser (`parsers/html_parser.py`)

**Implementation:**
- Trafilatura for content extraction
- Readability.js algorithm port as fallback
- Remove scripts, styles, navigation, ads
- Keep main content, images, code blocks

**Key Features:**
```python
class HTMLParser(BaseParser):
    """Parser for HTML files and URLs"""

    def parse(self, file_path_or_url: Path) -> Document:
        """
        Parse HTML file or URL using Trafilatura.

        Features:
        - Main content extraction (removes nav, ads, etc.)
        - Readability fallback
        - Image extraction with alt text
        - Code block preservation
        - Link handling
        """
        import trafilatura

        # Check if URL or file
        if str(file_path_or_url).startswith('http'):
            html = self._fetch_url(file_path_or_url)
        else:
            with open(file_path_or_url, 'r', encoding='utf-8') as f:
                html = f.read()

        # Extract main content
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_images=True,
            output_format='markdown'
        )

        # Fallback to readability if trafilatura fails
        if not text or len(text) < 100:
            text = self._readability_fallback(html)

        return self._build_document(text)

    def _fetch_url(self, url: str) -> str:
        """Fetch HTML from URL"""
        import requests

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def _readability_fallback(self, html: str) -> str:
        """Use readability algorithm as fallback"""
        from readability import Document as ReadabilityDocument

        doc = ReadabilityDocument(html)
        return self._html_to_markdown(doc.summary())

    def supports_format(self, file_path: Path) -> bool:
        return (
            file_path.suffix.lower() in ['.html', '.htm'] or
            str(file_path).startswith('http')
        )
```

**Dependencies:**
- `trafilatura>=1.6.0`
- `readability-lxml>=0.8.0`
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`

### 4.6 Markdown Parser (`parsers/markdown_parser.py`)

**Implementation:**
- Minimal processing (already in target format)
- Validate UTF-8 encoding
- Normalize line endings
- Extract frontmatter metadata

**Key Features:**
```python
class MarkdownParser(BaseParser):
    """Parser for Markdown files"""

    def parse(self, file_path: Path) -> Document:
        """
        Parse Markdown file with minimal processing.

        Features:
        - Frontmatter extraction (YAML/TOML)
        - Encoding normalization
        - Heading-based chapter detection
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        metadata = self._extract_frontmatter(content)

        # Remove frontmatter from content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        # Detect chapters from headings
        chapters = self._detect_chapters(content)

        return self._build_document(content, metadata, chapters)

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML/TOML frontmatter"""
        import yaml

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1])
        return {}

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.md', '.markdown']
```

**Dependencies:**
- `pyyaml>=6.0`

### 4.7 Text Parser (`parsers/text_parser.py`)

**Implementation:**
- Minimal processing
- Encoding detection and normalization
- Line ending normalization
- No chapter detection (single chapter)

**Key Features:**
```python
class TextParser(BaseParser):
    """Parser for plain text files"""

    def parse(self, file_path: Path) -> Document:
        """
        Parse plain text file.

        Features:
        - Encoding detection (UTF-8, Latin-1, etc.)
        - Line ending normalization
        - Minimal processing
        """
        # Detect encoding
        import chardet

        with open(file_path, 'rb') as f:
            raw = f.read()
            result = chardet.detect(raw)
            encoding = result['encoding']

        # Read with detected encoding
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Create single chapter
        chapter = Chapter(
            chapter_id=0,
            title=file_path.stem,
            content=content,
            start_position=0,
            end_position=len(content),
            word_count=len(content.split()),
            level=1
        )

        return self._build_document(content, [chapter])

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.txt'
```

**Dependencies:**
- `chardet>=5.2.0`

---

## 5. Post-Processing Components

### 5.1 Chapter Detection (`processors/chapter_detector.py`)

**Algorithm:**
- Detect headings (Markdown: `#`, HTML: `<h1>-<h6>`, DOCX: heading styles)
- Group content between headings into chapters
- Handle nested headings (subsections)
- Confidence scoring based on heading patterns

**Implementation:**
```python
def detect_chapters(
    content: str,
    format_type: str = "markdown",
    min_confidence: float = 0.5
) -> List[Chapter]:
    """
    Detect chapter boundaries based on headings.

    Args:
        content: Document content (markdown or HTML)
        format_type: "markdown", "html", or "plain"
        min_confidence: Minimum confidence threshold

    Returns:
        List of Chapter objects with boundaries
    """
    if format_type == "markdown":
        return _detect_markdown_chapters(content)
    elif format_type == "html":
        return _detect_html_chapters(content)
    else:
        # Plain text: heuristic-based detection
        return _detect_plain_chapters(content)

def _detect_markdown_chapters(content: str) -> List[Chapter]:
    """Detect chapters from markdown headings"""
    import re

    chapters = []
    lines = content.split('\n')

    current_chapter = None
    current_content = []

    for i, line in enumerate(lines):
        # Match headings: # Title, ## Subtitle, etc.
        match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if match:
            level = len(match.group(1))
            title = match.group(2).strip()

            # Save previous chapter
            if current_chapter:
                current_chapter.content = '\n'.join(current_content)
                current_chapter.end_position = sum(len(l) + 1 for l in current_content)
                chapters.append(current_chapter)

            # Start new chapter
            current_chapter = Chapter(
                chapter_id=len(chapters),
                title=title,
                content='',
                start_position=sum(len(l) + 1 for l in lines[:i]),
                end_position=0,
                word_count=0,
                level=level
            )
            current_content = []
        else:
            if current_chapter:
                current_content.append(line)

    # Save last chapter
    if current_chapter:
        current_chapter.content = '\n'.join(current_content)
        current_chapter.end_position = len(content)
        current_chapter.word_count = len(current_chapter.content.split())
        chapters.append(current_chapter)

    return chapters
```

### 5.2 Metadata Extraction (`processors/metadata_extractor.py`)

**Sources:**
- EPUB: OPF metadata
- PDF: Document properties
- DOCX: Core properties
- HTML: OpenGraph/meta tags
- Markdown: Frontmatter

**Implementation:**
```python
def extract_metadata(
    file_path: Path,
    format_type: str,
    content: str = None
) -> Metadata:
    """
    Extract metadata from document.

    Args:
        file_path: Path to document
        format_type: Document format ("epub", "pdf", etc.)
        content: Optional document content for HTML/Markdown

    Returns:
        Metadata object
    """
    extractors = {
        'epub': _extract_epub_metadata,
        'pdf': _extract_pdf_metadata,
        'docx': _extract_docx_metadata,
        'html': _extract_html_metadata,
        'markdown': _extract_markdown_metadata
    }

    extractor = extractors.get(format_type, _extract_default_metadata)
    return extractor(file_path, content)
```

### 5.3 Text Cleaning (`processors/text_cleaner.py`)

**Operations:**
- Normalize whitespace
- Fix encoding issues (ftfy)
- Remove page numbers/footers
- Normalize quotes and dashes
- Handle special characters

**Implementation:**
```python
def clean_text(
    text: str,
    remove_extra_whitespace: bool = True,
    fix_encoding: bool = True,
    normalize_quotes: bool = True
) -> str:
    """
    Clean and normalize text.

    Args:
        text: Raw text to clean
        remove_extra_whitespace: Remove multiple spaces/newlines
        fix_encoding: Fix encoding issues (mojibake)
        normalize_quotes: Convert fancy quotes to standard

    Returns:
        Cleaned text
    """
    import ftfy

    if fix_encoding:
        text = ftfy.fix_text(text)

    if remove_extra_whitespace:
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        # Remove multiple newlines (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

    if normalize_quotes:
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

    # Normalize em-dashes
    text = text.replace('—', '---')

    return text.strip()
```

---

## 6. Format Detection

### 6.1 Magic Bytes Detection (`utils/format_detector.py`)

**Implementation:**
```python
import magic

def detect_format(file_path: Path) -> str:
    """
    Detect file format using magic bytes.

    Args:
        file_path: Path to file

    Returns:
        Format identifier ("epub", "pdf", "docx", etc.)

    Raises:
        UnsupportedFormatError: If format is not supported
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

**Dependencies:**
- `python-magic>=0.4.27`

---

## 7. Exception Handling

### 7.1 Custom Exceptions (`exceptions.py`)

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

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test Each Parser:**
- Input: Sample file of each format
- Verify: Document structure, content extraction, metadata
- Edge cases: Corrupted files, empty files, large files

**Example:**
```python
# tests/unit/test_epub_parser.py
def test_epub_parser_basic():
    parser = EPUBParser()
    doc = parser.parse(Path("tests/fixtures/sample.epub"))

    assert doc.metadata.title is not None
    assert len(doc.chapters) > 0
    assert doc.word_count > 0

def test_epub_parser_with_images():
    parser = EPUBParser({"extract_images": True})
    doc = parser.parse(Path("tests/fixtures/sample_with_images.epub"))

    assert len(doc.images) > 0
    assert all(img.file_path for img in doc.images)
```

### 8.2 Integration Tests

**Full Pipeline:**
- Test `parse_document()` with each format
- Verify consistency of output structure
- Test format detection
- Test error handling

**Example:**
```python
# tests/integration/test_full_pipeline.py
@pytest.mark.parametrize("file_path,expected_format", [
    ("fixtures/sample.epub", "epub"),
    ("fixtures/sample.pdf", "pdf"),
    ("fixtures/sample.docx", "docx"),
])
def test_parse_document_formats(file_path, expected_format):
    doc = parse_document(file_path)

    assert doc.processing_info.parser_used == expected_format
    assert doc.content
    assert len(doc.chapters) > 0
```

### 8.3 Fixture Collection

**Test Documents:**
- EPUB: Fiction book, technical manual, comic/graphic novel
- PDF: Text-based, scanned (OCR), mixed
- DOCX: Simple, with images, with tables
- HTML: Article, blog post, documentation
- Markdown: With frontmatter, without frontmatter
- Text: UTF-8, Latin-1, with special characters

---

## 9. Package Configuration

### 9.1 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "omniparser"
version = "1.0.0"
description = "Universal document parser for multiple formats (EPUB, PDF, DOCX, HTML, Markdown, Text)"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "AutumnsGrove", email = "noreply@github.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Text Processing",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
requires-python = ">=3.10"
dependencies = [
    # Core
    "pyyaml>=6.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",

    # EPUB
    "ebooklib>=0.19",

    # PDF
    "PyMuPDF>=1.23.0",
    "pytesseract>=0.3.10",

    # DOCX
    "python-docx>=1.0.0",

    # HTML/URLs
    "trafilatura>=1.6.0",
    "readability-lxml>=0.8.0",
    "requests>=2.31.0",

    # Text processing
    "ftfy>=6.1.0",
    "chardet>=5.2.0",
    "python-magic>=0.4.27",

    # Utilities
    "Pillow>=10.0.0",
    "dataclasses-json>=0.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]

[project.urls]
Homepage = "https://github.com/AutumnsGrove/omniparser"
Repository = "https://github.com/AutumnsGrove/omniparser"
Issues = "https://github.com/AutumnsGrove/omniparser/issues"
Documentation = "https://omniparser.readthedocs.io"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--strict-markers --strict-config --verbose --cov=omniparser"
```

### 9.2 Installation

```bash
# Install from PyPI
pip install omniparser

# Or using UV
uv add omniparser

# Install with OCR support
pip install omniparser[ocr]

# Development installation
git clone https://github.com/AutumnsGrove/omniparser.git
cd omniparser
uv sync --dev
```

---

## 10. Usage Examples

### 10.1 Basic Usage

```python
from omniparser import parse_document

# Parse any supported format
doc = parse_document("book.epub")

# Access content
print(f"Title: {doc.metadata.title}")
print(f"Author: {doc.metadata.author}")
print(f"Chapters: {len(doc.chapters)}")
print(f"Word count: {doc.word_count}")

# Iterate chapters
for chapter in doc.chapters:
    print(f"Chapter {chapter.chapter_id}: {chapter.title}")
    print(f"Word count: {chapter.word_count}")

# Access full content as markdown
markdown_text = doc.content

# Save to JSON
doc.save_json("output.json")
```

### 10.2 Advanced Options

```python
# PDF with OCR
doc = parse_document(
    "scanned_document.pdf",
    ocr_enabled=True,
    custom_options={"extract_tables": True}
)

# HTML/URL parsing
doc = parse_document("https://example.com/article")

# Disable chapter detection
doc = parse_document("document.docx", detect_chapters=False)

# Custom image handling
doc = parse_document(
    "book.epub",
    extract_images=True,
    custom_options={"image_format": "png", "max_image_size": (1024, 1024)}
)
```

### 10.3 Batch Processing

```python
from omniparser import parse_document
from pathlib import Path

def process_directory(directory: Path):
    """Process all supported documents in a directory"""
    for file_path in directory.iterdir():
        if file_path.is_file():
            try:
                doc = parse_document(file_path)
                output_path = file_path.with_suffix('.json')
                doc.save_json(output_path)
                print(f"✓ Processed: {file_path.name}")
            except Exception as e:
                print(f"✗ Failed: {file_path.name} - {e}")

# Process all files in a directory
process_directory(Path("./documents"))
```

### 10.4 Integration with epub2tts

```python
# In epub2tts web backend
from omniparser import parse_document
from core.orchestrator import PipelineOrchestrator

async def process_uploaded_file(file_path: str):
    """Process uploaded document through omniparser + TTS pipeline"""

    # Step 1: Parse document
    try:
        doc = parse_document(
            file_path,
            extract_images=True,
            detect_chapters=True
        )
    except Exception as e:
        raise ProcessingError(f"Parsing failed: {e}")

    # Step 2: Process through TTS pipeline
    orchestrator = PipelineOrchestrator(config)
    result = await orchestrator.process_document({
        "content": doc.content,
        "chapters": [c.to_dict() for c in doc.chapters],
        "metadata": doc.metadata.to_dict()
    })

    return result
```

---

## 11. API Reference

### 11.1 Main Function

```python
parse_document(
    file_path: str | Path,
    extract_images: bool = True,
    detect_chapters: bool = True,
    clean_text: bool = True,
    ocr_enabled: bool = True,
    custom_options: dict | None = None
) -> Document
```

### 11.2 Document Methods

- `doc.get_chapter(chapter_id: int) -> Chapter | None`
- `doc.get_text_range(start: int, end: int) -> str`
- `doc.to_dict() -> dict`
- `doc.save_json(path: str) -> None`
- `Document.from_dict(data: dict) -> Document`
- `Document.load_json(path: str) -> Document`

### 11.3 Parser Registry

```python
from omniparser.base import BaseParser, register_parser

# Register custom parser
@register_parser("custom_format")
class CustomParser(BaseParser):
    def parse(self, file_path: Path) -> Document:
        # Implementation...
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix == '.custom'
```

---

## 12. Roadmap

### Version 1.0 (MVP)
- ✅ Core architecture
- ✅ EPUB parser (port from epub2tts)
- ✅ PDF parser (PyMuPDF + OCR)
- ✅ DOCX parser
- ✅ HTML/URL parser
- ✅ Markdown parser
- ✅ Text parser
- ✅ Chapter detection
- ✅ Metadata extraction
- ✅ PyPI package
- ✅ Comprehensive tests

### Version 1.1
- 📄 RTF parser
- 📄 ODT parser (LibreOffice)
- 🔍 Improved OCR quality
- 🏷️ Better metadata extraction
- 📊 Table extraction improvements

### Version 1.2
- 🧩 Plugin system for custom parsers
- 🌐 Advanced URL parsing (JavaScript rendering)
- 🎨 Better image handling (descriptions, alt text)
- 📈 Processing progress callbacks
- ⚡ Performance optimizations

### Version 2.0
- 🤖 AI-powered chapter detection
- 🧠 Semantic content analysis
- 🗂️ Multi-document parsing (archives)
- 🔄 Streaming API for large files
- 🌍 Internationalization support

---

## 13. Contributing

### 13.1 Adding a New Parser

1. Create `parsers/new_format_parser.py`
2. Inherit from `BaseParser`
3. Implement `parse()` and `supports_format()`
4. Add tests in `tests/unit/test_new_format_parser.py`
5. Update documentation
6. Submit pull request

### 13.2 Development Setup

```bash
# Clone repository
git clone https://github.com/AutumnsGrove/omniparser.git
cd omniparser

# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=omniparser --cov-report=html

# Format code
uv run black src/ tests/

# Type checking
uv run mypy src/
```

---

## 14. License

MIT License - see LICENSE file for details.

---

## 15. Acknowledgments

- **epub2tts**: Original EPUB processing logic
- **Trafilatura**: HTML content extraction
- **PyMuPDF**: PDF parsing
- **python-docx**: DOCX parsing
- **EbookLib**: EPUB parsing

---

**End of Omniparser Project Specification v1.0**

*This specification defines a professional, PyPI-ready universal document parser that serves as the parsing layer for epub2tts and other text processing applications.*
