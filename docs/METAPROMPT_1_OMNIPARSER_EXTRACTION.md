# Metaprompt #1: Omniparser Extraction

**Task Type:** Sequential implementation via general-purpose Task agent
**Objective:** Create standalone Omniparser repository with universal document parsing capabilities
**Prerequisites:** Read OMNIPARSER_PROJECT_SPEC.md
**Validation Required:** All tests pass before proceeding to Metaprompt #2

---

## Task Overview

You are creating a new standalone Python package called **Omniparser** - a universal document parser that converts multiple formats (EPUB, PDF, DOCX, HTML, URLs, Markdown, Text) into clean, structured markdown with metadata.

This package will be published to PyPI and used by epub2tts and other projects. It must have excellent test coverage, clean abstractions, and professional documentation.

---

## Context

**Current State:**
- epub2tts has excellent EPUB processing logic in `src/core/ebooklib_processor.py` (963 lines)
- This logic needs to be ported to Omniparser as the EPUB parser
- New parsers need to be created for other formats
- All parsers must implement a common `BaseParser` interface

**Target State:**
- Separate `omniparser` repository with PyPI package
- Professional, well-tested codebase
- Easy installation: `uv add omniparser`
- Clean API: `parse_document(path) -> Document`

---

## Implementation Phases

### Phase 1: Repository Setup & Structure

**Task:** Create new repository structure

**Directory Structure to Create:**
```
omniparser/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── CHANGELOG.md
├── .gitignore
├── src/
│   └── omniparser/
│       ├── __init__.py
│       ├── parser.py
│       ├── models.py
│       ├── exceptions.py
│       ├── base/
│       │   ├── __init__.py
│       │   └── base_parser.py
│       ├── parsers/
│       │   └── __init__.py
│       ├── processors/
│       │   └── __init__.py
│       └── utils/
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
│   └── README.md
└── examples/
    └── basic_usage.py
```

**Key Files to Create:**

1. **pyproject.toml** - Use UV package manager format from spec
2. **README.md** - Package overview, installation, quickstart
3. **LICENSE** - MIT License
4. **.gitignore** - Python gitignore template
5. **CHANGELOG.md** - Version history (start with 1.0.0)

**Implementation Instructions:**
- Use UV for package management (`uv init`)
- Follow Python best practices (src-layout)
- Include all dependencies from OMNIPARSER_PROJECT_SPEC.md section 9.1

**Validation:**
- Repository structure matches spec
- `uv sync` runs without errors
- Git initialized with proper gitignore

---

### Phase 2: Core Data Models

**Task:** Implement data models in `src/omniparser/models.py`

**Models to Implement:**
1. `ImageReference` - Image metadata and position
2. `Chapter` - Chapter content with boundaries
3. `Metadata` - Document metadata
4. `ProcessingInfo` - Parser metadata
5. `Document` - Main document object

**Requirements:**
- Use dataclasses with type hints
- Include all methods specified in spec (section 3.2):
  - `Document.get_chapter()`
  - `Document.get_text_range()`
  - `Document.to_dict()`
  - `Document.from_dict()`
  - `Document.save_json()`
  - `Document.load_json()`
- Add comprehensive docstrings
- Include serialization/deserialization logic

**Validation:**
- Create unit tests: `tests/unit/test_models.py`
- Test serialization/deserialization
- Test all helper methods
- All tests pass with pytest

---

### Phase 3: Base Parser Interface

**Task:** Implement abstract base parser in `src/omniparser/base/base_parser.py`

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
        from ..processors.text_cleaner import clean_text
        return clean_text(text)
```

**Requirements:**
- Full implementation per spec section 4.1
- Comprehensive docstrings with examples
- Type hints on all methods

**Validation:**
- Code is syntactically correct
- Imports work properly
- Abstract methods are properly decorated

---

### Phase 4: Utility Functions

**Task:** Implement utility modules

**4a. Format Detection (`utils/format_detector.py`):**
- Implement `detect_format(file_path: Path) -> str`
- Use python-magic for magic bytes detection
- Fallback to file extension
- Map MIME types to format strings
- Handle URLs (starts with http/https)

**4b. Encoding Utilities (`utils/encoding.py`):**
- Encoding detection with chardet
- UTF-8 normalization
- Line ending normalization

**4c. Validators (`utils/validators.py`):**
- File existence validation
- File size validation
- Format support validation

**Validation:**
- Unit tests for each utility function
- Test edge cases (missing files, corrupt files, URLs)
- All tests pass

---

### Phase 5: Exception Classes

**Task:** Implement custom exceptions in `src/omniparser/exceptions.py`

**Exceptions to Implement:**
- `OmniparserError` (base)
- `UnsupportedFormatError`
- `ParsingError`
- `FileReadError`
- `NetworkError`
- `ValidationError`

**Requirements:**
- Follow spec section 7.1 exactly
- Include helpful error messages
- Include context (parser name, original error)

**Validation:**
- Exceptions can be raised and caught
- Error messages are clear
- Inheritance hierarchy is correct

---

### Phase 6: EPUB Parser (Port from epub2tts)

**Task:** Port EPUB processing logic to `src/omniparser/parsers/epub_parser.py`

**Source:** epub2tts `src/core/ebooklib_processor.py`

**Implementation Steps:**
1. Read the existing ebooklib_processor.py carefully
2. Extract core EPUB processing logic
3. Adapt to BaseParser interface
4. Return Document object (not raw dict)
5. Handle images, chapters, metadata

**Key Features to Port:**
- EbookLib EPUB parsing
- TOC-based chapter detection
- Image extraction with base64 handling
- Metadata from OPF
- HTML to Markdown conversion (BeautifulSoup)

**Requirements:**
- Inherit from BaseParser
- Implement `parse()` and `supports_format()`
- Return properly formatted Document object
- Handle errors gracefully

**Validation:**
- Create `tests/unit/test_epub_parser.py`
- Test with sample EPUB file (create fixture)
- Verify chapters extracted correctly
- Verify metadata extracted
- Verify images cataloged
- All tests pass

---

### Phase 7: PDF Parser

**Task:** Implement `src/omniparser/parsers/pdf_parser.py`

**Implementation Requirements:**
- Use PyMuPDF (fitz) for PDF parsing
- Extract text with formatting information
- Font size-based heading detection
- Image extraction
- OCR fallback for scanned PDFs (Tesseract)
- Table extraction support

**Key Methods:**
```python
class PDFParser(BaseParser):
    def parse(self, file_path: Path) -> Document:
        # Main parsing logic
        pass

    def _extract_text_blocks(self, doc):
        # Extract text with formatting
        pass

    def _ocr_fallback(self, doc):
        # Tesseract OCR for scanned PDFs
        pass

    def _detect_headings(self, blocks):
        # Font size-based heading detection
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'
```

**Dependencies:**
- PyMuPDF>=1.23.0
- pytesseract>=0.3.10
- Pillow>=10.0.0

**Validation:**
- Create `tests/unit/test_pdf_parser.py`
- Test with text-based PDF fixture
- Test with scanned PDF (OCR)
- Verify heading detection
- Verify image extraction
- All tests pass

---

### Phase 8: DOCX Parser

**Task:** Implement `src/omniparser/parsers/docx_parser.py`

**Implementation Requirements:**
- Use python-docx for parsing
- Style-based heading detection (Heading 1, Heading 2, etc.)
- Image extraction from relationships
- Table parsing
- Preserve formatting (bold, italic) as markdown
- Metadata from core properties

**Key Methods:**
```python
class DOCXParser(BaseParser):
    def parse(self, file_path: Path) -> Document:
        # Main parsing logic
        pass

    def _extract_metadata(self, properties):
        # Extract title, author, etc.
        pass

    def _format_to_markdown(self, paragraph):
        # Convert DOCX formatting to markdown
        pass

    def _extract_images(self, docx):
        # Extract embedded images
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.docx', '.doc']
```

**Dependencies:**
- python-docx>=1.0.0
- Pillow>=10.0.0

**Validation:**
- Create `tests/unit/test_docx_parser.py`
- Test with simple DOCX fixture
- Test with images and tables
- Verify heading detection
- Verify formatting preservation
- All tests pass

---

### Phase 9: HTML/URL Parser

**Task:** Implement `src/omniparser/parsers/html_parser.py`

**Implementation Requirements:**
- Use Trafilatura for main content extraction
- Readability fallback if Trafilatura fails
- Support both files and URLs
- Remove scripts, styles, navigation, ads
- Keep main content, images, code blocks
- Handle HTTP requests with timeout

**Key Methods:**
```python
class HTMLParser(BaseParser):
    def parse(self, file_path_or_url: Path) -> Document:
        # Main parsing logic
        pass

    def _fetch_url(self, url: str) -> str:
        # Fetch HTML from URL
        pass

    def _readability_fallback(self, html: str) -> str:
        # Fallback content extraction
        pass

    def supports_format(self, file_path: Path) -> bool:
        return (
            file_path.suffix.lower() in ['.html', '.htm'] or
            str(file_path).startswith('http')
        )
```

**Dependencies:**
- trafilatura>=1.6.0
- readability-lxml>=0.8.0
- requests>=2.31.0
- beautifulsoup4>=4.12.0

**Validation:**
- Create `tests/unit/test_html_parser.py`
- Test with HTML file fixture
- Test with mock URL (use requests-mock)
- Verify main content extraction
- Verify ads/nav removal
- All tests pass

---

### Phase 10: Markdown & Text Parsers

**Task:** Implement simple parsers

**10a. Markdown Parser (`parsers/markdown_parser.py`):**
- Minimal processing (already in target format)
- YAML frontmatter extraction
- Encoding normalization
- Heading-based chapter detection

**10b. Text Parser (`parsers/text_parser.py`):**
- Encoding detection (chardet)
- Line ending normalization
- Single chapter (no detection)
- Minimal processing

**Requirements:**
- Both inherit from BaseParser
- Follow spec sections 4.6 and 4.7
- Handle encoding issues gracefully

**Validation:**
- Create test files for both parsers
- Test various encodings (UTF-8, Latin-1)
- Test frontmatter extraction (markdown)
- All tests pass

---

### Phase 11: Post-Processing Components

**Task:** Implement processor modules

**11a. Chapter Detector (`processors/chapter_detector.py`):**
```python
def detect_chapters(
    content: str,
    format_type: str = "markdown",
    min_confidence: float = 0.5
) -> List[Chapter]:
    """Detect chapter boundaries based on headings"""
    pass
```

**11b. Metadata Extractor (`processors/metadata_extractor.py`):**
```python
def extract_metadata(
    file_path: Path,
    format_type: str,
    content: str = None
) -> Metadata:
    """Extract metadata from document"""
    pass
```

**11c. Markdown Converter (`processors/markdown_converter.py`):**
```python
def html_to_markdown(html: str) -> str:
    """Convert HTML to clean markdown"""
    pass
```

**11d. Text Cleaner (`processors/text_cleaner.py`):**
```python
def clean_text(
    text: str,
    remove_extra_whitespace: bool = True,
    fix_encoding: bool = True,
    normalize_quotes: bool = True
) -> str:
    """Clean and normalize text"""
    pass
```

**Dependencies:**
- ftfy>=6.1.0 (for encoding fixes)

**Validation:**
- Unit tests for each processor
- Test with various inputs
- Test edge cases
- All tests pass

---

### Phase 12: Main Parser Function

**Task:** Implement main `parse_document()` function in `src/omniparser/parser.py`

**Implementation:**
```python
from pathlib import Path
from typing import Union
from .models import Document
from .utils.format_detector import detect_format
from .parsers import (
    EPUBParser, PDFParser, DOCXParser,
    HTMLParser, MarkdownParser, TextParser
)
from .exceptions import UnsupportedFormatError, ParsingError

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

    # Detect format
    if str(file_path).startswith('http'):
        format_type = 'html'
    else:
        format_type = detect_format(file_path)

    # Create parser
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

**Validation:**
- Integration tests with all formats
- Test error handling
- Test with invalid files
- All tests pass

---

### Phase 13: Package Exports

**Task:** Configure `src/omniparser/__init__.py`

**Implementation:**
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
- Can import: `from omniparser import parse_document`
- Can import: `from omniparser import Document`
- Version is accessible: `omniparser.__version__`

---

### Phase 14: Integration Tests

**Task:** Create comprehensive integration tests in `tests/integration/`

**Tests to Create:**

**14a. `test_full_pipeline.py`:**
```python
@pytest.mark.parametrize("file_path,expected_format", [
    ("fixtures/sample.epub", "epub"),
    ("fixtures/sample.pdf", "pdf"),
    ("fixtures/sample.docx", "docx"),
    ("fixtures/sample.html", "html"),
    ("fixtures/sample.md", "markdown"),
    ("fixtures/sample.txt", "text"),
])
def test_parse_document_all_formats(file_path, expected_format):
    """Test parse_document with all supported formats"""
    doc = parse_document(file_path)

    assert doc.processing_info.parser_used == expected_format
    assert doc.content
    assert len(doc.chapters) > 0
    assert doc.word_count > 0
```

**14b. `test_format_detection.py`:**
- Test automatic format detection
- Test format fallback to extension
- Test unsupported format error

**14c. `test_error_handling.py`:**
- Test with missing files
- Test with corrupted files
- Test with empty files
- Test with huge files

**14d. `test_serialization.py`:**
- Test Document.to_dict()
- Test Document.from_dict()
- Test Document.save_json()
- Test Document.load_json()

**Fixtures to Create:**
- `tests/fixtures/sample.epub` - Small test EPUB
- `tests/fixtures/sample.pdf` - Multi-page PDF
- `tests/fixtures/sample.docx` - DOCX with images
- `tests/fixtures/sample.html` - HTML article
- `tests/fixtures/sample.md` - Markdown with frontmatter
- `tests/fixtures/sample.txt` - Plain text

**Validation:**
- All integration tests pass
- Test coverage > 80%
- No skipped tests

---

### Phase 15: Documentation

**Task:** Create comprehensive documentation

**15a. README.md:**
- Project overview
- Features list
- Installation instructions
- Quickstart example
- API reference (brief)
- Link to full docs
- Contributing guidelines
- License

**15b. docs/api.md:**
- Full API documentation
- All functions and classes
- Parameters and return types
- Examples for each

**15c. docs/parsers.md:**
- How each parser works
- Supported features per format
- Limitations and known issues
- Custom parser implementation guide

**15d. examples/:**
- `basic_usage.py` - Simple examples
- `batch_processing.py` - Process directory
- `custom_parser.py` - Implement custom parser

**Validation:**
- README is clear and professional
- Examples run without errors
- Documentation is comprehensive

---

### Phase 16: Final Validation & Testing

**Task:** Comprehensive validation before declaring complete

**Validation Checklist:**
- [ ] All unit tests pass (pytest)
- [ ] All integration tests pass
- [ ] Test coverage > 80% (pytest-cov)
- [ ] Code formatted with Black
- [ ] No type errors (mypy)
- [ ] Package builds: `uv build`
- [ ] Package installs: `uv add ./dist/omniparser-1.0.0.tar.gz`
- [ ] Can import and use: `from omniparser import parse_document`
- [ ] All example scripts run successfully
- [ ] Documentation is complete
- [ ] CHANGELOG.md updated
- [ ] README.md is professional

**Test Commands:**
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=omniparser --cov-report=html

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/

# Build package
uv build

# Test installation
uv add ./dist/omniparser-1.0.0.tar.gz
```

**Final Deliverables:**
1. Fully functional Omniparser package
2. All tests passing (>80% coverage)
3. Complete documentation
4. Working examples
5. Professional README

---

## Success Criteria

**Must Have:**
- ✅ All parsers implemented (EPUB, PDF, DOCX, HTML, Markdown, Text)
- ✅ All tests passing
- ✅ Test coverage > 80%
- ✅ Package builds without errors
- ✅ Can install via: `uv add omniparser`
- ✅ API matches spec exactly
- ✅ Documentation complete

**Quality Metrics:**
- Clean, readable code following Python best practices
- Comprehensive docstrings on all public functions
- Type hints throughout
- Error handling on all parsers
- Professional README

**Validation Statement:**
Before proceeding to Metaprompt #2 (Repo Cleanup), you MUST confirm:

> "Omniparser extraction is COMPLETE. All tests pass. Package builds successfully. Ready for epub2tts integration."

---

## Important Notes

1. **Port EPUB logic carefully** - The existing ebooklib_processor.py is production-tested. Don't rewrite from scratch - adapt it.

2. **Test thoroughly** - Each parser must have comprehensive unit tests. Integration tests must cover all formats.

3. **Follow spec exactly** - The data models and API must match OMNIPARSER_PROJECT_SPEC.md precisely.

4. **Professional quality** - This will be published to PyPI. Code quality matters.

5. **Document everything** - Future developers (and future you) will thank you.

6. **Handle errors gracefully** - Every parser should fail gracefully with helpful error messages.

---

## Handoff to Metaprompt #2

Once Omniparser is complete and validated, the next step is:

**Metaprompt #2: Repo Cleanup & Reorganization**
- Add omniparser as dependency to epub2tts
- Reorganize epub2tts structure (/core/, /audio-processing/, /web/)
- Remove old EPUB processing code
- Update imports throughout
- Validate CLI still works

**Do NOT proceed to Metaprompt #2 until Omniparser is fully validated.**

---

**End of Metaprompt #1**

This metaprompt provides complete, step-by-step instructions for creating the Omniparser package from scratch, with validation at every step.
