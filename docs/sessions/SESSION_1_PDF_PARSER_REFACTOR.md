# Session 1: PDF Parser Refactoring

**Copy this entire prompt into a new Claude Code session**

---

## 📋 Session Metadata

| Field | Value |
|-------|-------|
| **Session ID** | SESSION_1_PDF |
| **Project** | OmniParser |
| **Branch Name** | `refactor/pdf-parser-modular` |
| **PR Title** | `refactor(pdf): Modularize PDF parser into functional components` |
| **Estimated Duration** | 4-5 hours |
| **Prerequisites** | None |
| **Target Lines** | 1,052 → ~600 (6 modules × ~100 lines) |
| **Deliverable** | Modular PDF parser with all tests passing |

---

## 🎯 Mission

Refactor `src/omniparser/parsers/pdf_parser.py` (1,052 lines) into modular components (50-200 lines per file) following functional patterns in `FUNCTIONAL_PATTERNS.md` and `PATTERNS_QUICK_REF.md`.

## 📋 Context

You are working in the OmniParser project at `/Users/mini/Documents/GitHub/OmniParser`.

**Current state:**
- PDF parser: 1,052 lines (monolithic)
- Target: 6-7 modules × ~150 lines each
- Test status: 872/923 tests passing (30 failures unrelated to PDF)
- Tests to maintain: All PDF-specific tests must pass after refactoring

**Key documents to read:**
1. `PATTERNS_QUICK_REF.md` - Quick reference (KEEP OPEN while coding)
2. `FUNCTIONAL_PATTERNS.md` - Detailed patterns
3. `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` - Full refactoring guide

## 🎯 Success Criteria

- ✅ All PDF parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ All PDF tests pass (`uv run pytest tests/ -k pdf`)
- ✅ No performance regression >20%
- ✅ Follow functional patterns (functions 15-30 lines, max 100)
- ✅ Atomic commits after each module extraction
- ✅ Continuous progress reports

## 📐 Target Architecture

```
src/omniparser/parsers/
  pdf/
    __init__.py          # PDFParser class (orchestrator, ~100 lines)
    validator.py         # Input validation (~60 lines)
    metadata.py          # Metadata extraction (~80 lines)
    extractor.py         # Text extraction, multi-column (~150 lines)
    image_handler.py     # Image extraction (~100 lines)
    chapter_detector.py  # Chapter detection (~120 lines)
```

## 🚀 Execution Plan

### Phase 0: Pre-Flight (15 minutes)

1. **Read documentation:**
   - Read `PATTERNS_QUICK_REF.md` (keep open)
   - Read `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` (Phase 1 section)

2. **Create feature branch:**
   ```bash
   cd /Users/mini/Documents/GitHub/OmniParser
   git checkout main
   git pull origin main
   git checkout -b refactor/pdf-parser-modular
   git push -u origin refactor/pdf-parser-modular
   ```

3. **Check environment:**
   ```bash
   uv run pytest --version
   uv run pytest tests/ -k pdf --collect-only
   ```

4. **Baseline measurement:**
   ```bash
   wc -l src/omniparser/parsers/pdf_parser.py
   uv run pytest tests/ -k pdf -v --tb=short
   ```

### Phase 1: Analysis (30 minutes)

**Use `house-research` subagent:**

Analyze `src/omniparser/parsers/pdf_parser.py`:
- Identify all methods and their line counts
- Identify logical groupings (validation, metadata, extraction, images, chapters)
- Create module breakdown plan
- Document dependencies between components

**Create:** `docs/refactoring/pdf-analysis.md` with findings

**Commit:**
```bash
git add docs/refactoring/pdf-analysis.md
git commit -m "docs: Add PDF parser analysis for refactoring"
git push origin refactor/pdf-parser-modular
```

### Phase 2: Create Structure (10 minutes)

```bash
mkdir -p src/omniparser/parsers/pdf
touch src/omniparser/parsers/pdf/__init__.py
touch src/omniparser/parsers/pdf/validator.py
touch src/omniparser/parsers/pdf/metadata.py
touch src/omniparser/parsers/pdf/extractor.py
touch src/omniparser/parsers/pdf/image_handler.py
touch src/omniparser/parsers/pdf/chapter_detector.py
```

**Commit:**
```bash
git add src/omniparser/parsers/pdf/
git commit -m "refactor(pdf): Create modular directory structure"
git push origin refactor/pdf-parser-modular
```

### Phase 3: Extract Modules (3-4 hours)

**For EACH module, use `house-coder` subagent:**

#### Step 1: Extract Validation (~30 min)
- Create `pdf/validator.py`
- Extract validation logic from pdf_parser.py
- Functions: `validate_pdf_file()`, `check_pdf_corruption()`
- Update imports in pdf_parser.py
- Run tests: `uv run pytest tests/ -k pdf -x`
- Format: `uv run black src/omniparser/parsers/pdf/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/pdf/validator.py src/omniparser/parsers/pdf_parser.py
  git commit -m "refactor(pdf): Extract validation to validator module"
  git push origin refactor/pdf-parser-modular
  ```

#### Step 2: Extract Metadata (~45 min)
- Create `pdf/metadata.py`
- Extract metadata extraction logic
- Functions: `extract_pdf_metadata()`, `parse_pdf_dates()`, `build_metadata()`
- Update imports
- Run tests: `uv run pytest tests/ -k pdf -x`
- Format: `uv run black src/omniparser/parsers/pdf/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/pdf/
  git commit -m "refactor(pdf): Extract metadata extraction to metadata module"
  git push origin refactor/pdf-parser-modular
  ```

#### Step 3: Extract Image Handling (~60 min)
- Create `pdf/image_handler.py`
- Extract image extraction logic
- Functions: `extract_pdf_images()`, `convert_image()`, `save_pdf_image()`
- Consider using shared `src/omniparser/processors/image_utils.py` if exists
- Update imports
- Run tests: `uv run pytest tests/ -k "pdf and image" -x`
- Format: `uv run black src/omniparser/parsers/pdf/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/pdf/
  git commit -m "refactor(pdf): Extract image handling to image_handler module"
  git push origin refactor/pdf-parser-modular
  ```

#### Step 4: Extract Content Extraction (~60 min)
- Create `pdf/extractor.py`
- Extract text extraction, multi-column detection, table handling
- Functions: `extract_pdf_content()`, `extract_page_text()`, `detect_multi_column()`, `extract_columns()`
- Update imports
- Run tests: `uv run pytest tests/unit/test_pdf_parser.py -x`
- Format: `uv run black src/omniparser/parsers/pdf/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/pdf/
  git commit -m "refactor(pdf): Extract content extraction to extractor module"
  git push origin refactor/pdf-parser-modular
  ```

#### Step 5: Extract Chapter Detection (~45 min)
- Create `pdf/chapter_detector.py`
- Extract chapter detection logic
- Check if can use shared `src/omniparser/processors/chapter_detector.py`
- Functions: `detect_pdf_chapters()`, `identify_headings()`, `split_into_chapters()`
- Update imports
- Run tests: `uv run pytest tests/ -k "pdf and chapter" -x`
- Format: `uv run black src/omniparser/parsers/pdf/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/pdf/
  git commit -m "refactor(pdf): Extract chapter detection to chapter_detector module"
  git push origin refactor/pdf-parser-modular
  ```

#### Step 6: Refactor Main Parser (~45 min)
- Create `pdf/__init__.py` with PDFParser class
- Import all extracted modules
- Orchestrate calls to extracted functions
- Keep parse() method simple (~20 lines):
  ```python
  def parse(self, file_path: Path, output_dir: Optional[Path] = None) -> Document:
      validate_pdf_file(file_path)
      doc = self._load_pdf(file_path)
      metadata = extract_pdf_metadata(doc, file_path)
      content, pages = extract_pdf_content(doc)
      chapters = detect_pdf_chapters(pages, metadata)
      images = extract_pdf_images(doc, output_dir) if output_dir else []
      return self._build_document(metadata, chapters, images, content)
  ```
- Delete old `pdf_parser.py`
- Update `src/omniparser/parsers/__init__.py` imports
- Run ALL tests: `uv run pytest tests/ -k pdf -v`
- Format: `uv run black src/omniparser/parsers/pdf/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/
  git commit -m "refactor(pdf): Complete PDF parser modularization"
  git push origin refactor/pdf-parser-modular
  ```

### Phase 4: Validation (30 minutes)

1. **Line count check:**
   ```bash
   wc -l src/omniparser/parsers/pdf/*.py
   # All files should be ≤200 lines
   ```

2. **Test status:**
   ```bash
   uv run pytest tests/ -k pdf -v
   # All PDF tests should pass
   ```

3. **Integration test:**
   ```bash
   uv run python -c "
   from omniparser import parse_document
   from pathlib import Path
   doc = parse_document(Path('tests/fixtures/pdf/simple.pdf'))
   print(f'✓ Parsed: {doc.metadata.title}')
   print(f'✓ Chapters: {len(doc.chapters)}')
   print(f'✓ Images: {len(doc.images)}')
   "
   ```

4. **Update TODOS.md:**
   - Mark "Extract common patterns from PDF parser" as complete
   - Add Phase 2 (DOCX refactoring) tasks

**Commit:**
```bash
git add TODOS.md
git commit -m "docs: Update TODOS after PDF parser refactoring"
git push origin refactor/pdf-parser-modular
```

### Phase 5: Pull Request Creation (15 minutes)

1. **Create PR:**
   ```bash
   gh pr create \
     --title "refactor(pdf): Modularize PDF parser into functional components" \
     --body "$(cat <<'EOF'
## 🎯 Summary
Refactored PDF parser from monolithic 1,052-line file into modular architecture with 6 focused modules.

## 📊 Changes
- **Before:** 1 file, 1,052 lines
- **After:** 6 modules, ~600 total lines (43% reduction)
- **Modules:**
  - `validator.py` - Input validation (~60 lines)
  - `metadata.py` - Metadata extraction (~80 lines)
  - `extractor.py` - Text extraction, multi-column (~150 lines)
  - `image_handler.py` - Image extraction (~100 lines)
  - `chapter_detector.py` - Chapter detection (~120 lines)
  - `__init__.py` - PDFParser orchestrator (~100 lines)

## ✅ Testing
- [x] All PDF tests pass (uv run pytest tests/ -k pdf)
- [x] Integration tested with sample PDFs
- [x] No performance regression

## 📏 Code Quality
- [x] All functions ≤100 lines
- [x] All files ≤200 lines
- [x] Follows functional patterns (PATTERNS_QUICK_REF.md)
- [x] Black formatted
- [x] Type hints on all functions
- [x] Comprehensive docstrings

## 🔗 Related
- Part of parser refactoring initiative (Sessions 1-5)
- Follows patterns in FUNCTIONAL_PATTERNS.md
- Foundation for DOCX/Markdown/Text parser refactoring

## 📝 Checklist
- [x] Tests pass
- [x] Code formatted (Black)
- [x] Documentation updated
- [x] Ready for review

---
🤖 Generated with [Claude Code](https://claude.ai/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" \
     --base main \
     --head refactor/pdf-parser-modular
   ```

2. **Verify PR created:**
   ```bash
   gh pr view
   ```

### Phase 6: Report (15 minutes)

Create completion report with:
- Start/end times
- Files created (with line counts)
- Tests status (before/after)
- Commits created
- Performance comparison
- Ready for Phase 2: YES/NO

## ⚠️ Critical Rules

1. **Use subagents for EVERYTHING:**
   - `house-research` for analysis
   - `house-coder` for code extraction
   - `house-bash` for commands

2. **Commit after EVERY module extraction** (atomic commits)

3. **Run tests after EVERY change:**
   ```bash
   uv run pytest tests/ -k pdf -x  # Stop on first failure
   ```

4. **Follow functional patterns strictly:**
   - Functions: 15-30 lines (max 100)
   - Files: 50-200 lines
   - No code repetition
   - Type hints on everything
   - Comprehensive docstrings

5. **Format code before every commit:**
   ```bash
   uv run black src/omniparser/parsers/pdf/
   ```

6. **Report progress continuously:**
   - After each module extraction
   - Include test status
   - Include what's next

## 🚨 If Something Goes Wrong

### Tests Fail After Extraction

```bash
# Check imports
uv run python -c "from omniparser.parsers.pdf import PDFParser"

# Run single test with verbose output
uv run pytest tests/unit/test_pdf_parser.py::test_name -vv --tb=short

# Check for circular imports
uv run python -c "import sys; sys.path.insert(0, 'src'); import omniparser"
```

### Branch Issues

```bash
# Check current branch
git branch --show-current

# If on wrong branch, switch to feature branch
git checkout refactor/pdf-parser-modular

# If need to sync with main
git checkout main
git pull origin main
git checkout refactor/pdf-parser-modular
git merge main
```

### Module Too Large

Break it down further:
- Extract helper functions
- Use comprehensions instead of loops
- Split complex logic into multiple functions
- Each function should do ONE thing

### Can't Find What to Extract

Read the code section by section:
- What does this block do? → Name it
- Can it be a separate function? → Extract it
- Is it used elsewhere? → Make it shared
- Is it >30 lines? → Break it down

## 📚 Quick Reference

**Key Commands:**
```bash
# Run PDF tests
uv run pytest tests/ -k pdf -v

# Format code
uv run black src/omniparser/parsers/pdf/

# Check line counts
wc -l src/omniparser/parsers/pdf/*.py

# Test single file
uv run pytest tests/unit/test_pdf_parser.py -x

# Commit
git add . && git commit -m "refactor(pdf): <message>"
```

**Functional Patterns Checklist:**
- [ ] No function >100 lines
- [ ] No file >200 lines
- [ ] No repeated code blocks
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] Used comprehensions where possible

---

## 🏁 Start Execution

**You are now ready to begin!**

1. Read `PATTERNS_QUICK_REF.md` (1 minute)
2. Execute Phase 0: Pre-Flight (create feature branch!)
3. Execute Phase 1: Analysis
4. Execute Phase 2: Create Structure
5. Execute Phase 3: Extract Modules (one at a time!)
6. Execute Phase 4: Validation
7. Execute Phase 5: Pull Request Creation
8. Execute Phase 6: Report

**EXECUTION MODE:** YOLO (auto-approve all actions)

**Report after each module extraction with:**
- Module name
- Lines of code
- Test status
- Commit hash (from git log)
- What's next

**After all commits:** Create PR and share the URL!

**Let's go! 🚀**
