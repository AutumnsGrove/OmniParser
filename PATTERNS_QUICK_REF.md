# Patterns Quick Reference Card

**Keep this open while coding!** 👀

## The Golden Rules
1. **Functions:** 15-30 lines (max 50)
2. **Files:** 50-200 lines per file
3. **No repetition:** Extract if used twice
4. **Comprehensions** > loops
5. **Type hints** on everything

---

## Quick Checklist ✓

Before committing:
- [ ] No function >50 lines
- [ ] No file >200 lines
- [ ] No repeated code blocks
- [ ] All public functions have docstrings
- [ ] Type hints on all functions
- [ ] Used comprehensions where possible
- [ ] Tests written and passing

---

## Template: New Parser

```python
# 1. Plan first (comments)
def parse_format(file_path: Path) -> Document:
    """Parse [FORMAT] into Document."""
    # Load file
    # Extract metadata
    # Extract content
    # Detect chapters
    # Assemble document
    pass

# 2. Break into small functions
def parse_format(file_path: Path) -> Document:
    doc = load_format_file(file_path)       # 15 lines
    metadata = extract_metadata(doc)        # 20 lines
    pages = extract_pages(doc)              # 25 lines
    chapters = detect_chapters(pages)       # 30 lines
    return assemble_document(metadata, pages, chapters)  # 10 lines

# 3. Use comprehensions
pages = [clean_page(doc[i].text()) for i in range(doc.page_count)]

# 4. Extract helpers
def clean_page(text: str) -> str:
    """Clean single page text."""
    return re.sub(r'\s+', ' ', text).strip()
```

---

## Common Patterns

### Extract Metadata
```python
def extract_metadata(doc: Any) -> Metadata:
    """Extract metadata from document."""
    return Metadata(
        title=extract_title(doc),
        author=extract_author(doc),
        language=extract_language(doc)
    )

def extract_title(doc: Any) -> str:
    """Extract title with fallback."""
    title = doc.get_metadata('title')
    return title.strip() if title else 'Unknown'
```

### Process List of Items
```python
# Use comprehension
chapters = [
    normalize_chapter(ch)
    for ch in raw_chapters
    if ch.word_count > 100
]

# Break into helpers
chapters = filter_short_chapters(raw_chapters)
chapters = [normalize_chapter(ch) for ch in chapters]
```

### Validation
```python
def validate_file(file_path: Path) -> Path:
    """Validate file exists and is readable."""
    if not file_path.exists():
        raise FileReadError(f"Not found: {file_path}")
    return file_path
```

---

## File Organization

```
src/parsers/[format]/
├── __init__.py      # Exports only
├── parser.py        # Main orchestration (40-60 lines)
├── loading.py       # File loading
├── metadata.py      # Metadata extraction
├── pages.py         # Page/content extraction
├── chapters.py      # Chapter detection
└── images.py        # Image extraction
```

---

## Red Flags 🚩

⚠️ **Function too long** → Split at logical boundaries
⚠️ **File too long** → Split by feature
⚠️ **Nested loops** → Extract inner loop to function
⚠️ **Complex conditional** → Extract to named predicate
⚠️ **Repeated code** → Extract to utility function

---

## When in Doubt

Ask yourself:
- "Can I understand this in 10 seconds?"
- "Is this doing ONE thing?"
- "Would this be easier to test if smaller?"

If NO → Make it smaller! ✂️

---

**Full Guide:** See `FUNCTIONAL_PATTERNS.md` for detailed examples and patterns.
