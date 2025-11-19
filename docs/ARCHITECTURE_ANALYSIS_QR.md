# OmniParser Architecture Analysis - QR Code Support Integration

## Executive Summary

OmniParser is a modular document parser supporting 6 formats (EPUB, PDF, DOCX, HTML, Markdown, Text) using a functional architecture pattern. It extracts structured content into a universal Document model with metadata, chapters, and images. The architecture is designed for extensibility through:
- Modular parsers following BaseParser interface
- Reusable processors for common tasks
- Shared utilities for cross-parser functionality
- Format-specific extraction modules

---

## 1. CORE DATA MODELS

### File Location
`/home/user/OmniParser/src/omniparser/models.py`

### Class Hierarchy

#### ImageReference
Represents an image found in a document.

**Attributes:**
```python
image_id: str                           # Unique identifier
position: int                           # Character position in document text
file_path: Optional[str] = None         # Local file path if extracted
alt_text: Optional[str] = None          # Alternative text description
size: Optional[tuple[int, int]] = None  # (width, height) in pixels
format: str = "unknown"                 # Image format (jpeg, png, webp, etc)
```

**Notes:** This is the ideal place to extend for QR code metadata storage.

---

#### Chapter
Represents a chapter or section with position tracking.

**Attributes:**
```python
chapter_id: int                              # Sequential chapter identifier
title: str                                   # Chapter title
content: str                                 # Full text content
start_position: int                          # Character position in full document
end_position: int                            # End character position
word_count: int                              # Number of words
level: int = 1                               # Heading level (1=main, 2=subsection)
metadata: Optional[Dict[str, Any]] = None    # Chapter-specific metadata
```

**Notes:** Could store QR code URLs per chapter in metadata field.

---

#### Metadata
Universal metadata applicable to any document format.

**Attributes:**
```python
title: Optional[str] = None                  # Document title
author: Optional[str] = None                 # Primary author
authors: Optional[List[str]] = None          # All authors/contributors
publisher: Optional[str] = None              # Publishing org
publication_date: Optional[datetime] = None  # Publication date
language: Optional[str] = None               # Language code (e.g., "en", "fr")
isbn: Optional[str] = None                   # ISBN for books
description: Optional[str] = None            # Summary/abstract
tags: Optional[List[str]] = None             # Keywords/categorization
original_format: Optional[str] = None        # Original format (epub, pdf, etc)
file_size: int = 0                           # File size in bytes
custom_fields: Optional[Dict[str, Any]] = None  # Format-specific metadata
```

**Integration Point:** Custom QR code metadata can be stored in `custom_fields`:
- `custom_fields['qr_codes']` = list of QR code URLs found in document
- `custom_fields['qr_detected']` = boolean flag for QR detection status

---

#### ProcessingInfo
Tracks parsing execution details.

**Attributes:**
```python
parser_used: str                         # Parser implementation name
parser_version: str                      # Parser version
processing_time: float                   # Time in seconds
timestamp: datetime                      # Completion datetime
warnings: List[str] = []                 # Non-fatal issues
options_used: Dict[str, Any] = {}        # Parsing options applied
```

**Notes:** QR detection processing time could be logged here.

---

#### Document (Main Container)
Universal representation of parsed document.

**Attributes:**
```python
document_id: str                          # Unique identifier
content: str                              # Full concatenated text
chapters: List[Chapter]                   # Chapter structure
images: List[ImageReference]              # Images found
metadata: Metadata                        # Document metadata
processing_info: ProcessingInfo           # Parsing execution info
word_count: int                           # Total words
estimated_reading_time: int               # Minutes based on 200-250 WPM
```

**Key Methods:**
- `get_chapter(chapter_id: int) -> Optional[Chapter]` - Retrieve chapter by ID
- `get_text_range(start: int, end: int) -> str` - Extract text between positions
- `to_dict()` / `from_dict()` - Serialization helpers
- `save_json()` / `load_json()` - Persistence helpers

---

## 2. BASE PARSER INTERFACE

### File Location
`/home/user/OmniParser/src/omniparser/base/base_parser.py`

### BaseParser Abstract Class

All format-specific parsers inherit from this interface.

**Constructor:**
```python
def __init__(self, options: Optional[Dict[str, Any]] = None):
    self.options = options or {}
```

**Required Abstract Methods:**

```python
@abstractmethod
def parse(self, file_path: Union[Path, str]) -> Document:
    """Parse document and return Document object.
    
    Args:
        file_path: Path to file or URL string
        
    Returns:
        Document object with parsed content
        
    Raises:
        ParsingError, FileReadError, NetworkError
    """
    pass

@abstractmethod
def supports_format(self, file_path: Union[Path, str]) -> bool:
    """Check if parser supports this file format.
    
    Args:
        file_path: Path or URL to check
        
    Returns:
        True if format supported
    """
    pass
```

**Optional Methods (with default implementations):**

```python
def extract_images(self, file_path: Union[Path, str]) -> List[ImageReference]:
    """Extract images from document (optional override).
    Default returns empty list.
    """
    return []

def clean_text(self, text: str) -> str:
    """Apply text cleaning (optional override).
    Uses shared text_cleaner processor if enabled.
    """
    if self.options.get("clean_text", True):
        from ..processors.text_cleaner import clean_text
        return clean_text(text)
    return text
```

**Integration Points:**
- Options passed to constructor control parser behavior
- Can extract images as ImageReference objects
- Can apply text cleaning through shared processor

---

## 3. PDF PARSER ARCHITECTURE

### Main Entry Point
`/home/user/OmniParser/src/omniparser/parsers/pdf/parser.py`

### parse_pdf() Function Signature

```python
def parse_pdf(
    file_path: Path,
    output_dir: Optional[Path] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Document:
```

### PDF Parsing Pipeline (Sequential Steps)

1. **Validation & Loading** - `validate_and_load_pdf(file_path)` returns fitz.Document
2. **Metadata Extraction** - `extract_pdf_metadata(doc, file_path)` returns Metadata
3. **Text Extraction** - `extract_text_content(doc, use_ocr, ocr_language, ocr_timeout, max_pages)`
   - Returns: (content, text_blocks) where text_blocks contain font info
4. **Heading Detection & Chapters** - `process_pdf_headings(text_blocks, content)`
   - Analyzes font size/weight to detect headings
   - Converts to markdown format
   - Returns: (markdown_content, chapters)
5. **Text Cleaning** - `clean_text(markdown_content)` if enabled
6. **Image Extraction** - `extract_pdf_images(doc, output_dir=output_dir)`
   - Returns: List[ImageReference]
7. **Table Extraction** - `extract_pdf_tables(doc)`
   - Returns: List[str] of markdown tables
8. **Word Counting & Reading Time** - `count_words()`, `estimate_reading_time()`
9. **Processing Info Building** - ProcessingInfo with parser metadata
10. **Document Construction** - Return complete Document object

### Supporting Modules

#### Image Extraction Module
**File:** `/home/user/OmniParser/src/omniparser/parsers/pdf/images.py`

**Key Functions:**
```python
def extract_pdf_images(
    doc: fitz.Document,
    output_dir: Optional[Path] = None,
    max_images: Optional[int] = None,
) -> List[ImageReference]:
    """Extract embedded images from PDF.
    
    Process:
    1. Iterate through pages
    2. Get image list: page.get_images()
    3. Extract image data: doc.extract_image(xref)
    4. Validate using MIN_IMAGE_SIZE filter
    5. Save using shared image_extractor utility
    6. Create ImageReference objects
    """

def extract_page_images(
    page: fitz.Page,
    page_num: int,
    output_dir: Path,
    counter: int,
    doc: fitz.Document,
    max_images: Optional[int] = None,
) -> Tuple[List[ImageReference], int]:
    """Extract images from single PDF page."""
```

**QR Integration Point:**
- This is where QR detection should be integrated
- Each extracted image can be analyzed for QR codes
- QR metadata added to ImageReference or separate QRCode model

---

#### Metadata Extraction Module
**File:** `/home/user/OmniParser/src/omniparser/parsers/pdf/metadata.py`

**Functions:**
```python
def extract_pdf_metadata(doc: fitz.Document, file_path: Path) -> Metadata:
    """Extract PDF properties and create Metadata object."""

def parse_pdf_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse PDF date format: D:YYYYMMDDHHmmSSOHH'mm'"""

def parse_keywords_to_tags(keywords: Optional[str]) -> List[str]:
    """Parse comma-separated keywords into tag list."""

def build_custom_fields(doc: fitz.Document, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Extract PDF-specific custom fields (page_count, creator, producer)."""
```

---

#### Heading Detection Module
**File:** `/home/user/OmniParser/src/omniparser/parsers/pdf/heading_detection.py`

**Key Functions:**
```python
def detect_headings_from_fonts(
    text_blocks: List[Dict], 
    max_heading_words: int = DEFAULT_MAX_HEADING_WORDS
) -> List[Tuple[str, int, int]]:
    """Detect headings based on font size analysis.
    
    Algorithm:
    1. Calculate average font size
    2. Calculate standard deviation
    3. Threshold = average + (1.5 * std_dev)
    4. Blocks above threshold = headings
    5. Map font sizes to heading levels (1-6)
    """

def map_font_size_to_level(font_size: float, unique_sizes: List[float]) -> int:
    """Map font size to heading level (1=largest, 6=smallest)."""
```

---

#### Text Extraction Module
**File:** `/home/user/OmniParser/src/omniparser/parsers/pdf/text_extraction.py`

**Key Functions:**
```python
def extract_text_content(
    doc: fitz.Document,
    use_ocr: bool = True,
    ocr_language: str = "eng",
    ocr_timeout: int = 300,
    max_pages: Optional[int] = None,
) -> Tuple[str, List[Dict]]:
    """Extract text with font information for heading detection.
    
    Returns:
    - full_text: Complete document text
    - text_blocks: List with keys:
        - text: Text content
        - font_size: Font size in points
        - is_bold: Whether text is bold
        - page_num: Page number (1-indexed)
        - position: Character position in full text
    """

def is_scanned_pdf(doc: fitz.Document, threshold: int = SCANNED_PDF_THRESHOLD) -> bool:
    """Determine if PDF is scanned (image-based) or text-based.
    
    Strategy:
    - Sample first 3 pages (or all if < 3)
    - Count extracted text characters
    - If < threshold chars per page on average, consider scanned
    """
```

**QR Integration Point:**
- Page-by-page iteration happens in `extract_text_content()`
- Each page is processed and images extracted
- Perfect place to analyze page images for QR codes

---

#### PDF Validation Module
**File:** `/home/user/OmniParser/src/omniparser/parsers/pdf/validation.py`

```python
def validate_and_load_pdf(file_path: Path) -> fitz.Document:
    """Validate PDF file and return fitz.Document for processing."""
```

---

#### PDF Tables Module
**File:** `/home/user/OmniParser/src/omniparser/parsers/pdf/tables.py`

```python
def extract_pdf_tables(doc: fitz.Document) -> List[str]:
    """Extract and convert tables to markdown format."""
```

---

## 4. PROCESSORS DIRECTORY

### File Location
`/home/user/OmniParser/src/omniparser/processors/`

### Available Processors

#### 1. Image Extraction Processor
**File:** `image_extractor.py`
**Functions:**
```python
def save_image(
    image_data: bytes,
    output_dir: Path,
    base_name: str = "image",
    extension: Optional[str] = None,
    counter: int = 1,
    preserve_subdirs: bool = False,
    original_path: Optional[str] = None,
) -> Tuple[Path, str]:
    """Save image data to file with auto-numbering."""

def get_image_dimensions(image_data: bytes) -> Tuple[Optional[int], Optional[int], str]:
    """Extract dimensions and format from image data using PIL."""

def validate_image_data(
    image_data: bytes,
    min_size: int = MIN_IMAGE_SIZE,
    max_size: int = MAX_IMAGE_SIZE,
) -> Tuple[bool, Optional[str]]:
    """Validate image data using PIL and size constraints."""

def extract_format_from_content_type(content_type: str) -> str:
    """Extract file extension from MIME content type."""
```

**Constants:**
```python
MIN_IMAGE_SIZE = 100  # Minimum image dimension in pixels
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
```

**QR Integration:** This processor could be extended to include QR code detection.

---

#### 2. Text Cleaner Processor
**File:** `text_cleaner.py`
**Purpose:** Clean and normalize text (whitespace, encoding, etc)

---

#### 3. Chapter Detector Processor
**File:** `chapter_detector.py`

**Functions:**
```python
def detect_chapters(text: str, min_level: int = 1, max_level: int = 2) -> List[Chapter]:
    """Detect chapters from markdown text based on heading hierarchy.
    
    Algorithm:
    1. Extract all markdown headings (# through ######)
    2. Filter by level range (min_level to max_level)
    3. For each chapter heading:
        - Determine content range (from heading to next heading)
        - Extract content substring
        - Calculate word count
        - Create Chapter object
    4. Handle no-heading documents (single chapter)
    """
```

**Helper Functions:**
```python
def _extract_headings(text: str) -> List[Tuple[int, str, int]]:
    """Extract all markdown headings with (level, title, position)."""

def _calculate_word_count(text: str) -> int:
    """Calculate word count for text."""
```

---

#### 4. Metadata Extractor Processor
**File:** `metadata_extractor.py`

**Functions:**
```python
def extract_html_metadata(html: str, url: Optional[str] = None) -> Metadata:
    """Extract metadata from HTML with priority-based fallback.
    
    Extraction priority:
    1. OpenGraph tags (og:title, og:description, og:article:author)
    2. Dublin Core meta tags (DC.title, DC.creator, DC.description)
    3. Standard meta tags (description, author, keywords)
    4. HTML title element
    5. Fallback values
    """
```

---

#### 5. Metadata Builder Processor
**File:** `metadata_builder.py`

**Class:**
```python
class MetadataBuilder:
    @staticmethod
    def build(
        title: Optional[str] = None,
        author: Optional[str] = None,
        authors: Optional[List[str]] = None,
        publisher: Optional[str] = None,
        publication_date: Optional[datetime] = None,
        language: Optional[str] = None,
        isbn: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        original_format: Optional[str] = None,
        file_size: int = 0,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Metadata:
        """Build Metadata object with standardized API."""
```

---

#### 6. Markdown Converter Processor
**File:** `markdown_converter.py`
**Purpose:** Convert HTML or other formats to markdown

---

#### 7. AI Processors (Optional Dependencies)
**Files:**
- `ai_summarizer.py` - Document summarization
- `ai_tagger.py` - Automatic tag generation
- `ai_image_analyzer.py` - Image content analysis
- `ai_image_describer.py` - Generate image descriptions
- `ai_quality.py` - Quality assessment

**Note:** Requires `anthropic` SDK (in optional `ai` dependencies)

---

## 5. UTILITIES DIRECTORY

### File Location
`/home/user/OmniParser/src/omniparser/utils/`

### Available Utilities

#### Format Detector
**File:** `format_detector.py`

```python
def detect_format(file_path: Path) -> str:
    """Detect file format using magic bytes with extension fallback.
    
    Returns: "epub", "pdf", "docx", "html", "markdown", or "text"
    Uses python-magic for magic bytes detection
    Falls back to extension checking
    """
```

---

#### Validators
**File:** `validators.py`

```python
def validate_file_exists(file_path: Path) -> None:
    """Validate that file exists and is a file (not directory)."""

def validate_file_size(file_path: Path, max_size_mb: int = 500) -> None:
    """Validate file size is within limits."""

def validate_format_supported(format_type: str) -> None:
    """Validate that format is supported."""
```

---

#### Encoding Utils
**File:** `encoding.py`
**Purpose:** Handle text encoding detection and normalization

---

#### HTML Extractor
**File:** `html_extractor.py`
**Purpose:** Extract content from HTML using BeautifulSoup

---

#### Secrets Management
**File:** `secrets.py`
**Purpose:** Handle API key and credential loading

---

#### Configuration
**File:** `config.py`
**Purpose:** Application configuration and settings

---

## 6. PARSER ENTRY POINT

### File Location
`/home/user/OmniParser/src/omniparser/parser.py`

### Main parse_document() Function

```python
def parse_document(
    file_path: str | Path, 
    options: Optional[Dict[str, Any]] = None
) -> Document:
    """Parse a document file or URL and return universal Document object.
    
    Automatically detects file format and routes to appropriate parser.
    
    Supported formats:
    - EPUB (.epub)
    - HTML (.html, .htm) - local files and URLs
    - PDF (.pdf)
    - DOCX (.docx)
    - Markdown (.md, .markdown)
    - Text (.txt, or no extension)
    """
```

**Format Detection Logic:**
1. Check if URL (http://, https://) → HTMLParser
2. Convert to Path, validate existence
3. Check file extension
4. Route to appropriate parser:
   - `.epub` → EPUBParser
   - `.pdf` → parse_pdf()
   - `.docx` → parse_docx()
   - `.html`, `.htm` → HTMLParser
   - `.md`, `.markdown` → MarkdownParser
   - `.txt` or no extension → TextParser

---

## 7. EXCEPTION HIERARCHY

### File Location
`/home/user/OmniParser/src/omniparser/exceptions.py`

```python
class OmniparserError(Exception):
    """Base exception for all OmniParser errors."""

class UnsupportedFormatError(OmniparserError):
    """Raised when file format not supported."""

class ParsingError(OmniparserError):
    """Raised when parsing fails.
    
    Attributes:
        message: Error description
        parser: Name of parser that failed
        original_error: Underlying exception
    """

class FileReadError(OmniparserError):
    """Raised when file cannot be read."""

class NetworkError(OmniparserError):
    """Raised when URL fetch fails."""

class ValidationError(OmniparserError):
    """Raised when input validation fails."""
```

---

## 8. DEPENDENCIES

### File Location
`/home/user/OmniParser/pyproject.toml`

### Core Dependencies
```toml
dependencies = [
    # Core
    "pyyaml>=6.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    # EPUB
    "ebooklib>=0.18",
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
    "regex>=2023.0.0",
]

[project.optional-dependencies]
ai = [
    "anthropic>=0.18.0",
    "openai>=1.12.0",
]
```

**For QR Code Detection:**
- `pyzbar>=0.1.9` - QR code detection library
- `opencv-python>=4.8.0` - Image processing (alternative to PIL/Pillow)
- `pillow` - Already included, used for image handling

---

## 9. PDF CONSTANTS

### File Location
`/home/user/OmniParser/src/omniparser/parsers/pdf/utils.py`

```python
SCANNED_PDF_THRESHOLD = 100      # Character count for OCR trigger
OCR_DPI = 300                    # DPI for OCR processing
HEADING_SEARCH_WINDOW = 100      # Character window for heading search
READING_SPEED_WPM = 250          # Words per minute for reading time
DEFAULT_OCR_TIMEOUT = 300        # OCR timeout in seconds (5 minutes)
DEFAULT_MAX_HEADING_WORDS = 25   # Maximum words in heading
MIN_TABLE_ROWS = 2               # Minimum table rows for extraction
MIN_IMAGE_SIZE = 100             # Minimum image dimension (pixels)
```

---

## KEY INTEGRATION POINTS FOR QR CODE SUPPORT

### 1. **Image Reference Extension**
   - Location: `src/omniparser/models.py` (ImageReference class)
   - Approach: Add optional QR code metadata field or create QRCodeReference model
   - Data: Store QR code URL/content detected in the image

### 2. **Image Extraction Pipeline**
   - Location: `src/omniparser/parsers/pdf/images.py` (extract_page_images function)
   - Approach: Analyze each extracted image for QR codes
   - Integration: After image validation, run QR detection before creating ImageReference

### 3. **Processor Pattern**
   - Location: Create new file `src/omniparser/processors/qr_detector.py`
   - Approach: Follow shared image processor pattern
   - Functions: 
     - `detect_qr_codes(image_data: bytes) -> List[str]`
     - `extract_qr_from_page(page: fitz.Page) -> List[str]`

### 4. **Text Extraction Integration**
   - Location: `src/omniparser/parsers/pdf/text_extraction.py`
   - Approach: During page-by-page iteration, also analyze for QR codes
   - Data: Store QR codes found per page with position information

### 5. **Metadata Storage**
   - Location: `src/omniparser/models.py` (Document.metadata.custom_fields)
   - Approach: Store document-level QR code findings
   - Data: `metadata.custom_fields['qr_codes']` = list of URLs
   - Metadata: `metadata.custom_fields['qr_detection_enabled']` = boolean

### 6. **Processing Options**
   - Location: Parser options dict
   - New options:
     - `detect_qr_codes: bool` (default: False)
     - `qr_code_output_dir: Optional[Path]` (for QR visualization)

### 7. **URL Fetching**
   - Location: Create utility in `src/omniparser/utils/qr_url_fetcher.py`
   - Purpose: Fetch and validate URLs extracted from QR codes
   - Use existing: `requests` library already in dependencies

---

## ARCHITECTURE PATTERNS

### 1. **Functional Approach**
- Parsers use functional approach rather than classes (except BaseParser)
- Main entry point: `parse_pdf()`, `parse_docx()`, etc.
- Coordinate specialized modules while maintaining clean flow

### 2. **Module Separation**
- PDF parser has dedicated modules:
  - Validation (validate_and_load_pdf)
  - Metadata (extract_pdf_metadata)
  - Text extraction (extract_text_content)
  - Images (extract_pdf_images)
  - Tables (extract_pdf_tables)
  - Headings (process_pdf_headings)
  - Utilities (count_words, estimate_reading_time)

### 3. **Shared Processors**
- Common tasks extracted to `processors/` directory
- Used across multiple parsers
- Examples: image_extractor, metadata_builder, chapter_detector

### 4. **Utility Functions**
- Reusable helper functions in `utils/` directory
- Format detection, validation, encoding handling
- Cross-cutting concerns

### 5. **Options-Based Configuration**
- Parsers accept options dict for runtime behavior
- Options propagated through pipeline
- Document processing_info logs options_used

---

## SUMMARY TABLE

| Component | Location | Purpose | QR Integration |
|-----------|----------|---------|-----------------|
| Models | src/omniparser/models.py | Data structures | Extend ImageReference |
| BaseParser | src/omniparser/base/base_parser.py | Parser interface | Inherit in custom parsers |
| PDF Parser | src/omniparser/parsers/pdf/parser.py | PDF orchestration | Add QR detection step |
| PDF Images | src/omniparser/parsers/pdf/images.py | Image extraction | Analyze extracted images |
| PDF Metadata | src/omniparser/parsers/pdf/metadata.py | Metadata extraction | Store QR metadata |
| PDF Text | src/omniparser/parsers/pdf/text_extraction.py | Text + OCR | Page iteration hook |
| Image Processor | src/omniparser/processors/image_extractor.py | Image utilities | Reuse for QR images |
| Chapter Detector | src/omniparser/processors/chapter_detector.py | Chapter structure | Link QR to chapters |
| Main Parser | src/omniparser/parser.py | Format routing | Pass QR options |
| Utils | src/omniparser/utils/ | Helpers | Add QR URL fetcher |

---

## NEXT STEPS FOR QR INTEGRATION

1. **Create QRCodeReference Model** - In models.py, define QR code data structure
2. **Create QR Detector Processor** - In processors/, implement QR detection logic
3. **Integrate into Image Pipeline** - In pdf/images.py, analyze extracted images
4. **Add URL Fetching Utility** - In utils/, create QR URL fetcher with validation
5. **Update Document Model** - Add custom_fields entries for QR metadata
6. **Add Parser Options** - Support `detect_qr_codes` and `qr_output_dir` options
7. **Test with PDF samples** - Verify QR detection across different PDF types
8. **Document API** - Add QR detection to parse_document() docstring

