# Parser Refactoring Plan

## Context

The 4 new parsers (PDF, DOCX, Markdown, Text) were created in remote Claude Code sessions without access to FUNCTIONAL_PATTERNS.md, resulting in files that exceed target guidelines.

**Current State:**
- PDFParser: 1,052 lines (target: 50-200 per file)
- DOCXParser: 757 lines (target: 50-200 per file)
- MarkdownParser: 737 lines (target: 50-200 per file)
- TextParser: 577 lines (target: 50-200 per file)

**Target:** Break each parser into 4-6 focused modules following FUNCTIONAL_PATTERNS.md

---

## Goals

1. **Modularity**: Each file has single responsibility (50-200 lines)
2. **Testability**: Smaller units easier to test in isolation
3. **Maintainability**: Changes localized to specific modules
4. **Consistency**: All parsers follow same architectural pattern
5. **Reusability**: Shared logic extracted to processors/

---

## Proposed Architecture Pattern

Each parser should be broken into:

```
parsers/
  pdf/
    __init__.py          # PDFParser class (main orchestrator, ~100 lines)
    extractor.py         # Text extraction logic (~150 lines)
    image_handler.py     # Image extraction (~100 lines)
    metadata_parser.py   # Metadata extraction (~80 lines)
    chapter_detector.py  # Chapter detection (~120 lines)
    validator.py         # Input validation (~60 lines)
```

---

## Refactoring Strategy by Parser

### PDF Parser (1,052 lines → 6 modules)

**Current Structure Analysis:**
- Main parse() method: ~150 lines
- Image extraction: ~200 lines
- Text extraction: ~300 lines
- Metadata parsing: ~100 lines
- Chapter detection: ~150 lines
- Validation/error handling: ~150 lines

**Proposed Breakdown:**
1. `pdf/__init__.py` - PDFParser class (orchestrator)
2. `pdf/extractor.py` - Text extraction, column detection
3. `pdf/image_handler.py` - Image extraction, conversion
4. `pdf/metadata_parser.py` - PDF metadata parsing
5. `pdf/chapter_detector.py` - Chapter/section detection
6. `pdf/validator.py` - Input validation, error handling

### DOCX Parser (757 lines → 5 modules)

**Proposed Breakdown:**
1. `docx/__init__.py` - DOCXParser class
2. `docx/extractor.py` - Paragraph/text extraction
3. `docx/table_handler.py` - Table extraction/conversion
4. `docx/image_handler.py` - Image extraction
5. `docx/metadata_parser.py` - DOCX properties parsing

### Markdown Parser (737 lines → 4 modules)

**Proposed Breakdown:**
1. `markdown/__init__.py` - MarkdownParser class
2. `markdown/frontmatter.py` - YAML frontmatter parsing
3. `markdown/content_parser.py` - Markdown content processing
4. `markdown/chapter_detector.py` - Heading-based chapters

### Text Parser (577 lines → 4 modules)

**Proposed Breakdown:**
1. `text/__init__.py` - TextParser class
2. `text/encoder_detector.py` - Encoding detection
3. `text/chapter_detector.py` - Pattern-based chapter detection
4. `text/cleaner.py` - Text normalization

---

## Implementation Timeline

**Phase 3.1: Foundation** (2 days)
- Set up new directory structure
- Define interfaces between modules
- Create base classes/utilities

**Phase 3.2: PDF Parser Refactoring** (3 days)
- Implement all 6 modules
- Update tests
- Verify functionality preserved

**Phase 3.3: DOCX Parser Refactoring** (2 days)
- Implement all 5 modules
- Update tests
- Complete beta features during refactor

**Phase 3.4: Markdown & Text Parsers** (3 days)
- Refactor both parsers
- Update tests
- Standardize patterns

**Phase 3.5: Integration & Testing** (2 days)
- Run full test suite
- Performance testing
- Documentation updates

**Total Estimated Time: 12 days (2.5 weeks)**

---

## Success Metrics

✅ All parser files ≤ 200 lines
✅ All tests pass (357+ tests)
✅ No functionality regressions
✅ Test coverage maintained or improved
✅ Clear module boundaries
✅ Shared logic extracted to processors/
✅ Documentation updated

---

## Priority

**Phase 3.0** - After current cleanup (Phase 2.9) and initial production release (v0.3.0)

**Rationale:** Current parsers work correctly. Refactoring is about maintainability and consistency, not functionality. Better to ship working code, then improve architecture.

---

## Related Documents

- FUNCTIONAL_PATTERNS.md - Target patterns and guidelines
- PATTERNS_QUICK_REF.md - Quick reference for functional style
- ARCHITECTURE_PLAN.md - Overall project architecture

---

*This document serves as the roadmap for systematically refactoring all parsers to follow consistent, maintainable patterns. It should be executed as a dedicated phase AFTER the current cleanup and release.*
