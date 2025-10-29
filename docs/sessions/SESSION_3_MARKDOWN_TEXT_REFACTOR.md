# Session 3: Markdown & Text Parser Refactoring

**Copy this entire prompt into a new Claude Code session**

---

## 📋 Session Metadata

| Field | Value |
|-------|-------|
| **Session ID** | SESSION_3_MARKDOWN_TEXT |
| **Project** | OmniParser |
| **Branch Name** | `refactor/markdown-text-parsers` |
| **PR Title** | `refactor(markdown,text): Modularize Markdown and Text parsers` |
| **Estimated Duration** | 4-5 hours |
| **Prerequisites** | SESSION_1 and SESSION_2 complete recommended |
| **Target Lines** | 1,321 → ~900 (Markdown: 741→500, Text: 580→400) |
| **Deliverable** | Two modular parsers (Markdown + Text) with all tests passing |

---

## 🎯 Mission

Refactor both `markdown_parser.py` (741 lines) and `text_parser.py` (580 lines) into modular components. These are simpler parsers, so we'll do both in one session.

## 📋 Context

You are working in the OmniParser project at `/Users/mini/Documents/GitHub/OmniParser`.

**Current state:**
- Markdown parser: 741 lines (monolithic)
- Text parser: 580 lines (monolithic)
- Test status: 872/923 tests passing
- Both are production-ready, just need refactoring for maintainability

**Prerequisites:**
- Sessions 1 & 2 (PDF and DOCX refactoring) should be complete
- Apply learned patterns from previous refactorings

**Key documents:**
1. `PATTERNS_QUICK_REF.md` - Keep open
2. `src/omniparser/parsers/pdf/` - Reference patterns
3. `src/omniparser/parsers/docx/` - Reference patterns

## 🎯 Success Criteria

- ✅ All Markdown parser files ≤200 lines
- ✅ All Text parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ All Markdown tests pass
- ✅ All Text tests pass
- ✅ Follow functional patterns
- ✅ Atomic commits

## 📐 Target Architecture

### Markdown Parser
```
src/omniparser/parsers/
  markdown/
    __init__.py          # MarkdownParser (~100 lines)
    validator.py         # File validation (~60 lines)
    frontmatter.py       # YAML frontmatter parsing (~100 lines)
    content_parser.py    # Markdown content processing (~150 lines)
    chapter_detector.py  # Heading-based chapters (~120 lines)
```

### Text Parser
```
src/omniparser/parsers/
  text/
    __init__.py          # TextParser (~100 lines)
    validator.py         # File validation (~60 lines)
    encoding_detector.py # Encoding detection (~100 lines)
    chapter_detector.py  # Pattern-based chapters (~120 lines)
    cleaner.py           # Text normalization (~100 lines)
```

## 🚀 Execution Plan

### Phase 0: Pre-Flight (15 minutes)

1. **Check previous refactorings:**
   ```bash
   cd /Users/mini/Documents/GitHub/OmniParser
   ls -la src/omniparser/parsers/pdf/
   ls -la src/omniparser/parsers/docx/
   ```

2. **Create feature branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b refactor/markdown-text-parsers
   git push -u origin refactor/markdown-text-parsers
   ```

3. **Check current status:**
   ```bash
   wc -l src/omniparser/parsers/markdown_parser.py
   wc -l src/omniparser/parsers/text_parser.py
   uv run pytest tests/ -k "markdown or text" -v --tb=short
   ```

---

## Part 1: Markdown Parser Refactoring (2-3 hours)

### Phase 1.1: Analysis (20 minutes)

**Use `house-research` subagent:**

Analyze `src/omniparser/parsers/markdown_parser.py`:
- Identify YAML frontmatter parsing logic
- Identify markdown content processing
- Identify chapter detection (heading-based)
- Check if can use shared `processors/chapter_detector.py`
- Create module breakdown

**Create:** `docs/refactoring/markdown-analysis.md`

**Commit:** `docs: Add Markdown parser analysis for refactoring`

### Phase 1.2: Create Structure (5 minutes)

```bash
mkdir -p src/omniparser/parsers/markdown
touch src/omniparser/parsers/markdown/__init__.py
touch src/omniparser/parsers/markdown/validator.py
touch src/omniparser/parsers/markdown/frontmatter.py
touch src/omniparser/parsers/markdown/content_parser.py
touch src/omniparser/parsers/markdown/chapter_detector.py
```

**Commit:** `refactor(markdown): Create modular directory structure`

### Phase 1.3: Extract Modules (2 hours)

**Use `house-coder` for each:**

#### Step 1: Extract Validation (~20 min)
- Create `markdown/validator.py`
- Functions: `validate_markdown_file()`, `check_encoding()`
- **Commit:** `refactor(markdown): Extract validation to validator module`

#### Step 2: Extract Frontmatter (~30 min)
- Create `markdown/frontmatter.py`
- Functions: `extract_frontmatter()`, `parse_yaml_frontmatter()`, `merge_with_defaults()`
- Handle YAML, TOML, JSON frontmatter
- **Commit:** `refactor(markdown): Extract frontmatter parsing to frontmatter module`

#### Step 3: Extract Content Parser (~30 min)
- Create `markdown/content_parser.py`
- Functions: `parse_markdown_content()`, `extract_code_blocks()`, `extract_links()`
- **Commit:** `refactor(markdown): Extract content parsing to content_parser module`

#### Step 4: Extract Chapter Detection (~30 min)
- Create `markdown/chapter_detector.py`
- Check if can use shared `processors/chapter_detector.py`
- Functions: `detect_markdown_chapters()`, `parse_headings()`, `split_by_headings()`
- **Commit:** `refactor(markdown): Extract chapter detection to chapter_detector module`

#### Step 5: Refactor Main Parser (~30 min)
- Create `markdown/__init__.py` with MarkdownParser
- Orchestrate module calls
- Delete old `markdown_parser.py`
- Update imports
- Run tests: `uv run pytest tests/ -k markdown -v`
- **Commit:** `refactor(markdown): Complete Markdown parser modularization`

### Phase 1.4: Validation (10 minutes)

```bash
wc -l src/omniparser/parsers/markdown/*.py
uv run pytest tests/ -k markdown -v
```

**Commit:** `docs: Update TODOS after Markdown parser refactoring`

---

## Part 2: Text Parser Refactoring (1.5-2 hours)

### Phase 2.1: Analysis (20 minutes)

**Use `house-research` subagent:**

Analyze `src/omniparser/parsers/text_parser.py`:
- Identify encoding detection logic (chardet)
- Identify text normalization/cleaning
- Identify chapter detection (pattern-based)
- Create module breakdown

**Create:** `docs/refactoring/text-analysis.md`

**Commit:** `docs: Add Text parser analysis for refactoring`

### Phase 2.2: Create Structure (5 minutes)

```bash
mkdir -p src/omniparser/parsers/text
touch src/omniparser/parsers/text/__init__.py
touch src/omniparser/parsers/text/validator.py
touch src/omniparser/parsers/text/encoding_detector.py
touch src/omniparser/parsers/text/chapter_detector.py
touch src/omniparser/parsers/text/cleaner.py
```

**Commit:** `refactor(text): Create modular directory structure`

### Phase 2.3: Extract Modules (1.5 hours)

**Use `house-coder` for each:**

#### Step 1: Extract Validation (~20 min)
- Create `text/validator.py`
- Functions: `validate_text_file()`, `check_file_size()`
- **Commit:** `refactor(text): Extract validation to validator module`

#### Step 2: Extract Encoding Detection (~30 min)
- Create `text/encoding_detector.py`
- Functions: `detect_encoding()`, `decode_with_fallback()`, `normalize_encoding_name()`
- Use chardet library
- **Commit:** `refactor(text): Extract encoding detection to encoding_detector module`

#### Step 3: Extract Text Cleaner (~25 min)
- Create `text/cleaner.py`
- Functions: `clean_text()`, `normalize_whitespace()`, `remove_control_chars()`
- **Commit:** `refactor(text): Extract text cleaning to cleaner module`

#### Step 4: Extract Chapter Detection (~30 min)
- Create `text/chapter_detector.py`
- Functions: `detect_text_chapters()`, `find_chapter_markers()`, `split_by_patterns()`
- Pattern-based detection (Chapter 1, CHAPTER I, etc.)
- **Commit:** `refactor(text): Extract chapter detection to chapter_detector module`

#### Step 5: Refactor Main Parser (~25 min)
- Create `text/__init__.py` with TextParser
- Orchestrate module calls
- Delete old `text_parser.py`
- Update imports
- Run tests: `uv run pytest tests/ -k text -v`
- **Commit:** `refactor(text): Complete Text parser modularization`

### Phase 2.4: Validation (10 minutes)

```bash
wc -l src/omniparser/parsers/text/*.py
uv run pytest tests/ -k text -v
```

**Commit:** `docs: Update TODOS after Text parser refactoring`

---

## Phase 3: Final Validation (30 minutes)

### Both Parsers Together

1. **Line counts:**
   ```bash
   echo "=== Markdown Parser ==="
   wc -l src/omniparser/parsers/markdown/*.py
   echo "=== Text Parser ==="
   wc -l src/omniparser/parsers/text/*.py
   ```

2. **All tests:**
   ```bash
   uv run pytest tests/ -k "markdown or text" -v
   ```

3. **Integration tests:**
   ```bash
   uv run python -c "
   from omniparser import parse_document
   from pathlib import Path

   # Test Markdown
   md_doc = parse_document(Path('tests/fixtures/markdown/simple.md'))
   print(f'✓ Markdown: {md_doc.metadata.title}')

   # Test Text
   txt_doc = parse_document(Path('tests/fixtures/text/simple.txt'))
   print(f'✓ Text: {len(txt_doc.chapters)} chapters')
   "
   ```

4. **Update TODOS.md:**
   - Mark Markdown refactoring complete
   - Mark Text refactoring complete
   - Note that ALL 4 parsers now refactored

**Commit:**
```bash
git add TODOS.md
git commit -m "docs: Complete parser refactoring phase (PDF, DOCX, Markdown, Text)"
git push origin refactor/markdown-text-parsers
```

---

## Phase 4: Pull Request Creation (15 minutes)

1. **Create PR:**
   ```bash
   gh pr create \
     --title "refactor(markdown,text): Modularize Markdown and Text parsers" \
     --body "$(cat <<'EOF'
## 🎯 Summary
Refactored Markdown (741→500 lines) and Text (580→400 lines) parsers into modular architectures.

## 📊 Changes

### Markdown Parser
- **Before:** 1 file, 741 lines
- **After:** 5 modules, ~500 total lines (33% reduction)
- **Modules:**
  - `validator.py` - File validation (~60 lines)
  - `frontmatter.py` - YAML/TOML/JSON frontmatter (~100 lines)
  - `content_parser.py` - Markdown content (~150 lines)
  - `chapter_detector.py` - Heading-based chapters (~120 lines)
  - `__init__.py` - MarkdownParser orchestrator (~100 lines)

### Text Parser
- **Before:** 1 file, 580 lines
- **After:** 5 modules, ~400 total lines (31% reduction)
- **Modules:**
  - `validator.py` - File validation (~60 lines)
  - `encoding_detector.py` - Encoding detection (~100 lines)
  - `chapter_detector.py` - Pattern-based chapters (~120 lines)
  - `cleaner.py` - Text normalization (~100 lines)
  - `__init__.py` - TextParser orchestrator (~100 lines)

## ✅ Testing
- [x] All Markdown tests pass
- [x] All Text tests pass
- [x] Integration tested
- [x] No performance regression

## 📏 Code Quality
- [x] Follows functional patterns
- [x] Black formatted
- [x] Type hints
- [x] Comprehensive docstrings

## 🔗 Related
- Part of parser refactoring initiative
- Follows SESSION_1 (PDF) and SESSION_2 (DOCX) patterns
- 4 of 6 parsers now refactored

## 📝 Checklist
- [x] Both parsers refactored
- [x] Tests pass
- [x] Documentation updated
- [x] Ready for review

---
🤖 Generated with [Claude Code](https://claude.ai/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" \
     --base main \
     --head refactor/markdown-text-parsers
   ```

2. **Verify PR created:**
   ```bash
   gh pr view
   ```

---

## Phase 5: Report (15 minutes)

Create completion report with:
- Start/end times
- Both parsers completed
- Files created (with line counts)
- Tests status
- Commits created
- All 4 parsers now modular ✅
- Ready for Phase 4 (Shared Processors): YES/NO

## ⚠️ Critical Rules

**IMPORTANT:** Add `git push origin refactor/markdown-text-parsers` after EVERY `git commit` command throughout this session!

1. **Do Markdown first, then Text** (sequential, not parallel)
2. **Use subagents for everything**
3. **Commit after each module extraction** (and push to branch!)
4. **Run tests after every change**
5. **Follow functional patterns**
6. **Format before commits: `uv run black .`**
7. **Report progress continuously**

## 📚 Quick Reference

**Key Commands:**
```bash
# Test both parsers
uv run pytest tests/ -k "markdown or text" -v

# Test individually
uv run pytest tests/ -k markdown -v
uv run pytest tests/ -k text -v

# Format
uv run black src/omniparser/parsers/markdown/
uv run black src/omniparser/parsers/text/

# Line counts
wc -l src/omniparser/parsers/markdown/*.py
wc -l src/omniparser/parsers/text/*.py
```

**Functional Patterns Checklist:**
- [ ] No function >100 lines
- [ ] No file >200 lines
- [ ] Type hints everywhere
- [ ] Docstrings on public functions
- [ ] Used comprehensions
- [ ] No repeated code

---

## 🏁 Start Execution

**You are now ready to begin!**

1. Pre-Flight checks + create feature branch!
2. **Part 1:** Markdown Parser (2-3 hours)
3. **Part 2:** Text Parser (1.5-2 hours)
4. Final validation (both parsers)
5. Create Pull Request
6. Report

**EXECUTION MODE:** YOLO (auto-approve all actions)

**Remember:** Push to branch after every commit!

**After completion:**
- 4/6 parsers refactored ✅
- Only EPUB and HTML remain (will defer those)
- Ready for shared processor extraction

**Let's go! 🚀**
