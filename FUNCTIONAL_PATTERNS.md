# Functional Patterns Guide - Gradual Adoption

**Purpose:** A practical guide for writing new code (PDF, DOCX parsers, etc.) using functional patterns that work well with ADHD cognitive styles. This is **not** a mandate to refactor existing code - use these patterns going forward, and we'll refactor old code later when we have multiple examples to learn from.

**Philosophy:** Small functions, clear data flow, easy to understand and test.

---

## Quick Reference

When writing new code, aim for:
- ✅ Functions: 10-80 lines (sweet spot: 15-45)
- ✅ Files: 50-200 lines per file
- ✅ Use comprehensions over loops
- ✅ Break complex logic into named helper functions
- ✅ Prefer pure functions (same input → same output)
- ✅ Use composition when orchestrating steps

**Don't worry about being perfect!** These are guidelines, not laws. If a function needs 60 lines, that's fine. If breaking it up makes it harder to read, don't break it up.

---

## Pattern 1: Small, Focused Functions

### ❌ Before (Large Function)
```python
def parse_pdf(file_path: Path) -> Document:
    # Open PDF
    doc = fitz.open(file_path)

    # Extract metadata
    metadata = doc.metadata
    title = metadata.get('title', 'Unknown')
    author = metadata.get('author', 'Unknown')

    # Get all pages
    pages = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        pages.append(text)

    # Detect chapters
    chapters = []
    current_chapter = None
    for page_text in pages:
        if re.match(r'^Chapter \d+', page_text):
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = Chapter(title=..., content=...)
        # ... 30 more lines

    # Build document
    full_content = '\n\n'.join(pages)
    return Document(...)
```

### ✅ After (Small Functions)
```python
def parse_pdf(file_path: Path) -> Document:
    """Parse PDF file into Document."""
    pdf_doc = load_pdf(file_path)
    metadata = extract_pdf_metadata(pdf_doc)
    pages = extract_all_pages(pdf_doc)
    chapters = detect_chapters_from_pages(pages)
    full_content = join_pages(pages)

    return Document(
        content=full_content,
        chapters=chapters,
        metadata=metadata,
        word_count=count_words(full_content)
    )

def load_pdf(file_path: Path) -> fitz.Document:
    """Load PDF file using PyMuPDF."""
    return fitz.open(file_path)

def extract_pdf_metadata(pdf_doc: fitz.Document) -> Metadata:
    """Extract metadata from PDF document."""
    meta = pdf_doc.metadata
    return Metadata(
        title=meta.get('title', 'Unknown'),
        author=meta.get('author', 'Unknown'),
        publisher=meta.get('subject'),
        language=meta.get('lang', 'en')
    )

def extract_all_pages(pdf_doc: fitz.Document) -> list[str]:
    """Extract and clean text from all pages."""
    return [
        clean_page_text(pdf_doc[page_num].get_text())
        for page_num in range(pdf_doc.page_count)
    ]

def clean_page_text(text: str) -> str:
    """Clean extracted page text."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
```

**Why this is better:**
- Each function has ONE clear job
- Easy to test each piece independently
- Easy to find and fix bugs
- Function names document what the code does
- Can read `parse_pdf` and understand the flow without implementation details

---

## Pattern 2: Comprehensions Over Loops

### ❌ Avoid (Imperative Loops)
```python
def extract_images(pdf_doc: fitz.Document) -> list[ImageReference]:
    images = []
    for page_num in range(pdf_doc.page_count):
        page = pdf_doc[page_num]
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_doc.extract_image(xref)
            if base_image['width'] > 50 and base_image['height'] > 50:
                image_ref = ImageReference(
                    image_id=f"img_{page_num}_{img_index}",
                    file_path=None,
                    position=page_num
                )
                images.append(image_ref)
    return images
```

### ✅ Prefer (Comprehensions + Helpers)
```python
def extract_images(pdf_doc: fitz.Document) -> list[ImageReference]:
    """Extract all images from PDF."""
    return [
        image_ref
        for page_num in range(pdf_doc.page_count)
        for image_ref in extract_page_images(pdf_doc, page_num)
    ]

def extract_page_images(pdf_doc: fitz.Document, page_num: int) -> list[ImageReference]:
    """Extract images from a single page."""
    page = pdf_doc[page_num]
    return [
        create_image_reference(img, page_num, img_index)
        for img_index, img in enumerate(page.get_images())
        if is_image_large_enough(pdf_doc, img)
    ]

def is_image_large_enough(pdf_doc: fitz.Document, img_info: tuple) -> bool:
    """Check if image meets minimum size requirements."""
    xref = img_info[0]
    base_image = pdf_doc.extract_image(xref)
    return base_image['width'] > 50 and base_image['height'] > 50

def create_image_reference(img_info: tuple, page_num: int, img_index: int) -> ImageReference:
    """Create ImageReference from PDF image info."""
    return ImageReference(
        image_id=f"img_{page_num}_{img_index}",
        file_path=None,
        position=page_num
    )
```

**Why this is better:**
- Less cognitive load - comprehensions read like natural language
- Fewer chances for bugs (no mutable state, no append operations)
- Each helper function is testable
- Easy to add filtering or transformations

---

## Pattern 3: File Organization (Feature-Based)

Instead of one massive file, split by feature/responsibility:

```
src/parsers/pdf/
├── __init__.py           # 20 lines: exports main function
├── parser.py             # 40 lines: main parse_pdf() orchestration
├── loading.py            # 60 lines: load_pdf, validate_pdf
├── metadata.py           # 80 lines: extract_pdf_metadata + helpers
├── pages.py              # 100 lines: page extraction and cleaning
├── chapters.py           # 120 lines: chapter detection logic
├── images.py             # 90 lines: image extraction
└── tables.py             # 80 lines: table extraction (if supported)
```

**Benefits:**
- Each file is scannable in one screen
- Easy to find what you're looking for
- Import only what you need
- Can work on one feature without loading entire parser in your head

---

## Pattern 4: Type Hints & Dataclasses for Data Flow

Use dataclasses to make data flow explicit:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PDFData:
    """Raw PDF data loaded from file."""
    file_path: Path
    pdf_doc: fitz.Document
    page_count: int

@dataclass
class PDFWithMetadata:
    """PDF data enriched with metadata."""
    pdf_data: PDFData
    metadata: Metadata

@dataclass
class PDFWithContent:
    """PDF data with extracted content."""
    pdf_metadata: PDFWithMetadata
    pages: list[str]
    full_content: str

# Then use these in your pipeline:
def parse_pdf(file_path: Path) -> Document:
    """Parse PDF through functional pipeline."""
    pdf_data = load_pdf_data(file_path)  # Returns PDFData
    pdf_with_meta = extract_metadata(pdf_data)  # Returns PDFWithMetadata
    pdf_with_content = extract_content(pdf_with_meta)  # Returns PDFWithContent
    chapters = detect_chapters(pdf_with_content)
    return assemble_document(pdf_with_content, chapters)
```

**Benefits:**
- Type checker catches errors
- Clear what data exists at each stage
- Easy to add new fields without breaking things
- Self-documenting pipeline

---

## Pattern 5: Composition for Reusable Logic

Create higher-order functions for common patterns:

```python
from typing import Callable, TypeVar

T = TypeVar('T')

def map_items(transform: Callable[[T], T]) -> Callable[[list[T]], list[T]]:
    """Apply transformation to all items in list."""
    def _map(items: list[T]) -> list[T]:
        return [transform(item) for item in items]
    return _map

def filter_items(predicate: Callable[[T], bool]) -> Callable[[list[T]], list[T]]:
    """Filter list items by predicate."""
    def _filter(items: list[T]) -> list[T]:
        return [item for item in items if predicate(item)]
    return _filter

# Usage:
normalize_chapters = map_items(normalize_chapter_title)
remove_short_chapters = filter_items(lambda ch: ch.word_count > 100)

def process_chapters(chapters: list[Chapter]) -> list[Chapter]:
    """Process chapters with composed transformations."""
    return remove_short_chapters(normalize_chapters(chapters))
```

---

## Pattern 6: No Repeated Code

If you write the same code twice, extract it:

### ❌ Repetition
```python
# In pdf_parser.py
chapters = []
for ch in raw_chapters:
    ch.title = ch.title.strip().title()
    ch.word_count = len(ch.content.split())
    chapters.append(ch)

# Later in docx_parser.py (same code!)
chapters = []
for ch in raw_chapters:
    ch.title = ch.title.strip().title()
    ch.word_count = len(ch.content.split())
    chapters.append(ch)
```

### ✅ Extract to Shared Utility
```python
# In src/utils/chapter_utils.py
def normalize_chapter(chapter: Chapter) -> Chapter:
    """Normalize chapter title and calculate word count."""
    return Chapter(
        chapter_id=chapter.chapter_id,
        title=chapter.title.strip().title(),
        content=chapter.content,
        word_count=len(chapter.content.split()),
        start_position=chapter.start_position,
        end_position=chapter.end_position,
        level=chapter.level
    )

# Use in both parsers:
from omniparser.utils.chapter_utils import normalize_chapter

chapters = [normalize_chapter(ch) for ch in raw_chapters]
```

---

## Pattern 7: Testing Small Functions

Small functions are easy to test:

```python
# src/parsers/pdf/metadata.py
def extract_author(pdf_metadata: dict) -> str:
    """Extract author from PDF metadata."""
    author = pdf_metadata.get('author', '').strip()
    return author if author else 'Unknown'

# tests/unit/pdf/test_metadata.py
def test_extract_author_with_author():
    metadata = {'author': '  Jane Austen  '}
    assert extract_author(metadata) == 'Jane Austen'

def test_extract_author_empty():
    metadata = {'author': ''}
    assert extract_author(metadata) == 'Unknown'

def test_extract_author_missing():
    metadata = {}
    assert extract_author(metadata) == 'Unknown'
```

**Benefits:**
- Fast tests (no file I/O needed)
- Easy to test edge cases
- Clear what each function does
- Build confidence as you code

---

## Practical Checklist for New Code

When writing a new parser or feature, follow this checklist:

### Planning Phase
- [ ] Sketch out main steps in comments
- [ ] Identify 5-8 main functions needed
- [ ] Decide which file each function belongs in
- [ ] Define any intermediate dataclasses

### Implementation Phase
- [ ] Write function signatures with type hints first
- [ ] Implement smallest/simplest functions first
- [ ] Test each function as you write it
- [ ] Use comprehensions for lists/filtering
- [ ] Extract repeated code (>5 lines) into helpers

### Review Phase
- [ ] Any function >50 lines? → Break it up
- [ ] Any file >200 lines? → Split by feature
- [ ] Any loops that could be comprehensions? → Refactor
- [ ] Any repeated code? → Extract to utility
- [ ] All functions have docstrings? → Add them
- [ ] All tests passing? → Commit!

---

## Example: PDF Parser Structure (Template)

Here's a complete example structure to follow:

```python
# src/parsers/pdf/__init__.py (20 lines)
"""PDF parser module."""
from .parser import parse_pdf

__all__ = ['parse_pdf']

# src/parsers/pdf/parser.py (40 lines)
"""Main PDF parsing orchestration."""
from pathlib import Path
from ...models import Document
from .loading import load_pdf_document
from .metadata import extract_metadata
from .pages import extract_pages
from .chapters import detect_chapters
from .images import extract_images

def parse_pdf(file_path: Path, **options) -> Document:
    """
    Parse PDF file into Document.

    Args:
        file_path: Path to PDF file
        extract_images: Extract images (default: True)
        detect_chapters: Detect chapters (default: True)

    Returns:
        Document with parsed content
    """
    # Load
    pdf_doc = load_pdf_document(file_path)

    # Extract metadata
    metadata = extract_metadata(pdf_doc)

    # Extract content
    pages = extract_pages(pdf_doc)
    full_content = '\n\n'.join(pages)

    # Optional: chapters
    chapters = []
    if options.get('detect_chapters', True):
        chapters = detect_chapters(pages)

    # Optional: images
    images = []
    if options.get('extract_images', True):
        images = extract_images(pdf_doc)

    return Document(
        content=full_content,
        chapters=chapters,
        images=images,
        metadata=metadata,
        word_count=len(full_content.split())
    )

# src/parsers/pdf/loading.py (60 lines)
"""PDF loading and validation."""
import fitz
from pathlib import Path
from ...exceptions import FileReadError, ValidationError

def load_pdf_document(file_path: Path) -> fitz.Document:
    """Load and validate PDF file."""
    validate_pdf_file(file_path)
    try:
        return fitz.open(str(file_path))
    except Exception as e:
        raise FileReadError(f"Cannot load PDF: {e}")

def validate_pdf_file(file_path: Path) -> None:
    """Validate PDF file exists and is readable."""
    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise ValidationError(f"Empty PDF file: {file_path}")

    # Check PDF magic bytes
    with open(file_path, 'rb') as f:
        magic = f.read(5)
        if magic != b'%PDF-':
            raise ValidationError(f"Not a valid PDF file: {file_path}")

# ... Continue this pattern for other modules
```

---

## Migration Path (For Later)

When you have PDF and DOCX parsers working well with these patterns:

### Phase 1: Learn & Document
- Use these patterns in PDF parser
- Use these patterns in DOCX parser
- Document what worked well
- Document what felt awkward
- Adjust patterns based on experience

### Phase 2: Create Shared Utilities
- Extract common patterns (chapter normalization, text cleaning, etc.)
- Build `src/utils/` library of reusable functions
- Create `src/core/` for composition utilities

### Phase 3: Refactor EPUB (Optional)
- Apply learned patterns to EPUB parser
- Break `epub_parser.py` into smaller files
- Extract EPUB-specific utilities
- Maintain 100% test coverage throughout

**Timeline:** Do this after 2-3 months, when you have multiple parsers and understand what works for you.

---

## Key Takeaways

1. **Start small** - Apply these patterns to new code, don't refactor old code yet
2. **Function size** - Aim for 15-30 lines, max 50 lines
3. **File size** - Keep files under 200 lines by splitting by feature
4. **Comprehensions** - Use them for lists, filtering, mapping
5. **Extract duplication** - If you write it twice, make it a function
6. **Type hints everywhere** - Helps catch bugs and documents intent
7. **Test as you go** - Small functions → easy tests
8. **Don't be dogmatic** - If it makes code harder to read, don't do it

---

## Questions to Ask Yourself

When writing new code:
- "Is this function doing more than one thing?"
- "Would this be easier to test if split into smaller pieces?"
- "Am I writing a loop that could be a comprehension?"
- "Have I written this code before? Should it be extracted?"
- "Can I understand this function in 10 seconds?"

If the answer suggests refactoring, do it! Small improvements compound.

---

## Resources

- **EPUB Parser** - `src/parsers/epub_parser.py` (what NOT to do - 1030 lines in one file)
- **Models** - `src/omniparser/models.py` (good example of clean dataclasses)
- **Tests** - `tests/unit/` (examples of testing patterns)

**Remember:** This is a guide, not a rulebook. Use what helps you, ignore what doesn't. The goal is code that's easy for YOU to understand and maintain. 🧠✨
