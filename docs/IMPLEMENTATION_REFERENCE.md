# OmniParser Implementation Reference
**Quick reference for developers implementing OmniParser**
**Companion to:** ARCHITECTURE_PLAN.md

---

## Quick Links

- **Main Spec:** `OMNIPARSER_PROJECT_SPEC.md` (same directory)
- **epub2tts Source:** Original EPUB processing implementation
  - `METAPROMPT_1_OMNIPARSER_EXTRACTION.md`
  - `src/core/ebooklib_processor.py`
  - `src/core/text_cleaner.py`
  - `tests/`

---

## Core Design Principles

1. **Format Agnostic:** OmniParser doesn't care about the source format
2. **TTS Agnostic:** No TTS-specific features (that's epub2tts's job)
3. **Universal Output:** All parsers return the same Document structure
4. **Optional Processing:** Everything is configurable via options dict
5. **Fail Gracefully:** Always provide helpful error messages

---

## Key API Contracts

### Main Entry Point
```python
from omniparser import parse_document

doc = parse_document(
    file_path,                      # str or Path
    extract_images=True,            # bool
    detect_chapters=True,           # bool
    clean_text=True,                # bool
    ocr_enabled=True,               # bool (PDF only)
    custom_options=None             # dict (parser-specific)
)
# Returns: Document object
```

### BaseParser Interface
```python
class MyParser(BaseParser):
    def __init__(self, options: dict = None):
        super().__init__(options)

    def parse(self, file_path: Path) -> Document:
        """REQUIRED: Main parsing logic"""
        # 1. Extract raw content
        # 2. Parse structure (chapters, metadata)
        # 3. Extract images if options['extract_images']
        # 4. Clean text if options['clean_text']
        # 5. Build Document object
        # 6. Return Document
        pass

    def supports_format(self, file_path: Path) -> bool:
        """REQUIRED: Check file extension/mime type"""
        return file_path.suffix.lower() in ['.ext']

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """OPTIONAL: Override if format has images"""
        return []

    def clean_text(self, text: str) -> str:
        """OPTIONAL: Override for custom cleaning"""
        return super().clean_text(text)
```

### Document Structure
```python
@dataclass
class Document:
    document_id: str                      # UUID
    content: str                          # Full text as markdown
    chapters: List[Chapter]               # Detected chapters
    images: List[ImageReference]          # Extracted images
    metadata: Metadata                    # Title, author, etc.
    processing_info: ProcessingInfo       # Parser metadata
    word_count: int                       # Total words
    estimated_reading_time: int           # Minutes (word_count // 200)

    # Helper methods
    def get_chapter(self, chapter_id: int) -> Optional[Chapter]
    def get_text_range(self, start: int, end: int) -> str
    def to_dict(self) -> dict
    def save_json(self, path: str) -> None
    @classmethod
    def from_dict(cls, data: dict) -> 'Document'
    @classmethod
    def load_json(cls, path: str) -> 'Document'
```

---

## EPUB Parser Port Checklist

### Direct Ports (Keep as-is)
- [x] `_extract_metadata()` - Adapt to return Metadata model
- [x] `_extract_toc_structure()` - Keep TocEntry structure
- [x] `_extract_text_from_item()` - Keep HTML extraction logic
- [x] `_extract_content_for_href()` - Keep href resolution
- [x] TOC-based chapter detection logic
- [x] Spine fallback logic

### Adaptations Needed
- [x] Remove `Config` dependency → Use `self.options` dict
- [x] Remove `progress_tracker` → No UI updates in OmniParser
- [x] Remove `TextCleaner` tight coupling → Use simple clean_text()
- [x] Return `Document` instead of `ProcessingResult`
- [x] Remove chapter splitting logic → Make optional via options
- [x] Remove temp directory management → Caller responsibility
- [x] Adapt image extraction to return `ImageReference` objects

### Key Differences
```python
# epub2tts (OLD)
def __init__(self, config: Config, progress_tracker=None):
    self.config = config
    self.cleaner = TextCleaner()
    min_words = self.config.chapters.min_words_per_chapter

# OmniParser (NEW)
def __init__(self, options: dict = None):
    self.options = options or {}
    min_words = self.options.get('min_words_per_chapter', 100)
```

---

## Text Cleaning Strategy

### What to Port from epub2tts TextCleaner
```python
# processors/text_cleaner.py
def clean_text(text: str, **options) -> str:
    """Basic cleaning - NO TTS features"""

    # ✅ Include these:
    - ftfy.fix_text() for encoding issues
    - Normalize quotes (" → ", ' → ')
    - Normalize whitespace (multiple spaces → single)
    - Normalize line breaks (3+ → 2)
    - Strip leading/trailing whitespace

    # ❌ Exclude these (TTS-specific):
    - Pause markers ([PAUSE: 2.0])
    - TTS replacements (& → and)
    - Chapter markers ([CHAPTER_START: ...])
    - Dialogue markers ([DIALOGUE_END])
    - Regex pattern loading from YAML
```

### What epub2tts Keeps
```python
# epub2tts keeps TTS-specific cleaning
from omniparser import parse_document

doc = parse_document(epub_path)
# doc.content is already basically clean

# Apply TTS-specific processing
tts_cleaner = TextCleaner()  # epub2tts's version
tts_text = tts_cleaner.add_pause_markers(doc.content)
tts_text = tts_cleaner.apply_tts_replacements(tts_text)
```

---

## Testing Checklist

### Per-Parser Unit Tests
```python
# tests/unit/test_epub_parser.py

def test_parse_valid_epub():
    """Basic parsing works"""
    parser = EPUBParser()
    doc = parser.parse(Path("fixtures/sample.epub"))
    assert doc.metadata.title is not None
    assert len(doc.chapters) > 0
    assert doc.word_count > 0

def test_parse_epub_without_toc():
    """Falls back to spine processing"""
    parser = EPUBParser()
    doc = parser.parse(Path("fixtures/no_toc.epub"))
    assert len(doc.chapters) > 0

def test_parse_epub_with_images():
    """Image extraction works"""
    parser = EPUBParser({'extract_images': True})
    doc = parser.parse(Path("fixtures/images.epub"))
    assert len(doc.images) > 0

def test_parse_corrupted_epub():
    """Fails gracefully"""
    parser = EPUBParser()
    with pytest.raises(ParsingError):
        parser.parse(Path("fixtures/corrupted.epub"))

def test_supports_format():
    """Correctly identifies EPUB files"""
    parser = EPUBParser()
    assert parser.supports_format(Path("book.epub"))
    assert not parser.supports_format(Path("book.pdf"))
```

### Integration Tests
```python
# tests/integration/test_full_pipeline.py

@pytest.mark.parametrize("file_path,expected_format", [
    ("fixtures/sample.epub", "epub"),
    ("fixtures/sample.pdf", "pdf"),
    ("fixtures/sample.docx", "docx"),
])
def test_parse_document_all_formats(file_path, expected_format):
    """Main API works for all formats"""
    doc = parse_document(file_path)
    assert doc.processing_info.parser_used == expected_format
    assert doc.content
    assert len(doc.chapters) > 0
    assert doc.word_count > 0
```

---

## Common Patterns

### Pattern 1: Parser Implementation
```python
class EPUBParser(BaseParser):
    def parse(self, file_path: Path) -> Document:
        # 1. Initialize tracking
        start_time = time.time()
        warnings = []

        # 2. Load format-specific library
        import ebooklib
        from ebooklib import epub
        book = epub.read_epub(str(file_path))

        # 3. Extract metadata
        metadata = self._extract_metadata(book)

        # 4. Extract structure (chapters)
        chapters = self._extract_chapters(book)

        # 5. Extract images (if enabled)
        images = []
        if self.options.get('extract_images', True):
            images = self._extract_images(book)

        # 6. Build full content
        full_content = '\n\n'.join(ch.content for ch in chapters)

        # 7. Clean text (if enabled)
        if self.options.get('clean_text', True):
            full_content = self.clean_text(full_content)

        # 8. Build Document
        return Document(
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
                warnings=warnings,
                options_used=self.options
            ),
            word_count=len(full_content.split()),
            estimated_reading_time=len(full_content.split()) // 200
        )
```

### Pattern 2: Error Handling
```python
def parse(self, file_path: Path) -> Document:
    try:
        # Parsing logic
        return document
    except FileNotFoundError as e:
        raise FileReadError(f"File not found: {file_path}") from e
    except PermissionError as e:
        raise FileReadError(f"Permission denied: {file_path}") from e
    except Exception as e:
        raise ParsingError(
            f"Failed to parse EPUB: {file_path}",
            parser="epub",
            original_error=e
        ) from e
```

### Pattern 3: Options Handling
```python
def __init__(self, options: dict = None):
    super().__init__(options)

    # Get options with defaults
    self.extract_images = self.options.get('extract_images', True)
    self.detect_chapters = self.options.get('detect_chapters', True)
    self.min_words = self.options.get('min_words_per_chapter', 100)
    self.ocr_enabled = self.options.get('ocr_enabled', True)
```

---

## Dependency Matrix

### Core Dependencies (All Parsers)
```toml
pyyaml>=6.0              # Config files
beautifulsoup4>=4.12.0   # HTML parsing
lxml>=5.0.0              # XML parsing
ftfy>=6.1.0              # Encoding fixes
python-magic>=0.4.27     # Format detection
dataclasses-json>=0.6.0  # Serialization
```

### Parser-Specific Dependencies
```toml
# EPUB
ebooklib>=0.19

# PDF
PyMuPDF>=1.23.0
pytesseract>=0.3.10      # OCR
Pillow>=10.0.0

# DOCX
python-docx>=1.0.0

# HTML/URLs
trafilatura>=1.6.0
readability-lxml>=0.8.0
requests>=2.31.0

# Text
chardet>=5.2.0
```

---

## File Size Reference

**ebooklib_processor.py:** 963 lines (will be replaced by EPUBParser)
**text_cleaner.py:** 522 lines (subset ported to text_cleaner.py)

**Estimated OmniParser LOC:**
- Core models: ~200 lines
- Base parser: ~50 lines
- EPUB parser: ~600 lines (port of ebooklib_processor)
- Other parsers: ~300 lines each (PDF, DOCX, HTML)
- Processors: ~400 lines total
- Utilities: ~200 lines
- Tests: ~2000 lines
- **Total: ~4500-5000 lines**

---

## Command Reference

### Development Commands
```bash
# Setup (from project root)
uv init
uv sync

# Testing
uv run pytest                                    # Run all tests
uv run pytest tests/unit/test_epub_parser.py -v # Run specific test
uv run pytest --cov=omniparser --cov-report=html # Coverage report

# Formatting
uv run black src/ tests/                         # Format code
uv run black --check .                           # Check formatting

# Type checking
uv run mypy src/                                 # Type check

# Building
uv build                                         # Build package
uv add ./dist/omniparser-1.0.0.tar.gz           # Test local install

# Publishing (when ready)
uv publish                                       # Publish to PyPI
```

### Usage Examples
```python
# Basic usage
from omniparser import parse_document
doc = parse_document("book.epub")
print(f"Title: {doc.metadata.title}")
print(f"Chapters: {len(doc.chapters)}")

# With options
doc = parse_document(
    "document.pdf",
    extract_images=True,
    ocr_enabled=True,
    custom_options={'extract_tables': True}
)

# Serialization
doc.save_json("output.json")
loaded_doc = Document.load_json("output.json")

# Chapter access
first_chapter = doc.get_chapter(0)
print(f"Chapter 1: {first_chapter.title}")
print(f"Words: {first_chapter.word_count}")
```

---

## Troubleshooting Guide

### Problem: "Module not found: omniparser"
**Solution:** Install package: `uv add omniparser` or run from project root with `uv run`

### Problem: "UnsupportedFormatError"
**Solution:** Check format detection with `detect_format(path)`, ensure file extension correct

### Problem: "ParsingError with EPUB"
**Solution:** Validate EPUB structure, check if file is corrupted, ensure ebooklib installed

### Problem: Tests fail with "FileNotFoundError"
**Solution:** Ensure test fixtures exist in `tests/fixtures/`, check paths are absolute

### Problem: Coverage below 80%
**Solution:** Add tests for edge cases, uncovered branches, error handling

---

## epub2tts Migration Checklist

### Step 1: Install OmniParser
```toml
# epub2tts/pyproject.toml
[project.dependencies]
omniparser>=1.0.0
```

### Step 2: Update Imports
```python
# epub2tts/src/core/epub_processor.py
# OLD
from core.ebooklib_processor import EbookLibProcessor

# NEW
from omniparser import parse_document, Document
```

### Step 3: Adapter Function
```python
def _omniparser_to_epub2tts(doc: Document) -> ProcessingResult:
    """Convert OmniParser Document to epub2tts ProcessingResult"""
    return ProcessingResult(
        success=True,
        text_content=doc.content,
        chapters=[_convert_chapter(ch) for ch in doc.chapters],
        metadata=_convert_metadata(doc.metadata),
        image_info=[_convert_image(img) for img in doc.images],
        cleaning_stats=CleaningStats(
            original_length=len(doc.content),
            cleaned_length=len(doc.content),
            patterns_applied=0,
            transformations_made=0,
            errors_encountered=0
        ),
        processing_time=doc.processing_info.processing_time
    )
```

### Step 4: Update EPUBProcessor
```python
class EPUBProcessor:
    def process_epub(self, epub_path: Path, output_dir: Path) -> ProcessingResult:
        # Parse with OmniParser
        doc = parse_document(epub_path, extract_images=True, detect_chapters=True)

        # Convert to epub2tts format
        result = _omniparser_to_epub2tts(doc)

        # Apply TTS-specific processing
        result.text_content = self._apply_tts_processing(result.text_content)

        return result
```

### Step 5: Remove Old Code
- Delete `src/core/ebooklib_processor.py`
- Update tests to use OmniParser
- Remove ebooklib from dependencies (if not used elsewhere)

### Step 6: Validate
```bash
# Run full epub2tts test suite
cd epub2tts
uv run pytest

# Test specific EPUB processing
uv run pytest tests/integration/test_epub_processor.py -v
```

---

## Success Criteria Quick Check

**Before declaring Phase complete:**
- [ ] All files created
- [ ] All tests passing
- [ ] Code formatted with Black
- [ ] No obvious bugs
- [ ] Documentation updated

**Before declaring OmniParser v1.0 complete:**
- [ ] All 6 parsers working
- [ ] >80% test coverage
- [ ] Package builds: `uv build`
- [ ] Can install: `uv add omniparser`
- [ ] Examples run successfully
- [ ] epub2tts integration works

---

## Additional Resources

**EbookLib Documentation:**
- https://github.com/aerkalov/ebooklib
- https://ebooklib.readthedocs.io/

**PyMuPDF Documentation:**
- https://pymupdf.readthedocs.io/

**python-docx Documentation:**
- https://python-docx.readthedocs.io/

**Trafilatura Documentation:**
- https://trafilatura.readthedocs.io/

**UV Documentation:**
- https://github.com/astral-sh/uv
- https://astral.sh/blog/uv

---

**Last Updated:** October 16, 2025
**Companion to:** ARCHITECTURE_PLAN.md
**Status:** Ready for Reference During Implementation
