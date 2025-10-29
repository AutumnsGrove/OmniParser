# TODOS - OmniParser

**Last Updated:** 2025-10-29
**Current Phase:** Phase 2.5 Complete - HTML Parser with Image Extraction Production-Ready (v0.2.1)

---

## ✅ Recently Completed (2025-10-29)

### Phase 2.5: HTML/URL Parser Implementation - COMPLETE
- ✅ Implemented HTMLParser with Trafilatura + Readability fallback
- ✅ Live URL support with configurable timeout (default 10s)
- ✅ Local HTML file parsing (.html, .htm)
- ✅ Comprehensive image extraction:
  - ✅ Download images from URLs with Pillow processing
  - ✅ Alt text and dimension extraction
  - ✅ Format detection (JPEG, PNG, GIF, WebP, etc.)
  - ✅ Support for temp and persistent image directories
  - ✅ Sequential image IDs (img_001, img_002, etc.)
- ✅ Three shared processor utilities:
  - ✅ `markdown_converter.py` - HTML to Markdown conversion
  - ✅ `chapter_detector.py` - Heading-based chapter detection (reusable for PDF/DOCX)
  - ✅ `metadata_extractor.py` - OpenGraph/Dublin Core/meta tag extraction
- ✅ 62 HTML parser unit tests (100% passing)
- ✅ 32 integration tests
- ✅ 445 total tests passing (98% pass rate)
- ✅ Updated BaseParser to support Union[Path, str] for URL handling
- ✅ Full documentation and examples

**Commits:**
- `1b80945` - feat: Add HTML parser with live URL support and shared processors
- `e5fddd7` - feat: Add comprehensive image extraction to HTML parser

---

## Active Tasks

### Phase 3: Package Release (Recommended Next Phase)
- [ ] Update documentation for v0.1.0 release
- [ ] Set up CI/CD pipeline (GitHub Actions)
  - [ ] Automated testing on push
  - [ ] Code coverage reporting
  - [ ] Black formatting check
  - [ ] mypy type checking
- [ ] Publish to PyPI as EPUB-focused parser
  - [ ] Configure pyproject.toml for PyPI
  - [ ] Create distribution packages
  - [ ] Test installation from TestPyPI
  - [ ] Publish to production PyPI
- [ ] Create demo repository with examples
- [ ] Write user onboarding guide

### Phase 2.4: PDF Parser Implementation (Next Parser Priority)
- [ ] Implement PDFParser with PyMuPDF
  - [ ] Basic PDF text extraction
  - [ ] Reuse chapter_detector.py for heading-based chapter detection
  - [ ] Metadata extraction from PDF properties
  - [ ] Image extraction from PDFs
- [ ] Add OCR support for scanned PDFs (pytesseract)
- [ ] Write comprehensive PDF unit tests
- [ ] Add PDF integration tests with real files
- [ ] Update documentation for PDF support

### Phase 2.6: DOCX Parser Implementation
- [ ] Implement DOCXParser with python-docx
  - [ ] Text extraction from Word documents
  - [ ] Reuse chapter_detector.py for heading detection
  - [ ] Metadata extraction from document properties
  - [ ] Image extraction from embedded images
  - [ ] Table and list handling
- [ ] Write comprehensive DOCX unit tests
- [ ] Add DOCX integration tests with real files
- [ ] Update documentation for DOCX support

---

## Code Quality & Maintenance

### Testing
- [ ] Maintain >90% test coverage
- [ ] Add edge case tests for EPUB parser
- [ ] Create performance benchmarks

### Documentation
- [ ] Keep README.md in sync with implementation
- [ ] Update API documentation as features are added
- [ ] Document common usage patterns

### Code Quality
- [ ] Continue using Black formatter (automated)
- [ ] Maintain mypy type checking (currently strict mode)
- [ ] Review and update docstrings as needed

---

## Future Phases (Post v0.1.0)

### Additional Parsers (Planned)
- [x] Phase 2.5: HTML/URL Parser (COMPLETE - 2025-10-29)
- [ ] Phase 2.7: Markdown Parser (3-5 days)
- [ ] Phase 2.8: Text Parser (3-5 days)

### Advanced Features (v1.1+)
- [ ] Web & Social: Twitter/X, Reddit, LinkedIn, Medium, RSS/Atom
- [ ] Cloud Platforms: Google Docs, Notion, Confluence, Dropbox Paper
- [ ] Structured Data: JSON, XML, CSV, YAML parsing
- [ ] Archives: ZIP/TAR support with batch processing
- [ ] Technical: Jupyter notebooks, code documentation, API specs
- [ ] LLM-powered enhancements:
  - [ ] Image analysis → text descriptions (for PDFs, EPUBs)
  - [ ] Smart content summarization
  - [ ] Semantic chapter detection
- [ ] Export format options:
  - [ ] Plain text (.txt) export
  - [ ] PDF export from markdown
  - [ ] HTML export with styling

### epub2tts Integration (Phase 4)
- [ ] Make OmniParser a dependency in epub2tts
- [ ] Update epub2tts to use OmniParser for document parsing
- [ ] Run epub2tts test suite with OmniParser
- [ ] Verify no performance regression >20%
- [ ] Update epub2tts documentation

---

## Notes

### Current Strengths
- ✅ Excellent test coverage (445 tests, 98% passing)
- ✅ Two production-ready parsers: EPUB and HTML
- ✅ Three reusable shared processors (markdown_converter, chapter_detector, metadata_extractor)
- ✅ Well-documented codebase with comprehensive docstrings
- ✅ Following conventional commit style (100% adherence)
- ✅ Strong architecture with modular design
- ✅ Performance exceeds targets (0.25s for EPUB, <0.2s for HTML)
- ✅ Image extraction capability for HTML parser
- ✅ URL fetching with timeout handling

### Development Resources
- **Workflow Guides:** See `ClaudeUsage/` directory for comprehensive development workflows
- **Architecture:** See `docs/ARCHITECTURE_PLAN.md` for complete implementation plan
- **Specification:** See `docs/OMNIPARSER_PROJECT_SPEC.md` for technical details
- **Git Workflow:** See `ClaudeUsage/git_workflow.md` for branch strategy recommendations

### Key Commands
```bash
# Run tests
uv run pytest

# Format code
uv run black .

# Type check
uv run mypy src/

# Build package
uv build

# Install locally
uv sync
```

---

**Remember:** Always check this file at the start of each coding session and update it as tasks progress!
