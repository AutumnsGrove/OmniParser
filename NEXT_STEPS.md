# Next Steps: Phase 2.2 - EPUB Parser Extraction from epub2tts

## ✅ Phase 2.1 Status: COMPLETE

**Completed on:** 2025-10-16
**Commit:** `8160e2f feat: Complete Phase 2.1 foundation`

### What Was Built:
- ✅ Complete repository structure
- ✅ Core data models (5 dataclasses + 6 helper methods)
- ✅ BaseParser abstract interface
- ✅ Exception hierarchy (6 classes)
- ✅ Utility modules (format detection, encoding, validation)
- ✅ Comprehensive test suite (171 tests, 87% coverage)
- ✅ Project configuration (pyproject.toml, LICENSE, CHANGELOG)

**Stats:** 26 files created, 2,530 lines of code, 100% tests passing

---

## 🎯 Phase 2.2 Objective: Extract EPUB Parser from epub2tts

**Goal:** Port all reusable EPUB processing code from epub2tts to create a production-ready `EPUBParser` that inherits from `BaseParser` and returns OmniParser's universal `Document` model.

**Source Project:** `/Users/autumn/Documents/Projects/epub2tts`
**Estimated Effort:** 2-3 weeks (86 hours)
**Priority:** CRITICAL (this is the first format parser)

---

## 📖 Required Reading (Start Here)

### Before Starting Phase 2.2:

1. **epub2tts Codebase Analysis** (Complete - see research output above)
   - Comprehensive component inventory
   - 50+ files analyzed
   - Extraction priorities identified
   - Risk areas mapped

2. **Key epub2tts Files to Study:**
   - `/Users/autumn/Documents/Projects/epub2tts/src/core/ebooklib_processor.py` (965 lines) - **MOST CRITICAL**
   - `/Users/autumn/Documents/Projects/epub2tts/src/core/text_cleaner.py` (522 lines) - Text cleaning
   - `/Users/autumn/Documents/Projects/epub2tts/src/utils/config.py` (316 lines) - Config patterns
   - `/Users/autumn/Documents/Projects/epub2tts/config/regex_patterns.yaml` (108 lines) - Cleaning rules
   - `/Users/autumn/Documents/Projects/epub2tts/tests/integration/test_epub_processor.py` (353 lines) - Test patterns

3. **OmniParser Documentation:**
   - `ARCHITECTURE_PLAN.md` Section 4 (EPUB Parser Port Strategy)
   - `RESEARCH_SYNTHESIS_SUMMARY.md` (Phase 1 findings)
   - `OMNIPARSER_PROJECT_SPEC.md` Section 4.2 (EPUB Parser Specification)

---

## 📦 Complete Component Extraction Plan

### Priority 1: Critical Foundation (Week 1 - Must Extract)

These components are production-tested in epub2tts and form the core of EPUB processing:

#### 1.1 Core Data Structures
**Source Files:**
- `epub2tts/src/core/ebooklib_processor.py` lines 35-75
- `epub2tts/src/core/text_cleaner.py` lines 20-70

**What to Extract:**
- ✅ `EbookMetadata` dataclass (30 lines) → Map to OmniParser's `Metadata`
- ✅ `TocEntry` dataclass (10 lines) → Internal structure for TOC parsing
- ✅ `HTMLTextExtractor` class (35 lines) → HTML to text conversion
- ⚠️ `Chapter` dataclass → Already in OmniParser, verify compatibility
- ⚠️ `CleaningStats` dataclass (40 lines) → Keep if useful for debugging

**Adaptation Notes:**
- Map `EbookMetadata` fields to OmniParser's `Metadata` model
- `TocEntry` is internal, doesn't need to match public API
- `HTMLTextExtractor` can be used as-is with minor type hint fixes

---

#### 1.2 EPUB Processing Core
**Source File:** `epub2tts/src/core/ebooklib_processor.py` lines 78-965

**Class:** `EbookLibProcessor` (863 lines) → Becomes `EPUBParser`

**Key Methods to Extract:**

| epub2tts Method | Lines | OmniParser Method | Priority | Notes |
|-----------------|-------|-------------------|----------|-------|
| `process_epub()` | 120 | `parse()` | ⭐⭐⭐⭐⭐ | Main entry point |
| `validate_epub()` | 30 | `validate_epub()` | ⭐⭐⭐⭐⭐ | Input validation |
| `_extract_metadata()` | 80 | `_extract_metadata()` | ⭐⭐⭐⭐⭐ | OPF parsing |
| `_extract_toc_structure()` | 120 | `_extract_toc()` | ⭐⭐⭐⭐⭐ | TOC parsing |
| `_extract_content_with_chapters()` | 150 | `_extract_content()` | ⭐⭐⭐⭐⭐ | Main content extraction |
| `_extract_chapters_from_toc()` | 180 | `_detect_chapters_toc()` | ⭐⭐⭐⭐⭐ | TOC-based detection |
| `_extract_chapters_from_spine()` | 100 | `_detect_chapters_spine()` | ⭐⭐⭐⭐ | Fallback detection |
| `_extract_text_from_item()` | 60 | `_extract_html_text()` | ⭐⭐⭐⭐⭐ | HTML parsing |
| `_extract_images()` | 80 | `extract_images()` | ⭐⭐⭐⭐ | Image extraction |
| `_post_process_chapters()` | 70 | `_postprocess_chapters()` | ⭐⭐⭐ | Chapter filtering |

**Critical Implementation Notes:**
- `process_epub()` returns `ProcessingResult` in epub2tts → Must return `Document` in OmniParser
- Keep the two-stage approach: TOC-based first, spine fallback if needed
- Preserve chapter boundary detection logic (this is production-tested)
- Image extraction uses temp directories - ensure proper cleanup
- HTML parsing via `HTMLTextExtractor` works well, reuse it

**Code Structure Pattern:**
```python
class EPUBParser(BaseParser):
    """EPUB parser using EbookLib (ported from epub2tts)."""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        # Initialize options

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is EPUB."""
        return file_path.suffix.lower() in ['.epub']

    def parse(self, file_path: Path) -> Document:
        """Parse EPUB file and return Document object."""
        # Port from EbookLibProcessor.process_epub()

        # 1. Validate
        self._validate_epub(file_path)

        # 2. Load with ebooklib
        book = epub.read_epub(str(file_path))

        # 3. Extract metadata
        metadata = self._extract_metadata(book)

        # 4. Extract TOC
        toc_entries = self._extract_toc(book)

        # 5. Extract content and chapters
        content, chapters = self._extract_content(book, toc_entries)

        # 6. Extract images (if enabled)
        images = self.extract_images(file_path) if self.options.get('extract_images') else []

        # 7. Create Document
        return Document(
            document_id=str(uuid.uuid4()),
            content=content,
            chapters=chapters,
            images=images,
            metadata=metadata,
            processing_info=self._create_processing_info(),
            word_count=self._count_words(content),
            estimated_reading_time=self._estimate_reading_time(content)
        )
```

---

#### 1.3 Text Cleaning (Subset)
**Source File:** `epub2tts/src/core/text_cleaner.py` lines 73-522

**Class:** `TextCleaner` (472 lines)

**What to Extract (SUBSET ONLY):**

✅ **Keep These Methods:**
- `clean_text()` - Main cleaning entry point (adapt to remove TTS markers)
- `_apply_removal_patterns()` - Remove unwanted patterns
- `_apply_transformation_patterns()` - Transform patterns
- `_normalize_whitespace()` - Whitespace cleanup
- `_fix_encoding()` - Use ftfy for encoding issues

❌ **Exclude These Methods (TTS-Specific):**
- `add_pause_markers()` - Adds `[PAUSE: X]` for TTS
- `segment_chapters()` - Adds `[CHAPTER_START: X]` markers
- `_calculate_pause_duration()` - TTS timing
- Any method with "tts" in the name

**Target:** Create `src/omniparser/processors/text_cleaner.py` (~200 lines, simplified)

**Implementation Strategy:**
1. Copy core cleaning logic
2. Remove all TTS marker insertion
3. Remove chapter segmentation (we use TOC-based chapters)
4. Keep regex pattern application
5. Keep encoding fixes
6. Simplify statistics tracking (optional)

---

#### 1.4 Regex Patterns & Configuration
**Source Files:**
- `epub2tts/config/regex_patterns.yaml` (108 lines)
- `epub2tts/config/default_config.yaml` (107 lines)
- `epub2tts/src/utils/config.py` (316 lines)

**What to Extract:**

**A. Regex Patterns (Adapt 80%)**
From `regex_patterns.yaml`:
```yaml
cleaning_rules:
  remove:
    - pattern: '\[\d+\]'          # Footnote markers → KEEP
    - pattern: '\*\*\*+'          # Section breaks → KEEP
    - pattern: 'http[s]?://\S+'   # URLs → KEEP
    # ... extract ~20 patterns

  transform:
    - pattern: '—'
      replacement: ' -- '          # Em dashes → KEEP
    # ... extract ~10 patterns

  tts_replacements:              # → ADAPT (remove TTS-specific)
    - pattern: '&'
      replacement: 'and'          # KEEP for general use
```

**B. Configuration Structure**
From `config.py` - Adapt these dataclasses:
- `ChapterConfig` → Port to OmniParser options
- `CleaningConfig` → Port subset
- Configuration validation patterns

**Target Files:**
- `src/omniparser/config/cleaning_patterns.yaml` (~80 lines)
- `src/omniparser/processors/text_cleaner.py` (load patterns)

---

### Priority 2: Testing Infrastructure (Week 2)

#### 2.1 Test File Adaptation
**Source Files:**
- `epub2tts/tests/unit/test_text_cleaner.py` (272 lines)
- `epub2tts/tests/integration/test_epub_processor.py` (353 lines)

**What to Adapt:**

**A. Unit Tests for Text Cleaning:**
- Test pattern removal
- Test pattern transformation
- Test encoding fixes
- Test whitespace normalization
- Skip: TTS marker tests

**B. Integration Tests for EPUB Parsing:**
- Test with real EPUB files
- Test TOC-based chapter detection
- Test spine-based fallback
- Test metadata extraction
- Test image extraction
- Test validation

**Target Files:**
- `tests/unit/test_text_cleaner.py` (~150 lines)
- `tests/unit/test_epub_parser.py` (~200 lines)
- `tests/integration/test_epub_parsing.py` (~250 lines)

---

#### 2.2 Test Fixtures
**Source:** `epub2tts/tests/fixtures/sample_epubs/`

**What to Extract:**
- Simple EPUB (1 chapter, basic metadata)
- Complex EPUB (multiple chapters, nested TOC, images)
- No-TOC EPUB (for spine-based fallback testing)
- Malformed EPUB (for error handling testing)

**Target:** `tests/fixtures/epub/` directory

**Create New Fixtures:**
- Minimal test EPUB (~10KB, 1 chapter)
- Standard test EPUB (~50KB, 5 chapters, 2 images)
- Complex test EPUB (~200KB, 20 chapters, nested TOC)

---

### Priority 3: Optional Enhancements (Phase 3 - Later)

#### 3.1 Advanced Text Processing (Optional Dependency)
**Source:** `epub2tts/src/text/modern_text_processor.py` (564 lines)

**Features:**
- spaCy-based NLP chapter detection
- Semantic text chunking
- Named entity extraction
- Topic extraction

**Decision:** Phase 3 (after basic EPUB parser works)
- Heavy dependencies (spaCy = 500MB+)
- Make it optional: `pip install omniparser[nlp]`
- Feature flag: `use_nlp_chapter_detection=False`

---

## 🗂️ File Creation Checklist

### Week 1: Core Implementation

**Parser Implementation:**
- [ ] `src/omniparser/parsers/epub_parser.py` (~600 lines)
  - [ ] `EPUBParser` class (inherits from `BaseParser`)
  - [ ] `supports_format()` method
  - [ ] `parse()` method (main entry point)
  - [ ] `_validate_epub()` method
  - [ ] `_extract_metadata()` method
  - [ ] `_extract_toc()` method
  - [ ] `_extract_content()` method
  - [ ] `_detect_chapters_toc()` method
  - [ ] `_detect_chapters_spine()` method (fallback)
  - [ ] `_extract_html_text()` method
  - [ ] `extract_images()` method override
  - [ ] `_create_processing_info()` helper
  - [ ] `_count_words()` helper
  - [ ] `_estimate_reading_time()` helper

**Text Processing:**
- [ ] `src/omniparser/processors/text_cleaner.py` (~200 lines)
  - [ ] `clean_text()` function
  - [ ] `_apply_removal_patterns()` function
  - [ ] `_apply_transformation_patterns()` function
  - [ ] `_normalize_whitespace()` function
  - [ ] `_fix_encoding()` function (use ftfy)
  - [ ] Pattern loading from YAML

**HTML Extraction:**
- [ ] `src/omniparser/utils/html_extractor.py` (~50 lines)
  - [ ] Port `HTMLTextExtractor` class from epub2tts
  - [ ] Clean HTML to text conversion
  - [ ] Handle special tags (lists, tables, etc.)

**Configuration:**
- [ ] `src/omniparser/config/cleaning_patterns.yaml` (~80 lines)
  - [ ] Port removal patterns from epub2tts
  - [ ] Port transformation patterns (adapt)
  - [ ] Port general text replacements
  - [ ] Exclude TTS-specific patterns

**Internal Data Structures:**
- [ ] Add to `src/omniparser/models.py`:
  - [ ] `TocEntry` dataclass (internal use)
  - [ ] `EpubMetadata` dataclass (or map directly to `Metadata`)

### Week 2: Testing

**Unit Tests:**
- [ ] `tests/unit/test_epub_parser.py` (~200 lines)
  - [ ] Test `supports_format()`
  - [ ] Test `_validate_epub()`
  - [ ] Test `_extract_metadata()`
  - [ ] Test `_extract_toc()`
  - [ ] Test `_detect_chapters_toc()`
  - [ ] Test `_detect_chapters_spine()`
  - [ ] Test `_extract_html_text()`
  - [ ] Test image extraction
  - [ ] Test error handling

- [ ] `tests/unit/test_text_cleaner.py` (~150 lines)
  - [ ] Test pattern removal
  - [ ] Test pattern transformation
  - [ ] Test encoding fixes
  - [ ] Test whitespace normalization

- [ ] `tests/unit/test_html_extractor.py` (~100 lines)
  - [ ] Test HTML to text conversion
  - [ ] Test special tag handling
  - [ ] Test whitespace handling

**Integration Tests:**
- [ ] `tests/integration/test_epub_parsing.py` (~250 lines)
  - [ ] Test end-to-end EPUB parsing
  - [ ] Test with simple EPUB
  - [ ] Test with complex EPUB (nested TOC)
  - [ ] Test with no-TOC EPUB (spine fallback)
  - [ ] Test with image-heavy EPUB
  - [ ] Test with Unicode content
  - [ ] Test error cases (malformed EPUB)

**Test Fixtures:**
- [ ] `tests/fixtures/epub/simple.epub` (create)
- [ ] `tests/fixtures/epub/complex.epub` (create)
- [ ] `tests/fixtures/epub/no_toc.epub` (create)
- [ ] `tests/fixtures/epub/with_images.epub` (create)
- [ ] `tests/fixtures/epub/unicode.epub` (create)
- [ ] `tests/fixtures/epub/malformed.epub` (create for error testing)

### Week 3: Integration & Documentation

**Integration:**
- [ ] Update `src/omniparser/__init__.py` to export `EPUBParser`
- [ ] Update `src/omniparser/parser.py` (main `parse_document()` function)
  - [ ] Add EPUB format detection
  - [ ] Route to `EPUBParser` when format is 'epub'
  - [ ] Handle EPUB-specific errors

**Documentation:**
- [ ] `docs/epub_parser.md` - EPUB parser documentation
- [ ] Update `README.md` with EPUB parsing examples
- [ ] Add usage examples to `examples/epub_parsing.py`
- [ ] Update `ARCHITECTURE_PLAN.md` to mark Phase 6 complete
- [ ] Update `CHANGELOG.md` with v1.1.0 entry

**Quality Checks:**
- [ ] Run `uv run black src/ tests/` (format code)
- [ ] Run `uv run mypy src/` (type checking)
- [ ] Run `uv run pytest --cov=src/omniparser --cov-report=term-missing` (test coverage)
- [ ] Target: >85% coverage for EPUB parser
- [ ] All tests passing
- [ ] No type errors

---

## 📊 Extraction Complexity Estimates

### Lines of Code to Port

| Component | Source Lines | Est. Port Lines | Complexity | Effort |
|-----------|--------------|-----------------|------------|--------|
| **Core Parser Logic** | | | | |
| EbookLibProcessor → EPUBParser | 863 | 600 | High | 24h |
| HTMLTextExtractor | 35 | 40 | Low | 2h |
| Metadata structures | 30 | 25 | Low | 1h |
| TOC structures | 10 | 10 | Low | 30m |
| **Text Processing** | | | | |
| TextCleaner (subset) | ~200 | 150 | Medium | 8h |
| Regex patterns | 108 | 80 | Low | 3h |
| **Testing** | | | | |
| Unit tests | ~500 | 450 | Medium | 16h |
| Integration tests | ~350 | 250 | Medium | 12h |
| Test fixtures | N/A | N/A | Low | 4h |
| **Documentation** | | | | |
| API docs & examples | N/A | ~500 | Low | 8h |
| **Integration** | | | | |
| parse_document() integration | N/A | ~50 | Low | 4h |
| Package exports | N/A | ~20 | Low | 2h |
| **TOTAL** | **~2,096** | **~2,175** | | **~86h** |

**Total Estimated Time:** 86 hours (2-3 weeks full-time)

---

## 🎯 Success Metrics

### Functional Requirements
- ✅ Parse EPUB files with TOC → Extract accurate chapters
- ✅ Parse EPUB files without TOC → Use spine-based fallback
- ✅ Extract complete metadata (title, author, publisher, ISBN, language, etc.)
- ✅ Extract images with proper base64 encoding or file references
- ✅ Handle Unicode and various encodings correctly
- ✅ Validate EPUB files before processing
- ✅ Clean text (remove footnotes, normalize whitespace, fix encoding)
- ✅ Return standard OmniParser `Document` object

### Performance Requirements
- ⚡ Parse 300-page EPUB in <5 seconds
- ⚡ Memory usage <500MB for large EPUBs (>10MB files)
- ⚡ No memory leaks (proper temp directory cleanup)
- ⚡ Handle files up to 500MB (configurable)

### Quality Requirements
- 🧪 Test coverage >85% for EPUB parser
- 🧪 All critical paths (chapter detection, metadata) >90% coverage
- 🐛 Zero known bugs in core functionality
- 📝 Complete API documentation with examples
- 🎯 Matches OmniParser `Document` model exactly
- ✅ All 171 existing tests still passing
- ✅ New EPUB tests passing

### Integration Requirements
- 🔗 Works seamlessly with `parse_document(file_path)`
- 🔗 Returns standard `Document` object
- 🔗 Handles errors with standard exceptions (`ParsingError`, `FileReadError`, etc.)
- 🔗 Logging compatible with OmniParser patterns
- 🔗 No breaking changes to existing APIs

---

## ⚠️ Critical Risk Areas

### 1. TTS-Specific Code Removal
**Risk:** HIGH - Accidentally keeping TTS markers in output

**Mitigation:**
- ❌ Remove all `[PAUSE: X]` insertion logic
- ❌ Remove `[CHAPTER_START: X]` markers
- ❌ Remove `[DIALOGUE_END]` markers
- ❌ Skip `add_pause_markers()` method entirely
- ❌ Skip `segment_chapters()` method (we use TOC-based)
- ✅ Keep only general text cleaning (whitespace, encoding, patterns)
- ✅ Test output doesn't contain any `[...]` markers

**Validation:**
- [ ] Run regex search: `\[PAUSE:|\[CHAPTER_START:|\[DIALOGUE` in output
- [ ] Should return 0 matches
- [ ] Create specific test: `test_no_tts_markers_in_output()`

---

### 2. Image Temporary Directory Cleanup
**Risk:** MEDIUM - Memory leaks if temp dirs not cleaned up

**Current Implementation (epub2tts):**
```python
temp_dir = tempfile.mkdtemp()
try:
    # Extract images to temp_dir
    images = self._extract_images(book, temp_dir)
finally:
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
```

**Improved Implementation (OmniParser):**
```python
with tempfile.TemporaryDirectory() as temp_dir:
    # Extract images to temp_dir
    images = self._extract_images(book, Path(temp_dir))
    # Context manager ensures cleanup even on exception
```

**Validation:**
- [ ] Test with exception during image extraction
- [ ] Verify temp dir is deleted
- [ ] Monitor system temp dir during long test runs

---

### 3. Chapter Detection Edge Cases
**Risk:** MEDIUM - Incorrect chapter boundaries

**Known Edge Cases:**
1. **No TOC:** epub2tts falls back to spine-based detection → Keep this logic
2. **Nested TOC:** Children chapters might be missed → Test with complex EPUB
3. **Empty chapters:** TOC entries with no content → Filter these out
4. **Duplicate titles:** Multiple chapters with same title → Add chapter_id disambiguation

**Mitigation:**
- ✅ Keep two-stage detection (TOC primary, spine fallback)
- ✅ Add confidence scoring to chapters (optional metadata)
- ✅ Test with 5+ different EPUB structures
- ✅ Log warnings for edge cases
- ✅ Add `chapter.metadata['detection_method']` = 'toc' or 'spine'

**Test Cases Needed:**
- [ ] Test EPUB with no TOC (spine fallback)
- [ ] Test EPUB with nested TOC (3+ levels)
- [ ] Test EPUB with empty chapters (filter them)
- [ ] Test EPUB with duplicate titles (disambiguation)
- [ ] Test EPUB with mixed content (text + images)

---

### 4. Encoding Issues
**Risk:** MEDIUM - Unicode/encoding errors in HTML extraction

**epub2tts Approach:**
```python
# Uses errors='ignore' in some places
content = html.decode('utf-8', errors='ignore')
```

**Improved Approach:**
1. Try `ftfy.fix_text()` first (fixes mojibake)
2. Then decode with UTF-8
3. Fallback to chardet detection if needed
4. Log warnings for encoding issues

**Validation:**
- [ ] Test with UTF-8 EPUB
- [ ] Test with Latin-1 encoded content
- [ ] Test with mixed encodings
- [ ] Test with emoji and special characters

---

### 5. Circular Import Risk
**Risk:** LOW - epub2tts has some circular imports

**epub2tts Pattern:**
```python
# In epub_processor.py
from .ebooklib_processor import EbookLibProcessor  # Import at top
from ..models import ProcessingResult  # Late import in method
```

**OmniParser Solution:**
- ✅ All dataclasses in `models.py` (flat structure)
- ✅ No circular dependencies in design
- ✅ Parsers import from models, not vice versa
- ✅ Use `TYPE_CHECKING` for type hints if needed

---

## 🔄 Development Workflow

### Week 1: Core Implementation

**Day 1-2: Parser Foundation**
1. [ ] Read `epub2tts/src/core/ebooklib_processor.py` completely
2. [ ] Create `src/omniparser/parsers/epub_parser.py`
3. [ ] Implement `EPUBParser` class skeleton (inherits from `BaseParser`)
4. [ ] Implement `supports_format()` method
5. [ ] Implement `_validate_epub()` method
6. [ ] Write initial tests
7. **Commit:** `feat: Add EPUBParser skeleton with validation`

**Day 3-4: Metadata & TOC Extraction**
1. [ ] Port `_extract_metadata()` from epub2tts
2. [ ] Map `EbookMetadata` to OmniParser's `Metadata` model
3. [ ] Port `_extract_toc_structure()` from epub2tts
4. [ ] Create `TocEntry` dataclass
5. [ ] Write unit tests for metadata/TOC
6. **Commit:** `feat: Add EPUB metadata and TOC extraction`

**Day 5: HTML Text Extraction**
1. [ ] Port `HTMLTextExtractor` class
2. [ ] Create `src/omniparser/utils/html_extractor.py`
3. [ ] Port `_extract_text_from_item()` method
4. [ ] Write unit tests
5. **Commit:** `feat: Add HTML text extraction for EPUB`

---

### Week 2: Content Extraction & Testing

**Day 6-7: Chapter Detection**
1. [ ] Port `_extract_content_with_chapters()` from epub2tts
2. [ ] Port `_extract_chapters_from_toc()` (TOC-based detection)
3. [ ] Port `_extract_chapters_from_spine()` (fallback)
4. [ ] Implement `_postprocess_chapters()` (filtering)
5. [ ] Write chapter detection tests
6. **Commit:** `feat: Add TOC-based and spine-based chapter detection`

**Day 8: Image Extraction**
1. [ ] Port `_extract_images()` method
2. [ ] Implement temp directory context manager
3. [ ] Test image extraction
4. [ ] Test cleanup on errors
5. **Commit:** `feat: Add image extraction for EPUB`

**Day 9: Text Cleaning**
1. [ ] Create `src/omniparser/processors/text_cleaner.py`
2. [ ] Port core cleaning methods (exclude TTS)
3. [ ] Create `config/cleaning_patterns.yaml`
4. [ ] Port regex patterns
5. [ ] Write text cleaning tests
6. **Commit:** `feat: Add text cleaning processor (adapted from epub2tts)`

**Day 10: Main parse() Method**
1. [ ] Implement `EPUBParser.parse()` method
2. [ ] Wire up all extraction steps
3. [ ] Create `Document` object
4. [ ] Handle errors and edge cases
5. [ ] Write end-to-end parser test
6. **Commit:** `feat: Complete EPUBParser.parse() implementation`

---

### Week 3: Testing, Integration & Documentation

**Day 11: Integration Tests**
1. [ ] Create test fixtures (simple, complex, no-TOC EPUBs)
2. [ ] Write `tests/integration/test_epub_parsing.py`
3. [ ] Test with real EPUB files
4. [ ] Test edge cases
5. [ ] Fix bugs found in testing
6. **Commit:** `test: Add comprehensive EPUB parser integration tests`

**Day 12: Integration with parse_document()**
1. [ ] Update `src/omniparser/parser.py`
2. [ ] Add EPUB format detection
3. [ ] Route to `EPUBParser`
4. [ ] Test end-to-end: `parse_document("book.epub")`
5. [ ] Verify returns `Document` object
6. **Commit:** `feat: Integrate EPUBParser into main parse_document() API`

**Day 13: Code Quality**
1. [ ] Run `uv run black src/ tests/`
2. [ ] Run `uv run mypy src/` - Fix all type errors
3. [ ] Run `uv run pytest --cov` - Aim for >85% coverage
4. [ ] Code review and refactoring
5. **Commit:** `refactor: Code cleanup and type fixes for EPUB parser`

**Day 14: Documentation**
1. [ ] Write `docs/epub_parser.md`
2. [ ] Add usage examples to `examples/epub_parsing.py`
3. [ ] Update `README.md` with EPUB section
4. [ ] Add docstrings to all public methods
5. [ ] Update `ARCHITECTURE_PLAN.md` (mark Phase 6 complete)
6. **Commit:** `docs: Add comprehensive EPUB parser documentation`

**Day 15: Final Testing & Release Prep**
1. [ ] Run full test suite (all 171+ tests)
2. [ ] Performance testing (300-page EPUB <5s)
3. [ ] Memory leak testing
4. [ ] Update `CHANGELOG.md` (v1.1.0)
5. [ ] Final commit and tag
6. **Commit:** `feat: Release OmniParser v1.1.0 with EPUB parser`

---

## 🧪 Test Coverage Requirements

### Unit Tests (Target: >90%)

**EPUBParser Tests:**
- [ ] `test_supports_format_epub()` - .epub extension
- [ ] `test_supports_format_not_epub()` - other extensions
- [ ] `test_validate_epub_valid()` - valid EPUB file
- [ ] `test_validate_epub_invalid()` - raises error
- [ ] `test_extract_metadata_complete()` - all fields
- [ ] `test_extract_metadata_partial()` - missing fields
- [ ] `test_extract_toc_nested()` - nested TOC structure
- [ ] `test_extract_toc_flat()` - flat TOC
- [ ] `test_extract_toc_missing()` - no TOC (None)
- [ ] `test_detect_chapters_toc()` - TOC-based detection
- [ ] `test_detect_chapters_spine()` - spine fallback
- [ ] `test_extract_html_text()` - HTML to text conversion
- [ ] `test_extract_images()` - image extraction
- [ ] `test_image_cleanup_on_error()` - temp dir cleanup
- [ ] `test_parse_end_to_end()` - full parse returns Document

**Text Cleaner Tests:**
- [ ] `test_remove_patterns()` - pattern removal
- [ ] `test_transform_patterns()` - pattern transformation
- [ ] `test_normalize_whitespace()` - whitespace cleanup
- [ ] `test_fix_encoding()` - ftfy encoding fixes
- [ ] `test_no_tts_markers()` - verify no TTS markers in output

**HTML Extractor Tests:**
- [ ] `test_extract_text_from_html()` - basic extraction
- [ ] `test_handle_lists()` - list formatting
- [ ] `test_handle_tables()` - table formatting
- [ ] `test_handle_whitespace()` - whitespace normalization
- [ ] `test_handle_special_chars()` - special character handling

### Integration Tests (Target: >85%)

**End-to-End EPUB Parsing:**
- [ ] `test_parse_simple_epub()` - 1 chapter, basic metadata
- [ ] `test_parse_complex_epub()` - 20+ chapters, nested TOC
- [ ] `test_parse_no_toc_epub()` - spine-based fallback
- [ ] `test_parse_image_epub()` - with images
- [ ] `test_parse_unicode_epub()` - Unicode content
- [ ] `test_parse_malformed_epub()` - error handling
- [ ] `test_document_structure()` - verify Document fields
- [ ] `test_chapter_boundaries()` - verify start/end positions
- [ ] `test_metadata_completeness()` - all metadata fields
- [ ] `test_image_references()` - image metadata correct

**Performance Tests:**
- [ ] `test_parse_large_epub()` - 300+ pages <5s
- [ ] `test_memory_usage()` - <500MB for large files
- [ ] `test_no_memory_leaks()` - repeated parsing

---

## 📦 Dependencies

### Already in pyproject.toml (No Changes Needed)
- ✅ `ebooklib>=0.18` - EPUB parsing
- ✅ `beautifulsoup4>=4.12.0` - HTML parsing
- ✅ `lxml>=5.0.0` - XML parsing
- ✅ `pyyaml>=6.0` - Config files
- ✅ `ftfy>=6.1.0` - Text fixing
- ✅ `chardet>=5.2.0` - Encoding detection
- ✅ `python-magic>=0.4.27` - Format detection

### Need to Add
- 🆕 `regex>=2023.0.0` - Advanced pattern matching

**Add with:**
```bash
cd /Users/autumn/Documents/Projects/OmniParser
uv add "regex>=2023.0.0"
```

### Optional (Phase 3 - Later)
- 🤔 `spacy>=3.7.0` - NLP chapter detection (optional extra)
- 🤔 `clean-text>=0.6.0` - Advanced text cleaning (optional extra)

---

## 📝 Code Quality Checklist

Before marking Phase 2.2 complete:

**Code Quality:**
- [ ] All code formatted with Black (line length 88)
- [ ] All code passes mypy type checking (no errors)
- [ ] All public functions have Google-style docstrings
- [ ] All functions have type hints
- [ ] No circular imports
- [ ] No print statements (use logging)

**Testing:**
- [ ] All new tests passing (171+ existing + ~50 new = 220+ total)
- [ ] Test coverage >85% for EPUB parser
- [ ] Integration tests with real EPUB files passing
- [ ] Performance tests passing (<5s for 300-page EPUB)
- [ ] No memory leaks detected

**Documentation:**
- [ ] EPUB parser API documented in `docs/epub_parser.md`
- [ ] Usage examples in `examples/epub_parsing.py`
- [ ] README.md updated with EPUB section
- [ ] CHANGELOG.md updated with v1.1.0 entry
- [ ] All public methods have docstrings with examples

**Integration:**
- [ ] `parse_document("file.epub")` works end-to-end
- [ ] Returns standard `Document` object
- [ ] Handles errors with standard exceptions
- [ ] No breaking changes to existing APIs
- [ ] All 171 existing tests still passing

**Git Hygiene:**
- [ ] Commits follow conventional commit style
- [ ] Each commit is focused and atomic
- [ ] Commit messages are descriptive
- [ ] All commits reference relevant files/line numbers

---

## 🎯 Definition of Done (Phase 2.2)

Phase 2.2 is COMPLETE when:

### Functional Requirements
✅ Can parse EPUB files with the following:
1. Extract complete metadata (title, author, publisher, etc.)
2. Detect chapters via TOC (primary)
3. Detect chapters via spine (fallback)
4. Extract and clean text content
5. Extract images (if enabled)
6. Return OmniParser `Document` object

### Quality Requirements
✅ Code quality:
- 220+ tests passing (100% pass rate)
- >85% test coverage for EPUB parser
- Zero mypy errors
- Black formatted
- Complete docstrings

✅ Performance:
- Parse 300-page EPUB in <5 seconds
- Memory usage <500MB for large EPUBs
- No memory leaks

✅ Documentation:
- API documentation complete
- Usage examples provided
- CHANGELOG updated
- README updated

### Integration Requirements
✅ Integration complete:
- Works with `parse_document()`
- No breaking changes to existing APIs
- All existing tests still passing
- Can be imported: `from omniparser import EPUBParser`

### Release Criteria
✅ Ready for release:
- Git tag created: `v1.1.0`
- CHANGELOG entry added
- All commits follow conventional style
- No known critical bugs

---

## 📞 Questions or Blockers?

If you encounter issues during Phase 2.2:

### Technical Questions
1. **Reference epub2tts source code:**
   - `/Users/autumn/Documents/Projects/epub2tts/src/core/ebooklib_processor.py`
   - Read the implementation carefully - it's production-tested

2. **Check OmniParser architecture:**
   - `ARCHITECTURE_PLAN.md` Section 4 (EPUB Parser Port Strategy)
   - `OMNIPARSER_PROJECT_SPEC.md` Section 4.2 (EPUB Parser Spec)

3. **Review research findings:**
   - Research output above (complete component analysis)
   - `RESEARCH_SYNTHESIS_SUMMARY.md` (Phase 1 findings)

### Design Decisions
- **When to deviate from epub2tts?**
  - Remove ALL TTS-specific code
  - Simplify when possible (OmniParser is simpler than epub2tts)
  - Preserve chapter detection logic (production-tested)

- **What to exclude?**
  - TTS markers (`[PAUSE:]`, `[CHAPTER_START:]`)
  - TTS-specific text transformations
  - Audio-related processing
  - UI components

- **What to keep exactly as-is?**
  - TOC parsing logic
  - Chapter boundary detection
  - Spine-based fallback
  - HTML text extraction
  - Image extraction patterns

### Common Pitfalls to Avoid
1. ❌ Don't copy TTS marker insertion code
2. ❌ Don't use `ProcessingResult` (use `Document` instead)
3. ❌ Don't use config files (use options dict)
4. ❌ Don't skip spine-based fallback (needed for TOC-less EPUBs)
5. ❌ Don't ignore temp directory cleanup (memory leaks)

---

## 🚀 Ready to Start Phase 2.2!

**Estimated Timeline:** 2-3 weeks (86 hours)
**Priority:** CRITICAL
**Risk Level:** Low-Medium (porting production-tested code)
**Value:** HIGHEST (first format parser, validates architecture)

**First Step:** Read `epub2tts/src/core/ebooklib_processor.py` lines 1-965 completely before starting implementation.

**Success Indicator:** `parse_document("book.epub")` returns a complete `Document` object with accurate chapters, metadata, and content.

Good luck! 🎉
