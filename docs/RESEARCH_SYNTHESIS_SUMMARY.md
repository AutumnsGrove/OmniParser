# Research Agent 4: Architecture Planning - Synthesis Summary

**Agent Mission:** Create detailed architecture plan for OmniParser based on findings from research agents and project specifications

**Date:** October 16, 2025
**Status:** ✅ COMPLETE

---

## Deliverables Created

### 1. ARCHITECTURE_PLAN.md (10,500 words)
**Comprehensive blueprint covering:**
- Executive summary and project goals
- Layered architecture design
- Data model design and epub2tts mapping
- EPUB parser port strategy (detailed analysis of ebooklib_processor.py)
- Phase-by-phase implementation plan (16 phases with validation)
- epub2tts migration strategy
- Risk assessment and mitigation
- Implementation timeline (60-70 hours)
- Success metrics

### 2. IMPLEMENTATION_REFERENCE.md (3,500 words)
**Quick reference guide covering:**
- Core API contracts
- EPUB parser port checklist
- Text cleaning strategy
- Testing checklist
- Common patterns
- Command reference
- epub2tts migration steps
- Troubleshooting guide

### 3. ARCHITECTURE_DIAGRAMS.md (2,500 words)
**Visual reference covering:**
- System context diagram
- Layered architecture
- Parser flow diagram
- Document object structure
- EPUB parser internal flow
- Parser inheritance hierarchy
- epub2tts integration flow
- Error handling flow
- Testing structure
- Package structure

---

## Key Research Findings

### Source Analysis

**1. ebooklib_processor.py (963 lines)**
- Production-tested EPUB processing using EbookLib
- TOC-based chapter detection
- Comprehensive metadata extraction
- Image extraction with base64 handling
- HTML text extraction with BeautifulSoup
- Chapter post-processing (splitting, filtering)

**2. text_cleaner.py (522 lines)**
- Advanced text cleaning with ftfy
- Regex pattern-based transformations
- TTS-specific features (pause markers)
- Whitespace normalization
- Chapter segmentation

**3. Dependencies Analysis**
- Core: ebooklib, beautifulsoup4, lxml, pyyaml
- Text processing: ftfy, chardet, regex
- Additional parsers needed: PyMuPDF, python-docx, trafilatura

---

## Architecture Decisions

### 1. Data Model Design

**Key Change: Generalized Chapter Model**
```python
# epub2tts (TTS-specific)
@dataclass
class Chapter:
    chapter_num: int
    title: str
    content: str
    word_count: int
    estimated_duration: float  # TTS concern
    confidence: float          # Internal

# OmniParser (Universal)
@dataclass
class Chapter:
    chapter_id: int            # Renamed for clarity
    title: str
    content: str               # Markdown formatted
    start_position: int        # NEW: enables text range extraction
    end_position: int          # NEW: enables text range extraction
    word_count: int
    level: int                 # NEW: heading hierarchy
    metadata: Optional[Dict]   # NEW: chapter-specific data
```

**Rationale:**
- Remove TTS-specific fields (estimated_duration, confidence)
- Add position tracking for precise text ranges
- Add level for hierarchical structure
- Make universally useful for all document types

### 2. EPUB Parser Port Strategy

**What Stays the Same:**
- Core ebooklib API usage
- TOC-based chapter detection logic
- HTML text extraction with BeautifulSoup
- Recursive TOC traversal
- Metadata extraction from OPF

**What Changes:**
- Config object → options dict
- ProcessingResult → Document
- Remove progress_tracker (no UI updates)
- Simplify TextCleaner integration (basic only)
- Remove chapter splitting (make optional)
- Remove temp directory management

**Code Impact:**
- ~600 lines ported from ebooklib_processor.py
- ~200 lines adaptation code
- Total EPUBParser: ~800 lines

### 3. Text Cleaning Strategy

**OmniParser Scope (Universal):**
✅ ftfy for encoding fixes
✅ Quote normalization
✅ Whitespace normalization
✅ Line ending normalization

**epub2tts Scope (TTS-Specific):**
❌ Pause markers ([PAUSE: 2.0])
❌ TTS replacements (& → and)
❌ Chapter markers
❌ Dialogue markers
❌ Regex patterns from YAML

**Clean Separation:**
- OmniParser provides clean, normalized text
- epub2tts applies TTS-specific processing on top
- No circular dependencies

### 4. API Design

**Consistent Interface Across Parsers:**
```python
class BaseParser(ABC):
    def __init__(self, options: dict = None)
    def parse(self, file_path: Path) -> Document
    def supports_format(self, file_path: Path) -> bool
    def extract_images(self, file_path: Path) -> List[ImageReference]
    def clean_text(self, text: str) -> str
```

**Main Entry Point:**
```python
parse_document(
    file_path: Union[str, Path],
    extract_images: bool = True,
    detect_chapters: bool = True,
    clean_text: bool = True,
    ocr_enabled: bool = True,
    custom_options: dict = None
) -> Document
```

---

## Implementation Plan Summary

### Phase Breakdown (16 Phases)

**Foundation (Phases 1-5):** 18 hours
- Repository setup, models, base classes, utilities, exceptions

**Core Parsers (Phases 6-7):** 12 hours
- EPUB parser (port from epub2tts)
- PDF parser (PyMuPDF + OCR)

**Additional Parsers (Phases 8-10):** 9 hours
- DOCX parser
- HTML/URL parser
- Markdown & Text parsers

**Integration (Phases 11-14):** 17 hours
- Post-processors (chapter detector, metadata extractor, text cleaner)
- Main parser function
- Package exports
- Integration tests

**Polish (Phases 15-16):** 8 hours
- Documentation
- Final validation

**Total Estimated:** 64 hours (8 working days)

### Critical Path

```
Phase 1-2 (Setup + Models)
    │
    ▼
Phase 3 (BaseParser)
    │
    ▼
Phase 6 (EPUB Parser) ◄─── CRITICAL (largest, most complex)
    │
    ▼
Phase 11 (Processors)
    │
    ▼
Phase 12 (Main Function)
    │
    ▼
Phase 14 (Integration Tests)
    │
    ▼
Phase 16 (Final Validation)
```

---

## epub2tts Migration Plan

### Step 1: Add Dependency
```toml
# epub2tts/pyproject.toml
[project.dependencies]
omniparser>=1.0.0
```

### Step 2: Adapter Function
```python
def _omniparser_to_epub2tts(doc: Document) -> ProcessingResult:
    """Convert OmniParser Document to epub2tts format"""
    return ProcessingResult(
        success=True,
        text_content=doc.content,
        chapters=[_convert_chapter(ch) for ch in doc.chapters],
        metadata=_convert_metadata(doc.metadata),
        ...
    )
```

### Step 3: Update EPUBProcessor
```python
class EPUBProcessor:
    def process_epub(self, epub_path: Path) -> ProcessingResult:
        # Use OmniParser
        doc = parse_document(epub_path)

        # Convert to epub2tts format
        result = _omniparser_to_epub2tts(doc)

        # Apply TTS-specific processing
        result.text_content = self._apply_tts_processing(result.text_content)

        return result
```

### Step 4: Cleanup
- Delete `src/core/ebooklib_processor.py` (~1000 lines removed)
- Update tests
- Remove ebooklib dependency (if not used elsewhere)

### Step 5: Validation
- Run full epub2tts test suite
- Compare outputs with old implementation
- Verify audio generation works

---

## Risk Assessment

### High-Risk Issues

**Risk 1: API Incompatibility**
- **Impact:** epub2tts can't use OmniParser
- **Mitigation:** Careful data model design upfront, adapter layer
- **Status:** ✅ Addressed with Document model design

**Risk 2: Missing epub2tts Features**
- **Impact:** Loss of functionality during migration
- **Mitigation:** Feature parity matrix, keep TTS features in epub2tts
- **Status:** ✅ Addressed with clean separation

### Medium-Risk Issues

**Risk 3: Performance Regression**
- **Impact:** OmniParser slower than current implementation
- **Mitigation:** Profile and optimize, acceptable trade-off for abstraction
- **Status:** ⚠️ Monitor during implementation

**Risk 4: Incomplete Test Coverage**
- **Impact:** Bugs in production
- **Mitigation:** Target >80% coverage, comprehensive integration tests
- **Status:** ⚠️ Phase 14 dedicated to testing

### Low-Risk Issues

**Risk 5: Dependency Conflicts**
- **Impact:** Installation issues
- **Mitigation:** UV for clean dependency resolution
- **Status:** ✅ UV handles this well

---

## Success Metrics

### Code Quality
- [ ] All parsers implement BaseParser
- [ ] Type hints on all public APIs
- [ ] Docstrings on all public functions
- [ ] Black formatting applied
- [ ] No mypy errors

### Test Coverage
- [ ] >80% code coverage
- [ ] 100% coverage on data models
- [ ] All parsers have unit tests
- [ ] Integration tests for all formats
- [ ] Error handling tested

### Functionality
- [ ] All 6 parsers working
- [ ] Format detection accurate
- [ ] Chapter detection working
- [ ] Metadata extraction complete
- [ ] Image extraction functional

### Package Quality
- [ ] Builds: `uv build`
- [ ] Installs: `uv add omniparser`
- [ ] Imports work
- [ ] Examples run
- [ ] README clear

### epub2tts Integration
- [ ] epub2tts uses OmniParser
- [ ] All tests pass
- [ ] Audio generation works
- [ ] No performance regression >20%

---

## Key Design Patterns

### Pattern 1: Universal Parser Interface
```python
# All parsers follow same structure
class EPUBParser(BaseParser):
    def parse(self, file_path: Path) -> Document:
        # 1. Load format-specific library
        # 2. Extract metadata
        # 3. Extract structure (chapters)
        # 4. Extract images
        # 5. Clean text
        # 6. Build Document object
        # 7. Return Document
```

### Pattern 2: Options-Based Configuration
```python
# No Config object dependency
def __init__(self, options: dict = None):
    self.options = options or {}
    self.extract_images = self.options.get('extract_images', True)
```

### Pattern 3: Graceful Error Handling
```python
try:
    # Parsing logic
except FileNotFoundError as e:
    raise FileReadError(...) from e
except Exception as e:
    raise ParsingError(..., original_error=e) from e
```

---

## Dependencies Analysis

### Core Dependencies (Required)
- pyyaml>=6.0 - Config files
- beautifulsoup4>=4.12.0 - HTML parsing
- lxml>=5.0.0 - XML parsing
- ftfy>=6.1.0 - Encoding fixes
- python-magic>=0.4.27 - Format detection
- dataclasses-json>=0.6.0 - Serialization

### Parser-Specific Dependencies
- ebooklib>=0.19 - EPUB
- PyMuPDF>=1.23.0 - PDF
- pytesseract>=0.3.10 - PDF OCR
- python-docx>=1.0.0 - DOCX
- trafilatura>=1.6.0 - HTML
- readability-lxml>=0.8.0 - HTML fallback
- requests>=2.31.0 - URL fetching
- chardet>=5.2.0 - Text encoding
- Pillow>=10.0.0 - Image handling

### Total: 14 direct dependencies

---

## Testing Strategy

### Test Structure
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_models.py       # Data models
│   ├── test_epub_parser.py  # EPUB parser
│   ├── test_pdf_parser.py   # PDF parser
│   └── ...
├── integration/             # Slower, end-to-end tests
│   ├── test_full_pipeline.py
│   ├── test_format_detection.py
│   └── test_error_handling.py
└── fixtures/                # Test data
    ├── sample.epub
    ├── sample.pdf
    └── ...
```

### Coverage Goals
- Overall: >80%
- Models: 100%
- Parsers: >90%
- Utilities: >85%
- Integration: Full format coverage

---

## Timeline and Milestones

### Week 1: Foundation
- Days 1-2: Setup, models, base classes
- Days 3-4: Utilities, exceptions, tests
- **Milestone:** Core infrastructure complete

### Week 2: EPUB Parser
- Days 5-7: Port ebooklib_processor.py
- Days 8-9: PDF parser
- **Milestone:** Primary parsers working

### Week 3: Additional Parsers
- Day 10: DOCX parser
- Day 11: HTML/URL parser
- Day 12: Markdown & Text parsers
- **Milestone:** All parsers implemented

### Week 4: Integration
- Day 13: Post-processors
- Day 14: Main parser function
- Day 15: Package exports
- Days 16-17: Integration tests
- **Milestone:** Package feature-complete

### Week 5: Polish
- Days 18-19: Documentation
- Day 20: Final validation
- Day 21: Buffer
- **Milestone:** Ready for release

### Week 6: Migration
- Days 22-23: Update epub2tts
- Day 24: Testing
- Day 25: Cleanup
- **Milestone:** epub2tts using OmniParser

---

## Recommendations

### Immediate Actions (Start of Phase 1)
1. Create OmniParser repository
2. Setup UV package structure
3. Initialize git repository
4. Create initial pyproject.toml
5. Setup development environment

### Development Best Practices
1. Follow TDD (write tests first)
2. Run tests frequently (`uv run pytest`)
3. Format code regularly (`uv run black .`)
4. Type check often (`uv run mypy src/`)
5. Document as you go

### Quality Gates
1. All tests must pass before moving to next phase
2. Coverage must be >80% before declaring v1.0 complete
3. All examples must run successfully
4. Documentation must be complete
5. epub2tts integration must be validated

### Post-v1.0 Roadmap
1. Publish to PyPI
2. Update epub2tts to use OmniParser
3. Remove old EPUB processing code
4. Monitor performance and gather feedback
5. Plan v1.1 features (RTF, ODT, improved OCR)

---

## Conclusion

### What We Achieved

This research synthesis provides:
1. **Complete architectural blueprint** for OmniParser
2. **Detailed port strategy** from epub2tts's production code
3. **Clear migration path** for epub2tts integration
4. **Comprehensive risk assessment** with mitigation strategies
5. **Realistic timeline** (60-70 hours over 6 weeks)

### Key Insights

1. **epub2tts has excellent EPUB code** - Don't rewrite, port carefully
2. **Separation of concerns is critical** - OmniParser is format-agnostic, epub2tts handles TTS
3. **Data model design is foundational** - Get Document structure right first
4. **Testing is non-negotiable** - >80% coverage prevents regressions
5. **Clean APIs enable adoption** - Simple parse_document() interface

### Next Steps

**Immediate:**
- Begin Phase 1 (Repository Setup)
- Create initial file structure
- Setup development environment

**Short-term:**
- Complete Phases 1-5 (Foundation)
- Begin EPUB parser port (Phase 6)
- Maintain momentum with regular commits

**Long-term:**
- Complete all 16 phases
- Publish to PyPI
- Migrate epub2tts
- Gather feedback and iterate

---

## Document Index

**Primary Documents Created:**
1. `ARCHITECTURE_PLAN.md` - Main blueprint (same directory)
2. `IMPLEMENTATION_REFERENCE.md` - Quick reference (same directory)
3. `ARCHITECTURE_DIAGRAMS.md` - Visual reference (same directory)
4. `RESEARCH_SYNTHESIS_SUMMARY.md` - This document

**Source Documents Analyzed:**
1. `OMNIPARSER_PROJECT_SPEC.md` (same directory)
2. **epub2tts:** Original EPUB processing implementation
   - `METAPROMPT_1_OMNIPARSER_EXTRACTION.md`
   - `src/core/ebooklib_processor.py`
   - `src/core/text_cleaner.py`
   - `pyproject.toml`

---

## Final Checklist

**Architecture Planning Complete:**
- [x] Executive summary and goals defined
- [x] Architecture design documented
- [x] Data models designed with epub2tts mapping
- [x] EPUB parser port strategy detailed
- [x] All 16 phases planned with validation
- [x] epub2tts migration strategy documented
- [x] Risk assessment completed
- [x] Success metrics defined
- [x] Visual diagrams created
- [x] Implementation reference guide created
- [x] Testing strategy documented
- [x] Timeline and milestones established

**Ready for Implementation:**
- [x] All requirements understood
- [x] Architecture decisions documented
- [x] Technical approach validated
- [x] Dependencies identified
- [x] Risks assessed and mitigated
- [x] Success criteria clear
- [x] Documentation comprehensive

**Status:** ✅ **SYNTHESIS COMPLETE - READY FOR PHASE 1 IMPLEMENTATION**

---

**Research Agent 4 - Mission Accomplished**
**Date:** October 16, 2025
**Total Deliverables:** 4 comprehensive documents (16,500+ words)
**Status:** Architecture planning complete, ready for development

**Next Agent/Phase:** Begin Phase 1 (Repository Setup) of METAPROMPT_1
