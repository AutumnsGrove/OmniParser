# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **docx**: List extraction with nested list support (ordered and unordered)
- **docx**: Hyperlink extraction and markdown `[text](url)` formatting
- **docx**: DOCX test fixtures (5 public domain books from Project Gutenberg)

### Changed

- **docx**: Promoted from 🔶 Beta to ✅ Production-Ready
- **docx**: Enhanced feature set: text, tables, lists, hyperlinks, images, metadata
- Update README.md to reflect DOCX production-ready status

### Documentation

- Update CHANGELOG.md with DOCX refactoring details
- Consolidate CHANGELOG with 9 duplicate sections from merges
- Update README to reflect 6 parsers and AI features (Phase 2.8)
- Update CLAUDE.md project overview to Phase 2.8
- Update NEXT_STEPS.md with Phase 2.8 completion and future roadmap
- Update TODOS.md to reflect Phase 2.8 completion
- Update DOCX parser status from beta to production
- Add comprehensive parser refactoring plan (Phase 3.0)
- Add CHANGELOG management strategy to prevent future corruption
- Add cleanup completion report (Phase 2.9)

### Refactored

- **pdf**: Modularize PDF parser into functional components (1,052 lines → 9 modules, 1,485 lines)
  - Extract utils module with constants and helper functions (113 lines)
  - Extract validation module for file validation and loading (87 lines)
  - Extract metadata module for PDF metadata extraction (162 lines)
  - Extract tables module for table extraction and markdown conversion (147 lines)
  - Extract images module for image extraction and processing (186 lines)
  - Extract text_extraction module with OCR support (309 lines)
  - Extract heading_detection module for font-based heading analysis (283 lines)
  - Create parser orchestrator for functional pipeline coordination (175 lines)
  - Remove monolithic pdf_parser.py, update all imports to use modular structure
  - All modules follow functional patterns (functions ≤100 lines, modules ≤309 lines)
  - Comprehensive test suite: 122 tests, 94-100% coverage per module
  - Breaking change: PDFParser class no longer available for direct use
- **docx**: Modularize DOCX parser into functional components (755 lines → 12 modules, 1,759 lines)
  - Extract validation module for file validation and document loading (102 lines)
  - Extract metadata module for core properties extraction (119 lines)
  - Extract tables module for table-to-markdown conversion (98 lines)
  - Extract headings module for heading detection (90 lines)
  - Extract paragraphs module for paragraph/run formatting (109 lines)
  - Extract images module for image extraction with shared utilities (231 lines)
  - Extract utils module for word count and reading time (114 lines)
  - Extract content_extraction module for orchestration (202 lines)
  - **NEW:** Implement lists module for list detection and markdown formatting (195 lines)
  - **NEW:** Implement hyperlinks module for hyperlink extraction (197 lines)
  - Create parse_docx() orchestrator following functional pattern (182 lines)
  - Remove monolithic docx_parser.py (755 lines deleted)
  - Comprehensive test suite: 45 tests (23 lists + 22 hyperlinks)
  - Net code reduction: 395 lines saved through deduplication
  - Breaking change: DOCXParser class no longer available for direct use
- Extract shared metadata building logic to processor
- Extract shared image extraction logic to processor module

### Styling

- Standardize import organization across all parsers
- Add missing type hints across AI and utility modules

### Miscellaneous Tasks

- Bump version to 0.3.0 for release

## [Unreleased]

## [0.3.0] - 2025-10-29

### Added

- Add automated changelog generation with git-cliff
- Add release-please for automated version management
- **ai**: Add AI configuration module with multi-provider support (Anthropic, OpenAI, OpenRouter, Ollama, LM Studio)
- **ai**: Add AI-powered document processors (tagging, summarization, quality scoring)
- **ai**: Add AI-powered image analysis pipeline (OCR, description, classification)
- **ai**: Add file size validation for image processing
- **ai**: Add vision model validation and improve response parsing
- **ai**: Optional [ai] dependency group for AI features
- Add secrets management and configuration system for AI providers
- Add test image fixtures for vision integration testing
- **epub**: EPUBParser implementation with TOC-based chapter detection
- **pdf**: Add PDFParser implementation with font-based heading detection
- **pdf**: Integrate PDFParser with main parser module
- **docx**: Add DOCX parser implementation
- **markdown**: Add MarkdownParser class
- **markdown**: Register MarkdownParser in parser registry
- **text**: Implement TextParser with encoding detection and chapter detection
- **html**: HTML parser support

### Changed

- Move files and updated cliff.toml file
- **ai**: Improve AI config with retry logic and better error handling

### Fixed

- Update changelog workflow to use git-cliff-action v4
- Configure git-cliff to use prepend mode instead of regenerating changelog
- Remove conflicting OUTPUT env variable from git-cliff workflow
- Address PR review feedback for AI features
- **ai**: Add parsing failure warnings to AI processors
- **ai**: Complete input validation and error handling improvements
- **text**: Fix word count mismatch and implement PR review feedback
- **markdown**: Improve word counting, heading normalization, and image format detection
- **pdf**: Address PR review feedback with critical fixes
- **pdf**: Implement final PR review improvements
- Address PR review feedback for DOCX parser
- Final PR review fixes for production readiness
- Updated changelog workflow
- Resolve parser.py syntax errors from merge conflicts

### Documentation

- Update CHANGELOG.md
- Add troubleshooting for changelog content loss and tag requirements
- Update CHANGELOG.md
- Update CHANGELOG.md
- Add comprehensive agent prompts for parallel parser development
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- **ai**: Add usage guide and memory documentation
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Add guidance for file paths with spaces in CLI commands
- Update CHANGELOG.md
- Update CHANGELOG.md
- Add comprehensive test fixtures README
- Update CHANGELOG.md
- Add comprehensive NEXT_STEPS action plan for AI testing
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- **pdf**: Add comprehensive documentation and improve code quality
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update CHANGELOG.md
- Add comprehensive AI testing completion summary
- Update CHANGELOG.md

### Performance

- **markdown**: Add regex compilation optimization and metadata validation

### Refactored

- **ai**: Improve AI config with retry logic and better error handling
- **pdf**: Address PR review feedback with critical fixes
- **pdf**: Implement final PR review improvements

### Testing

- **ai**: Add comprehensive tests for AI features
- Add comprehensive integration tests for AI vision features
- **pdf**: Add comprehensive unit tests for PDFParser
- **pdf**: Add integration tests for PDF parsing
- Update parser tests to reflect PDF support
- **markdown**: Add test fixtures for markdown parser
- **markdown**: Add comprehensive unit tests for MarkdownParser
- **markdown**: Add integration tests for MarkdownParser
- Add LM Studio integration with Anthropic fallback for AI tests
- Add comprehensive unit tests for critical AI modules (Phase 3)

### Miscellaneous Tasks

- Move files and updated cliff.toml file
- Reorganize AI testing documentation into dedicated directory

## [Unreleased]

### Added

- Add automated changelog generation with git-cliff
- Add release-please for automated version management
- **ai**: Add AI configuration module with multi-provider support
- **ai**: Add AI-powered document processors
- **ai**: Add AI-powered image analysis pipeline
- **ai**: Add file size validation for image processing
- **text**: Implement TextParser with encoding detection and chapter detection
- **ai**: Add vision model validation and improve response parsing
- Add secrets management and configuration system for AI providers
- Add test image fixtures for vision integration testing
- **pdf**: Add PDFParser implementation with font-based heading detection
- **pdf**: Integrate PDFParser with main parser module
- **markdown**: Add MarkdownParser class
- **markdown**: Register MarkdownParser in parser registry
- Add DOCX parser implementation

### Fixed

- Update changelog workflow to use git-cliff-action v4
- Configure git-cliff to use prepend mode instead of regenerating changelog
- Remove conflicting OUTPUT env variable from git-cliff workflow
- Address PR review feedback for AI features
- **ai**: Add parsing failure warnings to AI processors
- **ai**: Complete input validation and error handling improvements
- **text**: Fix word count mismatch and implement PR review feedback
- **markdown**: Improve word counting, heading normalization, and image format detection
- Address PR review feedback for DOCX parser
- Final PR review fixes for production readiness
- Updated changelog workflow

### Documentation

- Update CHANGELOG.md
- Add troubleshooting for changelog content loss and tag requirements
- Add comprehensive agent prompts for parallel parser development
- **ai**: Add usage guide and memory documentation
- **pdf**: Add comprehensive documentation and improve code quality
- Add guidance for file paths with spaces in CLI commands
- Add comprehensive test fixtures README
- Add comprehensive NEXT_STEPS action plan for AI testing
- Add comprehensive AI testing completion summary
- Add API documentation for AI features

### Performance

- **markdown**: Add regex compilation optimization and metadata validation

### Testing

- **ai**: Add comprehensive tests for AI features
- Add comprehensive integration tests for AI vision features
- **pdf**: Add comprehensive unit tests for PDFParser
- **pdf**: Add integration tests for PDF parsing
- Update parser tests to reflect PDF support
- **markdown**: Add test fixtures for markdown parser
- **markdown**: Add comprehensive unit tests for MarkdownParser
- **markdown**: Add integration tests for MarkdownParser
- Add LM Studio integration with Anthropic fallback for AI tests
- Add comprehensive unit tests for critical AI modules (Phase 3)

### Miscellaneous Tasks

- Move files and updated cliff.toml file
- Reorganize AI testing documentation into dedicated directory

## [0.1.0] - 2025-10-23

### Summary
First development release featuring a production-ready EPUB parser with comprehensive testing. This release establishes the foundation for OmniParser's universal document parsing platform with full EPUB support.

### Added - Phase 1: Planning & Research (2025-10-16)
- Complete project specification (36,000 words)
- Architecture planning with 16-phase implementation plan (40,000 words)
- Implementation reference guide (16,000 words)
- Architecture diagrams with 14 Mermaid visualizations (37,000 words)
- Git commit style guide and development standards
- Initial project structure and configuration

### Added - Phase 2.1: Foundation (2025-10-16)
- **Core Data Models** (318 lines in models.py):
  - `Document` - Universal document representation
  - `Chapter` - Chapter structure with position tracking
  - `Metadata` - Document metadata (Dublin Core fields)
  - `ImageReference` - Image tracking with format detection
  - `ProcessingInfo` - Parser execution metadata
  - Serialization methods: to_dict, from_dict, save_json, load_json

- **Exception Hierarchy** (145 lines in exceptions.py):
  - `OmniParserError` - Base exception
  - `UnsupportedFormatError` - Format not supported
  - `ParsingError` - Generic parsing error
  - `FileNotFoundError` - File not found
  - `InvalidFileError` - Invalid file format
  - `ExtractionError` - Content extraction failed

- **BaseParser Abstract Interface** (99 lines in base/base_parser.py):
  - Abstract base class for all parsers
  - Enforced API contract: parse(), supports_format()
  - Optional methods: extract_images(), clean_text()

- **Utility Modules** (445 lines total):
  - `format_detector.py` (68 lines) - Magic byte format detection
  - `html_extractor.py` (216 lines) - HTML to text conversion
  - `encoding.py` (74 lines) - Character encoding handling
  - `validators.py` (87 lines) - Input validation

- **Testing Infrastructure**:
  - 171 comprehensive unit tests (100% passing)
  - pytest fixtures for all models
  - Test coverage: 87% for foundation components

### Added - Phase 2.2: EPUB Parser (2025-10-20)
- **EPUBParser Implementation** (~1,030 lines in parsers/epub_parser.py):
  - TOC-based chapter detection (primary method)
  - Spine-based chapter fallback (for EPUBs without TOC)
  - Complete metadata extraction from OPF (Dublin Core fields)
  - HTML to Markdown text extraction
  - Image extraction with cleanup
  - Word count and reading time estimation
  - Position tracking for all content

- **Text Processing** (300 lines in processors/text_cleaner.py):
  - YAML-based cleaning pattern configuration
  - Pattern-based text normalization
  - Encoding fixes and whitespace handling
  - No TTS-specific features (clean separation)

- **Main API** (141 lines in parser.py):
  - `parse_document()` - Universal entry point
  - Automatic format detection
  - Parser routing by file type
  - Consistent error handling

- **Testing**:
  - 141 new EPUB parser tests
  - 342 total tests passing (100% success rate)
  - All code Black formatted and mypy strict mode compliant

### Added - Phase 2.3: Integration Testing & Validation (2025-10-20 to 2025-10-23)
- **Real EPUB Test Fixtures** (26MB total):
  - alice-in-wonderland.epub (189KB, 12 chapters, 11 images)
  - frankenstein.epub (476KB, 24 chapters)
  - jekyll-and-hyde.epub (305KB, 10 chapters)
  - moby-dick.epub (816KB, 135 chapters)
  - pride-and-prejudice.epub (24MB, 61 chapters)
  - All public domain from Project Gutenberg

- **Integration Tests** (221 lines in tests/integration/test_epub_parsing.py):
  - 15 integration tests with real EPUB files
  - End-to-end parsing validation
  - Document structure accuracy checks
  - Chapter boundary verification
  - Metadata completeness testing
  - Image extraction validation
  - Performance benchmarks

- **Demo Application** (213 lines in examples/epub_to_markdown.py):
  - Full EPUB to Markdown converter
  - YAML frontmatter with metadata
  - Auto-generated table of contents with anchor links
  - Chapter markers and structure preservation
  - Performance timing and statistics output
  - Comprehensive usage guide in examples/README.md

- **Persistent Image Extraction Feature**:
  - `image_output_dir` parameter for EPUBParser
  - Support for both temporary (default) and persistent directories
  - Obsidian-compatible markdown output
  - Relative image paths for portability
  - Preserves EPUB internal directory structure
  - Backward compatible with existing code

### Performance
- **Target exceeded by 20x**: Parses 5MB EPUB in ~0.25 seconds (vs 5s goal)
- Memory usage well under 500MB for large EPUBs (24MB test file)
- No crashes on malformed EPUBs
- Graceful error handling and informative error messages

### Testing
- **357 total tests** (100% passing)
  - 342 unit tests
  - 15 integration tests
- **>90% code coverage** for EPUB parser components
- **~4,755 lines** of test code
- Real-world validation with Project Gutenberg classics

### Documentation
- Complete architecture and planning documentation
- API documentation for all public classes and methods
- Usage examples and integration guide
- Troubleshooting and best practices
- Git commit style guide

### Technical Details
- **Production code**: ~2,543 lines
- **Test code**: ~4,755 lines
- **Python**: 3.10+ with full type hints
- **Code quality**: Black formatted, mypy strict mode
- **Dependencies**: 14 production dependencies (ebooklib, beautifulsoup4, lxml, ftfy, etc.)
- **License**: MIT

### Known Limitations
- Only EPUB format currently supported (PDF, DOCX, HTML planned for future releases)
- Dependencies for future parsers installed but not yet implemented
- Not yet published to PyPI (install from source)

### Notes for Developers
- Use UV for package management: `uv sync`
- Run tests: `uv run pytest`
- Format code: `uv run black .`
- Type check: `uv run mypy src/`

---

## [Unreleased]

### Planned for Future Releases
- v0.2.1: PDF parser implementation (Phase 2.4)
- v0.3.0: DOCX parser implementation (Phase 2.5)
- v0.4.0: HTML/URL parser implementation (Phase 2.5)
- v0.5.0: Markdown and Text parsers (Phase 2.6)
- v1.0.0: Multi-format release with 3+ parsers, PyPI publication
