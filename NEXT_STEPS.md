# Next Steps: Phase 2.1 - OmniParser Foundation Development

## 🎯 Objective
Build the OmniParser foundation (METAPROMPT_1 Phases 1-5):
- Repository structure
- Core data models
- BaseParser interface
- Exception classes
- Utility functions

---

## 📖 Required Reading (Start Here)

Before beginning implementation, read these documents in order:

### 1. Architecture & Design
**Start with the architecture plan to understand the overall system design:**
- **`ARCHITECTURE_PLAN.md`** - Complete implementation blueprint with all 16 phases
  - Section 1: Executive Summary (project goals and scope)
  - Section 2: Detailed Architecture (layered design)
  - Section 3: Data Model Design (Document, Chapter, Metadata classes)
  - Section 4: EPUB Parser Port Strategy (critical for Phase 6)
  - Section 5-7: Implementation details for each phase
  - Section 8: epub2tts Migration Strategy

### 2. Visual Reference
**Review all architectural diagrams for visual understanding:**
- **`ARCHITECTURE_DIAGRAMS.md`** - System architecture diagrams
- **`Diagrams/`** directory - All Mermaid diagrams
  - System architecture overview
  - Data flow diagrams
  - Parser inheritance hierarchy
  - Testing structure

### 3. Implementation Guide
**Quick reference for coding patterns:**
- **`IMPLEMENTATION_REFERENCE.md`** - Developer quick reference
  - API contracts
  - Code patterns
  - Testing checklist
  - Command reference

### 4. Research Findings
**Context from original epub2tts codebase:**
- **`RESEARCH_SYNTHESIS_SUMMARY.md`** - Executive summary of research findings
  - What was learned from ebooklib_processor.py analysis
  - Test strategy insights
  - Dependency requirements

### 5. Original Specification
**Detailed requirements:**
- **`OMNIPARSER_PROJECT_SPEC.md`** - Original project specification
  - Complete API reference
  - Parser implementation details
  - Data model specifications

---

## 🚀 Phase 2.1 Implementation Tasks

### Task 1: Repository Structure (Phase 1)
Create the complete directory structure:

```
omniparser/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── CHANGELOG.md
├── .gitignore
├── src/
│   └── omniparser/
│       ├── __init__.py
│       ├── parser.py
│       ├── models.py
│       ├── exceptions.py
│       ├── base/
│       │   ├── __init__.py
│       │   └── base_parser.py
│       ├── parsers/
│       │   └── __init__.py
│       ├── processors/
│       │   └── __init__.py
│       └── utils/
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
│   └── README.md
└── examples/
    └── basic_usage.py
```

**Reference:** ARCHITECTURE_PLAN.md Section 2 (Repository Structure)

---

### Task 2: Core Data Models (Phase 2)
Implement all data models in `src/omniparser/models.py`:

#### Classes to Implement:
1. **`ImageReference`** - Image metadata and position
2. **`Chapter`** - Chapter content with boundaries
3. **`Metadata`** - Document metadata
4. **`ProcessingInfo`** - Parser metadata
5. **`Document`** - Main document object with methods:
   - `get_chapter(chapter_id)`
   - `get_text_range(start, end)`
   - `to_dict()`
   - `from_dict()`
   - `save_json(path)`
   - `load_json(path)`

**Reference:**
- ARCHITECTURE_PLAN.md Section 3 (Data Model Design)
- OMNIPARSER_PROJECT_SPEC.md Section 3.2 (Data Models)

---

### Task 3: Base Parser Interface (Phase 3)
Implement abstract base parser in `src/omniparser/base/base_parser.py`:

#### BaseParser Class:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from ..models import Document

class BaseParser(ABC):
    def __init__(self, options: dict = None):
        self.options = options or {}

    @abstractmethod
    def parse(self, file_path: Path) -> Document:
        """Parse document and return Document object"""
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if this parser supports the file format"""
        pass

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """Extract images (optional override)"""
        return []

    def clean_text(self, text: str) -> str:
        """Apply text cleaning (optional override)"""
        from ..processors.text_cleaner import clean_text
        return clean_text(text)
```

**Reference:**
- ARCHITECTURE_PLAN.md Section 4 (BaseParser Design)
- OMNIPARSER_PROJECT_SPEC.md Section 4.1 (Base Parser Interface)

---

### Task 4: Exception Classes (Phase 5)
Implement custom exceptions in `src/omniparser/exceptions.py`:

#### Exceptions to Create:
1. `OmniparserError` (base exception)
2. `UnsupportedFormatError`
3. `ParsingError`
4. `FileReadError`
5. `NetworkError`
6. `ValidationError`

**Reference:**
- ARCHITECTURE_PLAN.md Section 5 (Exception Handling)
- OMNIPARSER_PROJECT_SPEC.md Section 7.1 (Custom Exceptions)

---

### Task 5: Utility Functions (Phase 4)
Implement utility modules:

#### 5a. Format Detection (`utils/format_detector.py`):
- `detect_format(file_path: Path) -> str`
- Use python-magic for magic bytes detection
- Fallback to file extension

#### 5b. Encoding Utilities (`utils/encoding.py`):
- Encoding detection with chardet
- UTF-8 normalization
- Line ending normalization

#### 5c. Validators (`utils/validators.py`):
- File existence validation
- File size validation
- Format support validation

**Reference:**
- ARCHITECTURE_PLAN.md Section 6 (Utility Functions)
- OMNIPARSER_PROJECT_SPEC.md Section 6 (Format Detection)

---

## 📋 Validation Checklist

Before completing Phase 2.1, ensure:

- [ ] All files created in correct locations
- [ ] `uv sync` runs without errors
- [ ] All data models have proper type hints
- [ ] BaseParser interface is complete
- [ ] All exceptions inherit correctly
- [ ] Unit tests created for each component:
  - [ ] `tests/unit/test_models.py`
  - [ ] `tests/unit/test_exceptions.py`
  - [ ] `tests/unit/test_validators.py`
  - [ ] `tests/unit/test_format_detector.py`
- [ ] All tests pass with pytest
- [ ] Code formatted with Black
- [ ] Git commits follow conventional commit style (see CLAUDE.md)

---

## 🔄 After Phase 2.1 Completion

Once foundation is complete, proceed to:
- **Phase 2.2:** Port EPUB Parser (Phase 6)
  - Read Research Agent 1's analysis of ebooklib_processor.py
  - Adapt 963-line processor to BaseParser interface
  - Focus on TOC-based chapter detection

---

## 📚 Key Implementation Notes

### Data Model Differences from epub2tts

**epub2tts Chapter:**
```python
@dataclass
class Chapter:
    chapter_num: int
    title: str
    content: str
    word_count: int
    estimated_duration: float  # TTS-specific
    confidence: float = 1.0     # EPUB-specific
```

**OmniParser Chapter (Universal):**
```python
@dataclass
class Chapter:
    chapter_id: int
    title: str
    content: str
    start_position: int   # Character position
    end_position: int     # Character position
    word_count: int
    level: int           # Heading level (1=main, 2=subsection)
    metadata: Optional[Dict] = None
```

**Rationale:**
- Removed TTS-specific fields (estimated_duration)
- Removed parser-specific fields (confidence)
- Added position tracking for text range extraction
- Added hierarchical level for nested chapters

### Configuration Pattern

**epub2tts uses Config object:**
```python
processor = EbookLibProcessor(config)
result = processor.process_epub(epub_path)
```

**OmniParser uses options dict:**
```python
parser = EPUBParser(options={
    'extract_images': True,
    'detect_chapters': True,
    'clean_text': True
})
document = parser.parse(epub_path)
```

**Rationale:** More flexible, testable, and doesn't require config file management.

---

## 🛠️ Development Commands

```bash
# Initialize project (if not done)
cd /Users/autumn/Documents/Projects/OmniParser
uv init

# Install dependencies
uv add pyyaml regex ftfy beautifulsoup4 lxml pydantic pillow python-magic chardet dataclasses-json

# Install dev dependencies
uv add --dev pytest pytest-cov black mypy

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/

# Build package
uv build
```

---

## ⚠️ Important Reminders

1. **Follow the architecture plan exactly** - Don't deviate without good reason
2. **Write tests alongside code** - Each component should have unit tests
3. **Use type hints everywhere** - Helps with IDE support and catches errors
4. **Document all public APIs** - Comprehensive docstrings
5. **Keep commits small and focused** - Follow conventional commit style
6. **Reference line numbers** - When discussing code, use `file_path:line_number` format

---

## 📞 Questions or Blockers?

If you encounter any ambiguity or need clarification:
1. Check ARCHITECTURE_PLAN.md Section 8 (Risk Assessment & Mitigation)
2. Review IMPLEMENTATION_REFERENCE.md for code patterns
3. Look at OMNIPARSER_PROJECT_SPEC.md for detailed specs
4. Refer to Research Agent findings for epub2tts context

---

**Ready to build! Start with Task 1 (Repository Structure) and work sequentially through Task 5.**

Good luck! 🚀
