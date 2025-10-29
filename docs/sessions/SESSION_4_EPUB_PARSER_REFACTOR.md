# Session 4: EPUB Parser Refactoring

**Copy this entire prompt into a new Claude Code session**

---

## 📋 Session Metadata

| Field | Value |
|-------|-------|
| **Session ID** | SESSION_4_EPUB |
| **Project** | OmniParser |
| **Branch Name** | `refactor/epub-parser-modular` |
| **PR Title** | `refactor(epub): Modularize EPUB parser into functional components` |
| **Estimated Duration** | 5-6 hours |
| **Prerequisites** | Sessions 1-3 complete recommended |
| **Target Lines** | 1,053 → ~750 (7 modules × ~110 lines) |
| **Deliverable** | Modular EPUB parser with all tests passing |

---

## 🎯 Mission

Refactor `src/omniparser/parsers/epub_parser.py` (1,053 lines) into modular components (50-200 lines per file) following functional patterns in `FUNCTIONAL_PATTERNS.md` and `PATTERNS_QUICK_REF.md`.

## 📋 Context

You are working in the OmniParser project at `/Users/mini/Documents/GitHub/OmniParser`.

**Current state:**
- EPUB parser: 1,053 lines (monolithic, production-ready)
- Target: 7 modules × ~110 lines each
- Test status: All EPUB tests should pass
- Tests to maintain: All EPUB-specific tests must pass after refactoring

**Key documents to read:**
1. `PATTERNS_QUICK_REF.md` - Quick reference (KEEP OPEN while coding)
2. `FUNCTIONAL_PATTERNS.md` - Detailed patterns
3. `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` - Full refactoring guide
4. `src/omniparser/parsers/pdf/` - Reference successful refactoring

## 🎯 Success Criteria

- ✅ All EPUB parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ All EPUB tests pass (`uv run pytest tests/ -k epub`)
- ✅ No performance regression >20%
- ✅ Follow functional patterns (functions 15-30 lines, max 100)
- ✅ Atomic commits after each module extraction
- ✅ Continuous progress reports

## 📐 Target Architecture

```
src/omniparser/parsers/
  epub/
    __init__.py          # EPUBParser class (orchestrator, ~100 lines)
    validator.py         # Input validation (~60 lines)
    metadata.py          # Metadata extraction from OPF (~100 lines)
    toc_parser.py        # TOC parsing and navigation (~120 lines)
    content_extractor.py # HTML to Markdown, text extraction (~150 lines)
    image_handler.py     # Image extraction (~100 lines)
    chapter_builder.py   # Chapter building from TOC (~120 lines)
```

## 🚀 Execution Plan

### Phase 0: Pre-Flight (15 minutes)

1. **Read documentation:**
   - Read `PATTERNS_QUICK_REF.md` (keep open)
   - Read `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` (Phase 1 section)
   - Review `src/omniparser/parsers/pdf/` for patterns

2. **Create feature branch:**
   ```bash
   cd /Users/mini/Documents/GitHub/OmniParser
   git checkout main
   git pull origin main
   git checkout -b refactor/epub-parser-modular
   git push -u origin refactor/epub-parser-modular
   ```

3. **Check environment:**
   ```bash
   uv run pytest --version
   uv run pytest tests/ -k epub --collect-only
   ```

4. **Baseline measurement:**
   ```bash
   wc -l src/omniparser/parsers/epub_parser.py
   uv run pytest tests/ -k epub -v --tb=short
   ```

### Phase 1: Analysis (30 minutes)

**Use `house-research` subagent:**

Analyze `src/omniparser/parsers/epub_parser.py`:
- Identify all methods and their line counts
- Identify logical groupings (validation, metadata, TOC, content, images, chapters)
- Create module breakdown plan
- Document dependencies between components
- Note EbookLib usage patterns

**Create:** `docs/refactoring/epub-analysis.md` with findings

**Commit:**
```bash
git add docs/refactoring/epub-analysis.md
git commit -m "docs: Add EPUB parser analysis for refactoring"
git push origin refactor/epub-parser-modular
```

### Phase 2: Create Structure (10 minutes)

```bash
mkdir -p src/omniparser/parsers/epub
touch src/omniparser/parsers/epub/__init__.py
touch src/omniparser/parsers/epub/validator.py
touch src/omniparser/parsers/epub/metadata.py
touch src/omniparser/parsers/epub/toc_parser.py
touch src/omniparser/parsers/epub/content_extractor.py
touch src/omniparser/parsers/epub/image_handler.py
touch src/omniparser/parsers/epub/chapter_builder.py
```

**Commit:**
```bash
git add src/omniparser/parsers/epub/
git commit -m "refactor(epub): Create modular directory structure"
git push origin refactor/epub-parser-modular
```

### Phase 3: Extract Modules (4-5 hours)

**For EACH module, use `house-coder` subagent:**

**IMPORTANT:** Add `git push origin refactor/epub-parser-modular` after EVERY commit!

#### Step 1: Extract Validation (~30 min)
- Create `epub/validator.py`
- Extract EPUB validation logic
- Functions: `validate_epub_file()`, `check_epub_structure()`, `verify_mimetype()`
- Update imports in epub_parser.py
- Run tests: `uv run pytest tests/ -k epub -x`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/epub/validator.py src/omniparser/parsers/epub_parser.py
  git commit -m "refactor(epub): Extract validation to validator module"
  git push origin refactor/epub-parser-modular
  ```

#### Step 2: Extract Metadata (~45 min)
- Create `epub/metadata.py`
- Extract OPF (package document) metadata parsing
- Functions: `extract_epub_metadata()`, `parse_opf_metadata()`, `parse_dublin_core()`, `build_metadata()`
- Update imports
- Run tests: `uv run pytest tests/ -k epub -x`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/epub/
  git commit -m "refactor(epub): Extract metadata extraction to metadata module"
  git push origin refactor/epub-parser-modular
  ```

#### Step 3: Extract TOC Parser (~60 min)
- Create `epub/toc_parser.py`
- Extract TOC (Table of Contents) parsing logic
- Functions: `parse_toc()`, `extract_toc_items()`, `build_toc_tree()`, `flatten_toc()`
- Handle NCX and NAV document types
- Update imports
- Run tests: `uv run pytest tests/ -k "epub and toc" -x`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/epub/
  git commit -m "refactor(epub): Extract TOC parsing to toc_parser module"
  git push origin refactor/epub-parser-modular
  ```

#### Step 4: Extract Image Handling (~45 min)
- Create `epub/image_handler.py`
- Extract image extraction logic
- Functions: `extract_epub_images()`, `get_image_items()`, `save_epub_image()`, `convert_image_format()`
- Consider using shared `src/omniparser/processors/image_utils.py` if exists
- Update imports
- Run tests: `uv run pytest tests/ -k "epub and image" -x`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/epub/
  git commit -m "refactor(epub): Extract image handling to image_handler module"
  git push origin refactor/epub-parser-modular
  ```

#### Step 5: Extract Content Extraction (~75 min)
- Create `epub/content_extractor.py`
- Extract HTML to Markdown conversion, text extraction
- Functions: `extract_epub_content()`, `extract_item_text()`, `html_to_markdown()`, `clean_html()`
- Handle BeautifulSoup processing
- Update imports
- Run tests: `uv run pytest tests/unit/test_epub_parser.py -x`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/epub/
  git commit -m "refactor(epub): Extract content extraction to content_extractor module"
  git push origin refactor/epub-parser-modular
  ```

#### Step 6: Extract Chapter Builder (~60 min)
- Create `epub/chapter_builder.py`
- Extract chapter building from TOC items
- Functions: `build_chapters()`, `create_chapter_from_toc()`, `merge_chapter_content()`, `calculate_chapter_metrics()`
- Update imports
- Run tests: `uv run pytest tests/ -k "epub and chapter" -x`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/epub/
  git commit -m "refactor(epub): Extract chapter building to chapter_builder module"
  git push origin refactor/epub-parser-modular
  ```

#### Step 7: Refactor Main Parser (~60 min)
- Create `epub/__init__.py` with EPUBParser class
- Import all extracted modules
- Orchestrate calls to extracted functions
- Keep parse() method simple (~25 lines):
  ```python
  def parse(self, file_path: Path, output_dir: Optional[Path] = None) -> Document:
      validate_epub_file(file_path)
      book = epub.read_epub(str(file_path))
      metadata = extract_epub_metadata(book, file_path)
      toc_items = parse_toc(book)
      content_map = extract_epub_content(book)
      chapters = build_chapters(toc_items, content_map, metadata)
      images = extract_epub_images(book, output_dir) if output_dir else []
      return self._build_document(metadata, chapters, images)
  ```
- Delete old `epub_parser.py`
- Update `src/omniparser/parsers/__init__.py` imports
- Run ALL tests: `uv run pytest tests/ -k epub -v`
- Format: `uv run black src/omniparser/parsers/epub/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/
  git commit -m "refactor(epub): Complete EPUB parser modularization"
  git push origin refactor/epub-parser-modular
  ```

### Phase 4: Validation (30 minutes)

1. **Line count check:**
   ```bash
   wc -l src/omniparser/parsers/epub/*.py
   # All files should be ≤200 lines
   ```

2. **Test status:**
   ```bash
   uv run pytest tests/ -k epub -v
   # All EPUB tests should pass
   ```

3. **Integration test:**
   ```bash
   uv run python -c "
   from omniparser import parse_document
   from pathlib import Path
   doc = parse_document(Path('tests/fixtures/epub/simple.epub'))
   print(f'✓ Parsed: {doc.metadata.title}')
   print(f'✓ Chapters: {len(doc.chapters)}')
   print(f'✓ Images: {len(doc.images)}')
   "
   ```

4. **Update TODOS.md:**
   - Mark "Refactor EPUB parser" as complete
   - Note that 5/6 parsers now refactored

**Commit:**
```bash
git add TODOS.md
git commit -m "docs: Update TODOS after EPUB parser refactoring"
git push origin refactor/epub-parser-modular
```

### Phase 5: Pull Request Creation (15 minutes)

1. **Create PR:**
   ```bash
   gh pr create \
     --title "refactor(epub): Modularize EPUB parser into functional components" \
     --body "$(cat <<'EOF'
## 🎯 Summary
Refactored EPUB parser from monolithic 1,053-line file into modular architecture with 7 focused modules.

## 📊 Changes
- **Before:** 1 file, 1,053 lines
- **After:** 7 modules, ~750 total lines (29% reduction)
- **Modules:**
  - `validator.py` - EPUB validation (~60 lines)
  - `metadata.py` - OPF metadata extraction (~100 lines)
  - `toc_parser.py` - TOC parsing (NCX/NAV) (~120 lines)
  - `content_extractor.py` - HTML→Markdown conversion (~150 lines)
  - `image_handler.py` - Image extraction (~100 lines)
  - `chapter_builder.py` - Chapter building from TOC (~120 lines)
  - `__init__.py` - EPUBParser orchestrator (~100 lines)

## ✅ Testing
- [x] All EPUB tests pass (uv run pytest tests/ -k epub)
- [x] Integration tested with sample EPUBs
- [x] TOC-based chapter detection working
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
- Follows patterns from PDF/DOCX/Markdown/Text refactoring
- 5 of 6 parsers now modular

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
     --head refactor/epub-parser-modular
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
- Ready for Phase 5 (HTML refactoring): YES/NO

## ⚠️ Critical Rules

**IMPORTANT:** Add `git push origin refactor/epub-parser-modular` after EVERY `git commit` command throughout this session!

1. **Use subagents for EVERYTHING:**
   - `house-research` for analysis
   - `house-coder` for code extraction
   - `house-bash` for commands

2. **Commit after EVERY module extraction** (atomic commits and push!)

3. **Run tests after EVERY change:**
   ```bash
   uv run pytest tests/ -k epub -x  # Stop on first failure
   ```

4. **Follow functional patterns strictly:**
   - Functions: 15-30 lines (max 100)
   - Files: 50-200 lines
   - No code repetition
   - Type hints on everything
   - Comprehensive docstrings

5. **Format code before every commit:**
   ```bash
   uv run black src/omniparser/parsers/epub/
   ```

6. **Report progress continuously:**
   - After each module extraction
   - Include test status
   - Include what's next

## 🚨 If Something Goes Wrong

### Tests Fail After Extraction

```bash
# Check imports
uv run python -c "from omniparser.parsers.epub import EPUBParser"

# Run single test with verbose output
uv run pytest tests/unit/test_epub_parser.py::test_name -vv --tb=short

# Check for circular imports
uv run python -c "import sys; sys.path.insert(0, 'src'); import omniparser"
```

### Branch Issues

```bash
# Check current branch
git branch --show-current

# If on wrong branch, switch to feature branch
git checkout refactor/epub-parser-modular

# If need to sync with main
git checkout main
git pull origin main
git checkout refactor/epub-parser-modular
git merge main
```

### Module Too Large

Break it down further:
- Extract helper functions
- Use comprehensions instead of loops
- Split complex logic into multiple functions
- Each function should do ONE thing

### EbookLib Complexity

The EPUB parser uses EbookLib heavily:
- Read the EbookLib docs if needed
- Keep EbookLib calls isolated in specific functions
- Don't spread EbookLib usage across modules
- Document EbookLib patterns in module docstrings

## 📚 Quick Reference

**Key Commands:**
```bash
# Run EPUB tests
uv run pytest tests/ -k epub -v

# Format code
uv run black src/omniparser/parsers/epub/

# Check line counts
wc -l src/omniparser/parsers/epub/*.py

# Test single file
uv run pytest tests/unit/test_epub_parser.py -x

# Commit and push
git add . && git commit -m "refactor(epub): <message>" && git push origin refactor/epub-parser-modular
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
