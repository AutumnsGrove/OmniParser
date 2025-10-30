# Claude Code Session Guide: epub2tts → OmniParser Migration

**Document Type:** Claude Code Session Initialization Meta-Prompt
**Purpose:** Guide autonomous migration of epub2tts to use OmniParser for EPUB parsing
**Target Audience:** Claude Code AI Agent working on epub2tts project
**Session Mode:** YOLO (Auto-approve) with Subagent-First Development
**Estimated Duration:** 6-8 hours of autonomous execution
**Created:** 2025-10-29

---

## 🎯 Mission Objective

Migrate epub2tts (v0.1.0) from its internal EPUB processing (`ebooklib_processor.py` - 965 lines) to use OmniParser as an external dependency for EPUB parsing, enabling epub2tts to benefit from OmniParser's unified document parsing interface while maintaining 100% feature compatibility.

**Success Criteria:**
- ✅ epub2tts successfully imports OmniParser as dependency
- ✅ EPUB processing uses `omniparser.parse_document()` instead of internal `EbookLibProcessor`
- ✅ All existing epub2tts tests pass (100% compatibility)
- ✅ No performance regression >20%
- ✅ Code complexity reduced (remove 965 lines of EPUB processing)
- ✅ Version bump to v0.2.0 with proper changelog
- ✅ Documentation updated

---

## 📊 Context: Understanding Both Projects

### OmniParser (v0.3.0)

**What it is:** Standalone universal document parser library (PyPI package)

**Key Features:**
- Parses 6 formats: EPUB, HTML, PDF, DOCX, Markdown, Text
- Unified `Document` data model
- TOC-based chapter detection (same approach as epub2tts)
- Comprehensive metadata extraction
- Image extraction support
- AI-powered enhancements (optional)

**Core API:**
```python
from omniparser import parse_document
from pathlib import Path

# Parse any document
document = parse_document(Path("book.epub"))

# Access structured data
print(document.metadata.title)       # str
print(document.metadata.author)      # str
print(len(document.chapters))        # int
for chapter in document.chapters:
    print(f"{chapter.title}: {chapter.word_count} words")
```

**Data Models:**
```python
@dataclass
class Document:
    metadata: Metadata
    chapters: List[Chapter]
    images: List[ImageReference]
    processing_info: ProcessingInfo
    full_text: str

@dataclass
class Chapter:
    chapter_number: int
    title: str
    content: str
    word_count: int
    level: int  # Heading level (1-6)

@dataclass
class Metadata:
    title: str
    author: str
    language: str
    publisher: Optional[str]
    publication_date: Optional[str]
    isbn: Optional[str]
    description: Optional[str]
    source_format: str
```

**Installation:**
```bash
# From PyPI (when published)
uv add omniparser

# From local development
uv add --editable /path/to/omniparser
```

**CRITICAL:** Accept version **0.1.0 and up**, not 1.0.0+
```toml
# pyproject.toml
[project.dependencies]
omniparser = ">=0.1.0,<2.0.0"  # ✅ Correct
omniparser = ">=1.0.0"          # ❌ Wrong - we haven't released 1.0 yet
```

---

### epub2tts (v0.1.0)

**What it is:** EPUB-to-audiobook converter with TTS engines

**Architecture:**
```
epub2tts Pipeline:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Input     │────>│   EbookLib   │────>│ Text Clean  │────>│   TTS    │
│   (.epub)   │     │  Processor   │     │  & Process  │     │ Pipeline │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
                         965 lines          522 lines
```

**Current EPUB Processing:** `src/core/ebooklib_processor.py` (965 lines)
- Uses `ebooklib` library directly
- TOC-based chapter detection
- Metadata extraction
- Image extraction
- HTML-to-text conversion
- Post-processing pipeline

**Data Models:**
```python
@dataclass
class EbookMetadata:
    title: str
    authors: List[str]
    publisher: Optional[str]
    publication_date: Optional[str]
    language: str
    identifier: str
    description: Optional[str]
    subjects: List[str]
    rights: Optional[str]
    spine_length: int
    has_toc: bool
    epub_version: str

@dataclass
class Chapter:
    chapter_num: int
    title: str
    content: str
    word_count: int
    estimated_duration: float
    confidence: float

@dataclass
class ProcessingResult:
    success: bool
    text_content: str
    chapters: List[Chapter]
    metadata: EbookMetadata
    image_info: List[Dict]
    cleaning_stats: CleaningStats
    error_message: Optional[str]
    processing_time: float
```

**Key Files:**
- `src/core/epub_processor.py` (507 lines) - Main orchestrator
- `src/core/ebooklib_processor.py` (965 lines) - EPUB parsing (TO BE REPLACED)
- `src/core/text_cleaner.py` (522 lines) - Text processing (KEEP)
- `src/pipelines/tts_pipeline.py` - TTS processing (KEEP)

---

## 🗺️ Migration Strategy Overview

### Phase 1: Preparation & Analysis
1. Add OmniParser as dependency
2. Analyze data model mapping
3. Create compatibility layer
4. Document integration points

### Phase 2: Integration
1. Import OmniParser in epub_processor.py
2. Create adapter layer for data model conversion
3. Replace EbookLibProcessor calls with OmniParser
4. Maintain backward compatibility

### Phase 3: Testing & Validation
1. Run existing test suite
2. Compare outputs (old vs new)
3. Performance benchmarking
4. Fix any compatibility issues

### Phase 4: Cleanup & Documentation
1. Remove ebooklib_processor.py
2. Update dependencies
3. Update documentation
4. Version bump and changelog

---

## 📋 Detailed Execution Plan

### Phase 1: Preparation & Analysis (1-2 hours)

#### Task 1.1: Add OmniParser Dependency (15 minutes)

**Use `house-bash` subagent:**

```bash
# Navigate to epub2tts project
cd /Users/mini/Documents/GitHub/epub2tts

# Add OmniParser as local development dependency
# CRITICAL: Use local path until OmniParser is published to PyPI
uv add --editable /Users/mini/Documents/GitHub/OmniParser

# Verify installation
uv run python -c "import omniparser; print(f'OmniParser version: {omniparser.__version__}')"

# Test basic functionality
uv run python -c "
from omniparser import parse_document
from pathlib import Path
doc = parse_document(Path('A System for Writing.epub'))
print(f'✓ Parsed: {doc.metadata.title}')
print(f'✓ Chapters: {len(doc.chapters)}')
"
```

**Expected Output:**
```
✓ Parsed: A System for Writing
✓ Chapters: X chapters
```

**Update pyproject.toml manually:**
```toml
[project.dependencies]
omniparser = ">=0.1.0,<2.0.0"  # Accept 0.1.0+, not 1.0.0+
```

**Commit:** `deps: Add OmniParser dependency for EPUB parsing`

#### Task 1.2: Analyze Data Model Mapping (30 minutes)

**Use `house-research` subagent:**

```
TASK: Analyze data model mapping between epub2tts and OmniParser

Read and compare:
1. epub2tts data models:
   - src/core/ebooklib_processor.py (EbookMetadata, Chapter, ProcessingResult)
   - src/core/text_cleaner.py (Chapter, CleaningStats)

2. OmniParser data models:
   - /Users/mini/Documents/GitHub/OmniParser/src/omniparser/models.py (Document, Chapter, Metadata)

Create: docs/integration/omniparser-data-mapping.md

Document:
- Field-by-field mapping (epub2tts → OmniParser)
- Compatible fields (direct mapping)
- Missing fields (need to preserve in epub2tts)
- Extra fields (OmniParser provides but epub2tts doesn't need)
- Proposed adapter layer interface

Example mapping:
epub2tts.EbookMetadata.title → omniparser.Metadata.title
epub2tts.EbookMetadata.authors (List[str]) → omniparser.Metadata.author (str) - needs joining
epub2tts.Chapter.estimated_duration → Not in OmniParser - calculate in epub2tts
```

**Expected Output:** Comprehensive mapping document

**Commit:** `docs: Add OmniParser data model mapping analysis`

#### Task 1.3: Design Adapter Layer (30 minutes)

**Use `general-purpose` subagent with `sonnet` model:**

```
TASK: Design adapter layer for OmniParser integration

Create: src/core/omniparser_adapter.py (~150-200 lines)

Design interface:
```python
"""Adapter layer for OmniParser integration."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from omniparser import parse_document
from omniparser.models import Document as OmniDocument

from .ebooklib_processor import EbookMetadata, Chapter, ProcessingResult


class OmniParserAdapter:
    """
    Adapter for integrating OmniParser with epub2tts.

    Converts OmniParser's Document model to epub2tts's ProcessingResult model,
    maintaining backward compatibility with existing epub2tts code.
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
        # Parse with OmniParser
        omni_doc = parse_document(epub_path, output_dir=output_dir)

        # Convert to epub2tts format
        metadata = self._convert_metadata(omni_doc.metadata)
        chapters = self._convert_chapters(omni_doc.chapters)
        image_info = self._convert_images(omni_doc.images)

        # Build ProcessingResult
        return ProcessingResult(
            success=True,
            text_content=omni_doc.full_text,
            chapters=chapters,
            metadata=metadata,
            image_info=image_info,
            cleaning_stats=None,  # Will be populated later by TextCleaner
            error_message=None,
            processing_time=0.0  # TODO: Add timing
        )

    def _convert_metadata(self, omni_meta) -> EbookMetadata:
        """Convert OmniParser Metadata to epub2tts EbookMetadata."""
        return EbookMetadata(
            title=omni_meta.title,
            authors=[omni_meta.author],  # OmniParser has single author string
            publisher=omni_meta.publisher,
            publication_date=omni_meta.publication_date,
            language=omni_meta.language,
            identifier=omni_meta.isbn or "unknown",
            description=omni_meta.description,
            subjects=[],  # Not in OmniParser base model
            rights=None,  # Not in OmniParser base model
            spine_length=len(omni_meta.extra.get("spine", [])) if hasattr(omni_meta, "extra") else 0,
            has_toc=True,  # OmniParser always uses TOC-based detection
            epub_version="3.0"  # Default, could parse from OmniParser if needed
        )

    def _convert_chapters(self, omni_chapters) -> List[Chapter]:
        """Convert OmniParser Chapters to epub2tts Chapters."""
        return [
            Chapter(
                chapter_num=ch.chapter_number,
                title=ch.title,
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
        """Estimate reading duration from word count."""
        # Average reading speed: 150-200 words per minute
        # Use 175 as middle ground
        return word_count / 175.0
```

Create skeleton file, commit with:
"feat: Add OmniParser adapter layer for epub2tts integration"
```

**Success Criteria:** ✅ Adapter layer designed and documented

#### Task 1.4: Identify Integration Points (15 minutes)

**Use `house-research` subagent:**

```
TASK: Identify all code locations that call EbookLibProcessor

Search for:
1. Import statements: "from .ebooklib_processor import"
2. Class usage: "EbookLibProcessor"
3. Method calls: ".process_epub("

Report locations:
- File path
- Line numbers
- Context (what's calling it)
- Complexity (simple call vs complex integration)

Expected primary location: src/core/epub_processor.py

Create: docs/integration/integration-points.md
```

**Commit:** `docs: Document EbookLibProcessor integration points`

---

### Phase 2: Integration (2-3 hours)

#### Task 2.1: Implement Adapter Layer (60 minutes)

**Use `house-coder` subagent:**

```
TASK: Implement OmniParserAdapter class

File: src/core/omniparser_adapter.py

Implement all methods from design in Task 1.3:
- process_epub() - Main entry point
- _convert_metadata() - Metadata conversion
- _convert_chapters() - Chapter conversion
- _convert_images() - Image info conversion
- _estimate_duration() - Duration calculation

Requirements:
- Type hints on all methods
- Comprehensive docstrings
- Error handling with try/except
- Logging for debugging
- Match ProcessingResult exactly

After implementation:
1. Format: uv run black src/core/omniparser_adapter.py
2. Type check: uv run mypy src/core/omniparser_adapter.py
3. Test import: uv run python -c "from src.core.omniparser_adapter import OmniParserAdapter; print('✓ Import successful')"
4. Commit: "feat: Implement OmniParserAdapter for data model conversion"
```

**Success Criteria:** ✅ Adapter fully implemented, imports successfully

#### Task 2.2: Update EPUBProcessor to Use Adapter (45 minutes)

**Use `house-coder` subagent:**

```
TASK: Update EPUBProcessor to use OmniParserAdapter

File: src/core/epub_processor.py (507 lines)

Changes needed:

1. Add import at top:
   from .omniparser_adapter import OmniParserAdapter

2. Add configuration flag to enable/disable OmniParser:
   self.use_omniparser = config.get("use_omniparser", True)  # Default to True

3. Update __init__ method:
   def __init__(self, config):
       self.config = config
       self.use_omniparser = config.get("use_omniparser", True)
       if self.use_omniparser:
           self.parser = OmniParserAdapter(config)
       else:
           self.parser = EbookLibProcessor()  # Legacy fallback

4. Update process() or main processing method:
   def process(self, epub_path: Path, output_dir: Optional[Path] = None) -> ProcessingResult:
       \"\"\"Process EPUB file.\"\"\"
       try:
           # Use OmniParser if enabled
           if self.use_omniparser:
               logger.info("Processing EPUB with OmniParser")
               result = self.parser.process_epub(epub_path, output_dir)
           else:
               logger.info("Processing EPUB with legacy EbookLibProcessor")
               result = self.parser.process_epub(epub_path, output_dir)

           # Continue with text cleaning and post-processing
           # (existing code remains unchanged)
           return result

       except Exception as e:
           logger.error(f"EPUB processing failed: {e}")
           # Fallback to legacy if OmniParser fails
           if self.use_omniparser:
               logger.warning("Falling back to EbookLibProcessor")
               self.parser = EbookLibProcessor()
               return self.parser.process_epub(epub_path, output_dir)
           raise

Strategy:
- Keep EbookLibProcessor as fallback initially
- Add feature flag for gradual rollout
- Maintain backward compatibility
- Log which processor is being used

After changes:
1. Format: uv run black src/core/epub_processor.py
2. Test import: uv run python -c "from src.core.epub_processor import EPUBProcessor; print('✓ Import successful')"
3. Commit: "feat: Integrate OmniParser into EPUBProcessor with fallback"
```

**Success Criteria:** ✅ EPUBProcessor uses OmniParser, fallback works

#### Task 2.3: Add Configuration Option (15 minutes)

**Use `house-coder` subagent:**

```
TASK: Add OmniParser configuration option

File: src/utils/config.py

Add configuration field:

```python
class ProcessingConfig:
    # Existing fields...

    # EPUB Processing
    use_omniparser: bool = True  # Use OmniParser for EPUB processing (default: True)
    epub_processor: str = "omniparser"  # Options: "omniparser", "ebooklib", "pandoc"
```

Also update any config loading from JSON/YAML to include this field.

Commit: "feat: Add OmniParser configuration options"
```

**Success Criteria:** ✅ Configuration supports OmniParser toggle

#### Task 2.4: Update CLI to Support Legacy Mode (15 minutes)

**Use `house-coder` subagent:**

```
TASK: Add CLI flag for legacy EPUB processing

File: src/cli.py

Add optional flag to convert command:

```python
@click.option(
    "--legacy-epub",
    is_flag=True,
    default=False,
    help="Use legacy EPUB processor instead of OmniParser"
)
def convert(file, legacy_epub, **kwargs):
    \"\"\"Convert EPUB to audiobook.\"\"\"
    config = load_config()
    config["use_omniparser"] = not legacy_epub

    processor = EPUBProcessor(config)
    # ... rest of processing
```

Commit: "feat: Add --legacy-epub CLI flag for fallback processing"
```

**Success Criteria:** ✅ Users can opt-in to legacy processing if needed

---

### Phase 3: Testing & Validation (2-3 hours)

#### Task 3.1: Create Integration Tests (45 minutes)

**Use `general-purpose` subagent:**

```
TASK: Create integration tests for OmniParser adapter

File: tests/integration/test_omniparser_integration.py

Create comprehensive test suite:

```python
import pytest
from pathlib import Path
from src.core.omniparser_adapter import OmniParserAdapter
from src.core.epub_processor import EPUBProcessor


class TestOmniParserIntegration:
    \"\"\"Integration tests for OmniParser adapter.\"\"\"

    @pytest.fixture
    def epub_file(self):
        return Path("A System for Writing.epub")

    @pytest.fixture
    def adapter(self):
        return OmniParserAdapter()

    def test_adapter_processes_epub(self, adapter, epub_file):
        \"\"\"Test adapter can process EPUB file.\"\"\"
        result = adapter.process_epub(epub_file)

        assert result.success is True
        assert result.text_content is not None
        assert len(result.chapters) > 0
        assert result.metadata is not None
        assert result.error_message is None

    def test_metadata_conversion(self, adapter, epub_file):
        \"\"\"Test metadata conversion from OmniParser to epub2tts format.\"\"\"
        result = adapter.process_epub(epub_file)
        metadata = result.metadata

        assert metadata.title is not None
        assert len(metadata.authors) > 0
        assert metadata.language is not None
        assert metadata.has_toc is True

    def test_chapter_conversion(self, adapter, epub_file):
        \"\"\"Test chapter conversion from OmniParser to epub2tts format.\"\"\"
        result = adapter.process_epub(epub_file)
        chapters = result.chapters

        assert len(chapters) > 0
        for ch in chapters:
            assert ch.chapter_num >= 0
            assert ch.title is not None
            assert ch.content is not None
            assert ch.word_count > 0
            assert ch.estimated_duration > 0
            assert ch.confidence > 0

    def test_epub_processor_uses_omniparser(self, epub_file):
        \"\"\"Test EPUBProcessor uses OmniParser by default.\"\"\"
        config = {"use_omniparser": True}
        processor = EPUBProcessor(config)

        result = processor.process(epub_file)

        assert result.success is True
        assert len(result.chapters) > 0

    def test_epub_processor_legacy_fallback(self, epub_file):
        \"\"\"Test EPUBProcessor can fall back to legacy processor.\"\"\"
        config = {"use_omniparser": False}
        processor = EPUBProcessor(config)

        result = processor.process(epub_file)

        assert result.success is True
        assert len(result.chapters) > 0

    def test_output_compatibility(self, epub_file):
        \"\"\"Test OmniParser output matches legacy output structure.\"\"\"
        # Process with OmniParser
        omni_config = {"use_omniparser": True}
        omni_processor = EPUBProcessor(omni_config)
        omni_result = omni_processor.process(epub_file)

        # Process with legacy
        legacy_config = {"use_omniparser": False}
        legacy_processor = EPUBProcessor(legacy_config)
        legacy_result = legacy_processor.process(epub_file)

        # Compare structure (not exact content, but structure)
        assert type(omni_result) == type(legacy_result)
        assert len(omni_result.chapters) == len(legacy_result.chapters)
        assert omni_result.metadata.title == legacy_result.metadata.title
```

Run tests:
uv run pytest tests/integration/test_omniparser_integration.py -v

Commit: "test: Add integration tests for OmniParser adapter"
```

**Success Criteria:** ✅ All integration tests pass

#### Task 3.2: Run Existing Test Suite (30 minutes)

**Use `house-bash` subagent:**

```
TASK: Run existing epub2tts test suite with OmniParser enabled

Commands:

1. Run unit tests:
   uv run pytest tests/unit/ -v

2. Run integration tests:
   uv run pytest tests/integration/ -v

3. Run EPUB-specific tests:
   uv run pytest tests/ -k epub -v

4. Run full test suite:
   uv run pytest tests/ -v --tb=short

Report:
- Total tests: X
- Passed: Y
- Failed: Z (list failures with details)
- Skipped: W

For any failures:
- Analyze root cause
- Check if data model conversion issue
- Check if missing field in adapter
- Propose fixes
```

**Expected:** Most tests should pass. Some may need adapter tweaks.

**Commit:** `test: Verify existing test suite with OmniParser`

#### Task 3.3: Comparison Testing (45 minutes)

**Use `general-purpose` subagent:**

```
TASK: Create comparison test between OmniParser and legacy processor

File: tests/validation/test_omniparser_comparison.py

Test same EPUB file with both processors and compare outputs:

```python
import pytest
from pathlib import Path
from src.core.omniparser_adapter import OmniParserAdapter
from src.core.ebooklib_processor import EbookLibProcessor


class TestProcessorComparison:
    \"\"\"Compare OmniParser vs legacy processor outputs.\"\"\"

    @pytest.fixture
    def epub_file(self):
        return Path("A System for Writing.epub")

    def test_chapter_count_matches(self, epub_file):
        \"\"\"Verify both processors extract same number of chapters.\"\"\"
        omni = OmniParserAdapter()
        legacy = EbookLibProcessor()

        omni_result = omni.process_epub(epub_file)
        legacy_result = legacy.process_epub(epub_file)

        # Should be very close (within 10%)
        omni_count = len(omni_result.chapters)
        legacy_count = len(legacy_result.chapters)
        diff_percent = abs(omni_count - legacy_count) / legacy_count * 100

        assert diff_percent < 10, f"Chapter count differs by {diff_percent}%"

    def test_total_word_count_matches(self, epub_file):
        \"\"\"Verify total word count is similar.\"\"\"
        omni = OmniParserAdapter()
        legacy = EbookLibProcessor()

        omni_result = omni.process_epub(epub_file)
        legacy_result = legacy.process_epub(epub_file)

        omni_words = sum(ch.word_count for ch in omni_result.chapters)
        legacy_words = sum(ch.word_count for ch in legacy_result.chapters)
        diff_percent = abs(omni_words - legacy_words) / legacy_words * 100

        assert diff_percent < 15, f"Word count differs by {diff_percent}%"

    def test_metadata_title_matches(self, epub_file):
        \"\"\"Verify metadata title is identical.\"\"\"
        omni = OmniParserAdapter()
        legacy = EbookLibProcessor()

        omni_result = omni.process_epub(epub_file)
        legacy_result = legacy.process_epub(epub_file)

        assert omni_result.metadata.title == legacy_result.metadata.title
```

Run comparison tests:
uv run pytest tests/validation/test_omniparser_comparison.py -v

Commit: "test: Add processor comparison validation tests"
```

**Success Criteria:** ✅ Outputs are equivalent (within acceptable variance)

#### Task 3.4: Performance Benchmarking (45 minutes)

**Use `house-bash` subagent:**

```
TASK: Benchmark OmniParser vs legacy processor performance

Create: scripts/benchmark_epub_processors.py

```python
import time
from pathlib import Path
from src.core.omniparser_adapter import OmniParserAdapter
from src.core.ebooklib_processor import EbookLibProcessor


def benchmark_processor(processor, epub_path, runs=5):
    \"\"\"Benchmark processor performance.\"\"\"
    times = []
    for _ in range(runs):
        start = time.time()
        processor.process_epub(epub_path)
        elapsed = time.time() - start
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return avg_time, min_time, max_time


def main():
    epub_path = Path("A System for Writing.epub")

    print("Benchmarking OmniParser...")
    omni = OmniParserAdapter()
    omni_avg, omni_min, omni_max = benchmark_processor(omni, epub_path)

    print("Benchmarking Legacy EbookLibProcessor...")
    legacy = EbookLibProcessor()
    legacy_avg, legacy_min, legacy_max = benchmark_processor(legacy, epub_path)

    print("\n=== Benchmark Results ===")
    print(f"OmniParser:    {omni_avg:.2f}s avg ({omni_min:.2f}s - {omni_max:.2f}s)")
    print(f"Legacy:        {legacy_avg:.2f}s avg ({legacy_min:.2f}s - {legacy_max:.2f}s)")

    if omni_avg < legacy_avg:
        speedup = (legacy_avg - omni_avg) / legacy_avg * 100
        print(f"\n✓ OmniParser is {speedup:.1f}% faster")
    else:
        slowdown = (omni_avg - legacy_avg) / legacy_avg * 100
        print(f"\n⚠️  OmniParser is {slowdown:.1f}% slower")

        if slowdown > 20:
            print("WARNING: Performance regression exceeds 20% threshold!")
            return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

Run benchmark:
uv run python scripts/benchmark_epub_processors.py

Report results and verify <20% regression.

Commit: "test: Add performance benchmarking script"
```

**Success Criteria:** ✅ No performance regression >20%

---

### Phase 4: Cleanup & Documentation (1-2 hours)

#### Task 4.1: Remove Legacy EbookLibProcessor (30 minutes)

**Use `house-coder` subagent:**

```
TASK: Remove ebooklib_processor.py after successful migration

CRITICAL: Only do this AFTER all tests pass and performance is acceptable!

Steps:

1. Verify OmniParser is working 100%:
   uv run pytest tests/ -v
   uv run python scripts/benchmark_epub_processors.py

2. If all tests pass:
   git rm src/core/ebooklib_processor.py

3. Remove imports from epub_processor.py:
   - Remove: from .ebooklib_processor import EbookLibProcessor
   - Remove fallback logic

4. Simplify EPUBProcessor:
   - Remove use_omniparser flag (always use OmniParser)
   - Remove legacy fallback code
   - Clean up conditional logic

5. Update configuration:
   - Remove legacy processor options from config

After removal:
1. Run full test suite: uv run pytest tests/ -v
2. Test CLI: uv run epub2tts convert "A System for Writing.epub"
3. Commit: "refactor: Remove legacy ebooklib_processor, use OmniParser exclusively"

LINES REMOVED: ~965 lines from src/core/ebooklib_processor.py
```

**Success Criteria:** ✅ 965 lines removed, all tests still pass

#### Task 4.2: Update Dependencies (15 minutes)

**Use `house-coder` subagent:**

```
TASK: Clean up dependencies after EbookLibProcessor removal

File: pyproject.toml

Check if these can be removed (only if not used elsewhere):
- ebooklib>=0.19 (now provided by OmniParser)

Keep these (still needed):
- beautifulsoup4 (used in text processing)
- ftfy (used in text cleaning)

Update [project.dependencies]:
1. Ensure omniparser = ">=0.1.0,<2.0.0" is listed
2. Remove ebooklib if only used in removed processor
3. Verify all dependencies still needed

Run:
uv sync  # Update lockfile

Test imports:
uv run python -c "
import omniparser
from src.core.epub_processor import EPUBProcessor
print('✓ All imports successful')
"

Commit: "deps: Clean up dependencies after EbookLibProcessor removal"
```

**Success Criteria:** ✅ Dependencies cleaned, lockfile updated

#### Task 4.3: Update Documentation (45 minutes)

**Use `general-purpose` subagent:**

```
TASK: Update all documentation to reflect OmniParser integration

Files to update:

1. README.md:
   - Update installation instructions (now requires OmniParser)
   - Update architecture diagram (show OmniParser as external dependency)
   - Add note about OmniParser version compatibility (>=0.1.0)

2. docs/ARCHITECTURE.md (if exists):
   - Update pipeline diagram
   - Show OmniParser as document parsing layer
   - Update component descriptions

3. docs/TROUBLESHOOTING.md:
   - Add OmniParser-specific troubleshooting
   - Remove ebooklib_processor issues
   - Add "OmniParser not found" error handling

4. docs/API.md (if exists):
   - Update EPUBProcessor API docs
   - Remove EbookLibProcessor references
   - Add OmniParserAdapter documentation

5. Create: docs/OMNIPARSER_MIGRATION.md
   - Document migration process
   - List breaking changes (if any)
   - Migration guide for contributors

Update all docstrings:
- src/core/epub_processor.py
- src/core/omniparser_adapter.py

Commit: "docs: Update documentation for OmniParser integration"
```

**Success Criteria:** ✅ All docs updated, no references to removed code

#### Task 4.4: Update CHANGELOG (15 minutes)

**Use `house-coder` subagent:**

```
TASK: Update CHANGELOG.md for v0.2.0 release

File: CHANGELOG.md

Add to [Unreleased] section:

## [Unreleased]

### Added
- OmniParser integration for EPUB parsing (replaces internal ebooklib_processor)
- OmniParserAdapter for data model conversion
- Performance benchmarking script for processor comparison
- Integration tests for OmniParser adapter

### Changed
- EPUB processing now uses OmniParser library (>=0.1.0) instead of internal processor
- EPUBProcessor simplified with single processing path
- Configuration updated to support OmniParser

### Removed
- ebooklib_processor.py (965 lines) - functionality moved to OmniParser
- Legacy EPUB processing fallback logic
- Direct ebooklib dependency (now provided by OmniParser)

### Performance
- Processing speed within 20% of legacy processor
- Reduced codebase complexity by ~1000 lines

Commit: "docs: Update CHANGELOG for OmniParser migration (v0.2.0)"
```

**Success Criteria:** ✅ CHANGELOG documents all changes

#### Task 4.5: Version Bump to v0.2.0 (15 minutes)

**Use `house-bash` subagent:**

```
TASK: Bump version to v0.2.0 for OmniParser integration release

Files to update:

1. pyproject.toml:
   version = "0.2.0"

2. src/__init__.py (if has __version__):
   __version__ = "0.2.0"

3. CHANGELOG.md:
   Change [Unreleased] to [0.2.0] - 2025-10-29
   Add new empty [Unreleased] section

Commands:
uv run python -c "import epub2tts; print(f'Version: {epub2tts.__version__}')"  # Verify

Commit: "chore: Bump version to 0.2.0 for OmniParser integration release"

Create git tag:
git tag -a v0.2.0 -m "Release v0.2.0: OmniParser integration"
```

**Success Criteria:** ✅ Version bumped, tagged for release

---

### Phase 5: Final Validation & Handoff (30 minutes)

#### Task 5.1: End-to-End Testing (15 minutes)

**Use `house-bash` subagent:**

```
TASK: Run complete end-to-end test of epub2tts with OmniParser

Test full pipeline:

1. Convert EPUB to audiobook:
   uv run epub2tts convert "A System for Writing.epub" --output test_output/

2. Verify output:
   - Check for generated audio files
   - Verify chapter count matches expected
   - Check logs for errors

3. Test CLI commands:
   uv run epub2tts info "A System for Writing.epub"
   uv run epub2tts validate "A System for Writing.epub"

4. Run full test suite one final time:
   uv run pytest tests/ -v

Report:
- All commands work: YES/NO
- Audio files generated: YES/NO
- Chapter count correct: YES/NO
- All tests pass: X/Y tests passing
- Any errors or warnings: [list]

If all checks pass, ready for release!
```

**Success Criteria:** ✅ Complete pipeline works end-to-end

#### Task 5.2: Create Migration Report (15 minutes)

**Use `general-purpose` subagent:**

```
TASK: Create comprehensive migration completion report

File: docs/OMNIPARSER_MIGRATION_REPORT.md

Content:

# epub2tts → OmniParser Migration Report

**Date:** 2025-10-29
**Version:** v0.1.0 → v0.2.0
**Duration:** X hours

## Summary

Successfully migrated epub2tts from internal EPUB processing (ebooklib_processor.py) to external OmniParser library, reducing codebase complexity and improving maintainability.

## Changes Made

### Code Changes
- **Added**: OmniParserAdapter (150 lines)
- **Modified**: EPUBProcessor integration logic
- **Removed**: ebooklib_processor.py (965 lines)
- **Net Change**: -815 lines

### Dependencies
- **Added**: omniparser>=0.1.0,<2.0.0
- **Removed**: ebooklib (now provided by OmniParser)

### Tests
- **Added**: X integration tests for adapter
- **Added**: Y comparison tests
- **All existing tests**: PASSING

### Performance
- OmniParser processing time: X.XX seconds
- Legacy processor time: Y.YY seconds
- Performance delta: ±Z%
- Within acceptable range: YES ✓

## Compatibility

### Data Model Mapping
- epub2tts.EbookMetadata ↔ omniparser.Metadata ✓
- epub2tts.Chapter ↔ omniparser.Chapter ✓
- epub2tts.ProcessingResult ← OmniParserAdapter ✓

### Feature Parity
- TOC-based chapter detection ✓
- Metadata extraction ✓
- Image extraction ✓
- HTML-to-text conversion ✓
- Post-processing pipeline ✓

## Testing Results

### Test Suite Status
- Unit tests: X/Y passing
- Integration tests: A/B passing
- Regression tests: M/N passing
- Total: XX/YY passing (ZZ%)

### Validation Tests
- Chapter count comparison: PASS
- Word count comparison: PASS
- Metadata accuracy: PASS
- Performance benchmark: PASS

## Known Issues

[None / List any known issues]

## Recommendations

### Immediate
- Monitor performance in production
- Gather user feedback on EPUB processing
- Watch for edge cases not covered in tests

### Future
- Add more EPUB test fixtures
- Contribute improvements back to OmniParser
- Consider extending OmniParser for TTS-specific features

## Conclusion

Migration completed successfully. epub2tts now uses OmniParser for EPUB parsing, reducing technical debt and improving maintainability. All tests pass, performance is acceptable, and the codebase is cleaner.

**Status:** ✅ READY FOR RELEASE (v0.2.0)

---

Commit: "docs: Add comprehensive OmniParser migration report"
```

**Success Criteria:** ✅ Complete migration report documenting all changes

---

## 🚨 Troubleshooting Guide

### Issue 1: Data Model Mismatch

**Symptom:** Tests fail due to missing fields in converted data

**Solution:**
1. Check adapter's `_convert_metadata()` and `_convert_chapters()` methods
2. Add missing fields with sensible defaults
3. Update ProcessingResult construction
4. Re-run tests

### Issue 2: OmniParser Not Found

**Symptom:** `ImportError: No module named 'omniparser'`

**Solution:**
```bash
# Verify OmniParser installed
uv run python -c "import omniparser; print('Found')"

# Reinstall if needed
uv add --editable /Users/mini/Documents/GitHub/OmniParser

# Verify path correct
ls /Users/mini/Documents/GitHub/OmniParser/src/omniparser/
```

### Issue 3: Performance Regression

**Symptom:** OmniParser >20% slower than legacy

**Solution:**
1. Profile both processors: `uv run python -m cProfile -s cumtime script.py`
2. Identify bottleneck (likely image extraction or HTML parsing)
3. Check if OmniParser doing extra work (AI features disabled?)
4. Consider caching frequently-accessed data
5. Report issue to OmniParser if genuinely slower

### Issue 4: Test Failures

**Symptom:** Existing tests fail after integration

**Solution:**
1. Check which tests fail: `uv run pytest tests/ -v --tb=short`
2. Common causes:
   - Missing field in adapter conversion
   - Type mismatch (list vs string)
   - Timing-dependent test (processing_time field)
3. Update adapter to match expected output
4. Update tests if expectations changed

### Issue 5: Chapter Count Mismatch

**Symptom:** OmniParser extracts different number of chapters

**Solution:**
1. Compare TOC structures: both use TOC-based detection
2. Check if OmniParser has different TOC parsing
3. Verify test EPUB has proper TOC structure
4. May be acceptable variance (±1-2 chapters)
5. Document variance in tests with tolerance

---

## 📚 Reference Documents

**epub2tts:**
- src/core/epub_processor.py - Main EPUB orchestrator
- src/core/ebooklib_processor.py - Legacy processor (to be removed)
- src/core/text_cleaner.py - Text processing (unchanged)
- tests/integration/test_epub_processor.py - Integration tests

**OmniParser:**
- /Users/mini/Documents/GitHub/OmniParser/src/omniparser/models.py - Data models
- /Users/mini/Documents/GitHub/OmniParser/src/omniparser/parsers/epub_parser.py - EPUB parser
- /Users/mini/Documents/GitHub/OmniParser/docs/API.md - API documentation

---

## 🎬 Session Initialization

**Execution Command:**

```
You are an autonomous Claude Code agent tasked with migrating epub2tts to use OmniParser.

PROJECT CONTEXT:
- epub2tts location: /Users/mini/Documents/GitHub/epub2tts
- OmniParser location: /Users/mini/Documents/GitHub/OmniParser
- Target version: v0.2.0
- OmniParser version requirement: >=0.1.0,<2.0.0 (NOT >=1.0.0)

INSTRUCTIONS:
1. Read this entire guide (CLAUDE_CODE_EPUB2TTS_MIGRATION_GUIDE.md)
2. Navigate to epub2tts project directory
3. Execute Phase 1: Preparation & Analysis
4. Execute Phase 2: Integration
5. Execute Phase 3: Testing & Validation
6. Execute Phase 4: Cleanup & Documentation
7. Execute Phase 5: Final Validation & Handoff

CRITICAL REQUIREMENTS:
- Use subagents for EVERY task
- Commit after EVERY significant change
- Run tests after EVERY code modification
- Version requirement: omniparser = ">=0.1.0,<2.0.0"
- Performance regression must be <20%
- All existing tests must pass
- Update TODOS.md after each phase
- Follow conventional commit format

EXECUTION MODE: YOLO (auto-approve all actions)

SAFETY:
- Keep EbookLibProcessor as fallback until fully validated
- Don't remove legacy code until all tests pass
- Create backup of critical files before major changes

Begin execution. Report after each phase:
- Phase name
- Tasks completed
- Test status (X/Y passing)
- Performance metrics
- Commits created
- Ready for next phase: YES/NO
```

---

## 📊 Expected Outcomes

### Code Metrics

**Before Migration:**
- Total lines: ~12,000
- EPUB processing: 965 lines (ebooklib_processor.py)
- Dependencies: ebooklib, beautifulsoup4, ftfy, etc.

**After Migration:**
- Total lines: ~11,200 (-800 lines)
- EPUB processing: 150 lines (omniparser_adapter.py)
- Dependencies: omniparser (includes EPUB parsing), beautifulsoup4, ftfy

**Complexity Reduction:** ~82% fewer EPUB-processing lines

### Test Coverage

- Existing tests: 100% passing
- New tests: 15+ integration tests
- Coverage maintained: ≥80%

### Performance

- Processing time delta: ±20% (acceptable range)
- Memory usage: Similar or better
- Startup time: Minimal impact

---

## ✅ Success Checklist

**Pre-Release Validation:**
- [ ] OmniParser installed with version >=0.1.0,<2.0.0
- [ ] OmniParserAdapter implemented and tested
- [ ] EPUBProcessor uses OmniParser
- [ ] All existing tests pass (100%)
- [ ] New integration tests pass
- [ ] Performance within 20% of baseline
- [ ] ebooklib_processor.py removed (~965 lines)
- [ ] Dependencies updated
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped to v0.2.0
- [ ] Git tag created
- [ ] Migration report generated
- [ ] End-to-end pipeline tested

**When all checked:** ✅ Ready to release v0.2.0!

---

**Document Version:** 1.0
**Created:** 2025-10-29
**Session Type:** YOLO (Auto-approve)
**Strategy:** Subagent-First Development with Incremental Integration
**Target:** epub2tts v0.2.0 with OmniParser dependency
