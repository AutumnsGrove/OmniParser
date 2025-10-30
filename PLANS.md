# OmniParser "Big Cleanup" Phase - Subagent Execution Plan

**Execution Mode**: YOLO (Auto-approve)
**Estimated Time**: 2-3 days (16-24 hours)
**Strategy**: Subagent-First Development with Atomic Commits
**Goal**: Fix broken code, sync documentation, standardize quality, prepare for v0.3.0 release

---

## 🎯 Critical Context for YOLO Execution

### Current State Summary
- **Status**: Code is BROKEN (parser.py syntax errors from merge conflicts)
- **Recent Activity**: 5 major merges on Oct 29, 2025 (~19,736 lines added)
- **New Features**: 4 new parsers (PDF, DOCX, Markdown, Text) + AI features
- **Test Coverage**: 357 tests exist but cannot run until parser.py is fixed
- **Documentation**: Severely outdated (claims Phase 2.5, actually Phase 2.8+)
- **CHANGELOG**: Corrupted with 9 duplicate "[Unreleased]" sections

### User Decisions (From AskUserQuestion)
1. **Approach**: Comprehensive planning, systematic execution
2. **DOCX Parser**: Document as beta/partial (6 TODO items remain)
3. **Functional Patterns**: Defer refactoring, create REFACTORING-PARSERS.md
4. **CHANGELOG**: Manual consolidation (spawn subagent)

### Subagent Strategy
**Use subagents for EVERYTHING to minimize context bloat:**
- Each task = 1 focused subagent
- Each subagent commits before completing
- Pass only essential context between subagents
- Use house-bash for all command execution
- Use house-research for multi-file searches
- Use general-purpose for code changes and documentation

---

## 📋 PHASE 0: Emergency Syntax Fix (P0 - BLOCKING)

### Task 0.1: Fix parser.py Syntax Errors

**Subagent Type**: `quick-code-patch`
**Model**: `haiku` (fast, simple fixes)
**Estimated Time**: 15 minutes

**Context to Provide**:
```
CRITICAL: src/omniparser/parser.py has syntax errors preventing all tests from running.

ISSUES TO FIX:

1. Lines 147-160: Multiple duplicate get_supported_formats() function definitions
   - Currently has 4 conflicting versions from merge conflicts
   - Consolidate to single function returning: [".epub", ".pdf", ".html", ".htm", ".docx", ".md", ".markdown", ".txt"]

2. Lines 139-143: Duplicate error message strings
   - Multiple "Supported formats:" strings
   - Keep single consolidated message listing all 8 formats

3. Lines 30-42: Duplicate docstring sections
   - Multiple "Currently supported formats:" sections
   - Clean up to single accurate docstring

REQUIREMENTS:
- Read src/omniparser/parser.py
- Fix all 3 syntax error locations
- Ensure all 6 parsers are registered (EPUB, HTML, PDF, DOCX, Markdown, Text)
- Format with Black after fixes
- Run: uv run python -c "import omniparser; print('Import successful')"
- Commit with: "fix: Resolve parser.py syntax errors from merge conflicts"
```

**Success Criteria**: ✅ parser.py imports without errors

---

### Task 0.2: Verify Tests Can Run

**Subagent Type**: `house-bash`
**Estimated Time**: 5 minutes

**Context to Provide**:
```
Now that parser.py is fixed, verify the test suite can be collected and started.

Run these commands:
1. uv run pytest --collect-only (should collect 357 tests)
2. uv run pytest -x -v (run tests, stop on first failure)

Report:
- How many tests were collected?
- Did any tests fail? If so, which ones and why?
- Overall test suite health assessment

DO NOT fix test failures yet - just report status.
```

**Success Criteria**: ✅ Tests can be collected and executed

---

## 📋 PHASE 1: CHANGELOG Consolidation (P1 - High Priority)

### Task 1.1: CHANGELOG Manual Consolidation

**Subagent Type**: `general-purpose`
**Model**: `sonnet` (needs intelligence for deduplication)
**Estimated Time**: 2 hours

**Context to Provide**:
```
TASK: Manually consolidate CHANGELOG.md which has 9 duplicate "[Unreleased]" sections from merge conflicts.

CURRENT STATE:
- CHANGELOG.md has duplicate sections at lines: 8, 114, 215, 309, 400, 482, 530, 596, 652, 703, 754, 796, 838, 868, 895, 918
- Each merge added its own section without removing previous ones
- Total: 1,095 lines with massive redundancy

REQUIREMENTS:
1. Read CHANGELOG.md carefully
2. Extract ALL unique changes from all 9 "[Unreleased]" sections
3. Consolidate into SINGLE "[Unreleased]" section at top
4. Organize by standard categories:
   - ### Added
   - ### Changed
   - ### Fixed
   - ### Removed
5. Remove all duplicate entries
6. Preserve all unique information
7. Keep chronological order within categories (newest first)
8. Maintain proper markdown formatting
9. Write consolidated CHANGELOG.md

EXPECTED CHANGES:
- 6 parsers in "Added": EPUB, HTML, PDF, DOCX, Markdown, Text
- AI features in "Added": Config, Summarizer, Tagger, Quality Scorer, Image Analyzer, Image Describer
- Test fixtures in "Added": PDF (5 files), Markdown (8 files), Text (10 files), Images (10 files)
- Documentation updates
- Any bug fixes

After consolidation:
1. Verify SINGLE "[Unreleased]" section exists
2. Verify all parsers/features are mentioned
3. Format with proper markdown
4. Commit with: "docs: Consolidate CHANGELOG with 9 duplicate sections from merges"

COMMIT IMMEDIATELY after creating the consolidated CHANGELOG.
```

**Success Criteria**: ✅ Single clean "[Unreleased]" section with all changes

---

## 📋 PHASE 2: Documentation Updates (P1 - High Priority)

### Task 2.1: Update README.md

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 1.5 hours

**Context to Provide**:
```
TASK: Update README.md to reflect current state (6 parsers + AI features, Phase 2.8 complete)

CURRENT README ISSUES:
- Line 3: Claims "Phase 2.5 Complete" → Should be "Phase 2.8 Complete"
- Lines 17-24: Parser table outdated → Missing 4 new parsers
- Lines 81-138: "What Works Today" → Doesn't mention PDF/DOCX/Markdown/Text parsers
- Missing: AI features section

CHANGES REQUIRED:

1. **Status Update** (Line 3):
   FROM: "Phase 2.5 Complete - HTML Parser Production-Ready"
   TO: "Phase 2.8 Complete - 6 Parsers + AI Features (v0.3.0)"

2. **Parser Status Table** (Lines 17-24):
   Add complete table with all 6 parsers:
   | Parser | Status | Features |
   |--------|--------|----------|
   | EPUB | ✅ Production | TOC chapters, images, metadata |
   | HTML | ✅ Production | Semantic parsing, URL support, images |
   | PDF | ✅ Production | Multi-column, images, tables |
   | DOCX | 🔶 Beta | Text, tables, basic images |
   | Markdown | ✅ Production | Frontmatter, code blocks, links |
   | Text | ✅ Production | Auto chapter detection, encoding |

3. **What Works Today** (Lines 81-138):
   Rewrite to showcase all 6 parsers with examples

4. **Add AI Features Section** (after parser features):
   ### AI-Powered Features (Optional)
   - Document Summarization
   - Auto-Tagging
   - Quality Scoring
   - Image Analysis & Description
   - Configurable AI providers (Anthropic, OpenRouter)

5. **Update Installation/Usage** if needed

Read README.md, make ALL changes above, commit with:
"docs: Update README to reflect 6 parsers and AI features (Phase 2.8)"
```

**Success Criteria**: ✅ README accurately describes current state

---

### Task 2.2: Update TODOS.md

**Subagent Type**: `general-purpose`
**Model**: `haiku` (simple status update)
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Update TODOS.md to reflect completed parsers and current priorities

CHANGES REQUIRED:

1. Update header status:
   FROM: "Phase 2.5 Complete"
   TO: "Phase 2.8 Complete - 6 Parsers + AI Features"

2. Move completed items from "Planned" to "Completed":
   - PDF Parser ✅ (Phase 2.6)
   - DOCX Parser 🔶 (Phase 2.7 - Beta)
   - Markdown Parser ✅ (Phase 2.8)
   - Text Parser ✅ (Phase 2.8)
   - AI Features ✅ (Phase 2.8)

3. Add new high-priority items:
   - [ ] DOCX Parser - Complete Beta Features (lists, hyperlinks)
   - [ ] Parser Refactoring (see REFACTORING-PARSERS.md)
   - [ ] Production Hardening & Error Handling
   - [ ] Performance Optimization

4. Update dates to 2025-10-29

Read TODOS.md, make updates, commit with:
"docs: Update TODOS.md to reflect Phase 2.8 completion"
```

**Success Criteria**: ✅ TODOS.md shows correct status

---

### Task 2.3: Update CLAUDE.md Project Overview

**Subagent Type**: `general-purpose`
**Model**: `haiku`
**Estimated Time**: 45 minutes

**Context to Provide**:
```
TASK: Update CLAUDE.md project overview section to reflect current state

LOCATION: Lines 5-30 (Project Overview section)

CHANGES REQUIRED:

1. Update Status Line:
   FROM: "Phase 2.3 Complete - EPUB Parser Production-Ready (v0.1.0)"
   TO: "Phase 2.8 Complete - 6 Parsers + AI Features (v0.3.0)"

2. Update Tech Stack:
   Add AI dependencies:
   - anthropic SDK (Claude API)
   - OpenRouter support
   - Vision API integration

3. Update Architecture section:
   - Format-specific parsers: 6 implemented (EPUB ✅, HTML ✅, PDF ✅, DOCX 🔶 beta, Markdown ✅, Text ✅)
   - Add: AI processors (5 modules: summarizer, tagger, quality, image_analyzer, image_describer)

4. Update test statistics:
   FROM: "(357 tests, 100% passing)"
   TO: Current count from test suite

5. Keep "Key Resources" section as-is (docs are still valid)

Read CLAUDE.md, update Project Overview section only, commit with:
"docs: Update CLAUDE.md project overview to Phase 2.8"
```

**Success Criteria**: ✅ CLAUDE.md reflects current state

---

### Task 2.4: Update docs/NEXT_STEPS.md

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 45 minutes

**Context to Provide**:
```
TASK: Rewrite docs/NEXT_STEPS.md to reflect completed work and future priorities

CURRENT PROBLEM:
- docs/NEXT_STEPS.md references Phase 2.3 (EPUB parser)
- Completely outdated - doesn't know about 4 new parsers or AI features

NEW CONTENT STRUCTURE:

# Next Steps for OmniParser

## What's Been Completed (Phase 2.8)

### Parsers (6 total)
- ✅ EPUB Parser (v0.1.0) - Production-ready
- ✅ HTML Parser (v0.2.0) - Production-ready
- ✅ PDF Parser (v0.3.0) - Production-ready
- 🔶 DOCX Parser (v0.3.0) - Beta (core features complete)
- ✅ Markdown Parser (v0.3.0) - Production-ready
- ✅ Text Parser (v0.3.0) - Production-ready

### AI Features (v0.3.0)
- ✅ Document Summarization
- ✅ Auto-Tagging
- ✅ Quality Scoring
- ✅ Image Analysis & Description
- ✅ Multi-provider support (Anthropic, OpenRouter)

## Immediate Priorities (Phase 2.9)

### 1. Code Quality & Standardization
- Standardize import organization across parsers
- Extract shared image extraction logic
- Extract shared metadata building logic
- Complete DOCX parser beta features

### 2. Testing & Validation
- Run comprehensive test suite with all fixtures
- Validate all 6 parsers with real documents
- Test AI features end-to-end

### 3. Production Hardening
- Comprehensive error handling
- Input validation
- Resource management (memory, file handles)
- Timeout handling

## Future Work (Phase 3.0+)

### Parser Refactoring
See REFACTORING-PARSERS.md for detailed plan
- Break large parser files into focused modules (50-200 lines)
- Follow FUNCTIONAL_PATTERNS.md guidelines
- Improve testability

### New Features
- Batch processing
- Streaming for large files
- Plugin architecture
- Additional format support (RTF, ODT, etc.)

---

Read docs/NEXT_STEPS.md, REWRITE entirely with above structure, commit with:
"docs: Update NEXT_STEPS.md with Phase 2.8 completion and future roadmap"
```

**Success Criteria**: ✅ NEXT_STEPS.md shows accurate roadmap

---

## 📋 PHASE 3: Code Quality Improvements (P2 - Medium Priority)

### Task 3.1: Document DOCX Parser Beta Status

**Subagent Type**: `quick-code-patch`
**Model**: `haiku`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Add "Beta Status" section to DOCX parser docstring documenting limitations

FILE: src/omniparser/parsers/docx_parser.py

CHANGES:

1. Add to class docstring (after main description):

    **Beta Status - Core Features Complete**

    Currently implemented:
    - Text extraction from paragraphs
    - Basic table extraction
    - Image extraction (embedded images)
    - Basic formatting (bold, italic, underline)
    - Metadata extraction

    Not yet implemented (TODO for future versions):
    - List conversion (bullets and numbered lists)
    - Hyperlink extraction and conversion to markdown
    - Complex table structures with merged cells
    - Advanced formatting (styles, colors, fonts)
    - Footnotes and endnotes
    - Comments and track changes

2. Update README.md parser table to mark DOCX as "🔶 Beta"

3. Commit with: "docs: Document DOCX parser beta status and limitations"
```

**Success Criteria**: ✅ DOCX limitations clearly documented

---

### Task 3.2: Standardize Import Organization

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 2 hours

**Context to Provide**:
```
TASK: Standardize import organization across ALL parser files

TARGET FILES:
- src/omniparser/parsers/epub_parser.py
- src/omniparser/parsers/html_parser.py
- src/omniparser/parsers/pdf_parser.py
- src/omniparser/parsers/docx_parser.py
- src/omniparser/parsers/markdown_parser.py
- src/omniparser/parsers/text_parser.py

STANDARD ORDER (per PEP 8):
1. Standard library imports (alphabetical)
2. Third-party imports (alphabetical)
3. Local imports (alphabetical)
4. Blank line between each group

EXAMPLE:
```python
# Standard library
import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party
import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

# Local
from ..base.base_parser import BaseParser
from ..exceptions import ParsingError
from ..models import Chapter, Document, Metadata
```

PROCESS:
1. Read each parser file
2. Reorganize imports following standard order
3. Run: uv run black src/omniparser/parsers/
4. Verify imports still work: uv run python -c "from omniparser.parsers import *"
5. Commit with: "style: Standardize import organization across all parsers"
```

**Success Criteria**: ✅ All parsers have consistent import order

---

### Task 3.3: Extract Shared Image Extraction Logic

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 3 hours

**Context to Provide**:
```
TASK: Create shared image extraction module and refactor parsers to use it

PROBLEM: Duplicate image extraction code in EPUB, PDF, DOCX parsers

STEPS:

1. CREATE: src/omniparser/processors/image_extractor.py

```python
"""Shared image extraction utilities for all parsers."""

from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import base64

logger = logging.getLogger(__name__)

class ImageExtractor:
    """Base class for extracting images from documents."""

    @staticmethod
    def save_image(
        image_data: bytes,
        output_dir: Path,
        base_name: str,
        extension: str = "png"
    ) -> str:
        """
        Save image data to file with auto-numbering.

        Args:
            image_data: Raw image bytes
            output_dir: Directory to save images
            base_name: Base filename (e.g., "image")
            extension: File extension (e.g., "png", "jpg")

        Returns:
            Relative path to saved image
        """
        # Implementation here
        pass

    @staticmethod
    def extract_base64_image(
        base64_str: str,
        output_dir: Path,
        image_name: str
    ) -> Optional[str]:
        """Extract and save base64-encoded image."""
        # Implementation here
        pass
```

2. REFACTOR each parser to use ImageExtractor:
   - epub_parser.py: Replace _extract_images() logic
   - pdf_parser.py: Replace _extract_images() logic
   - docx_parser.py: Replace _extract_images() logic

3. CREATE: tests/unit/test_image_extractor.py
   - Test save_image()
   - Test extract_base64_image()
   - Test auto-numbering
   - Test error handling

4. Run tests: uv run pytest tests/unit/test_image_extractor.py

5. Commit with: "refactor: Extract shared image extraction logic to processor module"
```

**Success Criteria**: ✅ DRY image extraction, parsers use shared code

---

### Task 3.4: Extract Shared Metadata Building Logic

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 2 hours

**Context to Provide**:
```
TASK: Create shared metadata builder and refactor parsers to use it

PROBLEM: Every parser has similar _build_metadata() with slightly different defaults

STEPS:

1. CREATE: src/omniparser/processors/metadata_builder.py

```python
"""Shared metadata building utilities for all parsers."""

from datetime import datetime
from typing import Optional
from ..models import Metadata

class MetadataBuilder:
    """Helper for building Metadata objects with sensible defaults."""

    @staticmethod
    def build(
        title: Optional[str] = None,
        author: Optional[str] = None,
        language: Optional[str] = None,
        created_date: Optional[str] = None,
        publisher: Optional[str] = None,
        isbn: Optional[str] = None,
        source_format: Optional[str] = None,
        **extra_fields
    ) -> Metadata:
        """
        Build Metadata with defaults.

        Defaults:
        - title: "Unknown" if None
        - author: "Unknown" if None
        - language: "en" if None
        - created_date: current ISO timestamp if None
        """
        return Metadata(
            title=title or "Unknown",
            author=author or "Unknown",
            language=language or "en",
            created_date=created_date or datetime.now().isoformat(),
            publisher=publisher,
            isbn=isbn,
            source_format=source_format,
            **extra_fields
        )
```

2. REFACTOR all 6 parsers to use MetadataBuilder.build()

3. CREATE: tests/unit/test_metadata_builder.py

4. Run tests: uv run pytest tests/unit/test_metadata_builder.py

5. Commit with: "refactor: Extract shared metadata building logic to processor"
```

**Success Criteria**: ✅ Consistent metadata defaults across parsers

---

### Task 3.5: Add Missing Type Hints

**Subagent Type**: `general-purpose`
**Model**: `haiku`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Add missing type hints, especially in AI modules

TARGET FILES:
- src/omniparser/processors/ai_*.py (5 files)
- src/omniparser/utils/*.py

FOCUS:
1. Replace generic `Any` types with specific types where possible
2. Add return type hints to utility functions
3. Add parameter type hints where missing

PROCESS:
1. Run: uv run mypy src/omniparser/ --strict
2. Fix any type hint issues found
3. Run: uv run mypy src/omniparser/ (should pass)
4. Commit with: "style: Add missing type hints across AI and utility modules"
```

**Success Criteria**: ✅ mypy passes with better type coverage

---

## 📋 PHASE 4: Future Planning Documentation (P3 - Low Priority)

### Task 4.1: Create REFACTORING-PARSERS.md

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 1 hour

**Context to Provide**:
```
TASK: Create comprehensive parser refactoring plan document

CREATE: docs/REFACTORING-PARSERS.md

CONTENT:

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

---

Commit with: "docs: Add comprehensive parser refactoring plan (Phase 3.0)"
```

**Success Criteria**: ✅ Clear roadmap for future refactoring

---

### Task 4.2: Add CHANGELOG Strategy to CLAUDE.md

**Subagent Type**: `quick-code-patch`
**Model**: `haiku`
**Estimated Time**: 15 minutes

**Context to Provide**:
```
TASK: Add section to CLAUDE.md about preventing future CHANGELOG corruption

FILE: CLAUDE.md

LOCATION: Add new section after "Git Commit Standards" (around line 60)

NEW SECTION:

---

## CHANGELOG Management

**CRITICAL:** Follow this strategy to prevent future CHANGELOG corruption

### Current Issue (Resolved Oct 29, 2025)
Multiple parallel branches each added their own "[Unreleased]" section, causing 9 duplicate sections when merged. This was manually consolidated.

### Prevention Strategy (Going Forward)

1. **Single Source of Truth**
   - Only ONE "[Unreleased]" section should ever exist at the top of CHANGELOG.md
   - Before starting work on a branch, pull latest CHANGELOG.md
   - Add your changes to the EXISTING "[Unreleased]" section

2. **Merge Conflict Resolution**
   - When merging, if there are CHANGELOG conflicts:
   - Keep only ONE "[Unreleased]" section
   - Merge all unique entries from both branches
   - Remove duplicate entries
   - Preserve chronological order (newest first)

3. **Automation Option (Future)**
   - Consider using git-cliff or keep-a-changelog tools
   - Generate CHANGELOG from conventional commit messages
   - Reduces manual maintenance burden

4. **Pre-Merge Checklist**
   - [ ] Only one "[Unreleased]" section exists
   - [ ] All new features/fixes are documented
   - [ ] No duplicate entries
   - [ ] Proper categorization (Added/Changed/Fixed/Removed)

### CHANGELOG Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features

## [0.3.0] - 2025-10-29
...
```

---

Commit with: "docs: Add CHANGELOG management strategy to prevent future corruption"
```

**Success Criteria**: ✅ CLAUDE.md documents CHANGELOG strategy

---

## 📋 PHASE 5: Verification & Testing (Critical)

### Task 5.1: Run Complete Test Suite

**Subagent Type**: `house-bash`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Run comprehensive test suite and report results

COMMANDS:

1. Run full test suite with coverage:
   uv run pytest --cov=omniparser --cov-report=term --cov-report=html -v

2. Check test count:
   uv run pytest --collect-only | grep "test session starts"

3. Run tests by category:
   - Unit tests: uv run pytest tests/unit/ -v
   - Integration tests: uv run pytest tests/integration/ -v

4. Check for any skipped/xfailed tests:
   uv run pytest --runxfail -v

REPORT:
- Total tests collected: ???
- Tests passed: ???
- Tests failed: ??? (list failures)
- Tests skipped: ??? (list skips)
- Coverage percentage: ???%
- Any concerning patterns?
- Recommendations for fixes

DO NOT fix failures yet - just report comprehensive status.
```

**Success Criteria**: ✅ Full visibility into test suite health

---

### Task 5.2: Test All Parsers with Real Fixtures

**Subagent Type**: `house-bash`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Manually test each parser with actual fixture files

TEST COMMANDS:

1. EPUB (6 fixtures):
   for file in tests/fixtures/epub/*.epub; do
     echo "Testing: $file"
     uv run python -c "from omniparser import parse_document; doc = parse_document('$file'); print(f'✓ {doc.metadata.title}')"
   done

2. PDF (5 fixtures):
   for file in tests/fixtures/pdf/*.pdf; do
     echo "Testing: $file"
     uv run python -c "from omniparser import parse_document; doc = parse_document('$file'); print(f'✓ {doc.metadata.title}')"
   done

3. HTML (6 fixtures):
   for file in tests/fixtures/html/*.html; do
     echo "Testing: $file"
     uv run python -c "from omniparser import parse_document; doc = parse_document('$file'); print(f'✓ Chapters: {len(doc.chapters)}')"
   done

4. Markdown (8 fixtures):
   for file in tests/fixtures/markdown/*.md; do
     echo "Testing: $file"
     uv run python -c "from omniparser import parse_document; doc = parse_document('$file'); print(f'✓ {doc.metadata.title}')"
   done

5. Text (10 fixtures):
   for file in tests/fixtures/text/*.txt; do
     echo "Testing: $file"
     uv run python -c "from omniparser import parse_document; doc = parse_document('$file'); print(f'✓ Chapters: {len(doc.chapters)}')"
   done

REPORT:
- Which parsers work correctly?
- Any failures? (file path + error message)
- Any concerning patterns?
```

**Success Criteria**: ✅ All parsers work with real files

---

### Task 5.3: Test AI Features (If API Keys Available)

**Subagent Type**: `house-bash`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Test AI features if API keys are available

PRELIMINARY CHECK:
1. Check if secrets.json exists
2. Check if ANTHROPIC_API_KEY or OPENROUTER_API_KEY are set

If API keys available:

TEST AI SUMMARIZER:
uv run python -c "
from omniparser import parse_document
from omniparser.processors.ai_summarizer import AISummarizer
doc = parse_document('tests/fixtures/epub/simple.epub')
summarizer = AISummarizer()
summary = summarizer.summarize(doc)
print(f'✓ Summary: {summary[:100]}...')
"

TEST AI TAGGER:
uv run python -c "
from omniparser import parse_document
from omniparser.processors.ai_tagger import AITagger
doc = parse_document('tests/fixtures/epub/simple.epub')
tagger = AITagger()
tags = tagger.generate_tags(doc)
print(f'✓ Tags: {tags}')
"

TEST IMAGE ANALYZER (with test fixtures):
uv run python -c "
from omniparser.processors.ai_image_analyzer import AIImageAnalyzer
analyzer = AIImageAnalyzer()
result = analyzer.analyze('tests/fixtures/images/test_image.jpg')
print(f'✓ Analysis: {result}')
"

REPORT:
- Are API keys available?
- Which AI features work?
- Any failures?
- Response quality acceptable?

If no API keys: Report "AI features not tested (no API keys)"
```

**Success Criteria**: ✅ AI features verified (if possible)

---

## 📋 PHASE 6: Git Commits & Release Prep (Final)

### Task 6.1: Review Git History

**Subagent Type**: `house-bash`
**Estimated Time**: 15 minutes

**Context to Provide**:
```
TASK: Review git commit history from this cleanup session

COMMANDS:

1. Show commits since start of cleanup:
   git log --oneline --since="2025-10-29 18:00" --graph

2. Show detailed stats:
   git log --since="2025-10-29 18:00" --stat --oneline

3. Verify commit message format:
   git log --since="2025-10-29 18:00" --pretty=format:"%h %s" | head -20

4. Check for any uncommitted changes:
   git status

5. Check branch status:
   git branch -v

REPORT:
- How many commits created during cleanup?
- All follow conventional commit format?
- Any uncommitted changes remaining?
- Recommended next steps?
```

**Success Criteria**: ✅ Clean git history, all work committed

---

### Task 6.2: Version Bump Preparation

**Subagent Type**: `general-purpose`
**Model**: `haiku`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Update version numbers for v0.3.0 release

CURRENT VERSION: Likely v0.2.0 or similar
TARGET VERSION: v0.3.0 (major feature release: 4 new parsers + AI features)

FILES TO UPDATE:

1. pyproject.toml:
   - version = "0.3.0"

2. src/omniparser/__init__.py:
   - __version__ = "0.3.0"

3. README.md:
   - Any version references

4. CHANGELOG.md:
   - Change "[Unreleased]" to "[0.3.0] - 2025-10-29"
   - Add new empty "[Unreleased]" section at top

PROCESS:
1. Read current version from pyproject.toml
2. Update all files listed above
3. Verify: uv run python -c "import omniparser; print(omniparser.__version__)"
4. Commit with: "chore: Bump version to 0.3.0 for release"

DO NOT create git tag yet - just update version numbers.
```

**Success Criteria**: ✅ Version numbers updated to 0.3.0

---

### Task 6.3: Final Cleanup Report

**Subagent Type**: `general-purpose`
**Model**: `sonnet`
**Estimated Time**: 30 minutes

**Context to Provide**:
```
TASK: Generate comprehensive cleanup completion report

CREATE: docs/cleanup-report-2025-10-29.md

CONTENT STRUCTURE:

# OmniParser Cleanup Report - October 29, 2025

## Executive Summary
- Cleanup Duration: [start time] to [end time]
- Total Time: X hours
- Commits Created: X
- Files Modified: X
- Lines Changed: +X -X

## Objectives Completed

### Phase 0: Emergency Fixes ✅
- [ ] Fixed parser.py syntax errors
- [ ] Verified tests can run

### Phase 1: CHANGELOG ✅
- [ ] Consolidated 9 duplicate sections
- [ ] Single clean "[Unreleased]" section

### Phase 2: Documentation Updates ✅
- [ ] Updated README.md
- [ ] Updated TODOS.md
- [ ] Updated CLAUDE.md
- [ ] Updated NEXT_STEPS.md

### Phase 3: Code Quality ✅
- [ ] Documented DOCX beta status
- [ ] Standardized imports
- [ ] Extracted shared image extraction
- [ ] Extracted shared metadata building
- [ ] Added missing type hints

### Phase 4: Future Planning ✅
- [ ] Created REFACTORING-PARSERS.md
- [ ] Added CHANGELOG strategy to CLAUDE.md

### Phase 5: Verification ✅
- [ ] Test suite status: X/357 passing
- [ ] All parsers tested with fixtures
- [ ] AI features tested (if applicable)

### Phase 6: Release Prep ✅
- [ ] Git history reviewed
- [ ] Version bumped to 0.3.0
- [ ] Ready for release

## Test Results Summary
[Paste results from Task 5.1]

## Known Issues
[List any remaining issues found during testing]

## Recommendations

### Immediate (Before Release)
- [ ] Any critical fixes needed

### Short-term (Phase 2.9)
- [ ] Complete DOCX beta features
- [ ] Production hardening
- [ ] Performance optimization

### Long-term (Phase 3.0+)
- [ ] Parser refactoring (see REFACTORING-PARSERS.md)
- [ ] Plugin architecture
- [ ] Additional format support

## Conclusion

The OmniParser "Big Cleanup" phase successfully addressed all critical issues resulting from the rapid 5-branch merge on October 29, 2025. The codebase is now:

✅ Functional (no syntax errors)
✅ Documented (all docs reflect current state)
✅ Tested (comprehensive test suite)
✅ Standardized (consistent code quality)
✅ Ready for v0.3.0 release

**Recommendation:** Proceed with v0.3.0 release after final review.

---

**Report Generated:** [timestamp]
**Cleanup Session ID:** YOLO-2025-10-29

---

Commit with: "docs: Add cleanup completion report (Phase 2.9)"
```

**Success Criteria**: ✅ Comprehensive cleanup report generated

---

## 🎯 FINAL CHECKLIST FOR YOLO EXECUTION

Before marking this plan complete, verify:

- [ ] **P0 Fixed**: parser.py imports without errors
- [ ] **Tests Run**: pytest can collect and run tests
- [ ] **CHANGELOG**: Single clean "[Unreleased]" section
- [ ] **README**: Shows 6 parsers + AI features, Phase 2.8
- [ ] **TODOS.md**: Completed parsers moved from "Planned"
- [ ] **CLAUDE.md**: Project overview updated to Phase 2.8
- [ ] **NEXT_STEPS.md**: Rewritten with current state
- [ ] **DOCX Beta**: Limitations documented
- [ ] **Imports**: Standardized across all parsers
- [ ] **Image Extract**: Shared processor created
- [ ] **Metadata Build**: Shared processor created
- [ ] **Type Hints**: Added to AI modules
- [ ] **REFACTORING.md**: Parser refactoring plan created
- [ ] **CHANGELOG Strategy**: Documented in CLAUDE.md
- [ ] **Tests**: Full suite run and results documented
- [ ] **Fixtures**: All parsers tested with real files
- [ ] **AI Features**: Tested (if API keys available)
- [ ] **Git History**: All work committed, clean history
- [ ] **Version**: Bumped to 0.3.0
- [ ] **Report**: Cleanup report generated

---

## 💡 SUBAGENT USAGE NOTES FOR YOLO MODE

### Context Management Strategy

**Keep context minimal for each subagent:**
- ✅ DO: Reference files by path (let subagent read them)
- ✅ DO: List specific tasks and requirements
- ✅ DO: Include commit message templates
- ❌ DON'T: Paste entire file contents
- ❌ DON'T: Include irrelevant project history
- ❌ DON'T: Repeat information subagent can discover

**Target context per subagent: <4000 tokens**

### Commit Strategy

**Every subagent MUST commit before completing:**
1. Complete assigned task
2. Review changes: `git diff`
3. Stage: `git add .`
4. Commit: `git commit -m "<type>: <description>"`
5. Report commit hash in completion artifact

**Commit types by phase:**
- Emergency fixes (P0): `fix:`
- Documentation (P1/P2): `docs:`
- Code quality (P2): `refactor:`, `style:`
- Planning (P3): `docs:`
- Testing (P5): `test:`, `docs:`
- Release (P6): `chore:`

### Subagent Selection Guide

| Task Type | Recommended Subagent | Model |
|-----------|---------------------|-------|
| Simple syntax fixes | `quick-code-patch` | `haiku` |
| Command execution | `house-bash` | `haiku` |
| Multi-file search | `house-research` | `haiku` |
| Documentation writing | `general-purpose` | `sonnet` |
| Code refactoring | `general-purpose` | `sonnet` |
| Code quality tasks | `general-purpose` | `haiku` |
| Architecture docs | `general-purpose` | `sonnet` |

### Execution Order

Execute tasks **SEQUENTIALLY** within each phase:
- Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Within phases, tasks can run in parallel if they don't depend on each other.

**Dependencies:**
- Task 0.2 depends on Task 0.1 (must fix syntax before testing)
- All Phase 2+ tasks depend on Task 0.1 (parser must import)
- Task 6.2 depends on all previous phases (version bump is last)

---

## 🚀 START EXECUTION

**User Instructions:**
1. Copy this entire PLANS.md file
2. Start new Claude Code session with YOLO permissions
3. Provide this file and say: "Execute this plan systematically. Use subagents for every task as specified. Report progress after each phase."
4. Go get dinner! 🍕

**Expected Outcome:**
- Duration: 2-3 hours of execution time
- Commits: ~15-20 atomic commits
- Result: Clean, documented, tested codebase ready for v0.3.0 release

---

**Plan Version:** 1.0
**Created:** 2025-10-29
**Strategy:** Subagent-First Development with Atomic Commits
**Mode:** YOLO (Auto-approve)

---

## 📞 Support & Troubleshooting

If execution encounters issues:

1. **Syntax errors persist after Task 0.1:**
   - Manually review parser.py lines 30-160
   - Look for unclosed strings, missing colons, indent issues

2. **Tests won't run after syntax fix:**
   - Check imports: `uv run python -c "import omniparser"`
   - Check dependencies: `uv sync`
   - Review test collection: `uv run pytest --collect-only`

3. **Subagent fails to commit:**
   - Check for uncommitted changes: `git status`
   - Review git config: `git config user.name`, `git config user.email`
   - Retry with explicit commit message

4. **Context overflow:**
   - Reduce context in subagent prompt
   - Use file references instead of inline content
   - Split task into smaller subtasks

5. **Merge conflicts:**
   - Shouldn't happen (no parallel branches)
   - If occurs, favor "current" (working) version

---

**Ready for YOLO execution. Good luck! 🚀**
