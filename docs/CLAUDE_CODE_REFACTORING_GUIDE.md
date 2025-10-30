# Claude Code Session Guide: Parser Refactoring Task

**Document Type:** Claude Code Session Initialization Guide
**Purpose:** Guide an autonomous Claude Code session to refactor OmniParser parsers following functional patterns
**Target Audience:** Claude Code AI Agent
**Session Mode:** YOLO (Auto-approve) with Subagent-First Development
**Estimated Duration:** 8-12 hours of autonomous execution
**Created:** 2025-10-29

---

## 🎯 Mission Objective

Refactor 4 large OmniParser parsers (PDF, DOCX, Markdown, Text) from monolithic files (580-1052 lines) into modular, maintainable components (50-200 lines per file) following functional programming patterns defined in `FUNCTIONAL_PATTERNS.md` and `PATTERNS_QUICK_REF.md`.

**Success Criteria:**
- ✅ All parser files ≤200 lines
- ✅ All module files 50-200 lines
- ✅ 100% test pass rate maintained (current: 830/880 passing = 94.3%)
- ✅ No functionality regressions
- ✅ Improved testability and maintainability
- ✅ Consistent architecture across all parsers
- ✅ All commits follow conventional commit style

---

## 📊 Current State Analysis

### Parser File Sizes (Pre-Refactoring)

| Parser | Current Lines | Target | Modules Needed | Priority |
|--------|--------------|--------|----------------|----------|
| PDF Parser | 1,052 lines | 6 modules × ~150 lines | 6-7 | **HIGH** |
| DOCX Parser | 755 lines | 5 modules × ~120 lines | 5-6 | **HIGH** |
| Markdown Parser | 741 lines | 4 modules × ~150 lines | 4-5 | **MEDIUM** |
| Text Parser | 580 lines | 4 modules × ~120 lines | 3-4 | **MEDIUM** |
| EPUB Parser | 1,053 lines | ⚠️ DEFER | N/A | **DEFER** |
| HTML Parser | 686 lines | ⚠️ DEFER | N/A | **DEFER** |

**Note:** EPUB and HTML parsers are working production code from earlier phases. Defer their refactoring until after we've established patterns with the 4 newer parsers.

### Target Architecture Pattern

Each parser will follow this structure:

```
parsers/
  [format]/                    # Format-specific directory
    __init__.py                # Parser class (orchestrator, ~100 lines)
    extractor.py               # Content extraction (~150 lines)
    metadata.py                # Metadata parsing (~80 lines)
    chapter_detector.py        # Chapter detection (~120 lines)
    image_handler.py           # Image extraction (~100 lines) [if applicable]
    validator.py               # Input validation (~60 lines)
```

---

## 🧠 Context: Why This Refactoring?

### Background
The 4 new parsers (PDF, DOCX, Markdown, Text) were implemented in remote Claude Code sessions **without access to `FUNCTIONAL_PATTERNS.md`**. They work correctly but exceed maintainability guidelines:

**Functional Patterns Targets:**
- Functions: 15-30 lines (max 100 lines)
- Files: 50-200 lines per file
- No code repetition (DRY principle)
- Clear separation of concerns

**Current Problems:**
1. **Monolithic files:** Hard to navigate, understand, and modify
2. **Mixed concerns:** Validation, extraction, conversion, formatting in same functions
3. **Difficult testing:** Large functions hard to unit test in isolation
4. **Code duplication:** Similar logic repeated across parsers (metadata building, image extraction)

### Strategy
- **Incremental:** Refactor one parser at a time (PDF → DOCX → Markdown → Text)
- **Test-driven:** Run tests after each module extraction to catch regressions
- **Pattern-first:** Establish clear patterns with PDF parser, then apply consistently
- **Commit-heavy:** Atomic commits after each module extraction for easy rollback

---

## 📋 Execution Plan: Phase-by-Phase

### Phase 0: Pre-Flight Checks (30 minutes)

**Goal:** Ensure clean starting state and understand current codebase

#### Task 0.1: Environment Verification
```bash
# Verify UV environment works
uv run python --version
uv run pytest --version

# Verify tests can run
uv run pytest --collect-only

# Check current test status
uv run pytest -x --tb=short
```

**Expected Output:**
- Python 3.10+
- 880 tests collected
- Report current pass/fail status

#### Task 0.2: Baseline Measurement
```bash
# Create baseline metrics
wc -l src/omniparser/parsers/*.py > docs/refactoring-baseline.txt

# Run full test suite with coverage
uv run pytest --cov=omniparser --cov-report=html --cov-report=term

# Document baseline coverage
echo "Baseline Coverage: [percentage]%" >> docs/refactoring-baseline.txt
```

**Commit:** `docs: Add refactoring baseline metrics`

#### Task 0.3: Create Backup Branch
```bash
# Create backup branch in case rollback needed
git checkout -b backup/pre-refactoring-$(date +%Y%m%d)
git push origin backup/pre-refactoring-$(date +%Y%m%d)

# Return to main branch
git checkout main
```

**Success Criteria:** ✅ Clean environment, tests running, baseline documented, backup created

---

### Phase 1: PDF Parser Refactoring (4-5 hours)

**Target:** `src/omniparser/parsers/pdf_parser.py` (1,052 lines → 6 modules)

#### Why Start with PDF?
- Largest parser (most to gain)
- Complex logic (multi-column detection, image extraction, tables)
- Good test coverage already exists
- Will establish patterns for others to follow

#### Task 1.1: Analysis & Planning (30 minutes)

**Use `house-research` subagent to analyze current structure:**

```
TASK: Analyze pdf_parser.py structure and create refactoring plan

Read: src/omniparser/parsers/pdf_parser.py (1,052 lines)

Identify:
1. Main PDFParser class (line ranges)
2. All methods with line counts
3. Helper functions and utilities
4. Import dependencies
5. Logical groupings (metadata, text extraction, images, chapters, validation)

Create: docs/refactoring/pdf-parser-analysis.md with:
- Method inventory (name, lines, purpose)
- Proposed module breakdown
- Dependency map
- Extraction order (which modules first)

Report back summary only (not full file content).
```

**Expected Output:** Analysis document showing clear module boundaries

#### Task 1.2: Create Module Structure (15 minutes)

```bash
# Create new directory structure
mkdir -p src/omniparser/parsers/pdf

# Create module files
touch src/omniparser/parsers/pdf/__init__.py
touch src/omniparser/parsers/pdf/extractor.py
touch src/omniparser/parsers/pdf/metadata.py
touch src/omniparser/parsers/pdf/chapter_detector.py
touch src/omniparser/parsers/pdf/image_handler.py
touch src/omniparser/parsers/pdf/validator.py
```

**Commit:** `refactor(pdf): Create modular directory structure for PDF parser`

#### Task 1.3: Extract Validation Module (30 minutes)

**Use `house-coder` subagent:**

```
TASK: Extract validation logic from pdf_parser.py to pdf/validator.py

Read: src/omniparser/parsers/pdf_parser.py
Focus on: Input validation, file existence checks, format verification

Create: src/omniparser/parsers/pdf/validator.py (~60 lines)

Include:
- validate_pdf_file(file_path: Path) -> Path
- check_pdf_corruption(file_path: Path) -> bool
- Any PDF-specific validation helpers

Follow: PATTERNS_QUICK_REF.md guidelines
- Functions 15-30 lines
- Type hints on all functions
- Comprehensive docstrings

After creation:
1. Update pdf_parser.py to import from validator
2. Run: uv run black src/omniparser/parsers/pdf/
3. Run: uv run pytest tests/ -k pdf -x
4. Commit: "refactor(pdf): Extract validation logic to validator module"
```

**Success Criteria:** ✅ validator.py created, tests pass, atomic commit

#### Task 1.4: Extract Metadata Module (45 minutes)

**Use `house-coder` subagent:**

```
TASK: Extract metadata extraction from pdf_parser.py to pdf/metadata.py

Read: src/omniparser/parsers/pdf_parser.py
Focus on: PDF metadata extraction, property parsing, author/title extraction

Create: src/omniparser/parsers/pdf/metadata.py (~80-100 lines)

Include:
- extract_pdf_metadata(doc: fitz.Document, file_path: Path) -> Metadata
- extract_pdf_info(doc: fitz.Document) -> Dict[str, Any]
- parse_pdf_dates(date_str: str) -> str
- build_metadata(info: Dict, defaults: Dict) -> Metadata

Follow functional patterns:
- Small, focused functions
- Use comprehensions where applicable
- Clear type hints

After creation:
1. Update pdf_parser.py imports
2. Format: uv run black src/omniparser/parsers/pdf/
3. Test: uv run pytest tests/unit/test_pdf_parser.py tests/integration/test_pdf_parser.py -x
4. Commit: "refactor(pdf): Extract metadata extraction to metadata module"
```

**Success Criteria:** ✅ metadata.py created, tests pass, atomic commit

#### Task 1.5: Extract Image Handling Module (60 minutes)

**Use `house-coder` subagent:**

```
TASK: Extract image handling from pdf_parser.py to pdf/image_handler.py

Read: src/omniparser/parsers/pdf_parser.py
Focus on: Image extraction, image conversion, image saving logic

Create: src/omniparser/parsers/pdf/image_handler.py (~100-120 lines)

Include:
- extract_pdf_images(doc: fitz.Document, output_dir: Path) -> List[ImageReference]
- extract_image_from_page(page: fitz.Page, img_index: int) -> Optional[bytes]
- convert_image_to_format(image_bytes: bytes, target_format: str) -> bytes
- save_pdf_image(image_data: bytes, output_dir: Path, image_id: str) -> ImageReference

Consider extracting to shared processor:
- If logic is generic (not PDF-specific), create src/omniparser/processors/image_utils.py
- Make PDF module use shared utilities

After creation:
1. Update pdf_parser.py imports
2. Format: uv run black src/omniparser/parsers/pdf/
3. Test: uv run pytest tests/ -k "pdf and image" -x
4. Commit: "refactor(pdf): Extract image handling to image_handler module"
```

**Success Criteria:** ✅ image_handler.py created, tests pass, atomic commit

#### Task 1.6: Extract Content Extraction Module (60 minutes)

**Use `house-coder` subagent:**

```
TASK: Extract text extraction from pdf_parser.py to pdf/extractor.py

Read: src/omniparser/parsers/pdf_parser.py
Focus on: Text extraction, page processing, multi-column detection, table handling

Create: src/omniparser/parsers/pdf/extractor.py (~150-180 lines)

Include:
- extract_pdf_content(doc: fitz.Document) -> Tuple[str, List[str]]
- extract_page_text(page: fitz.Page) -> str
- detect_multi_column(page: fitz.Page) -> bool
- extract_columns(page: fitz.Page) -> List[str]
- extract_tables(page: fitz.Page) -> List[str]

Follow patterns:
- Break complex logic into small helpers
- Use comprehensions for page iteration
- Clear separation between detection and extraction

After creation:
1. Update pdf_parser.py imports
2. Format: uv run black src/omniparser/parsers/pdf/
3. Test: uv run pytest tests/unit/test_pdf_parser.py -x
4. Commit: "refactor(pdf): Extract content extraction to extractor module"
```

**Success Criteria:** ✅ extractor.py created, tests pass, atomic commit

#### Task 1.7: Extract Chapter Detection Module (45 minutes)

**Use `house-coder` subagent:**

```
TASK: Extract chapter detection from pdf_parser.py to pdf/chapter_detector.py

Read: src/omniparser/parsers/pdf_parser.py
Focus on: Chapter detection logic, heading identification, section splitting

Create: src/omniparser/parsers/pdf/chapter_detector.py (~120 lines)

Check if logic can use shared processor:
- Read: src/omniparser/processors/chapter_detector.py
- If shared logic exists, use it
- If PDF-specific logic needed, create PDF-specific module

Include:
- detect_pdf_chapters(pages: List[str], metadata: Metadata) -> List[Chapter]
- identify_chapter_headings(text: str) -> List[Tuple[int, str]]
- split_into_chapters(text: str, headings: List) -> List[Chapter]

After creation:
1. Update pdf_parser.py imports
2. Format: uv run black src/omniparser/parsers/pdf/
3. Test: uv run pytest tests/ -k "pdf and chapter" -x
4. Commit: "refactor(pdf): Extract chapter detection to chapter_detector module"
```

**Success Criteria:** ✅ chapter_detector.py created, tests pass, atomic commit

#### Task 1.8: Refactor Main Parser Class (45 minutes)

**Use `house-coder` subagent:**

```
TASK: Refactor PDFParser class to orchestrate extracted modules

Read: src/omniparser/parsers/pdf_parser.py (should be much shorter now)

Create: src/omniparser/parsers/pdf/__init__.py (~100-120 lines)

Structure:
```python
from pathlib import Path
from typing import Optional

from ...base.base_parser import BaseParser
from ...models import Document
from .validator import validate_pdf_file
from .metadata import extract_pdf_metadata
from .extractor import extract_pdf_content
from .chapter_detector import detect_pdf_chapters
from .image_handler import extract_pdf_images

class PDFParser(BaseParser):
    \"\"\"Parser for PDF files using PyMuPDF.\"\"\"

    def parse(self, file_path: Path, output_dir: Optional[Path] = None) -> Document:
        \"\"\"
        Parse PDF file into structured Document.

        High-level orchestration only - delegates to specialized modules.
        \"\"\"
        # Validate
        validate_pdf_file(file_path)

        # Load
        doc = self._load_pdf(file_path)

        # Extract components
        metadata = extract_pdf_metadata(doc, file_path)
        content, pages = extract_pdf_content(doc)
        chapters = detect_pdf_chapters(pages, metadata)
        images = extract_pdf_images(doc, output_dir) if output_dir else []

        # Assemble
        return self._build_document(metadata, chapters, images, content)
```

After creation:
1. Delete old pdf_parser.py
2. Update src/omniparser/parsers/__init__.py imports
3. Format: uv run black src/omniparser/parsers/pdf/
4. Run full test suite: uv run pytest tests/ -x
5. Verify no regressions
6. Commit: "refactor(pdf): Complete PDF parser modularization"
```

**Success Criteria:** ✅ PDFParser refactored, all tests pass, clean architecture

#### Task 1.9: Update Tests & Documentation (30 minutes)

**Use `general-purpose` subagent:**

```
TASK: Update tests and documentation for refactored PDF parser

Actions:
1. Review tests/unit/test_pdf_parser.py
   - Add tests for new modules if needed
   - Update imports
   - Verify coverage

2. Review tests/integration/test_pdf_parser.py
   - Verify end-to-end tests still pass
   - Add integration tests for edge cases

3. Update documentation:
   - Update docs/parsers.md (if exists)
   - Add module docstrings
   - Update inline comments

4. Run coverage check:
   uv run pytest --cov=omniparser.parsers.pdf --cov-report=term

5. Commit: "test(pdf): Update tests and docs for modular PDF parser"
```

**Success Criteria:** ✅ Tests updated, coverage maintained, documentation current

#### Task 1.10: Phase 1 Validation (15 minutes)

**Use `house-bash` subagent:**

```
TASK: Validate PDF parser refactoring completion

Run comprehensive validation:

1. Line counts:
   wc -l src/omniparser/parsers/pdf/*.py

2. Test status:
   uv run pytest tests/ -k pdf -v

3. Coverage:
   uv run pytest --cov=omniparser.parsers.pdf --cov-report=term

4. Integration test with real PDF:
   uv run python -c "
   from omniparser import parse_document
   from pathlib import Path
   doc = parse_document(Path('tests/fixtures/pdf/simple.pdf'))
   print(f'✓ Parsed: {doc.metadata.title}')
   print(f'✓ Chapters: {len(doc.chapters)}')
   print(f'✓ Images: {len(doc.images)}')
   "

Report:
- All module files ≤200 lines? YES/NO
- All tests passing? X/Y tests
- Coverage percentage: Z%
- Integration test: PASS/FAIL
- Ready for Phase 2? YES/NO
```

**Success Criteria:** ✅ All validation checks pass, ready to proceed

---

### Phase 2: DOCX Parser Refactoring (3-4 hours)

**Target:** `src/omniparser/parsers/docx_parser.py` (755 lines → 5 modules)

**Strategy:** Apply patterns learned from PDF parser

#### Module Breakdown:
1. `docx/validator.py` (~60 lines) - DOCX validation
2. `docx/metadata.py` (~80 lines) - Document properties extraction
3. `docx/extractor.py` (~150 lines) - Paragraph and text extraction
4. `docx/table_handler.py` (~120 lines) - Table extraction and formatting
5. `docx/image_handler.py` (~100 lines) - Image extraction (may share with PDF)
6. `docx/__init__.py` (~100 lines) - DOCXParser orchestrator

#### Task 2.1: Analysis & Planning (20 minutes)
```
Use house-research to analyze docx_parser.py structure
Create docs/refactoring/docx-parser-analysis.md
Identify shared logic with PDF parser
```

#### Task 2.2-2.8: Extract Modules (2.5 hours)
Follow same pattern as PDF parser:
- Extract validator → commit
- Extract metadata → commit
- Extract table_handler → commit
- Extract image_handler (reuse PDF logic) → commit
- Extract extractor → commit
- Refactor main class → commit
- Update tests → commit

#### Task 2.9: Beta Features Completion (1 hour)

**Bonus objective:** While refactoring, complete beta features

```
TASK: Implement list and hyperlink extraction during refactoring

In docx/extractor.py, add:
- extract_lists(para: Paragraph) -> List[str]
- extract_hyperlinks(para: Paragraph) -> List[Tuple[str, str]]

Update DOCXParser to use new functionality
Update tests to cover new features
Update README to change DOCX from Beta to Production-Ready

Commit: "feat(docx): Add list and hyperlink extraction, promote to production"
```

#### Task 2.10: Phase 2 Validation (15 minutes)
Same validation checklist as Phase 1

---

### Phase 3: Markdown Parser Refactoring (2-3 hours)

**Target:** `src/omniparser/parsers/markdown_parser.py` (741 lines → 4 modules)

#### Module Breakdown:
1. `markdown/validator.py` (~60 lines) - File validation
2. `markdown/frontmatter.py` (~100 lines) - YAML frontmatter parsing
3. `markdown/content_parser.py` (~150 lines) - Markdown content processing
4. `markdown/chapter_detector.py` (~120 lines) - Heading-based chapter detection
5. `markdown/__init__.py` (~100 lines) - MarkdownParser orchestrator

Follow same extraction pattern: analyze → extract modules → refactor → test → validate

---

### Phase 4: Text Parser Refactoring (2 hours)

**Target:** `src/omniparser/parsers/text_parser.py` (580 lines → 4 modules)

#### Module Breakdown:
1. `text/validator.py` (~60 lines) - File validation
2. `text/encoding_detector.py` (~100 lines) - Encoding detection and normalization
3. `text/chapter_detector.py` (~120 lines) - Pattern-based chapter detection
4. `text/cleaner.py` (~100 lines) - Text cleaning and normalization
5. `text/__init__.py` (~100 lines) - TextParser orchestrator

Follow same extraction pattern: analyze → extract modules → refactor → test → validate

---

### Phase 5: Shared Processors Extraction (2 hours)

**Goal:** Extract common logic to `src/omniparser/processors/`

#### Task 5.1: Image Utilities (45 minutes)

```
TASK: Create shared image processing utilities

Analyze image handling across PDF, DOCX, HTML parsers
Extract common patterns to processors/image_utils.py

Include:
- save_image(image_data: bytes, output_dir: Path, name: str) -> ImageReference
- validate_image_format(data: bytes) -> str
- resize_image_if_needed(data: bytes, max_size: int) -> bytes

Update all parsers to use shared utilities
Commit: "refactor: Extract shared image utilities to processors"
```

#### Task 5.2: Metadata Builder (30 minutes)

```
TASK: Create shared metadata builder

Extract common metadata building logic to processors/metadata_utils.py

Include:
- build_metadata(**kwargs) -> Metadata (with sensible defaults)
- normalize_author(author: str) -> str
- parse_date(date_str: str) -> str

Update all parsers to use MetadataBuilder
Commit: "refactor: Extract shared metadata builder to processors"
```

#### Task 5.3: Chapter Detection Utilities (45 minutes)

```
TASK: Enhance shared chapter detection

Review processors/chapter_detector.py
Add any patterns found in PDF/DOCX/Markdown/Text
Ensure all parsers use consistent chapter detection

Commit: "refactor: Enhance shared chapter detection utilities"
```

---

### Phase 6: Testing & Validation (2 hours)

#### Task 6.1: Comprehensive Test Suite Run

```bash
# Full test suite
uv run pytest -v --tb=short

# Coverage report
uv run pytest --cov=omniparser --cov-report=html --cov-report=term

# Test all parsers with fixtures
for format in epub html pdf docx markdown text; do
  echo "Testing $format parser..."
  uv run pytest tests/ -k $format -v
done
```

#### Task 6.2: Integration Testing

```bash
# Test each parser with real files
uv run python -c "
from omniparser import parse_document
from pathlib import Path

formats = [
    'tests/fixtures/epub/simple.epub',
    'tests/fixtures/pdf/simple.pdf',
    'tests/fixtures/docx/simple.docx',
    'tests/fixtures/markdown/simple.md',
    'tests/fixtures/text/simple.txt'
]

for file_path in formats:
    doc = parse_document(Path(file_path))
    print(f'✓ {file_path}: {len(doc.chapters)} chapters')
"
```

#### Task 6.3: Performance Benchmarking

```bash
# Compare performance before/after refactoring
uv run python scripts/benchmark_parsers.py

# Expected result: No regression >20%
```

#### Task 6.4: Documentation Updates

```
Update docs:
- README.md - Update parser status table
- docs/ARCHITECTURE_PLAN.md - Update with new structure
- docs/REFACTORING-PARSERS.md - Mark as complete
- CHANGELOG.md - Document refactoring

Commit: "docs: Update documentation after parser refactoring"
```

---

### Phase 7: Final Cleanup & Release (1 hour)

#### Task 7.1: Code Quality Checks

```bash
# Format all code
uv run black .

# Type checking
uv run mypy src/omniparser/

# Lint check (if configured)
uv run ruff check src/omniparser/
```

#### Task 7.2: Git History Review

```bash
# Review all refactoring commits
git log --oneline --since="[start-date]" --graph

# Verify commit message format
git log --since="[start-date]" --pretty=format:"%h %s" | grep -E "^[a-f0-9]+ (feat|fix|refactor|test|docs|chore):"

# Check for any uncommitted changes
git status
```

#### Task 7.3: Create Summary Report

```
Create: docs/refactoring-completion-report.md

Include:
- Start and end timestamps
- Total time spent
- Number of commits created
- Lines of code metrics (before/after)
- Test coverage (before/after)
- Performance comparison
- Lessons learned
- Recommendations for future refactoring

Commit: "docs: Add refactoring completion report"
```

#### Task 7.4: Version Bump (Optional)

```
If releasing as v0.4.0:
- Update pyproject.toml version
- Update __init__.py __version__
- Update CHANGELOG.md
- Create git tag

Commit: "chore: Bump version to 0.4.0 for refactored release"
```

---

## 🛠️ Subagent Usage Strategy

### When to Use Which Subagent

| Task Type | Subagent | Model | Why |
|-----------|----------|-------|-----|
| Code analysis | `house-research` | Default | Searches across multiple files without context bloat |
| Command execution | `house-bash` | Default | Handles long outputs efficiently |
| Code extraction | `house-coder` | Default | Focused surgical code changes |
| Planning | `general-purpose` | `sonnet` | Requires reasoning and architecture design |
| Quick fixes | `quick-code-patch` | `haiku` | Fast, simple modifications |

### Context Management

**Minimize context per subagent:**
- ✅ Reference files by path (let subagent read)
- ✅ Provide specific requirements
- ✅ Include commit message template
- ❌ Don't paste entire file contents
- ❌ Don't include irrelevant history

**Target: <5000 tokens per subagent prompt**

### Commit Strategy

**Every subagent MUST commit before completing:**
1. Complete task
2. Review changes: `git diff`
3. Format code: `uv run black .`
4. Run tests: `uv run pytest -x`
5. Stage: `git add .`
6. Commit: `git commit -m "<type>: <description>"`
7. Report commit hash

**Commit types:**
- `refactor:` - Code restructuring without functionality changes
- `test:` - Test updates
- `docs:` - Documentation only
- `feat:` - New functionality (e.g., DOCX lists)
- `fix:` - Bug fixes found during refactoring

---

## 📊 Success Metrics & Validation

### Code Metrics

**Before Refactoring:**
```
PDF Parser:     1,052 lines
DOCX Parser:      755 lines
Markdown Parser:  741 lines
Text Parser:      580 lines
Total:          3,128 lines (4 monolithic files)
```

**After Refactoring Target:**
```
PDF Parser:     ~700 lines (6 modules × ~120 lines)
DOCX Parser:    ~580 lines (5 modules × ~115 lines)
Markdown Parser:~520 lines (4 modules × ~130 lines)
Text Parser:    ~400 lines (4 modules × ~100 lines)
Total:        ~2,200 lines (19 modules + 4 orchestrators)
```

**Metrics to Track:**
- [ ] All modules 50-200 lines ✅
- [ ] All functions <100 lines ✅
- [ ] Test coverage maintained or improved ✅
- [ ] No performance regression >20% ✅
- [ ] All tests passing ✅

### Test Validation

**Current Test Status:** 830/880 tests passing (94.3%)

**Post-Refactoring Targets:**
- [ ] ≥880 tests passing (100% of current passing tests)
- [ ] Coverage ≥80% (current baseline)
- [ ] All parser integration tests pass
- [ ] No test execution time regression >20%

### Quality Checks

**Code Quality:**
- [ ] `uv run black .` - No formatting changes needed
- [ ] `uv run mypy src/` - No type errors
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No duplicate code blocks >5 lines

**Git Quality:**
- [ ] All commits follow conventional commit format
- [ ] Each commit is atomic (single logical change)
- [ ] No merge conflicts
- [ ] Clean git history

---

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Tests Fail After Module Extraction

**Symptoms:** Tests pass individually but fail after extraction

**Debug Steps:**
```bash
# Check imports
uv run python -c "from omniparser.parsers.pdf import PDFParser"

# Check specific test
uv run pytest tests/unit/test_pdf_parser.py::test_specific_function -vv

# Check if circular imports
uv run python -c "import sys; sys.path.insert(0, 'src'); import omniparser"
```

**Solutions:**
- Check for circular imports between modules
- Verify all imports updated in main parser class
- Check if helper functions properly exported
- Run single test file to isolate issue

#### Issue 2: Performance Regression

**Symptoms:** Tests take significantly longer after refactoring

**Debug Steps:**
```bash
# Profile specific parser
uv run python -m cProfile -s cumtime -c "
from omniparser import parse_document
from pathlib import Path
doc = parse_document(Path('tests/fixtures/pdf/large.pdf'))
"
```

**Solutions:**
- Check for unnecessary re-computation (caching needed?)
- Verify no redundant file reads
- Check if lazy loading broken
- Profile before/after with same file

#### Issue 3: Module Import Errors

**Symptoms:** `ModuleNotFoundError` or `ImportError`

**Solutions:**
```python
# Ensure __init__.py exists in all directories
touch src/omniparser/parsers/pdf/__init__.py

# Verify relative imports correct
from ...base.base_parser import BaseParser  # Correct
from omniparser.base.base_parser import BaseParser  # Also correct
```

#### Issue 4: Context Overflow in Subagent

**Symptoms:** Subagent reports token limit exceeded

**Solutions:**
- Break task into smaller subtasks
- Use file paths instead of inline content
- Ask subagent to read files directly
- Reduce background context in prompt

#### Issue 5: Test Fixtures Not Found

**Symptoms:** Tests can't find fixture files after refactoring

**Solutions:**
```python
# Use Path resolution relative to test file
import pathlib
fixture_dir = pathlib.Path(__file__).parent.parent / "fixtures"

# Verify fixture paths
assert fixture_dir.exists()
```

---

## 📚 Key Reference Documents

**MUST READ before starting:**
1. **FUNCTIONAL_PATTERNS.md** - Comprehensive refactoring patterns guide
2. **PATTERNS_QUICK_REF.md** - Quick reference card (keep open while coding)
3. **ARCHITECTURE_PLAN.md** - Overall project architecture
4. **REFACTORING-PARSERS.md** - Original refactoring plan

**Reference during execution:**
- `CLAUDE.md` - Project-specific Claude Code guidelines
- `GIT_COMMIT_STYLE_GUIDE.md` - Commit message format
- `docs/IMPLEMENTATION_REFERENCE.md` - Implementation patterns

---

## 🎬 Session Initialization Checklist

**Before starting autonomous execution:**

### Pre-Flight Checklist
- [ ] Read all reference documents (FUNCTIONAL_PATTERNS.md, PATTERNS_QUICK_REF.md)
- [ ] Verify UV environment: `uv run python --version`
- [ ] Run baseline tests: `uv run pytest --collect-only`
- [ ] Create backup branch
- [ ] Document baseline metrics
- [ ] Review git status: `git status` (should be clean)

### Execution Mode Verification
- [ ] **YOLO mode enabled:** Auto-approve all tool uses
- [ ] **Subagent-first strategy:** Use subagents for every task
- [ ] **Atomic commits:** Commit after each module extraction
- [ ] **Test-driven:** Run tests after each change

### Expected Session Duration
- **Phase 1 (PDF):** 4-5 hours
- **Phase 2 (DOCX):** 3-4 hours
- **Phase 3 (Markdown):** 2-3 hours
- **Phase 4 (Text):** 2 hours
- **Phase 5 (Shared):** 2 hours
- **Phase 6 (Testing):** 2 hours
- **Phase 7 (Cleanup):** 1 hour

**Total Estimated Time:** 16-21 hours of autonomous execution

### Success Criteria
- [ ] All parser files ≤200 lines
- [ ] All modules 50-200 lines
- [ ] ≥880 tests passing (100% of baseline)
- [ ] No performance regression >20%
- [ ] Clean git history with conventional commits
- [ ] Documentation updated
- [ ] Ready for v0.4.0 release

---

## 🚀 Execution Commands

### Starting the Session

**Copy this entire guide and provide to Claude Code:**

```
You are an autonomous Claude Code agent tasked with refactoring OmniParser parsers.

INSTRUCTIONS:
1. Read this entire document (CLAUDE_CODE_REFACTORING_GUIDE.md)
2. Read FUNCTIONAL_PATTERNS.md and PATTERNS_QUICK_REF.md
3. Execute Phase 0: Pre-Flight Checks
4. Execute Phase 1: PDF Parser Refactoring
5. Execute Phase 2: DOCX Parser Refactoring
6. Execute Phase 3: Markdown Parser Refactoring
7. Execute Phase 4: Text Parser Refactoring
8. Execute Phase 5: Shared Processors Extraction
9. Execute Phase 6: Testing & Validation
10. Execute Phase 7: Final Cleanup & Release

CRITICAL RULES:
- Use subagents for EVERY task (house-research, house-coder, house-bash, general-purpose)
- Commit after EVERY module extraction (atomic commits)
- Run tests after EVERY change (pytest)
- Follow FUNCTIONAL_PATTERNS.md guidelines strictly
- No files >200 lines, no functions >100 lines
- Update TODOS.md after each phase
- Report progress after each phase completion

EXECUTION MODE: YOLO (auto-approve all actions)

Begin execution. Report after each phase completion with:
- Phase name
- Tasks completed
- Test status
- Commits created
- Ready to proceed to next phase: YES/NO
```

---

## 📝 Final Notes

### Remember
- **Incremental progress:** One module at a time, one test at a time
- **Always test:** Never commit without running tests
- **Document decisions:** Update docs as you go, not at the end
- **Ask for help:** If stuck for >30 minutes, pause and report status

### After Completion
- Merge backup branch can be deleted
- Create GitHub release for v0.4.0
- Update project README with refactoring achievement
- Share learnings in team documentation

---

**Ready for autonomous execution! 🚀**

**Document Version:** 1.0
**Last Updated:** 2025-10-29
**Session Type:** YOLO (Auto-approve)
**Strategy:** Subagent-First Development with Atomic Commits
