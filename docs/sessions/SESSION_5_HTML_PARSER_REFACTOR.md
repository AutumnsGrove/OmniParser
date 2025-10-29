# Session 5: HTML Parser Refactoring

**Copy this entire prompt into a new Claude Code session**

---

## 📋 Session Metadata

| Field | Value |
|-------|-------|
| **Session ID** | SESSION_5_HTML |
| **Project** | OmniParser |
| **Branch Name** | `refactor/html-parser-modular` |
| **PR Title** | `refactor(html): Modularize HTML parser into functional components` |
| **Estimated Duration** | 4-5 hours |
| **Prerequisites** | Sessions 1-4 complete recommended |
| **Target Lines** | 686 → ~500 (5-6 modules × ~85 lines) |
| **Deliverable** | Modular HTML parser with all tests passing |

---

## 🎯 Mission

Refactor `src/omniparser/parsers/html_parser.py` (686 lines) into modular components (50-200 lines per file) following functional patterns in `FUNCTIONAL_PATTERNS.md` and `PATTERNS_QUICK_REF.md`.

## 📋 Context

You are working in the OmniParser project at `/Users/mini/Documents/GitHub/OmniParser`.

**Current state:**
- HTML parser: 686 lines (monolithic, production-ready)
- Target: 5-6 modules × ~85-100 lines each
- Test status: All HTML tests should pass
- Tests to maintain: All HTML-specific tests must pass after refactoring

**Key documents to read:**
1. `PATTERNS_QUICK_REF.md` - Quick reference (KEEP OPEN while coding)
2. `FUNCTIONAL_PATTERNS.md` - Detailed patterns
3. `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` - Full refactoring guide
4. `src/omniparser/parsers/pdf/` - Reference successful refactoring
5. `src/omniparser/parsers/epub/` - Reference recent refactoring

## 🎯 Success Criteria

- ✅ All HTML parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ All HTML tests pass (`uv run pytest tests/ -k html`)
- ✅ No performance regression >20%
- ✅ Follow functional patterns (functions 15-30 lines, max 100)
- ✅ Atomic commits after each module extraction
- ✅ Continuous progress reports

## 📐 Target Architecture

```
src/omniparser/parsers/
  html/
    __init__.py          # HTMLParser class (orchestrator, ~100 lines)
    validator.py         # URL/file validation (~60 lines)
    url_fetcher.py       # HTTP fetching, caching (~100 lines)
    content_extractor.py # HTML to Markdown, text extraction (~150 lines)
    metadata.py          # HTML metadata extraction (~80 lines)
    image_downloader.py  # Image downloading (optional, ~100 lines)
```

## 🚀 Execution Plan

### Phase 0: Pre-Flight (15 minutes)

1. **Read documentation:**
   - Read `PATTERNS_QUICK_REF.md` (keep open)
   - Read `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` (Phase 1 section)
   - Review `src/omniparser/parsers/pdf/` and `src/omniparser/parsers/epub/` for patterns

2. **Create feature branch:**
   ```bash
   cd /Users/mini/Documents/GitHub/OmniParser
   git checkout main
   git pull origin main
   git checkout -b refactor/html-parser-modular
   git push -u origin refactor/html-parser-modular
   ```

3. **Check environment:**
   ```bash
   uv run pytest --version
   uv run pytest tests/ -k html --collect-only
   ```

4. **Baseline measurement:**
   ```bash
   wc -l src/omniparser/parsers/html_parser.py
   uv run pytest tests/ -k html -v --tb=short
   ```

### Phase 1: Analysis (30 minutes)

**Use `house-research` subagent:**

Analyze `src/omniparser/parsers/html_parser.py`:
- Identify all methods and their line counts
- Identify logical groupings (validation, fetching, extraction, metadata, images)
- Create module breakdown plan
- Document dependencies between components
- Note requests and BeautifulSoup usage patterns

**Create:** `docs/refactoring/html-analysis.md` with findings

**Commit:**
```bash
git add docs/refactoring/html-analysis.md
git commit -m "docs: Add HTML parser analysis for refactoring"
git push origin refactor/html-parser-modular
```

### Phase 2: Create Structure (10 minutes)

```bash
mkdir -p src/omniparser/parsers/html
touch src/omniparser/parsers/html/__init__.py
touch src/omniparser/parsers/html/validator.py
touch src/omniparser/parsers/html/url_fetcher.py
touch src/omniparser/parsers/html/content_extractor.py
touch src/omniparser/parsers/html/metadata.py
touch src/omniparser/parsers/html/image_downloader.py  # Optional
```

**Commit:**
```bash
git add src/omniparser/parsers/html/
git commit -m "refactor(html): Create modular directory structure"
git push origin refactor/html-parser-modular
```

### Phase 3: Extract Modules (3-4 hours)

**For EACH module, use `house-coder` subagent:**

**IMPORTANT:** Add `git push origin refactor/html-parser-modular` after EVERY commit!

#### Step 1: Extract Validation (~30 min)
- Create `html/validator.py`
- Extract URL/file validation logic
- Functions: `validate_html_source()`, `validate_url()`, `validate_html_file()`, `check_url_accessibility()`
- Update imports in html_parser.py
- Run tests: `uv run pytest tests/ -k html -x`
- Format: `uv run black src/omniparser/parsers/html/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/html/validator.py src/omniparser/parsers/html_parser.py
  git commit -m "refactor(html): Extract validation to validator module"
  git push origin refactor/html-parser-modular
  ```

#### Step 2: Extract URL Fetcher (~45 min)
- Create `html/url_fetcher.py`
- Extract HTTP fetching, caching, session management
- Functions: `fetch_html()`, `create_session()`, `handle_redirects()`, `cache_response()`
- Handle requests library usage
- Update imports
- Run tests: `uv run pytest tests/ -k "html and fetch" -x`
- Format: `uv run black src/omniparser/parsers/html/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/html/
  git commit -m "refactor(html): Extract URL fetching to url_fetcher module"
  git push origin refactor/html-parser-modular
  ```

#### Step 3: Extract Metadata (~40 min)
- Create `html/metadata.py`
- Extract HTML metadata parsing (meta tags, Open Graph, Twitter Cards)
- Functions: `extract_html_metadata()`, `parse_meta_tags()`, `parse_opengraph()`, `parse_twitter_cards()`, `build_metadata()`
- Update imports
- Run tests: `uv run pytest tests/ -k "html and metadata" -x`
- Format: `uv run black src/omniparser/parsers/html/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/html/
  git commit -m "refactor(html): Extract metadata extraction to metadata module"
  git push origin refactor/html-parser-modular
  ```

#### Step 4: Extract Image Downloader (~45 min, Optional)
- Create `html/image_downloader.py`
- Extract image downloading/processing logic
- Functions: `download_images()`, `fetch_image()`, `save_image()`, `resolve_image_url()`
- Consider using shared `src/omniparser/processors/image_utils.py` if exists
- Update imports
- Run tests: `uv run pytest tests/ -k "html and image" -x`
- Format: `uv run black src/omniparser/parsers/html/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/html/
  git commit -m "refactor(html): Extract image downloading to image_downloader module"
  git push origin refactor/html-parser-modular
  ```

#### Step 5: Extract Content Extraction (~60 min)
- Create `html/content_extractor.py`
- Extract HTML to Markdown conversion, text extraction, cleaning
- Functions: `extract_html_content()`, `html_to_markdown()`, `clean_html()`, `extract_article_content()`, `remove_boilerplate()`
- Handle BeautifulSoup processing
- Update imports
- Run tests: `uv run pytest tests/unit/test_html_parser.py -x`
- Format: `uv run black src/omniparser/parsers/html/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/html/
  git commit -m "refactor(html): Extract content extraction to content_extractor module"
  git push origin refactor/html-parser-modular
  ```

#### Step 6: Refactor Main Parser (~45 min)
- Create `html/__init__.py` with HTMLParser class
- Import all extracted modules
- Orchestrate calls to extracted functions
- Keep parse() method simple (~20-25 lines):
  ```python
  def parse(self, source: Union[str, Path], output_dir: Optional[Path] = None) -> Document:
      validate_html_source(source)
      html_content = fetch_html(source) if isinstance(source, str) else Path(source).read_text()
      soup = BeautifulSoup(html_content, 'html.parser')
      metadata = extract_html_metadata(soup, source)
      content = extract_html_content(soup)
      images = download_images(soup, source, output_dir) if output_dir else []
      return self._build_document(metadata, content, images)
  ```
- Delete old `html_parser.py`
- Update `src/omniparser/parsers/__init__.py` imports
- Run ALL tests: `uv run pytest tests/ -k html -v`
- Format: `uv run black src/omniparser/parsers/html/`
- **Commit:**
  ```bash
  git add src/omniparser/parsers/
  git commit -m "refactor(html): Complete HTML parser modularization"
  git push origin refactor/html-parser-modular
  ```

### Phase 4: Validation (30 minutes)

1. **Line count check:**
   ```bash
   wc -l src/omniparser/parsers/html/*.py
   # All files should be ≤200 lines
   ```

2. **Test status:**
   ```bash
   uv run pytest tests/ -k html -v
   # All HTML tests should pass
   ```

3. **Integration test:**
   ```bash
   uv run python -c "
   from omniparser import parse_document
   from pathlib import Path
   doc = parse_document(Path('tests/fixtures/html/simple.html'))
   print(f'✓ Parsed: {doc.metadata.title}')
   print(f'✓ Content length: {len(doc.full_text)} chars')
   "
   ```

4. **Update TODOS.md:**
   - Mark "Refactor HTML parser" as complete
   - Note that ALL 6 parsers now refactored ✅

**Commit:**
```bash
git add TODOS.md
git commit -m "docs: Complete all parser refactoring (6/6 parsers modular)"
git push origin refactor/html-parser-modular
```

### Phase 5: Pull Request Creation (15 minutes)

1. **Create PR:**
   ```bash
   gh pr create \
     --title "refactor(html): Modularize HTML parser into functional components" \
     --body "$(cat <<'EOF'
## 🎯 Summary
Refactored HTML parser from monolithic 686-line file into modular architecture with 5-6 focused modules.

## 📊 Changes
- **Before:** 1 file, 686 lines
- **After:** 5-6 modules, ~500 total lines (27% reduction)
- **Modules:**
  - `validator.py` - URL/file validation (~60 lines)
  - `url_fetcher.py` - HTTP fetching, caching (~100 lines)
  - `content_extractor.py` - HTML→Markdown conversion (~150 lines)
  - `metadata.py` - HTML metadata (meta tags, OG, Twitter) (~80 lines)
  - `image_downloader.py` - Image downloading (~100 lines, optional)
  - `__init__.py` - HTMLParser orchestrator (~100 lines)

## ✅ Testing
- [x] All HTML tests pass (uv run pytest tests/ -k html)
- [x] Integration tested with sample HTML files and URLs
- [x] Metadata extraction working
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
- Follows patterns from PDF/DOCX/Markdown/Text/EPUB refactoring
- **ALL 6 PARSERS NOW MODULAR** 🎉

## 📝 Checklist
- [x] Tests pass
- [x] Code formatted (Black)
- [x] Documentation updated
- [x] Ready for review
- [x] Final parser in refactoring initiative

---
🤖 Generated with [Claude Code](https://claude.ai/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" \
     --base main \
     --head refactor/html-parser-modular
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
- **ALL 6 PARSERS NOW REFACTORED** ✅
- Ready for shared processors extraction: YES/NO

## ⚠️ Critical Rules

**IMPORTANT:** Add `git push origin refactor/html-parser-modular` after EVERY `git commit` command throughout this session!

1. **Use subagents for EVERYTHING:**
   - `house-research` for analysis
   - `house-coder` for code extraction
   - `house-bash` for commands

2. **Commit after EVERY module extraction** (atomic commits and push!)

3. **Run tests after EVERY change:**
   ```bash
   uv run pytest tests/ -k html -x  # Stop on first failure
   ```

4. **Follow functional patterns strictly:**
   - Functions: 15-30 lines (max 100)
   - Files: 50-200 lines
   - No code repetition
   - Type hints on everything
   - Comprehensive docstrings

5. **Format code before every commit:**
   ```bash
   uv run black src/omniparser/parsers/html/
   ```

6. **Report progress continuously:**
   - After each module extraction
   - Include test status
   - Include what's next

## 🚨 If Something Goes Wrong

### Tests Fail After Extraction

```bash
# Check imports
uv run python -c "from omniparser.parsers.html import HTMLParser"

# Run single test with verbose output
uv run pytest tests/unit/test_html_parser.py::test_name -vv --tb=short

# Check for circular imports
uv run python -c "import sys; sys.path.insert(0, 'src'); import omniparser"
```

### Branch Issues

```bash
# Check current branch
git branch --show-current

# If on wrong branch, switch to feature branch
git checkout refactor/html-parser-modular

# If need to sync with main
git checkout main
git pull origin main
git checkout refactor/html-parser-modular
git merge main
```

### Module Too Large

Break it down further:
- Extract helper functions
- Use comprehensions instead of loops
- Split complex logic into multiple functions
- Each function should do ONE thing

### HTTP/Network Issues

The HTML parser uses requests library:
- Handle connection errors gracefully
- Implement proper timeouts
- Cache responses when possible
- Document network interaction patterns

## 📚 Quick Reference

**Key Commands:**
```bash
# Run HTML tests
uv run pytest tests/ -k html -v

# Format code
uv run black src/omniparser/parsers/html/

# Check line counts
wc -l src/omniparser/parsers/html/*.py

# Test single file
uv run pytest tests/unit/test_html_parser.py -x

# Commit and push
git add . && git commit -m "refactor(html): <message>" && git push origin refactor/html-parser-modular
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

**Celebration:** This is the FINAL parser refactoring! All 6 parsers will be modular! 🎉

**Let's go! 🚀**
