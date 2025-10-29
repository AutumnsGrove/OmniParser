# Session: epub2tts → OmniParser Migration

**Copy this entire prompt into a new Claude Code session in the epub2tts project**

---

## 📋 Session Metadata

| Field | Value |
|-------|-------|
| **Session ID** | SESSION_EPUB2TTS_MIGRATION |
| **Project** | epub2tts (NOT OmniParser!) |
| **Branch Name** | `feat/integrate-omniparser` |
| **PR Title** | `feat: Migrate to OmniParser for EPUB parsing (v0.2.0)` |
| **Estimated Duration** | 5-6 hours |
| **Prerequisites** | OmniParser v0.1.0+ available |
| **Target Lines** | Remove 965 lines, add ~150 (adapter) = -815 net |
| **Deliverable** | epub2tts v0.2.0 using OmniParser, full TTS pipeline tested |

---

## 🎯 Mission

Migrate epub2tts (v0.1.0 → v0.2.0) from internal EPUB processing (`ebooklib_processor.py` - 965 lines) to use OmniParser as an external dependency. Go all-in: remove legacy processor completely after validation. Test full TTS pipeline to ensure end-to-end compatibility.

## 📋 Context

**Projects:**
- **epub2tts:** `/Users/mini/Documents/GitHub/epub2tts` (your current working directory)
- **OmniParser:** `/Users/mini/Documents/GitHub/OmniParser` (dependency location)

**Current state:**
- epub2tts: v0.1.0 (production TTS converter)
- Internal EPUB processing: 965 lines in `src/core/ebooklib_processor.py`
- Test status: All epub2tts tests should pass
- Strategy: **Go all-in** (no legacy fallback after validation)

**Key documents to read:**
1. `docs/CLAUDE_CODE_EPUB2TTS_MIGRATION_GUIDE.md` in OmniParser repo (full guide)
2. This session prompt (streamlined execution)

## 🎯 Success Criteria

- ✅ OmniParser installed as dependency (>=0.1.0)
- ✅ epub2tts uses `omniparser.parse_document()` for EPUB parsing
- ✅ ebooklib_processor.py removed (965 lines deleted)
- ✅ All epub2tts tests pass (100% compatibility)
- ✅ **Full TTS pipeline tested** (EPUB → audiobook)
- ✅ No performance regression >20%
- ✅ Version bumped to v0.2.0
- ✅ Documentation updated

## 📐 Architecture

### Before Migration
```
epub2tts → EbookLibProcessor (965 lines) → TextCleaner → TTS Pipeline
```

### After Migration
```
epub2tts → OmniParser (external) → OmniParserAdapter → TextCleaner → TTS Pipeline
                                         (150 lines)
```

## 🚀 Execution Plan

### Phase 0: Pre-Flight (15 minutes)

1. **Navigate to epub2tts:**
   ```bash
   cd /Users/mini/Documents/GitHub/epub2tts
   pwd  # Should be /Users/mini/Documents/GitHub/epub2tts
   ```

2. **Create feature branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/integrate-omniparser
   git push -u origin feat/integrate-omniparser
   ```

3. **Check current status:**
   ```bash
   ls -la src/core/ebooklib_processor.py
   wc -l src/core/ebooklib_processor.py
   uv run pytest --collect-only
   ```

4. **Verify OmniParser exists:**
   ```bash
   ls -la /Users/mini/Documents/GitHub/OmniParser/
   cat /Users/mini/Documents/GitHub/OmniParser/pyproject.toml | grep version
   ```

---

### Phase 1: Add OmniParser Dependency (30 minutes)

#### Step 1: Install OmniParser (15 min)

```bash
# Add OmniParser as local editable dependency
uv add --editable /Users/mini/Documents/GitHub/OmniParser

# Verify installation
uv run python -c "import omniparser; print(f'OmniParser {omniparser.__version__} installed')"

# Test basic functionality
uv run python -c "
from omniparser import parse_document
from pathlib import Path
doc = parse_document(Path('A System for Writing.epub'))
print(f'✓ Parsed: {doc.metadata.title}')
print(f'✓ Chapters: {len(doc.chapters)}')
print(f'✓ Full text length: {len(doc.full_text)} chars')
"
```

**Commit:**
```bash
git add pyproject.toml uv.lock
git commit -m "deps: Add OmniParser dependency for EPUB parsing"
git push origin feat/integrate-omniparser
```

#### Step 2: Update pyproject.toml (5 min)

Edit `pyproject.toml` to include:
```toml
[project.dependencies]
omniparser = ">=0.1.0"  # Accept 0.1.0 and up (NOT >=1.0.0!)
```

**CRITICAL:** Use `>=0.1.0`, not `>=1.0.0` (version 1.0 not released yet)

**Commit:** `deps: Add OmniParser version constraint (>=0.1.0)`

#### Step 3: Document Data Models (10 min)

**Use `house-research` subagent:**

Create `docs/integration/omniparser-data-mapping.md` with field mappings:

```
epub2tts.EbookMetadata → omniparser.Metadata
epub2tts.Chapter → omniparser.Chapter
epub2tts.ProcessingResult ← OmniParserAdapter
```

**Commit:** `docs: Add OmniParser data model mapping`

---

### Phase 2: Create Adapter Layer (60 minutes)

#### Step 1: Implement Adapter (45 min)

**Use `house-coder` subagent:**

Create `src/core/omniparser_adapter.py` (~150-180 lines):

```python
"""Adapter layer for OmniParser integration."""

from pathlib import Path
from typing import Optional, List, Dict
import time

from omniparser import parse_document
from omniparser.models import Document as OmniDocument

from .ebooklib_processor import EbookMetadata, Chapter, ProcessingResult


class OmniParserAdapter:
    """
    Adapter for integrating OmniParser with epub2tts.

    Converts OmniParser's Document model to epub2tts's ProcessingResult model,
    maintaining backward compatibility with existing epub2tts pipeline.
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize adapter with optional configuration."""
        self.config = config or {}

    def process_epub(
        self,
        epub_path: Path,
        output_dir: Optional[Path] = None
    ) -> ProcessingResult:
        """
        Process EPUB using OmniParser and convert to epub2tts format.

        Args:
            epub_path: Path to EPUB file
            output_dir: Optional directory for extracted images

        Returns:
            ProcessingResult compatible with epub2tts pipeline
        """
        start_time = time.time()

        try:
            # Parse with OmniParser
            omni_doc = parse_document(epub_path, output_dir=output_dir)

            # Convert to epub2tts format
            metadata = self._convert_metadata(omni_doc.metadata, omni_doc)
            chapters = self._convert_chapters(omni_doc.chapters)
            image_info = self._convert_images(omni_doc.images)

            processing_time = time.time() - start_time

            # Build ProcessingResult
            return ProcessingResult(
                success=True,
                text_content=omni_doc.full_text,
                chapters=chapters,
                metadata=metadata,
                image_info=image_info,
                cleaning_stats=None,  # Will be populated by TextCleaner
                error_message=None,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                text_content="",
                chapters=[],
                metadata=self._default_metadata(),
                image_info=[],
                cleaning_stats=None,
                error_message=str(e),
                processing_time=processing_time
            )

    def _convert_metadata(self, omni_meta, omni_doc) -> EbookMetadata:
        """Convert OmniParser Metadata to epub2tts EbookMetadata."""
        return EbookMetadata(
            title=omni_meta.title or "Unknown",
            authors=[omni_meta.author] if omni_meta.author else ["Unknown"],
            publisher=omni_meta.publisher,
            publication_date=omni_meta.publication_date,
            language=omni_meta.language or "en",
            identifier=omni_meta.isbn or "unknown",
            description=omni_meta.description,
            subjects=[],  # Not in OmniParser base model
            rights=None,  # Not in OmniParser base model
            spine_length=len(omni_doc.chapters),  # Use chapter count
            has_toc=True,  # OmniParser uses TOC-based detection
            epub_version="3.0"  # Default
        )

    def _convert_chapters(self, omni_chapters) -> List[Chapter]:
        """Convert OmniParser Chapters to epub2tts Chapters."""
        return [
            Chapter(
                chapter_num=ch.chapter_number,
                title=ch.title or f"Chapter {ch.chapter_number}",
                content=ch.content,
                word_count=ch.word_count,
                estimated_duration=self._estimate_duration(ch.word_count),
                confidence=1.0  # OmniParser uses TOC, high confidence
            )
            for ch in omni_chapters
        ]

    def _convert_images(self, omni_images) -> List[Dict]:
        """Convert OmniParser ImageReferences to epub2tts image_info format."""
        return [
            {
                "path": str(img.file_path),
                "alt_text": img.alt_text or "",
                "format": img.format or "unknown"
            }
            for img in omni_images
        ]

    def _estimate_duration(self, word_count: int) -> float:
        """Estimate reading duration from word count (words per minute)."""
        WPM = 175  # Average reading speed
        return word_count / WPM

    def _default_metadata(self) -> EbookMetadata:
        """Return default metadata for error cases."""
        return EbookMetadata(
            title="Unknown",
            authors=["Unknown"],
            publisher=None,
            publication_date=None,
            language="en",
            identifier="unknown",
            description=None,
            subjects=[],
            rights=None,
            spine_length=0,
            has_toc=False,
            epub_version="3.0"
        )
```

**Requirements:**
- Type hints on all methods
- Comprehensive docstrings
- Error handling with try/except
- Timing measurement (processing_time)

**After implementation:**
1. Format: `uv run black src/core/omniparser_adapter.py`
2. Test import: `uv run python -c "from src.core.omniparser_adapter import OmniParserAdapter; print('✓ Import successful')"`
3. **Commit:** `feat: Implement OmniParser adapter for epub2tts integration`

#### Step 2: Test Adapter Standalone (15 min)

Create quick test script `scripts/test_adapter.py`:

```python
from pathlib import Path
from src.core.omniparser_adapter import OmniParserAdapter

adapter = OmniParserAdapter()
result = adapter.process_epub(Path("A System for Writing.epub"))

print(f"Success: {result.success}")
print(f"Title: {result.metadata.title}")
print(f"Chapters: {len(result.chapters)}")
print(f"Word count: {sum(ch.word_count for ch in result.chapters)}")
print(f"Processing time: {result.processing_time:.2f}s")
```

Run:
```bash
uv run python scripts/test_adapter.py
```

**Commit:** `test: Add standalone adapter test script`

---

### Phase 3: Integration with EPUBProcessor (45 minutes)

#### Step 1: Update EPUBProcessor (30 min)

**Use `house-coder` subagent:**

Edit `src/core/epub_processor.py`:

1. **Add import:**
   ```python
   from .omniparser_adapter import OmniParserAdapter
   ```

2. **Update __init__:**
   ```python
   def __init__(self, config):
       self.config = config
       self.parser = OmniParserAdapter(config)  # Use OmniParser directly
   ```

3. **Update main processing method:**
   ```python
   def process(self, epub_path: Path, output_dir: Optional[Path] = None) -> ProcessingResult:
       """Process EPUB file using OmniParser."""
       logger.info(f"Processing EPUB with OmniParser: {epub_path}")

       try:
           # Use OmniParser adapter
           result = self.parser.process_epub(epub_path, output_dir)

           if not result.success:
               logger.error(f"OmniParser processing failed: {result.error_message}")
               return result

           # Continue with text cleaning (existing code)
           # ... rest of pipeline unchanged

           return result

       except Exception as e:
           logger.error(f"EPUB processing failed: {e}")
           raise
   ```

4. **Remove EbookLibProcessor imports and references**

**After changes:**
1. Format: `uv run black src/core/epub_processor.py`
2. Test import: `uv run python -c "from src.core.epub_processor import EPUBProcessor; print('✓')"`
3. **Commit:** `feat: Integrate OmniParser into EPUBProcessor`

#### Step 2: Test Integration (15 min)

```bash
# Test EPUB processing
uv run python -c "
from pathlib import Path
from src.core.epub_processor import EPUBProcessor
from src.utils.config import Config

config = Config()
processor = EPUBProcessor(config)
result = processor.process(Path('A System for Writing.epub'))

print(f'Success: {result.success}')
print(f'Chapters: {len(result.chapters)}')
print(f'Title: {result.metadata.title}')
"
```

**Commit:** `test: Verify EPUBProcessor integration with OmniParser`

---

### Phase 4: Testing & Validation (90 minutes)

#### Step 1: Create Integration Tests (30 min)

**Use `general-purpose` subagent:**

Create `tests/integration/test_omniparser_integration.py`:

```python
import pytest
from pathlib import Path
from src.core.omniparser_adapter import OmniParserAdapter
from src.core.epub_processor import EPUBProcessor


class TestOmniParserIntegration:
    """Integration tests for OmniParser adapter."""

    @pytest.fixture
    def epub_file(self):
        return Path("A System for Writing.epub")

    @pytest.fixture
    def adapter(self):
        return OmniParserAdapter()

    def test_adapter_processes_epub(self, adapter, epub_file):
        """Test adapter can process EPUB file."""
        result = adapter.process_epub(epub_file)
        assert result.success is True
        assert result.text_content is not None
        assert len(result.chapters) > 0
        assert result.metadata.title is not None

    def test_chapter_structure(self, adapter, epub_file):
        """Test chapter structure matches expectations."""
        result = adapter.process_epub(epub_file)
        for ch in result.chapters:
            assert ch.chapter_num >= 0
            assert ch.title is not None
            assert ch.content is not None
            assert ch.word_count > 0
            assert ch.estimated_duration > 0

    def test_epub_processor_uses_omniparser(self, epub_file):
        """Test EPUBProcessor uses OmniParser."""
        from src.utils.config import Config
        processor = EPUBProcessor(Config())
        result = processor.process(epub_file)
        assert result.success is True
        assert len(result.chapters) > 0
```

Run:
```bash
uv run pytest tests/integration/test_omniparser_integration.py -v
```

**Commit:** `test: Add OmniParser integration tests`

#### Step 2: Run Existing Test Suite (20 min)

```bash
# Run all tests
uv run pytest tests/ -v --tb=short

# Run epub-specific tests
uv run pytest tests/ -k epub -v
```

**Report failures and propose fixes.**

**Commit:** `test: Verify existing test suite with OmniParser`

#### Step 3: Full TTS Pipeline Test (40 min)

**CRITICAL: Test the complete EPUB → audiobook pipeline!**

```bash
# Test CLI conversion
uv run epub2tts convert "A System for Writing.epub" --output test_output/

# Verify:
# - Audio files generated?
# - Correct chapter count?
# - Audio quality acceptable?
# - Processing time reasonable?

# Test other CLI commands
uv run epub2tts info "A System for Writing.epub"
uv run epub2tts validate "A System for Writing.epub"
```

**Check output:**
- Audio files exist in `test_output/`
- Chapter count matches expectations
- No errors in logs
- TTS pipeline completed successfully

**Commit:** `test: Verify full TTS pipeline with OmniParser`

---

### Phase 5: Remove Legacy Code (30 minutes)

**CRITICAL: Only proceed if ALL tests pass!**

#### Step 1: Remove ebooklib_processor.py (15 min)

```bash
# Verify OmniParser is working 100%
uv run pytest tests/ -v

# If all pass:
git rm src/core/ebooklib_processor.py

# Remove any remaining imports
# Search for references:
grep -r "ebooklib_processor" src/ tests/
```

**Remove all references to EbookLibProcessor**

**Commit:** `refactor: Remove legacy ebooklib_processor (965 lines)`

#### Step 2: Clean Up Dependencies (15 min)

Edit `pyproject.toml`:

Check if `ebooklib` is still needed elsewhere:
```bash
grep -r "import ebooklib" src/
grep -r "from ebooklib" src/
```

If only used in removed file:
- Remove `ebooklib>=0.19` from dependencies

Keep:
- `beautifulsoup4` (used in text processing)
- `ftfy` (used in text cleaning)

Run:
```bash
uv sync  # Update lockfile
```

**Commit:** `deps: Remove ebooklib dependency (provided by OmniParser)`

---

### Phase 6: Documentation & Release (45 minutes)

#### Step 1: Update Documentation (30 min)

**Files to update:**

1. **README.md:**
   - Add OmniParser to dependencies section
   - Update architecture diagram
   - Add installation note about OmniParser

2. **docs/ARCHITECTURE.md:**
   - Update pipeline diagram (show OmniParser)
   - Remove EbookLibProcessor references

3. **Create docs/OMNIPARSER_MIGRATION.md:**
   ```markdown
   # Migration to OmniParser

   ## Overview
   epub2tts v0.2.0 migrated from internal EPUB processing to OmniParser library.

   ## Changes
   - EPUB parsing now uses OmniParser (>=0.1.0)
   - Removed internal ebooklib_processor.py (965 lines)
   - Added OmniParserAdapter for data model conversion

   ## Breaking Changes
   None - fully backward compatible

   ## Performance
   Processing speed within 20% of v0.1.0

   ## Migration Notes
   For developers: If you were importing from `src.core.ebooklib_processor`,
   use `omniparser` directly instead.
   ```

4. **Update CHANGELOG.md:**
   ```markdown
   ## [Unreleased]

   ## [0.2.0] - 2025-10-29

   ### Changed
   - EPUB processing now uses OmniParser library (>=0.1.0)
   - Simplified EPUBProcessor with external parsing dependency

   ### Added
   - OmniParserAdapter for data model conversion
   - Integration tests for OmniParser

   ### Removed
   - ebooklib_processor.py (965 lines) - functionality moved to OmniParser
   - Direct ebooklib dependency (now provided by OmniParser)

   ### Performance
   - Processing speed within 20% of v0.1.0
   - Reduced codebase complexity by ~1000 lines
   ```

**Commit:** `docs: Update documentation for OmniParser migration`

#### Step 2: Version Bump (15 min)

1. **Update pyproject.toml:**
   ```toml
   version = "0.2.0"
   ```

2. **Update __init__.py (if has __version__):**
   ```python
   __version__ = "0.2.0"
   ```

3. **Update CHANGELOG.md:**
   - Change `[Unreleased]` → `[0.2.0] - 2025-10-29`
   - Add new `[Unreleased]` section

4. **Create git tag:**
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0: OmniParser integration"
   ```

**Commit:**
```bash
git add pyproject.toml src/__init__.py CHANGELOG.md
git commit -m "chore: Bump version to 0.2.0 for OmniParser migration release"
git push origin feat/integrate-omniparser
```

---

### Phase 7: Pull Request Creation (15 minutes)

1. **Create PR:**
   ```bash
   gh pr create \
     --title "feat: Migrate to OmniParser for EPUB parsing (v0.2.0)" \
     --body "$(cat <<'EOF'
## 🎯 Summary
Migrated epub2tts from internal EPUB processing (965 lines) to OmniParser library. This reduces codebase complexity and leverages OmniParser's robust EPUB parsing.

## 📊 Changes
- **Removed:** `ebooklib_processor.py` (965 lines)
- **Added:** `omniparser_adapter.py` (150 lines)
- **Modified:** `epub_processor.py` (integration)
- **Net Change:** -815 lines (~85% reduction in EPUB processing code)

## 🔄 Migration Details
- Added OmniParser dependency (>=0.1.0)
- Created adapter layer for data model conversion
- Removed direct ebooklib dependency (now via OmniParser)
- Updated EPUBProcessor to use OmniParser
- Maintained backward compatibility with existing TTS pipeline

## ✅ Testing
- [x] All existing tests pass
- [x] New integration tests for OmniParser
- [x] Full TTS pipeline tested (EPUB → audiobook)
- [x] Performance within 20% of previous version

## 📏 Code Quality
- [x] Type hints on all new code
- [x] Comprehensive docstrings
- [x] Black formatted
- [x] Integration tests added

## 🔗 Related
- Depends on OmniParser v0.1.0+
- Version bump: v0.1.0 → v0.2.0
- Simplifies EPUB processing architecture

## 📝 Checklist
- [x] OmniParser integrated
- [x] Legacy code removed
- [x] Tests pass
- [x] TTS pipeline tested
- [x] Documentation updated
- [x] Version bumped
- [x] Ready for release

---
🤖 Generated with [Claude Code](https://claude.ai/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" \
     --base main \
     --head feat/integrate-omniparser
   ```

2. **Verify PR created:**
   ```bash
   gh pr view
   ```

---

### Phase 8: Final Validation & Report (30 minutes)

#### Step 1: End-to-End Testing (15 min)

```bash
# Full pipeline test
uv run epub2tts convert "A System for Writing.epub" --output final_test/

# Run all tests
uv run pytest tests/ -v

# Check version
uv run python -c "import epub2tts; print(f'Version: {epub2tts.__version__}')"
```

**All should pass!**

#### Step 2: Create Migration Report (15 min)

Create `docs/OMNIPARSER_MIGRATION_REPORT.md`:

```markdown
# epub2tts → OmniParser Migration Report

**Date:** 2025-10-29
**Version:** v0.1.0 → v0.2.0
**Duration:** X hours

## Summary
Successfully migrated epub2tts from internal EPUB processing to OmniParser library.

## Changes Made

### Code Changes
- **Added**: OmniParserAdapter (150 lines)
- **Modified**: EPUBProcessor integration
- **Removed**: ebooklib_processor.py (965 lines)
- **Net Change**: -815 lines

### Dependencies
- **Added**: omniparser>=0.1.0
- **Removed**: ebooklib

### Tests
- All existing tests: PASSING ✅
- New integration tests: X added
- Full TTS pipeline: TESTED ✅

### Performance
- OmniParser time: X.XX seconds
- Legacy time: Y.YY seconds
- Delta: ±Z% (within 20% threshold)

## Validation

- [x] EPUB parsing works
- [x] All tests pass
- [x] Full TTS pipeline tested
- [x] Audio files generated correctly
- [x] Performance acceptable
- [x] Documentation updated
- [x] Version bumped to v0.2.0

## Status

✅ **READY FOR RELEASE**

Migration completed successfully. epub2tts now uses OmniParser for EPUB parsing.
```

**Commit:** `docs: Add OmniParser migration completion report`

---

## ⚠️ Critical Rules

**IMPORTANT:** Add `git push origin feat/integrate-omniparser` after EVERY `git commit` command throughout this session!

1. **Project location:** Work in `/Users/mini/Documents/GitHub/epub2tts`
2. **Version constraint:** `>=0.1.0` (NOT `>=1.0.0`)
3. **Go all-in:** Remove legacy code after validation (no fallback)
4. **Test full pipeline:** EPUB → TTS → audio files
5. **Use subagents:**
   - `house-research` for analysis
   - `house-coder` for code changes
   - `house-bash` for testing
6. **Commit frequently** (atomic commits and push to branch!)
7. **Report progress continuously**

## 🚨 Troubleshooting

### OmniParser Not Found
```bash
uv add --editable /Users/mini/Documents/GitHub/OmniParser
uv run python -c "import omniparser; print('OK')"
```

### Tests Fail
Check adapter conversion:
- Metadata fields match?
- Chapter structure correct?
- Image info format compatible?

### Performance Regression
Profile both:
```bash
uv run python -m cProfile -s cumtime scripts/test_adapter.py
```

### TTS Pipeline Fails
Check:
- TextCleaner still works?
- Chapter content format correct?
- Audio generation still receives proper input?

## 📚 Quick Reference

```bash
# Key commands (in epub2tts directory)
uv run pytest tests/ -v
uv run epub2tts convert "file.epub"
uv run python scripts/test_adapter.py

# Check status
wc -l src/core/omniparser_adapter.py
git log --oneline

# Format
uv run black src/
```

---

## 🏁 Start Execution

**You are now ready to begin!**

**IMPORTANT:** You are working in `/Users/mini/Documents/GitHub/epub2tts` (NOT OmniParser!)

1. Phase 0: Pre-Flight (create feature branch!)
2. Phase 1: Add OmniParser Dependency
3. Phase 2: Create Adapter Layer
4. Phase 3: Integration
5. Phase 4: Testing (including full TTS pipeline!)
6. Phase 5: Remove Legacy Code
7. Phase 6: Documentation & Release
8. Phase 7: Create Pull Request
9. Phase 8: Final Validation

**EXECUTION MODE:** YOLO (auto-approve all actions)

**Report after each phase:**
- Phase completed
- Test status
- What's next
- Any issues

**Remember:** Push to branch after every commit!

**Let's go! 🚀**
