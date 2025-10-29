# Session 2: DOCX Parser Refactoring + Beta Completion

**Copy this entire prompt into a new Claude Code session**

---

## 📋 Session Metadata

| Field | Value |
|-------|-------|
| **Session ID** | SESSION_2_DOCX |
| **Project** | OmniParser |
| **Branch Name** | `refactor/docx-parser-modular` |
| **PR Title** | `feat(docx): Refactor parser and complete beta features (lists + hyperlinks)` |
| **Estimated Duration** | 4-5 hours |
| **Prerequisites** | SESSION_1 (PDF) complete recommended |
| **Target Lines** | 755 → ~620 (6 modules × ~100 lines) |
| **Deliverable** | Modular DOCX parser with lists/hyperlinks, production-ready status |

---

## 🎯 Mission

Refactor `src/omniparser/parsers/docx_parser.py` (755 lines) into modular components AND complete beta features (list + hyperlink extraction) to promote DOCX parser to production-ready.

## 📋 Context

You are working in the OmniParser project at `/Users/mini/Documents/GitHub/OmniParser`.

**Current state:**
- DOCX parser: 755 lines (monolithic, BETA status)
- Target: 5-6 modules × ~120 lines each
- Test status: 872/923 tests passing
- **Missing features:** List extraction, hyperlink extraction
- **Goal:** Refactor AND promote to production-ready

**Prerequisites:**
- Session 1 (PDF refactoring) should be complete
- Learn from PDF refactoring patterns

**Key documents:**
1. `PATTERNS_QUICK_REF.md` - Keep open while coding
2. `src/omniparser/parsers/pdf/` - Reference for patterns
3. `TODOS.md` - Check DOCX beta completion tasks

## 🎯 Success Criteria

- ✅ All DOCX parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ **NEW:** List extraction implemented
- ✅ **NEW:** Hyperlink extraction implemented
- ✅ All DOCX tests pass + new tests for lists/hyperlinks
- ✅ Update README: DOCX from 🔶 Beta → ✅ Production
- ✅ Follow functional patterns
- ✅ Atomic commits after each change

## 📐 Target Architecture

```
src/omniparser/parsers/
  docx/
    __init__.py          # DOCXParser class (orchestrator, ~100 lines)
    validator.py         # DOCX validation (~60 lines)
    metadata.py          # Document properties (~80 lines)
    extractor.py         # Paragraph/text extraction + LISTS + HYPERLINKS (~180 lines)
    table_handler.py     # Table extraction (~120 lines)
    image_handler.py     # Image extraction (~100 lines) - reuse PDF logic?
```

## 🚀 Execution Plan

### Phase 0: Pre-Flight (15 minutes)

1. **Check PDF refactoring completion:**
   ```bash
   cd /Users/mini/Documents/GitHub/OmniParser
   ls -la src/omniparser/parsers/pdf/
   wc -l src/omniparser/parsers/pdf/*.py
   ```

2. **Create feature branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b refactor/docx-parser-modular
   git push -u origin refactor/docx-parser-modular
   ```

3. **Check DOCX current status:**
   ```bash
   wc -l src/omniparser/parsers/docx_parser.py
   uv run pytest tests/ -k docx --collect-only
   uv run pytest tests/ -k docx -v --tb=short
   ```

### Phase 1: Analysis (30 minutes)

**Use `house-research` subagent:**

Analyze `src/omniparser/parsers/docx_parser.py`:
- Identify all methods and line counts
- Identify what logic can be reused from PDF (image handling)
- Document where to add list extraction
- Document where to add hyperlink extraction
- Create module breakdown plan

**Create:** `docs/refactoring/docx-analysis.md`

**Commit:**
```bash
git add docs/refactoring/docx-analysis.md
git commit -m "docs: Add DOCX parser analysis for refactoring"
git push origin refactor/docx-parser-modular
```

### Phase 2: Create Structure (10 minutes)

```bash
mkdir -p src/omniparser/parsers/docx
touch src/omniparser/parsers/docx/__init__.py
touch src/omniparser/parsers/docx/validator.py
touch src/omniparser/parsers/docx/metadata.py
touch src/omniparser/parsers/docx/extractor.py
touch src/omniparser/parsers/docx/table_handler.py
touch src/omniparser/parsers/docx/image_handler.py
```

**Commit:** `refactor(docx): Create modular directory structure`

### Phase 3: Extract Modules (3-4 hours)

**For EACH module, use `house-coder` subagent:**

#### Step 1: Extract Validation (~30 min)
- Create `docx/validator.py`
- Extract DOCX validation logic
- Functions: `validate_docx_file()`, `check_docx_structure()`
- Update imports
- Run tests: `uv run pytest tests/ -k docx -x`
- Format: `uv run black src/omniparser/parsers/docx/`
- **Commit:** `refactor(docx): Extract validation to validator module`

#### Step 2: Extract Metadata (~45 min)
- Create `docx/metadata.py`
- Extract document properties parsing
- Functions: `extract_docx_metadata()`, `parse_core_properties()`
- Update imports
- Run tests: `uv run pytest tests/ -k docx -x`
- Format: `uv run black src/omniparser/parsers/docx/`
- **Commit:** `refactor(docx): Extract metadata extraction to metadata module`

#### Step 3: Extract Table Handling (~45 min)
- Create `docx/table_handler.py`
- Extract table extraction and markdown formatting
- Functions: `extract_tables()`, `table_to_markdown()`, `format_cell()`
- Update imports
- Run tests: `uv run pytest tests/ -k docx -x`
- Format: `uv run black src/omniparser/parsers/docx/`
- **Commit:** `refactor(docx): Extract table handling to table_handler module`

#### Step 4: Extract Image Handling (~60 min)
- Create `docx/image_handler.py`
- **Check if can reuse PDF image_handler logic**
- If similar, consider shared `processors/image_utils.py`
- Functions: `extract_docx_images()`, `save_docx_image()`
- Update imports
- Run tests: `uv run pytest tests/ -k "docx and image" -x`
- Format: `uv run black src/omniparser/parsers/docx/`
- **Commit:** `refactor(docx): Extract image handling to image_handler module`

#### Step 5: Extract Content + ADD BETA FEATURES (~90 min)

**CRITICAL: This step also implements missing beta features!**

Create `docx/extractor.py` with:

**Existing functionality:**
- `extract_paragraphs()` - Extract paragraph text
- `extract_text_from_paragraph()` - Get text with formatting

**NEW: List extraction (implement this!)**
- `extract_lists()` - Extract ordered and unordered lists
- `detect_list_type()` - Identify bullet vs numbered
- `format_list_to_markdown()` - Convert to markdown list format

**NEW: Hyperlink extraction (implement this!)**
- `extract_hyperlinks()` - Extract hyperlinks from paragraphs
- `format_hyperlink_markdown()` - Convert to `[text](url)` format

**Example implementation:**
```python
def extract_lists(paragraph) -> Optional[str]:
    """Extract lists from paragraph if it's a list item."""
    if paragraph.style.name.startswith('List'):
        # Get list level
        level = paragraph._element.pPr.numPr.ilvl.val if hasattr(...) else 0
        # Get list marker (bullet or number)
        marker = detect_list_marker(paragraph)
        # Format as markdown
        indent = "  " * level
        return f"{indent}{marker} {paragraph.text}"
    return None

def extract_hyperlinks(paragraph) -> List[Tuple[str, str]]:
    """Extract hyperlinks from paragraph."""
    links = []
    for run in paragraph.runs:
        if run.hyperlink:
            text = run.text
            url = run.hyperlink.address
            links.append((text, url))
    return links
```

**Testing:**
- Create test fixtures with lists and hyperlinks
- Add unit tests for `extract_lists()` and `extract_hyperlinks()`
- Update integration tests

**Steps:**
1. Extract existing paragraph logic
2. **Implement list extraction (NEW)**
3. **Implement hyperlink extraction (NEW)**
4. Add comprehensive tests
5. Update imports
6. Run tests: `uv run pytest tests/ -k docx -v`
7. Format: `uv run black src/omniparser/parsers/docx/`

**Commit:** `feat(docx): Add list and hyperlink extraction, complete beta features`

#### Step 6: Refactor Main Parser (~45 min)
- Create `docx/__init__.py` with DOCXParser class
- Import all extracted modules
- Orchestrate calls (similar to PDF pattern)
- Delete old `docx_parser.py`
- Update `src/omniparser/parsers/__init__.py` imports
- Run ALL tests: `uv run pytest tests/ -k docx -v`
- Format: `uv run black src/omniparser/parsers/docx/`
- **Commit:** `refactor(docx): Complete DOCX parser modularization`

### Phase 4: Update Status to Production (30 minutes)

**DOCX is now production-ready! Update documentation:**

1. **Update README.md:**
   ```markdown
   | Parser | Status | Features |
   |--------|--------|----------|
   | DOCX | ✅ Production | Text, tables, lists, hyperlinks, images |
   ```
   Change from 🔶 Beta to ✅ Production

2. **Update TODOS.md:**
   - Move DOCX tasks from "Active" to "✅ Recently Completed"
   - Mark "Complete DOCX beta features" as done

3. **Update CHANGELOG.md:**
   ```markdown
   ### Changed
   - DOCX parser promoted from Beta to Production-Ready (v0.3.0)

   ### Added
   - DOCX parser: List extraction (ordered and unordered)
   - DOCX parser: Hyperlink extraction and markdown formatting
   ```

4. **Update docstring in docx/__init__.py:**
   ```python
   class DOCXParser(BaseParser):
       """
       Parser for DOCX files using python-docx.

       **Status:** Production-Ready ✅

       Features:
       - Text extraction from paragraphs
       - Table extraction and markdown formatting
       - List extraction (bullets and numbered lists)
       - Hyperlink extraction
       - Image extraction
       - Metadata extraction from document properties
       """
   ```

**Commit:** `docs: Promote DOCX parser to production-ready status`

### Phase 5: Validation (30 minutes)

1. **Line count check:**
   ```bash
   wc -l src/omniparser/parsers/docx/*.py
   ```

2. **Test status:**
   ```bash
   uv run pytest tests/ -k docx -v
   ```

3. **Integration test with lists and hyperlinks:**
   ```bash
   uv run python -c "
   from omniparser import parse_document
   from pathlib import Path
   doc = parse_document(Path('tests/fixtures/docx/with_lists.docx'))
   print(f'✓ Parsed: {doc.metadata.title}')
   print(f'✓ Has lists: {\"- \" in doc.full_text or \"1. \" in doc.full_text}')
   print(f'✓ Has links: {\"[\" in doc.full_text and \"](\" in doc.full_text}')
   "
   ```

4. **Update TODOS.md:**
   - Mark DOCX refactoring complete
   - Add Phase 3 (Markdown refactoring) tasks

**Commit:**
```bash
git add TODOS.md
git commit -m "docs: Update TODOS after DOCX parser refactoring and beta completion"
git push origin refactor/docx-parser-modular
```

### Phase 6: Pull Request Creation (15 minutes)

1. **Create PR:**
   ```bash
   gh pr create \
     --title "feat(docx): Refactor parser and complete beta features (lists + hyperlinks)" \
     --body "$(cat <<'EOF'
## 🎯 Summary
Refactored DOCX parser from monolithic 755-line file into modular architecture AND completed beta features (list + hyperlink extraction). DOCX parser is now production-ready!

## 📊 Changes
- **Before:** 1 file, 755 lines (Beta status)
- **After:** 6 modules, ~620 total lines (18% reduction)
- **Modules:**
  - `validator.py` - DOCX validation (~60 lines)
  - `metadata.py` - Document properties (~80 lines)
  - `extractor.py` - Paragraphs + LISTS + HYPERLINKS (~180 lines)
  - `table_handler.py` - Table extraction (~120 lines)
  - `image_handler.py` - Image extraction (~100 lines)
  - `__init__.py` - DOCXParser orchestrator (~100 lines)

## ✨ New Features
- ✅ List extraction (ordered and unordered)
- ✅ Hyperlink extraction and markdown formatting
- ✅ DOCX promoted from Beta → Production-Ready

## ✅ Testing
- [x] All DOCX tests pass
- [x] New tests for lists and hyperlinks
- [x] Integration tested
- [x] No performance regression

## 📏 Code Quality
- [x] Follows functional patterns
- [x] Black formatted
- [x] Type hints
- [x] Comprehensive docstrings

## 🔗 Related
- Part of parser refactoring initiative
- Follows SESSION_1 (PDF) patterns
- DOCX now production-ready ✅

## 📝 Checklist
- [x] Beta features complete
- [x] Tests pass
- [x] Documentation updated
- [x] Ready for review

---
🤖 Generated with [Claude Code](https://claude.ai/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" \
     --base main \
     --head refactor/docx-parser-modular
   ```

2. **Verify PR created:**
   ```bash
   gh pr view
   ```

### Phase 7: Report (15 minutes)

Create completion report with:
- Start/end times
- Files created (with line counts)
- Beta features implemented (lists, hyperlinks)
- Tests status (before/after)
- Commits created
- DOCX now production-ready ✅
- Ready for Phase 3 (Markdown): YES/NO

## ⚠️ Critical Rules

**IMPORTANT:** Add `git push origin refactor/docx-parser-modular` after EVERY `git commit` command throughout this session!

1. **Use subagents for everything**
2. **Commit after each module extraction** (and push to branch!)
3. **Run tests after every change**
4. **Implement beta features during refactoring**
5. **Update documentation when promoting to production**
6. **Follow functional patterns (15-30 line functions, max 100)**
7. **Format code before commits: `uv run black .`**

## 🚨 Special Notes for Beta Features

### List Extraction Tips

**Detection:**
- Check `paragraph.style.name` for "List" prefix
- Check `paragraph._element.pPr.numPr` for numbering properties
- Parse list level from `ilvl` (indentation level)

**Formatting:**
- Bullet lists: `- Item text`
- Numbered lists: `1. Item text`
- Nested lists: Use indentation (`  - Nested item`)

**Test cases:**
- Simple bullet list
- Numbered list
- Nested lists (2-3 levels)
- Mixed content (paragraphs + lists)

### Hyperlink Extraction Tips

**Detection:**
- Iterate through `paragraph.runs`
- Check `run.hyperlink` property
- Get URL from `run.hyperlink.address`

**Formatting:**
- Markdown: `[link text](url)`
- Preserve context in paragraph

**Test cases:**
- Single link in paragraph
- Multiple links
- Link with no text
- External vs internal links

## 📚 Quick Reference

**Key Commands:**
```bash
# Run DOCX tests
uv run pytest tests/ -k docx -v

# Format code
uv run black src/omniparser/parsers/docx/

# Check line counts
wc -l src/omniparser/parsers/docx/*.py

# Test with fixtures
ls tests/fixtures/docx/
```

**Functional Patterns Checklist:**
- [ ] No function >100 lines
- [ ] No file >200 lines
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] Lists extraction working
- [ ] Hyperlinks extraction working
- [ ] Tests pass for new features

---

## 🏁 Start Execution

**You are now ready to begin!**

1. Check PDF refactoring completion (Phase 0) + create feature branch!
2. Analyze DOCX parser (Phase 1)
3. Create structure (Phase 2)
4. Extract modules + implement beta features (Phase 3)
5. Update documentation to production (Phase 4)
6. Validate (Phase 5)
7. Create Pull Request (Phase 6)
8. Report (Phase 7)

**EXECUTION MODE:** YOLO (auto-approve all actions)

**Report after each major step:**
- What was completed
- Test status
- Commit hash
- What's next

**Remember:** Push to branch after every commit!

**Bonus: After completion, DOCX parser will be production-ready! 🎉**

**Let's go! 🚀**
