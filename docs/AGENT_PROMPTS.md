# OmniParser - Agent Prompts for Parallel Development

**Version:** 0.2.1
**Date:** October 28, 2025
**Purpose:** Comprehensive prompts for Claude Code remote agents working on parallel parser implementation

---

## Overview

This document contains **6 autonomous agent prompts** for implementing OmniParser's remaining parsers and enhancement features. Each agent will work in a separate branch and can operate independently.

**Execution Order:**
1. **Parallel (Agents 1-4):** PDF, DOCX, Markdown, Text parsers (can run simultaneously)
2. **Parallel (Agent 5):** AI Features (can run with parsers or after)
3. **Sequential (Agent 6):** Performance Optimization (MUST run last after all parsers complete)

---

## Agent 1: PDF Parser Implementation

### Branch: `feature/pdf-parser`

### Context

You are implementing the **PDF Parser** for OmniParser, a universal document parser that transforms documents into clean markdown with comprehensive metadata. This is Phase 2.4 of the implementation roadmap.

**Current Status:**
- ✅ EPUB Parser fully implemented (src/omniparser/parsers/epub_parser.py)
- ✅ HTML/URL Parser fully implemented (src/omniparser/parsers/html_parser.py)
- ✅ 468 tests passing (100% success rate)
- ✅ Shared processors ready: chapter_detector, text_cleaner, metadata_extractor, markdown_converter
- ✅ Universal data models: Document, Chapter, Metadata, ImageReference, ProcessingInfo
- ✅ Dependencies installed: PyMuPDF>=1.23.0, pytesseract>=0.3.10, Pillow>=10.0.0

**Your Mission:**
Implement a production-ready PDF parser that:
1. Extracts text from text-based PDFs using PyMuPDF
2. Detects headings based on font size/weight analysis
3. Falls back to OCR for scanned/image-based PDFs
4. Extracts embedded images with metadata
5. Converts tables to markdown format
6. Integrates with shared processors (chapter_detector, text_cleaner)
7. Returns universal Document model
8. Achieves >90% test coverage

### Essential Reading (Read These First!)

**MUST READ before starting:**
1. **docs/ARCHITECTURE_PLAN.md** - Phase 2.4 section (lines ~800-900)
2. **docs/IMPLEMENTATION_REFERENCE.md** - Parser implementation patterns
3. **src/omniparser/parsers/epub_parser.py** - Reference implementation (~1040 lines)
4. **src/omniparser/parsers/html_parser.py** - Alternative reference (~683 lines)
5. **src/omniparser/base/base_parser.py** - Abstract base class you MUST inherit from
6. **src/omniparser/models.py** - Data models you MUST use
7. **CLAUDE.md** - Project coding standards and conventions

### Reusable Components (DO NOT reimplement these!)

**Shared Processors (src/omniparser/processors/):**
- `chapter_detector.py` (183 lines) - Use this after converting font-based headings to markdown
- `text_cleaner.py` (300 lines) - Use this to clean extracted text
- `markdown_converter.py` (408 lines) - Optional: for HTML content in PDF annotations

**Utilities (src/omniparser/utils/):**
- `format_detector.py` - Format detection (already supports PDF)
- `encoding.py` - Text encoding utilities
- `validators.py` - File validation

**Base Classes:**
- `BaseParser` (src/omniparser/base/base_parser.py) - Your class MUST inherit from this

**Data Models (src/omniparser/models.py):**
- `Document` - Main output container
- `Chapter` - Chapter structure
- `Metadata` - Metadata container
- `ImageReference` - Image metadata
- `ProcessingInfo` - Parser execution info

### Technical Specification

#### File Location
```
src/omniparser/parsers/pdf_parser.py
```

#### Class Structure
```python
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from datetime import datetime

from ..base.base_parser import BaseParser
from ..models import Document, Chapter, Metadata, ImageReference, ProcessingInfo
from ..processors.chapter_detector import detect_chapters
from ..processors.text_cleaner import clean_text
from ..exceptions import ParsingError, FileReadError

class PDFParser(BaseParser):
    """
    Parser for PDF files using PyMuPDF with OCR fallback.

    Features:
    - Text extraction from text-based PDFs
    - Font-based heading detection for chapter structure
    - OCR fallback for scanned/image-based PDFs using Tesseract
    - Image extraction with metadata
    - Table extraction and markdown conversion
    - Metadata extraction from PDF properties

    Options:
        extract_images (bool): Extract embedded images (default: True)
        image_output_dir (Path): Directory for extracted images (default: temp)
        ocr_enabled (bool): Enable OCR for scanned PDFs (default: True)
        ocr_language (str): Tesseract language code (default: 'eng')
        min_heading_size (float): Minimum font size for headings (default: auto-detect)
        extract_tables (bool): Extract and convert tables (default: True)
        clean_text (bool): Apply text cleaning (default: True)

    Example:
        >>> parser = PDFParser({'extract_images': True, 'ocr_enabled': True})
        >>> doc = parser.parse(Path("document.pdf"))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize PDF parser with options."""
        super().__init__(options)

    def parse(self, file_path: Path) -> Document:
        """
        Parse PDF file and return Document object.

        Process:
        1. Open PDF with PyMuPDF
        2. Extract metadata from PDF properties
        3. Detect if text-based or scanned (check text content ratio)
        4. Extract text (native or OCR)
        5. Analyze font sizes to detect headings
        6. Convert detected headings to markdown
        7. Use chapter_detector to create chapters
        8. Extract images if enabled
        9. Extract tables if enabled
        10. Apply text cleaning
        11. Build and return Document

        Args:
            file_path: Path to PDF file

        Returns:
            Document object with parsed content

        Raises:
            FileReadError: If PDF cannot be opened
            ParsingError: If parsing fails
        """
        # Implementation here
        pass

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is PDF format."""
        return file_path.suffix.lower() == '.pdf'

    def _is_scanned_pdf(self, doc: fitz.Document) -> bool:
        """
        Determine if PDF is scanned (image-based) or text-based.

        Strategy:
        - Sample first 3 pages
        - Count extracted text characters
        - If < 100 chars per page on average, consider scanned

        Args:
            doc: PyMuPDF document object

        Returns:
            True if scanned (needs OCR), False if text-based
        """
        pass

    def _extract_text_with_formatting(self, doc: fitz.Document) -> Tuple[str, List[Dict]]:
        """
        Extract text with font information for heading detection.

        Returns:
        - full_text: Complete text content
        - text_blocks: List of dicts with {text, font_size, font_weight, is_bold, page_num}

        Args:
            doc: PyMuPDF document object

        Returns:
            Tuple of (full_text, text_blocks)
        """
        pass

    def _extract_text_with_ocr(self, doc: fitz.Document) -> str:
        """
        Extract text using OCR (Tesseract) for scanned PDFs.

        Process:
        1. Convert each page to PIL Image
        2. Run Tesseract OCR
        3. Combine results
        4. Add page markers

        Args:
            doc: PyMuPDF document object

        Returns:
            OCR-extracted text
        """
        pass

    def _detect_headings_from_fonts(
        self,
        text_blocks: List[Dict]
    ) -> List[Tuple[str, int, int]]:
        """
        Detect headings based on font size analysis.

        Algorithm:
        1. Calculate average font size across document
        2. Calculate standard deviation
        3. Threshold = average + (1.5 * std_dev)
        4. Blocks above threshold = headings
        5. Map font sizes to heading levels (1-6)

        Args:
            text_blocks: List of text blocks with font info

        Returns:
            List of (heading_text, level, position) tuples
        """
        pass

    def _convert_headings_to_markdown(
        self,
        text: str,
        headings: List[Tuple[str, int, int]]
    ) -> str:
        """
        Convert detected headings to markdown format.

        Replace heading text in content with markdown headings:
        - Level 1: # Heading
        - Level 2: ## Heading
        - etc.

        Args:
            text: Original text
            headings: Detected headings with levels

        Returns:
            Text with markdown headings
        """
        pass

    def _extract_metadata(self, doc: fitz.Document) -> Metadata:
        """
        Extract metadata from PDF properties.

        PDF Properties:
        - Title: doc.metadata['title']
        - Author: doc.metadata['author']
        - Subject: doc.metadata['subject']
        - Keywords: doc.metadata['keywords']
        - Creator: doc.metadata['creator']
        - Producer: doc.metadata['producer']
        - CreationDate: doc.metadata['creationDate']

        Args:
            doc: PyMuPDF document object

        Returns:
            Metadata object
        """
        pass

    def _extract_images(self, doc: fitz.Document) -> List[ImageReference]:
        """
        Extract embedded images from PDF.

        Process:
        1. Iterate through pages
        2. Get image list: page.get_images()
        3. Extract image data: doc.extract_image(xref)
        4. Save to output directory
        5. Create ImageReference objects

        Args:
            doc: PyMuPDF document object

        Returns:
            List of ImageReference objects
        """
        pass

    def _extract_tables(self, doc: fitz.Document) -> List[str]:
        """
        Extract tables and convert to markdown format.

        Note: PyMuPDF has basic table detection via page.find_tables()

        Args:
            doc: PyMuPDF document object

        Returns:
            List of markdown-formatted tables
        """
        pass
```

### Implementation Steps

#### Step 1: Create Parser File
```bash
# Create branch
git checkout -b feature/pdf-parser

# Create parser file
touch src/omniparser/parsers/pdf_parser.py
```

#### Step 2: Implement Core Methods (in order)
1. `__init__()` - Initialize with options
2. `supports_format()` - Check if PDF
3. `_extract_metadata()` - Extract PDF metadata
4. `_is_scanned_pdf()` - Detect scanned vs text-based
5. `_extract_text_with_formatting()` - Text + font info
6. `_extract_text_with_ocr()` - OCR fallback
7. `_detect_headings_from_fonts()` - Font-based heading detection
8. `_convert_headings_to_markdown()` - Convert to markdown headings
9. `_extract_images()` - Image extraction
10. `_extract_tables()` - Table extraction
11. `parse()` - Main orchestration method

#### Step 3: Integrate with Main Parser
Update `src/omniparser/parser.py`:
```python
from .parsers.pdf_parser import PDFParser

# In parse_document():
elif format_type == "pdf":
    parser = PDFParser(options)
    return parser.parse(file_path)
```

#### Step 4: Update Package Exports
Update `src/omniparser/__init__.py`:
```python
from .parsers.pdf_parser import PDFParser
```

### Testing Requirements

#### Test File: `tests/unit/test_pdf_parser.py`

**Required Test Coverage:**
```python
import pytest
from pathlib import Path
from omniparser.parsers.pdf_parser import PDFParser
from omniparser.models import Document
from omniparser.exceptions import FileReadError, ParsingError

class TestPDFParserInit:
    """Test parser initialization."""

    def test_init_default_options():
        """Test initialization with default options."""

    def test_init_custom_options():
        """Test initialization with custom options."""

class TestPDFParserFormatSupport:
    """Test format detection."""

    def test_supports_pdf_format():
        """Test PDF format detection."""

    def test_rejects_non_pdf_format():
        """Test rejection of non-PDF files."""

class TestPDFParserMetadata:
    """Test metadata extraction."""

    def test_extract_metadata_full():
        """Test extraction of all metadata fields."""

    def test_extract_metadata_partial():
        """Test metadata with missing fields."""

    def test_extract_metadata_empty():
        """Test PDF with no metadata."""

class TestPDFParserTextExtraction:
    """Test text extraction."""

    def test_extract_text_based_pdf():
        """Test extraction from text-based PDF."""

    def test_detect_scanned_pdf():
        """Test scanned PDF detection."""

    def test_extract_with_ocr():
        """Test OCR text extraction."""

    def test_text_extraction_with_formatting():
        """Test extraction preserves font info."""

class TestPDFParserHeadingDetection:
    """Test heading detection."""

    def test_detect_headings_from_fonts():
        """Test font-based heading detection."""

    def test_heading_level_mapping():
        """Test font size to heading level mapping."""

    def test_convert_headings_to_markdown():
        """Test markdown conversion."""

class TestPDFParserChapterDetection:
    """Test chapter detection."""

    def test_chapter_detection_basic():
        """Test basic chapter detection."""

    def test_chapter_detection_nested():
        """Test nested chapter structure."""

    def test_no_chapters_fallback():
        """Test single chapter fallback."""

class TestPDFParserImageExtraction:
    """Test image extraction."""

    def test_extract_images_enabled():
        """Test image extraction when enabled."""

    def test_extract_images_disabled():
        """Test no extraction when disabled."""

    def test_image_metadata():
        """Test image metadata is correct."""

class TestPDFParserTableExtraction:
    """Test table extraction."""

    def test_extract_tables():
        """Test table extraction and markdown conversion."""

    def test_tables_disabled():
        """Test no table extraction when disabled."""

class TestPDFParserTextCleaning:
    """Test text cleaning integration."""

    def test_text_cleaning_enabled():
        """Test text cleaning when enabled."""

    def test_text_cleaning_disabled():
        """Test no cleaning when disabled."""

class TestPDFParserFullParse:
    """Test complete parsing workflow."""

    def test_parse_complete_document():
        """Test full parse returns valid Document."""

    def test_parse_with_all_features():
        """Test parse with all features enabled."""

    def test_parse_minimal_options():
        """Test parse with minimal options."""

class TestPDFParserErrorHandling:
    """Test error handling."""

    def test_file_not_found():
        """Test FileReadError on missing file."""

    def test_corrupted_pdf():
        """Test ParsingError on corrupted PDF."""

    def test_invalid_format():
        """Test error on non-PDF file."""
```

**Target Coverage:** >90% for pdf_parser.py

#### Integration Tests: `tests/integration/test_pdf_parser_integration.py`

**Required Test Cases:**
```python
class TestPDFParserIntegration:
    """Integration tests with real PDF files."""

    def test_parse_text_pdf():
        """Test with real text-based PDF."""
        # Use: tests/fixtures/pdf/text_based.pdf

    def test_parse_scanned_pdf():
        """Test with real scanned PDF (OCR)."""
        # Use: tests/fixtures/pdf/scanned.pdf

    def test_parse_pdf_with_images():
        """Test PDF with embedded images."""
        # Use: tests/fixtures/pdf/with_images.pdf

    def test_parse_pdf_with_tables():
        """Test PDF with tables."""
        # Use: tests/fixtures/pdf/with_tables.pdf

    def test_parse_large_pdf():
        """Test with 100+ page PDF."""
        # Use: tests/fixtures/pdf/large_document.pdf

    def test_parse_pdf_no_metadata():
        """Test PDF with minimal metadata."""

    def test_integration_with_chapter_detector():
        """Test chapter_detector integration."""

    def test_integration_with_text_cleaner():
        """Test text_cleaner integration."""
```

#### Test Fixtures

**Create these test PDF files:**
```
tests/fixtures/pdf/
├── simple.pdf (1-2 pages, basic text)
├── text_based.pdf (10+ pages with headings)
├── scanned.pdf (image-based, needs OCR)
├── with_images.pdf (embedded images)
├── with_tables.pdf (contains tables)
├── large_document.pdf (100+ pages)
└── no_metadata.pdf (minimal metadata)
```

**Where to find test PDFs:**
- Project Gutenberg (public domain books)
- arXiv (scientific papers)
- Government reports (often public domain)
- Create your own with LibreOffice Writer → Export as PDF

### Success Criteria

Before considering this task complete, verify:

- [ ] PDFParser class fully implemented (~800-1000 lines)
- [ ] Inherits from BaseParser correctly
- [ ] All abstract methods implemented
- [ ] Type hints on all methods
- [ ] Comprehensive docstrings (Google style)
- [ ] Integrates with chapter_detector.py
- [ ] Integrates with text_cleaner.py
- [ ] Returns valid Document objects
- [ ] Metadata extraction working
- [ ] Font-based heading detection working
- [ ] OCR fallback working (test with scanned PDF)
- [ ] Image extraction working
- [ ] Table extraction working (basic)
- [ ] Unit tests written (>90% coverage)
- [ ] Integration tests with real PDFs (7+ files)
- [ ] All tests passing (uv run pytest)
- [ ] Code formatted with Black
- [ ] Type checked with mypy
- [ ] No merge conflicts with main
- [ ] Committed with conventional commit messages

### Git Workflow

```bash
# Create branch from main
git checkout main
git pull origin main
git checkout -b feature/pdf-parser

# Commit regularly with conventional commits
git add src/omniparser/parsers/pdf_parser.py
git commit -m "feat(pdf): Add PDFParser class with basic structure

- Implement BaseParser inheritance
- Add __init__ and supports_format methods
- Add docstrings and type hints
"

git add tests/unit/test_pdf_parser.py
git commit -m "test(pdf): Add unit tests for PDFParser

- Add test class structure
- Implement format support tests
- Add metadata extraction tests
"

# When complete, final commit
git add .
git commit -m "feat(pdf): Complete PDF parser implementation

- Font-based heading detection
- OCR fallback for scanned PDFs
- Image and table extraction
- Integration with chapter_detector and text_cleaner
- 95% test coverage with 150+ tests
- All integration tests passing

Closes Phase 2.4
"

# Do NOT merge yet - wait for user review
```

### Example Usage (for testing)

```python
from omniparser import parse_document

# Parse text-based PDF
doc = parse_document("document.pdf", {
    'extract_images': True,
    'ocr_enabled': False,
    'extract_tables': True
})

print(f"Title: {doc.metadata.title}")
print(f"Author: {doc.metadata.author}")
print(f"Pages: {doc.metadata.custom_fields.get('page_count')}")
print(f"Chapters: {len(doc.chapters)}")
print(f"Images: {len(doc.images)}")
print(f"Word count: {doc.word_count}")

# Parse scanned PDF with OCR
doc = parse_document("scan.pdf", {
    'ocr_enabled': True,
    'ocr_language': 'eng',
    'extract_images': True
})

# Access chapters
for chapter in doc.chapters:
    print(f"Chapter {chapter.chapter_id}: {chapter.title}")
    print(f"  Words: {chapter.word_count}")
    print(f"  Level: {chapter.level}")
```

### Performance Targets

- **Small PDF (1-10 pages):** < 1 second
- **Medium PDF (10-50 pages):** < 5 seconds
- **Large PDF (50-200 pages):** < 15 seconds
- **Scanned PDF (with OCR, 10 pages):** < 30 seconds

### Troubleshooting

**Common Issues:**

1. **Tesseract not found:**
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu
   sudo apt-get install tesseract-ocr
   ```

2. **PyMuPDF import error:**
   ```bash
   uv sync  # Reinstall dependencies
   ```

3. **Font detection issues:**
   - Some PDFs have inconsistent font metadata
   - Fallback to position-based detection if needed
   - Use heuristics (e.g., text at top of page might be heading)

4. **OCR accuracy:**
   - Ensure image quality is good (DPI > 300)
   - Try different Tesseract language models
   - Pre-process images (denoise, deskew) if needed

### Reference Implementation

Review the EPUB parser for patterns:
- `src/omniparser/parsers/epub_parser.py:1-1040`
- Especially the `parse()` method structure
- Error handling patterns
- Integration with shared processors

### Questions?

If you encounter ambiguity:
1. Check ARCHITECTURE_PLAN.md for design decisions
2. Follow patterns from epub_parser.py
3. Prioritize simplicity over perfection
4. Document any deviations in commit messages

---

## Agent 2: DOCX Parser Implementation

### Branch: `feature/docx-parser`

### Context

You are implementing the **DOCX Parser** for OmniParser, a universal document parser. This is Phase 2.6 of the implementation roadmap.

**Current Status:**
- ✅ EPUB Parser fully implemented
- ✅ HTML/URL Parser fully implemented
- ✅ Shared processors ready
- ✅ Dependencies installed: python-docx>=1.0.0, Pillow>=10.0.0

**Your Mission:**
Implement a production-ready DOCX parser that:
1. Extracts text from Microsoft Word documents using python-docx
2. Detects headings based on paragraph styles (Heading 1-6)
3. Preserves formatting (bold, italic, lists, links)
4. Extracts embedded images with metadata
5. Converts tables to markdown format
6. Integrates with shared processors (chapter_detector, text_cleaner)
7. Returns universal Document model
8. Achieves >90% test coverage

### Essential Reading

**MUST READ before starting:**
1. **docs/ARCHITECTURE_PLAN.md** - Phase 2.6 section
2. **docs/IMPLEMENTATION_REFERENCE.md** - Parser patterns
3. **src/omniparser/parsers/epub_parser.py** - Reference implementation
4. **src/omniparser/base/base_parser.py** - Abstract base class
5. **src/omniparser/models.py** - Data models
6. **CLAUDE.md** - Project standards

### Reusable Components

**Shared Processors:**
- `chapter_detector.py` - Use after converting styles to markdown headings
- `text_cleaner.py` - Clean extracted text
- `markdown_converter.py` - Could help with formatting conversions

**Utilities:**
- `format_detector.py` - Already supports DOCX
- `validators.py` - File validation

### Technical Specification

#### File Location
```
src/omniparser/parsers/docx_parser.py
```

#### Class Structure
```python
from pathlib import Path
from typing import Dict, Any, List, Optional
from docx import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from PIL import Image
from datetime import datetime
import io

from ..base.base_parser import BaseParser
from ..models import Document, Chapter, Metadata, ImageReference, ProcessingInfo
from ..processors.chapter_detector import detect_chapters
from ..processors.text_cleaner import clean_text
from ..exceptions import ParsingError, FileReadError

class DOCXParser(BaseParser):
    """
    Parser for Microsoft Word DOCX files using python-docx.

    Features:
    - Style-based heading detection (Heading 1 through Heading 6)
    - Formatting preservation (bold, italic, underline)
    - List conversion (bullets and numbered)
    - Link extraction and conversion
    - Image extraction with metadata
    - Table extraction and markdown conversion
    - Metadata from document properties

    Options:
        extract_images (bool): Extract embedded images (default: True)
        image_output_dir (Path): Directory for images (default: temp)
        preserve_formatting (bool): Preserve bold/italic/etc (default: True)
        extract_tables (bool): Extract and convert tables (default: True)
        clean_text (bool): Apply text cleaning (default: True)
        heading_styles (List[str]): Style names to treat as headings

    Example:
        >>> parser = DOCXParser({'extract_images': True})
        >>> doc = parser.parse(Path("report.docx"))
        >>> print(f"Chapters: {len(doc.chapters)}")
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize DOCX parser with options."""
        super().__init__(options)
        # Default heading styles
        self.heading_styles = self.options.get('heading_styles', [
            'Heading 1', 'Heading 2', 'Heading 3',
            'Heading 4', 'Heading 5', 'Heading 6'
        ])

    def parse(self, file_path: Path) -> Document:
        """
        Parse DOCX file and return Document object.

        Process:
        1. Open DOCX with python-docx
        2. Extract metadata from core properties
        3. Iterate through document elements (paragraphs, tables)
        4. Convert headings to markdown format
        5. Preserve formatting in text
        6. Extract images from relationships
        7. Convert tables to markdown
        8. Use chapter_detector for chapter structure
        9. Apply text cleaning
        10. Build and return Document
        """
        pass

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is DOCX format."""
        return file_path.suffix.lower() == '.docx'

    def _extract_metadata(self, doc: DocxDocument) -> Metadata:
        """
        Extract metadata from DOCX core properties.

        Available properties:
        - doc.core_properties.title
        - doc.core_properties.author
        - doc.core_properties.subject
        - doc.core_properties.keywords
        - doc.core_properties.comments
        - doc.core_properties.created
        - doc.core_properties.modified
        - doc.core_properties.last_modified_by
        """
        pass

    def _paragraph_to_markdown(self, para: Paragraph) -> str:
        """
        Convert DOCX paragraph to markdown.

        Handle:
        - Heading styles → markdown headings (# ## ###)
        - Bold text → **text**
        - Italic text → *text*
        - Underline → _text_ (or ignore if not in markdown spec)
        - Links → [text](url)
        - Lists → - item or 1. item

        Args:
            para: python-docx Paragraph object

        Returns:
            Markdown-formatted text
        """
        pass

    def _run_to_markdown(self, run) -> str:
        """
        Convert text run with formatting to markdown.

        Args:
            run: python-docx Run object

        Returns:
            Formatted text (e.g., **bold**, *italic*)
        """
        pass

    def _extract_images(self, doc: DocxDocument) -> List[ImageReference]:
        """
        Extract embedded images from DOCX.

        Process:
        1. Access document relationships (doc.part.rels)
        2. Find image relationships (rId)
        3. Extract image data
        4. Save to output directory
        5. Create ImageReference objects

        Args:
            doc: python-docx Document object

        Returns:
            List of ImageReference objects
        """
        pass

    def _table_to_markdown(self, table: Table) -> str:
        """
        Convert DOCX table to markdown table.

        Markdown table format:
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |

        Args:
            table: python-docx Table object

        Returns:
            Markdown-formatted table
        """
        pass

    def _is_heading(self, para: Paragraph) -> bool:
        """Check if paragraph is a heading style."""
        return para.style.name in self.heading_styles

    def _get_heading_level(self, para: Paragraph) -> int:
        """Get heading level (1-6) from style name."""
        style_name = para.style.name
        if 'Heading' in style_name:
            # Extract number from "Heading 1", "Heading 2", etc.
            try:
                return int(style_name.split()[-1])
            except (ValueError, IndexError):
                return 1
        return 1
```

### Implementation Steps

1. Create parser file: `src/omniparser/parsers/docx_parser.py`
2. Implement methods in order (same as PDF parser pattern)
3. Update `src/omniparser/parser.py` to include DOCX
4. Update `src/omniparser/__init__.py` exports
5. Write comprehensive tests

### Testing Requirements

#### Test Files
```
tests/unit/test_docx_parser.py
tests/integration/test_docx_parser_integration.py
```

#### Test Fixtures
```
tests/fixtures/docx/
├── simple.docx (1-2 pages)
├── with_headings.docx (structured with Heading 1-3)
├── with_images.docx (embedded images)
├── with_tables.docx (contains tables)
├── formatted.docx (bold, italic, lists)
├── with_links.docx (hyperlinks)
└── no_metadata.docx (minimal properties)
```

**Create test files with Microsoft Word or LibreOffice Writer.**

#### Coverage Target
>90% for docx_parser.py

### Success Criteria

- [ ] DOCXParser class fully implemented (~600-800 lines)
- [ ] Inherits from BaseParser
- [ ] All methods implemented with type hints
- [ ] Style-based heading detection working
- [ ] Formatting preservation (bold, italic)
- [ ] List conversion working
- [ ] Image extraction working
- [ ] Table conversion working
- [ ] Metadata extraction working
- [ ] Integrates with chapter_detector
- [ ] Integrates with text_cleaner
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests (7+ DOCX files)
- [ ] All tests passing
- [ ] Code formatted with Black
- [ ] Type checked with mypy
- [ ] Committed with conventional commits

### Git Workflow

```bash
git checkout main
git pull origin main
git checkout -b feature/docx-parser

# Regular commits
git commit -m "feat(docx): Add DOCXParser class structure"
git commit -m "feat(docx): Implement style-based heading detection"
git commit -m "feat(docx): Add formatting preservation"
git commit -m "test(docx): Add comprehensive unit tests"

# Final commit
git commit -m "feat(docx): Complete DOCX parser implementation

- Style-based heading detection (Heading 1-6)
- Formatting preservation (bold, italic, lists)
- Image and table extraction
- Integration with chapter_detector and text_cleaner
- 92% test coverage with 100+ tests

Closes Phase 2.6
"
```

### Example Usage

```python
from omniparser import parse_document

doc = parse_document("report.docx", {
    'extract_images': True,
    'preserve_formatting': True,
    'extract_tables': True
})

print(f"Title: {doc.metadata.title}")
print(f"Author: {doc.metadata.author}")
print(f"Chapters: {len(doc.chapters)}")

# Access formatted content
for chapter in doc.chapters:
    print(f"\n{chapter.title}")
    print(chapter.content)  # Includes **bold**, *italic*, etc.
```

### Performance Targets

- **Small DOCX (1-10 pages):** < 0.5 seconds
- **Medium DOCX (10-50 pages):** < 2 seconds
- **Large DOCX (50-100 pages):** < 5 seconds

---

## Agent 3: Markdown Parser Implementation

### Branch: `feature/markdown-parser`

### Context

You are implementing the **Markdown Parser** for OmniParser. This is Phase 2.7 of the roadmap.

**Your Mission:**
Implement a parser that:
1. Reads markdown files
2. Extracts YAML frontmatter (if present)
3. Normalizes markdown format
4. Detects chapters using chapter_detector
5. Returns universal Document model
6. Achieves >90% test coverage

### Essential Reading

1. **docs/ARCHITECTURE_PLAN.md** - Phase 2.7
2. **src/omniparser/parsers/epub_parser.py** - Reference
3. **src/omniparser/base/base_parser.py** - Base class
4. **src/omniparser/models.py** - Data models
5. **CLAUDE.md** - Standards

### Technical Specification

#### File Location
```
src/omniparser/parsers/markdown_parser.py
```

#### Class Structure
```python
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
import re
from datetime import datetime

from ..base.base_parser import BaseParser
from ..models import Document, Chapter, Metadata, ImageReference, ProcessingInfo
from ..processors.chapter_detector import detect_chapters
from ..processors.text_cleaner import clean_text
from ..exceptions import ParsingError, FileReadError

class MarkdownParser(BaseParser):
    """
    Parser for Markdown files with optional YAML frontmatter.

    Features:
    - YAML frontmatter extraction and parsing
    - Heading-based chapter detection (direct use of chapter_detector)
    - Markdown normalization (standardize heading styles)
    - Image reference extraction
    - Metadata from frontmatter

    Options:
        extract_frontmatter (bool): Extract YAML frontmatter (default: True)
        normalize_headings (bool): Standardize heading format (default: True)
        detect_chapters (bool): Use chapter_detector (default: True)
        clean_text (bool): Apply text cleaning (default: False)

    Example:
        >>> parser = MarkdownParser({'extract_frontmatter': True})
        >>> doc = parser.parse(Path("README.md"))
        >>> print(doc.metadata.title)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize Markdown parser."""
        super().__init__(options)

    def parse(self, file_path: Path) -> Document:
        """
        Parse Markdown file.

        Process:
        1. Read file with UTF-8 encoding
        2. Extract frontmatter if present
        3. Parse frontmatter YAML to Metadata
        4. Get markdown content (after frontmatter)
        5. Normalize markdown if enabled
        6. Use chapter_detector to detect chapters
        7. Extract image references
        8. Build and return Document
        """
        pass

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is Markdown."""
        return file_path.suffix.lower() in ['.md', '.markdown']

    def _extract_frontmatter(
        self,
        text: str
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Extract YAML frontmatter if present.

        Format:
        ---
        title: Document Title
        author: Author Name
        date: 2025-01-15
        tags: [python, parsing]
        ---

        Rest of markdown...

        Args:
            text: Full markdown text

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        pass

    def _frontmatter_to_metadata(
        self,
        frontmatter: Dict[str, Any],
        file_path: Path
    ) -> Metadata:
        """
        Convert frontmatter to Metadata object.

        Common frontmatter fields:
        - title
        - author / authors
        - date
        - tags / keywords
        - description / summary
        - language

        Args:
            frontmatter: Parsed YAML dict
            file_path: Source file path

        Returns:
            Metadata object
        """
        pass

    def _normalize_markdown(self, text: str) -> str:
        """
        Normalize markdown format.

        Normalizations:
        - Convert underline-style headings to # style
        - Standardize list markers
        - Normalize link format
        - Remove excessive blank lines

        Args:
            text: Original markdown

        Returns:
            Normalized markdown
        """
        pass

    def _extract_image_references(self, text: str) -> List[ImageReference]:
        """
        Extract image references from markdown.

        Format: ![alt text](image.png)

        Args:
            text: Markdown content

        Returns:
            List of ImageReference objects
        """
        pass
```

### Implementation Steps

1. Create `src/omniparser/parsers/markdown_parser.py`
2. Implement methods
3. Update `src/omniparser/parser.py`
4. Update `src/omniparser/__init__.py`
5. Write tests

### Testing Requirements

#### Test Files
```
tests/unit/test_markdown_parser.py
tests/integration/test_markdown_parser_integration.py
```

#### Test Fixtures
```
tests/fixtures/markdown/
├── simple.md (basic markdown)
├── with_frontmatter.md (YAML frontmatter)
├── no_frontmatter.md (no frontmatter)
├── with_images.md (image references)
├── complex_structure.md (nested headings)
├── underline_headings.md (underline-style headings)
└── obsidian_style.md (Obsidian-specific features)
```

#### Coverage Target
>90%

### Success Criteria

- [ ] MarkdownParser implemented (~300-400 lines)
- [ ] Frontmatter extraction working
- [ ] Metadata mapping working
- [ ] Markdown normalization working
- [ ] Image reference extraction working
- [ ] Integrates with chapter_detector
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests (7+ files)
- [ ] All tests passing
- [ ] Formatted with Black
- [ ] Type checked with mypy
- [ ] Conventional commits

### Git Workflow

```bash
git checkout -b feature/markdown-parser

git commit -m "feat(markdown): Add MarkdownParser class"
git commit -m "feat(markdown): Add frontmatter extraction"
git commit -m "test(markdown): Add comprehensive tests"

git commit -m "feat(markdown): Complete Markdown parser

- YAML frontmatter extraction
- Heading normalization
- Image reference extraction
- Integration with chapter_detector
- 94% test coverage

Closes Phase 2.7
"
```

### Example Usage

```python
from omniparser import parse_document

# Parse with frontmatter
doc = parse_document("README.md", {
    'extract_frontmatter': True,
    'normalize_headings': True
})

print(f"Title: {doc.metadata.title}")
print(f"Tags: {doc.metadata.tags}")
print(f"Chapters: {len(doc.chapters)}")
```

### Performance Targets

- **Small markdown (1-10 KB):** < 0.1 seconds
- **Medium markdown (10-100 KB):** < 0.3 seconds
- **Large markdown (>100 KB):** < 1 second

---

## Agent 4: Text Parser Implementation

### Branch: `feature/text-parser`

### Context

You are implementing the **Text Parser** for OmniParser. This is Phase 2.8 of the roadmap.

**Your Mission:**
Implement a parser that:
1. Detects file encoding automatically
2. Normalizes text (line endings, whitespace)
3. Attempts heuristic chapter detection
4. Applies text cleaning
5. Returns universal Document model
6. Achieves >90% test coverage

### Essential Reading

1. **docs/ARCHITECTURE_PLAN.md** - Phase 2.8
2. **src/omniparser/utils/encoding.py** - Encoding utilities (already implemented!)
3. **src/omniparser/base/base_parser.py** - Base class
4. **CLAUDE.md** - Standards

### Technical Specification

#### File Location
```
src/omniparser/parsers/text_parser.py
```

#### Class Structure
```python
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from ..base.base_parser import BaseParser
from ..models import Document, Chapter, Metadata, ImageReference, ProcessingInfo
from ..processors.text_cleaner import clean_text
from ..utils.encoding import detect_encoding, normalize_to_utf8
from ..exceptions import ParsingError, FileReadError

class TextParser(BaseParser):
    """
    Parser for plain text files with encoding detection.

    Features:
    - Automatic encoding detection (chardet)
    - Line ending normalization (Unix style)
    - Heuristic chapter detection from text patterns
    - Text cleaning and normalization
    - Fallback to single chapter if no structure detected

    Options:
        auto_detect_encoding (bool): Auto-detect encoding (default: True)
        encoding (str): Force specific encoding (default: None)
        normalize_line_endings (bool): Normalize line endings (default: True)
        attempt_chapter_detection (bool): Try to detect chapters (default: True)
        clean_text (bool): Apply text cleaning (default: True)

    Chapter Detection Patterns:
        - "Chapter 1", "Chapter One", "CHAPTER I"
        - "Part 1", "Section A"
        - "I. Introduction", "II. Methods"
        - Numbered patterns at line start

    Example:
        >>> parser = TextParser({'auto_detect_encoding': True})
        >>> doc = parser.parse(Path("notes.txt"))
        >>> print(doc.chapters[0].title)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize Text parser."""
        super().__init__(options)

        # Chapter detection patterns
        self.chapter_patterns = [
            r'^Chapter\s+(\d+|[IVX]+|One|Two|Three|Four|Five)',
            r'^CHAPTER\s+(\d+|[IVX]+)',
            r'^Part\s+(\d+|[IVX]+|One|Two|Three)',
            r'^Section\s+(\d+|[A-Z])',
            r'^([IVX]+)\.\s+[A-Z]',  # Roman numerals
            r'^(\d+)\.\s+[A-Z]',      # Numbers
        ]

    def parse(self, file_path: Path) -> Document:
        """
        Parse plain text file.

        Process:
        1. Detect encoding (or use specified)
        2. Read file with correct encoding
        3. Normalize line endings
        4. Attempt chapter detection
        5. If no chapters found, create single chapter
        6. Apply text cleaning
        7. Create minimal metadata
        8. Build and return Document
        """
        pass

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is plain text."""
        return file_path.suffix.lower() in ['.txt', '']

    def _read_with_encoding(self, file_path: Path) -> str:
        """
        Read file with detected or specified encoding.

        Uses encoding.py utilities:
        - detect_encoding()
        - normalize_to_utf8()
        """
        pass

    def _normalize_line_endings(self, text: str) -> str:
        """
        Normalize line endings to Unix style (\n).

        Converts:
        - Windows (\r\n) → \n
        - Old Mac (\r) → \n
        """
        pass

    def _detect_chapters_from_patterns(self, text: str) -> List[Chapter]:
        """
        Attempt to detect chapters using regex patterns.

        Process:
        1. Apply each pattern to find chapter markers
        2. If found, split text at markers
        3. Create Chapter objects with detected titles
        4. Return list of chapters

        If no patterns match, return empty list (caller creates single chapter).

        Args:
            text: Normalized text

        Returns:
            List of Chapter objects or empty list
        """
        pass

    def _create_single_chapter(self, text: str) -> List[Chapter]:
        """
        Create single chapter when no structure detected.

        Args:
            text: Full text content

        Returns:
            List with single Chapter object
        """
        pass

    def _create_metadata(self, file_path: Path) -> Metadata:
        """
        Create minimal metadata for text file.

        Can extract:
        - Title from first line (if short)
        - File size
        - Custom fields (detected encoding, line count)

        Args:
            file_path: Source file path

        Returns:
            Metadata object
        """
        pass
```

### Implementation Steps

1. Create `src/omniparser/parsers/text_parser.py`
2. Implement methods
3. Update `src/omniparser/parser.py`
4. Update `src/omniparser/__init__.py`
5. Write tests

### Testing Requirements

#### Test Files
```
tests/unit/test_text_parser.py
tests/integration/test_text_parser_integration.py
```

#### Test Fixtures
```
tests/fixtures/text/
├── simple.txt (basic text)
├── with_chapters.txt (chapter markers)
├── no_chapters.txt (unstructured text)
├── utf8.txt (UTF-8 encoding)
├── latin1.txt (Latin-1 encoding)
├── windows_line_endings.txt (CRLF)
├── mixed_line_endings.txt (mixed \r\n and \n)
└── project_gutenberg.txt (real book text)
```

#### Coverage Target
>90%

### Success Criteria

- [ ] TextParser implemented (~400-500 lines)
- [ ] Encoding detection working
- [ ] Line ending normalization working
- [ ] Pattern-based chapter detection working
- [ ] Single chapter fallback working
- [ ] Text cleaning integration working
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests (8+ files)
- [ ] All tests passing
- [ ] Formatted with Black
- [ ] Type checked
- [ ] Conventional commits

### Git Workflow

```bash
git checkout -b feature/text-parser

git commit -m "feat(text): Add TextParser class"
git commit -m "feat(text): Add encoding detection"
git commit -m "feat(text): Add chapter detection patterns"
git commit -m "test(text): Add comprehensive tests"

git commit -m "feat(text): Complete Text parser

- Automatic encoding detection
- Line ending normalization
- Pattern-based chapter detection
- Integration with text_cleaner
- 93% test coverage

Closes Phase 2.8
"
```

### Example Usage

```python
from omniparser import parse_document

# Parse with auto-detection
doc = parse_document("notes.txt", {
    'auto_detect_encoding': True,
    'attempt_chapter_detection': True
})

print(f"Encoding: {doc.processing_info.options_used['detected_encoding']}")
print(f"Chapters: {len(doc.chapters)}")

# Force specific encoding
doc = parse_document("latin1.txt", {
    'auto_detect_encoding': False,
    'encoding': 'latin-1'
})
```

### Performance Targets

- **Small text (<100 KB):** < 0.1 seconds
- **Medium text (100 KB - 1 MB):** < 0.5 seconds
- **Large text (1-10 MB):** < 3 seconds

---

## Agent 5: AI-Powered Features

### Branch: `feature/ai-enhancements`

### Context

You are adding **optional AI-powered features** to OmniParser. These are NEW processor modules that enhance parsed documents.

**CRITICAL:**
- Do NOT modify existing parsers
- These are OPTIONAL features (opt-in via options)
- Use environment variables for API keys
- Provide both Anthropic and OpenAI implementations

**Your Mission:**
Add AI-powered processors:
1. Auto-tagging (generate relevant tags for content)
2. Summarization (create document summaries)
3. Quality scoring (assess content quality)
4. Image description (generate alt text for images)

### Essential Reading

1. **docs/ARCHITECTURE_PLAN.md** - Future features section
2. **src/omniparser/processors/** - Existing processor patterns
3. **CLAUDE.md** - API key management guidelines
4. **ClaudeUsage/secrets_management.md** - Secrets handling

### Technical Specification

#### New Files to Create

1. **`src/omniparser/processors/ai_tagger.py`** - Auto-tagging
2. **`src/omniparser/processors/ai_summarizer.py`** - Summarization
3. **`src/omniparser/processors/ai_quality.py`** - Quality scoring
4. **`src/omniparser/processors/ai_image_describer.py`** - Image descriptions
5. **`src/omniparser/ai_config.py`** - Shared AI configuration

#### AI Configuration Module

```python
# src/omniparser/ai_config.py
"""
Shared AI configuration and client management.

Supports:
- Anthropic Claude (via anthropic SDK)
- OpenAI GPT (via openai SDK)
"""

import os
from typing import Optional, Dict, Any
from enum import Enum

class AIProvider(Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

class AIConfig:
    """
    Configuration for AI-powered features.

    API Keys (from environment):
    - ANTHROPIC_API_KEY
    - OPENAI_API_KEY

    Options:
        provider (str): "anthropic" or "openai" (default: anthropic)
        model (str): Model name (default: claude-3-haiku-20240307 or gpt-3.5-turbo)
        max_tokens (int): Maximum tokens per request (default: 1024)
        temperature (float): Sampling temperature (default: 0.3)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize AI config."""
        self.options = options or {}
        self.provider = self._get_provider()
        self.model = self._get_model()
        self.max_tokens = self.options.get('max_tokens', 1024)
        self.temperature = self.options.get('temperature', 0.3)

        # Initialize client
        self.client = self._init_client()

    def _get_provider(self) -> AIProvider:
        """Get AI provider from options or environment."""
        provider_str = self.options.get('ai_provider', 'anthropic')
        return AIProvider(provider_str)

    def _get_model(self) -> str:
        """Get model name."""
        if 'ai_model' in self.options:
            return self.options['ai_model']

        if self.provider == AIProvider.ANTHROPIC:
            return 'claude-3-haiku-20240307'  # Fast, cheap
        else:
            return 'gpt-3.5-turbo'

    def _init_client(self):
        """Initialize API client."""
        if self.provider == AIProvider.ANTHROPIC:
            import anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return anthropic.Anthropic(api_key=api_key)
        else:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            openai.api_key = api_key
            return openai

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate text using configured AI provider.

        Args:
            prompt: User prompt
            system: System prompt (optional)

        Returns:
            Generated text
        """
        if self.provider == AIProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, system)
        else:
            return self._generate_openai(prompt, system)

    def _generate_anthropic(self, prompt: str, system: Optional[str]) -> str:
        """Generate with Anthropic Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def _generate_openai(self, prompt: str, system: Optional[str]) -> str:
        """Generate with OpenAI GPT."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.ChatCompletion.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages
        )
        return response.choices[0].message.content
```

#### Auto-Tagger Processor

```python
# src/omniparser/processors/ai_tagger.py
"""
AI-powered automatic tagging for documents.

Generates relevant tags/keywords based on content analysis.
"""

from typing import List, Optional, Dict, Any
from ..ai_config import AIConfig
from ..models import Document

def generate_tags(
    document: Document,
    max_tags: int = 10,
    ai_options: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Generate tags for document using AI.

    Args:
        document: Parsed document
        max_tags: Maximum number of tags (default: 10)
        ai_options: AI configuration options

    Returns:
        List of generated tags

    Example:
        >>> tags = generate_tags(doc, max_tags=5)
        >>> print(tags)
        ['python', 'parsing', 'documents', 'markdown', 'epub']
    """
    ai_config = AIConfig(ai_options)

    # Prepare content sample (first 2000 chars)
    content_sample = document.content[:2000]

    system_prompt = (
        "You are a document tagging expert. Generate relevant tags/keywords "
        "for the document content. Return ONLY a comma-separated list of tags, "
        "no other text."
    )

    user_prompt = f"""Analyze this document and generate {max_tags} relevant tags.

Title: {document.metadata.title or 'Unknown'}
Content Preview:
{content_sample}

Tags (comma-separated):"""

    response = ai_config.generate(user_prompt, system_prompt)

    # Parse response
    tags = [tag.strip() for tag in response.split(',')]
    tags = [tag for tag in tags if tag]  # Remove empty

    return tags[:max_tags]
```

#### Summarizer Processor

```python
# src/omniparser/processors/ai_summarizer.py
"""
AI-powered document summarization.
"""

from typing import Optional, Dict, Any
from ..ai_config import AIConfig
from ..models import Document

def summarize_document(
    document: Document,
    max_length: int = 500,
    style: str = "concise",
    ai_options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate summary of document.

    Args:
        document: Parsed document
        max_length: Maximum summary length in words (default: 500)
        style: Summary style - "concise", "detailed", "bullet" (default: concise)
        ai_options: AI configuration options

    Returns:
        Document summary
    """
    ai_config = AIConfig(ai_options)

    # Prepare content (first 5000 chars or full content if shorter)
    content = document.content[:5000]

    style_instructions = {
        "concise": "Write a concise 2-3 sentence summary.",
        "detailed": f"Write a detailed summary of up to {max_length} words.",
        "bullet": "Write a bullet-point summary with key points."
    }

    system_prompt = (
        "You are a document summarization expert. Create clear, accurate summaries "
        "of document content. " + style_instructions.get(style, style_instructions["concise"])
    )

    user_prompt = f"""Summarize this document:

Title: {document.metadata.title or 'Unknown'}
Author: {document.metadata.author or 'Unknown'}
Word Count: {document.word_count}

Content:
{content}

Summary:"""

    summary = ai_config.generate(user_prompt, system_prompt)
    return summary.strip()
```

#### Quality Scorer Processor

```python
# src/omniparser/processors/ai_quality.py
"""
AI-powered content quality assessment.
"""

from typing import Dict, Any, Optional
from ..ai_config import AIConfig
from ..models import Document

def score_quality(
    document: Document,
    ai_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Assess document quality using AI.

    Evaluates:
    - Overall quality score (0-100)
    - Readability
    - Structure
    - Completeness
    - Suggestions for improvement

    Args:
        document: Parsed document
        ai_options: AI configuration options

    Returns:
        Dictionary with quality metrics

    Example:
        >>> quality = score_quality(doc)
        >>> print(quality['overall_score'])
        85
        >>> print(quality['suggestions'])
        ['Add more headings', 'Improve paragraph structure']
    """
    ai_config = AIConfig(ai_options)

    content_sample = document.content[:3000]

    system_prompt = (
        "You are a content quality analyst. Evaluate document quality on multiple "
        "dimensions. Return your assessment in this exact format:\n\n"
        "OVERALL_SCORE: [0-100]\n"
        "READABILITY: [0-100]\n"
        "STRUCTURE: [0-100]\n"
        "COMPLETENESS: [0-100]\n"
        "SUGGESTIONS:\n- [suggestion 1]\n- [suggestion 2]"
    )

    user_prompt = f"""Evaluate this document's quality:

Title: {document.metadata.title or 'Unknown'}
Chapters: {len(document.chapters)}
Word Count: {document.word_count}

Content Sample:
{content_sample}

Assessment:"""

    response = ai_config.generate(user_prompt, system_prompt)

    # Parse response
    quality_data = _parse_quality_response(response)
    return quality_data

def _parse_quality_response(response: str) -> Dict[str, Any]:
    """Parse AI quality assessment response."""
    # Implementation to parse the structured response
    # Return dict with scores and suggestions
    pass
```

### Dependencies to Add

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
ai = [
    "anthropic>=0.18.0",
    "openai>=1.12.0",
]
```

### Testing Requirements

#### Test Files
```
tests/unit/test_ai_tagger.py
tests/unit/test_ai_summarizer.py
tests/unit/test_ai_quality.py
tests/integration/test_ai_features_integration.py
```

#### Coverage Strategy
- Unit tests with **mocked AI responses** (don't call real APIs in tests)
- Integration tests with real API calls (mark with `@pytest.mark.integration`)
- Provide fixtures for common AI responses

### Success Criteria

- [ ] AI configuration module implemented
- [ ] Auto-tagger working
- [ ] Summarizer working
- [ ] Quality scorer working
- [ ] Both Anthropic and OpenAI supported
- [ ] Environment variable handling
- [ ] Unit tests with mocked responses (>85% coverage)
- [ ] Integration tests with real APIs
- [ ] Documentation for API key setup
- [ ] Examples in README
- [ ] All tests passing
- [ ] Formatted with Black
- [ ] Type checked

### Git Workflow

```bash
git checkout -b feature/ai-enhancements

git commit -m "feat(ai): Add AI configuration module"
git commit -m "feat(ai): Add auto-tagging processor"
git commit -m "feat(ai): Add summarization processor"
git commit -m "feat(ai): Add quality scoring processor"
git commit -m "test(ai): Add comprehensive tests with mocks"
git commit -m "docs(ai): Add API key setup guide"

git commit -m "feat(ai): Complete AI-powered enhancements

- Auto-tagging with Claude/GPT
- Document summarization
- Quality scoring and suggestions
- Support for Anthropic and OpenAI
- Opt-in via options
- Environment variable API key management
- 88% test coverage with mocked responses

New optional dependency group: omniparser[ai]
"
```

### Example Usage

```python
from omniparser import parse_document
from omniparser.processors.ai_tagger import generate_tags
from omniparser.processors.ai_summarizer import summarize_document
from omniparser.processors.ai_quality import score_quality

# Parse document
doc = parse_document("book.epub")

# Generate tags (requires ANTHROPIC_API_KEY or OPENAI_API_KEY)
tags = generate_tags(doc, max_tags=10, ai_options={
    'ai_provider': 'anthropic',
    'ai_model': 'claude-3-haiku-20240307'
})
print(f"Tags: {tags}")

# Generate summary
summary = summarize_document(doc, style="bullet")
print(f"Summary:\n{summary}")

# Score quality
quality = score_quality(doc)
print(f"Quality Score: {quality['overall_score']}/100")
print(f"Suggestions: {quality['suggestions']}")
```

---

## Agent 6: Performance Optimization (RUN LAST)

### Branch: `feature/performance-optimization`

### Context

You are optimizing OmniParser for **parallelization and concurrent processing**. This agent runs **LAST after all parsers are implemented**.

**Focus Areas:**
- Parallel chapter processing
- Concurrent parsing of multiple documents
- Async support
- ThreadPoolExecutor enhancements
- Batch processing utilities

**NOT in scope:**
- Large file streaming (not needed per user)
- Memory optimizations for huge files

### Essential Reading

1. **All parser implementations** (review patterns first)
2. **docs/ARCHITECTURE_PLAN.md** - Performance sections
3. **src/omniparser/parsers/html_parser.py** - Already uses ThreadPoolExecutor for images
4. **CLAUDE.md** - Performance guidelines

### Technical Specification

#### Areas to Optimize

1. **Parallel Chapter Processing**
   - Process multiple chapters concurrently
   - Apply text cleaning in parallel
   - Generate chapter metadata in parallel

2. **Concurrent Document Parsing**
   - Parse multiple documents at once
   - Batch processing API

3. **Async Support**
   - Async versions of parse methods
   - Async image downloads (HTML parser enhancement)

4. **Enhanced Image Downloading**
   - Expand HTML parser's ThreadPoolExecutor pattern to EPUB, PDF parsers

#### New Files to Create

1. **`src/omniparser/utils/parallel.py`** - Parallelization utilities
2. **`src/omniparser/async_parser.py`** - Async API
3. **`src/omniparser/batch.py`** - Batch processing API

#### Parallel Utilities

```python
# src/omniparser/utils/parallel.py
"""
Parallelization utilities for concurrent processing.
"""

from typing import List, Callable, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count

def parallel_map(
    func: Callable,
    items: List[Any],
    max_workers: int = None,
    use_processes: bool = False
) -> List[Any]:
    """
    Apply function to items in parallel.

    Args:
        func: Function to apply
        items: List of items
        max_workers: Number of workers (default: CPU count)
        use_processes: Use processes instead of threads

    Returns:
        List of results
    """
    if max_workers is None:
        max_workers = cpu_count()

    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor

    with executor_class(max_workers=max_workers) as executor:
        results = list(executor.map(func, items))

    return results
```

#### Async Parser API

```python
# src/omniparser/async_parser.py
"""
Async API for concurrent document parsing.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import Document
from .parser import parse_document

async def parse_document_async(
    file_path: str | Path,
    options: Optional[Dict[str, Any]] = None
) -> Document:
    """
    Async version of parse_document.

    Runs parsing in executor to avoid blocking.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        parse_document,
        file_path,
        options
    )

async def parse_documents_concurrent(
    file_paths: List[str | Path],
    options: Optional[Dict[str, Any]] = None,
    max_concurrent: int = 5
) -> List[Document]:
    """
    Parse multiple documents concurrently.

    Args:
        file_paths: List of file paths
        options: Parsing options
        max_concurrent: Maximum concurrent parses

    Returns:
        List of parsed Documents
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def parse_with_semaphore(file_path):
        async with semaphore:
            return await parse_document_async(file_path, options)

    tasks = [parse_with_semaphore(fp) for fp in file_paths]
    return await asyncio.gather(*tasks)
```

#### Batch Processing API

```python
# src/omniparser/batch.py
"""
Batch processing utilities for multiple documents.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging

from .models import Document
from .parser import parse_document

logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    """Result of batch parsing."""
    success: List[Document]
    failed: List[Dict[str, Any]]  # {file_path, error}
    total_time: float

def parse_directory(
    directory: Path,
    pattern: str = "*",
    options: Optional[Dict[str, Any]] = None,
    max_workers: int = 5,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> BatchResult:
    """
    Parse all matching files in directory.

    Args:
        directory: Directory to scan
        pattern: Glob pattern (default: "*")
        options: Parsing options
        max_workers: Number of parallel workers
        progress_callback: Called with (completed, total)

    Returns:
        BatchResult with success and failed lists

    Example:
        >>> result = parse_directory(
        ...     Path("books/"),
        ...     pattern="*.epub",
        ...     max_workers=10
        ... )
        >>> print(f"Parsed {len(result.success)} documents")
    """
    # Get matching files
    files = list(directory.glob(pattern))
    total = len(files)

    success = []
    failed = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(parse_document, f, options): f
            for f in files
        }

        # Process as completed
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                doc = future.result()
                success.append(doc)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                failed.append({
                    'file_path': str(file_path),
                    'error': str(e)
                })

            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    return BatchResult(
        success=success,
        failed=failed,
        total_time=0.0  # TODO: track time
    )
```

### Parser-Specific Optimizations

#### 1. Enhance EPUB Parser
- Add parallel chapter processing in `parse()`
- Use ThreadPoolExecutor for image extraction

#### 2. Enhance HTML Parser
- Already uses ThreadPoolExecutor for images ✅
- Could add async URL fetching

#### 3. Enhance PDF Parser
- Add parallel page processing
- Parallel OCR for scanned pages

#### 4. Enhance DOCX Parser
- Parallel paragraph processing

### Testing Requirements

#### Test Files
```
tests/unit/test_parallel_utils.py
tests/unit/test_async_parser.py
tests/unit/test_batch_processor.py
tests/integration/test_performance.py
```

#### Performance Benchmarks
Create benchmarks to measure improvements:
```python
# tests/integration/test_performance.py

def test_parallel_vs_sequential_parsing():
    """Compare parallel vs sequential parsing times."""

def test_batch_processing_speedup():
    """Verify batch processing is faster than sequential."""

def test_async_concurrent_parsing():
    """Test async parsing of multiple documents."""
```

### Success Criteria

- [ ] Parallel utilities implemented
- [ ] Async parser API implemented
- [ ] Batch processing API implemented
- [ ] EPUB parser parallelization added
- [ ] PDF parser parallelization added
- [ ] DOCX parser parallelization added
- [ ] HTML parser async enhancements
- [ ] Performance benchmarks showing improvement
- [ ] Unit tests (>85% coverage)
- [ ] Integration tests with benchmarks
- [ ] Documentation with examples
- [ ] All tests passing
- [ ] Formatted with Black
- [ ] Type checked

### Git Workflow

```bash
git checkout -b feature/performance-optimization

# Wait for all parser branches to be merged first!
git checkout main
git pull origin main
git checkout -b feature/performance-optimization

git commit -m "feat(perf): Add parallelization utilities"
git commit -m "feat(perf): Add async parser API"
git commit -m "feat(perf): Add batch processing API"
git commit -m "feat(perf): Add parallel chapter processing to EPUB"
git commit -m "feat(perf): Add parallel page processing to PDF"
git commit -m "test(perf): Add performance benchmarks"

git commit -m "feat(perf): Complete performance optimizations

- Parallel chapter processing in all parsers
- Async parsing API
- Batch processing with ThreadPoolExecutor
- Performance benchmarks showing 3-5x speedup
- 87% test coverage

Benchmarks:
- EPUB: 3.2x faster with parallel chapters
- PDF: 4.1x faster with parallel pages
- Batch: 4.8x faster for 10 documents
"
```

### Example Usage

```python
from omniparser import parse_document
from omniparser.async_parser import parse_documents_concurrent
from omniparser.batch import parse_directory
import asyncio

# Standard parsing (still works)
doc = parse_document("book.epub")

# Async parsing
async def main():
    files = ["book1.epub", "book2.epub", "book3.epub"]
    docs = await parse_documents_concurrent(files, max_concurrent=3)
    print(f"Parsed {len(docs)} documents concurrently")

asyncio.run(main())

# Batch directory parsing
result = parse_directory(
    Path("books/"),
    pattern="*.epub",
    max_workers=10,
    progress_callback=lambda done, total: print(f"{done}/{total}")
)

print(f"Success: {len(result.success)}")
print(f"Failed: {len(result.failed)}")
```

### Performance Targets

- **Parallel chapter processing:** 2-4x speedup for documents with 10+ chapters
- **Batch processing:** 3-5x speedup for 10+ documents (vs sequential)
- **Async concurrent:** Support 10+ concurrent parses without blocking

---

## General Guidelines for All Agents

### 1. Before Starting

- [ ] Read ALL essential documentation listed in your prompt
- [ ] Review existing parser implementations for patterns
- [ ] Check CLAUDE.md for project standards
- [ ] Understand the universal data models
- [ ] Review shared processors available

### 2. During Implementation

- [ ] Follow patterns from EPUB/HTML parsers
- [ ] Use type hints everywhere
- [ ] Write comprehensive docstrings (Google style)
- [ ] Keep functions focused (max ~50 lines)
- [ ] Extract helpers when needed
- [ ] Test as you go (don't defer testing)
- [ ] Format with Black: `uv run black .`
- [ ] Type check with mypy: `uv run mypy src/`

### 3. Testing Standards

- [ ] >90% coverage for parser code
- [ ] Unit tests for every method
- [ ] Integration tests with real files
- [ ] Edge case testing
- [ ] Error handling tests
- [ ] All tests passing: `uv run pytest`

### 4. Git Commit Standards

**CRITICAL:** Follow conventional commit format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:** feat, fix, test, docs, refactor, perf, chore

**Examples:**
```bash
feat(pdf): Add PDFParser class structure
feat(pdf): Implement font-based heading detection
test(pdf): Add unit tests for metadata extraction
docs(pdf): Add API documentation
```

### 5. Before Completing

- [ ] All success criteria checked
- [ ] Tests passing (100%)
- [ ] Code formatted (Black)
- [ ] Type checked (mypy)
- [ ] Documentation updated
- [ ] Examples working
- [ ] No merge conflicts with main
- [ ] Final commit with summary

### 6. Final Commit Template

```bash
git commit -m "feat(parser): Complete [PARSER NAME] implementation

- [Key feature 1]
- [Key feature 2]
- [Key feature 3]
- [Test coverage]% test coverage with [N]+ tests
- [Performance metric if applicable]

Closes Phase [X.Y]
"
```

---

## Coordination Notes

### Branch Management

Each agent works in isolated branch:
```
feature/pdf-parser
feature/docx-parser
feature/markdown-parser
feature/text-parser
feature/ai-enhancements
feature/performance-optimization
```

### Merge Order

1. **Parallel:** Agents 1-4 (parsers) can merge independently
2. **After parsers:** Agent 5 (AI features) can merge
3. **Last:** Agent 6 (performance) merges after all others

### Integration Points

**Shared Components** (all agents use these):
- `src/omniparser/base/base_parser.py`
- `src/omniparser/models.py`
- `src/omniparser/processors/` (all processors)
- `src/omniparser/utils/` (all utilities)
- `src/omniparser/exceptions.py`

**Parser-Specific** (no conflicts):
- `src/omniparser/parsers/[parser_name].py` (each agent has unique file)
- `tests/unit/test_[parser_name].py` (unique test files)
- `tests/fixtures/[format]/` (unique fixture directories)

**Potential Conflicts** (be aware):
- `src/omniparser/parser.py` - All parsers update this (add format routing)
- `src/omniparser/__init__.py` - All parsers update exports
- `README.md` - May have conflicts if multiple agents update
- `docs/` - Documentation updates

**Resolution Strategy:**
- For `parser.py` and `__init__.py`: Each agent adds their section
- For README/docs: User will merge manually
- Test for conflicts before final commit: `git fetch origin main && git merge origin/main`

---

## Questions During Implementation?

If you encounter:
- **Ambiguity in requirements:** Check ARCHITECTURE_PLAN.md Phase details
- **Unclear patterns:** Review epub_parser.py implementation
- **Missing dependencies:** Check pyproject.toml and install with `uv sync`
- **Test failures:** Review existing test patterns in tests/unit/
- **Performance issues:** Profile with cProfile, optimize hot paths

**General Guidance:**
- Prioritize **simplicity** over perfection
- Follow **existing patterns** from EPUB/HTML parsers
- When in doubt, **defer to architecture docs**
- **Document** any deviations or design decisions

---

## Ready to Start!

Each agent prompt above is complete and self-contained. Copy the relevant section and start your autonomous work!

**Remember:**
1. Read essential documentation first
2. Follow existing patterns
3. Test as you go
4. Use conventional commits
5. Check success criteria before completion

**Good luck!** 🚀
