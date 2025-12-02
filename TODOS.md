# TODOS.md

> Task tracking for OmniParser development. Update this file when tasks are completed, added, or changed.

---

## Current Status

**Version:** 0.3.1
**Parsers:** 7 implemented (EPUB, HTML, PDF, DOCX, Markdown, Text, Photo)
**Test Coverage:** 94.3% (830/880 passing)
**Last Updated:** 2025-12-02

---

## High Priority

- [ ] **Fix remaining 50 failing tests** - Investigate and resolve test failures
- [ ] **Add CLI interface** - Implement `omniparser` command-line tool for direct usage
- [ ] **Standardize options handling** - Create unified `ParserConfig` dataclass for all parsers

---

## Medium Priority

- [ ] **Create PyPI release workflow** - Automate package publishing with GitHub Actions
- [ ] **Add more AI providers** - Expand beyond Anthropic/OpenAI (e.g., Google Gemini, Cohere)
- [ ] **Performance benchmarks** - Document and track parser performance metrics
- [ ] **Add async support** - Implement async versions of parsers for concurrent processing

---

## Low Priority

- [ ] **Create API documentation** - Generate comprehensive API docs with Sphinx or MkDocs
- [ ] **Add migration guide** - Document upgrading from v0.2.x to v0.3.x
- [ ] **Create contributor guide** - Detailed guide for new contributors

---

## Parser Roadmap

### Phase 3: Ebook & Document Formats

#### 3.1 Kindle Ebooks (MOBI/AZW)
**Priority:** High
**Extensions:** `.mobi`, `.azw`, `.azw3`, `.kfx`
**Estimated Effort:** Medium (2-3 days)

**Description:**
Amazon Kindle ebook format parser. Natural complement to EPUB parser for comprehensive ebook support.

**Implementation Plan:**
1. **Research & Setup**
   - Evaluate libraries: `mobi`, `KindleUnpack`, `calibre` (as subprocess)
   - Test DRM-free extraction capabilities
   - Document format structure (PDB container, MOBI header, text records)

2. **Core Implementation** (`parsers/kindle/`)
   - `parser.py` - Main `parse_kindle()` function
   - `validation.py` - File validation and DRM detection
   - `metadata.py` - Extract MOBI metadata (title, author, ASIN, etc.)
   - `content.py` - Extract HTML content from records
   - `toc.py` - Parse NCX/navigation for chapter structure
   - `images.py` - Extract cover and embedded images

3. **Features:**
   - [ ] Metadata extraction (title, author, publisher, ASIN)
   - [ ] Chapter detection from NCX/TOC
   - [ ] Image extraction (cover, inline images)
   - [ ] DRM detection with clear error message
   - [ ] Fallback to EPUB conversion if needed

4. **Testing:**
   - Unit tests for each module
   - Integration tests with sample `.mobi` files
   - Edge cases: DRM files, malformed headers

**Dependencies:** `mobi` or `KindleUnpack`

---

#### 3.2 OpenDocument Text (ODT)
**Priority:** High
**Extensions:** `.odt`
**Estimated Effort:** Medium (2-3 days)

**Description:**
LibreOffice/OpenOffice document format. Open standard alternative to DOCX.

**Implementation Plan:**
1. **Research & Setup**
   - Use `odfpy` library (official ODF implementation)
   - Understand ODF structure (ZIP with XML content)
   - Map ODF elements to Document model

2. **Core Implementation** (`parsers/odt/`)
   - `parser.py` - Main `parse_odt()` function
   - `validation.py` - ZIP/ODF validation
   - `metadata.py` - Extract from `meta.xml`
   - `content_extraction.py` - Parse `content.xml`
   - `styles.py` - Handle formatting styles
   - `images.py` - Extract from `Pictures/` directory
   - `tables.py` - Convert tables to markdown

3. **Features:**
   - [ ] Full text extraction with formatting
   - [ ] Heading-based chapter detection
   - [ ] Table extraction as markdown
   - [ ] Image extraction with captions
   - [ ] List handling (ordered/unordered)
   - [ ] Hyperlink preservation

4. **Testing:**
   - Create test ODT files with various features
   - Compare output with DOCX parser for similar content

**Dependencies:** `odfpy`

---

#### 3.3 RTF (Rich Text Format)
**Priority:** Medium
**Extensions:** `.rtf`
**Estimated Effort:** Medium (2-3 days)

**Description:**
Legacy document format still widely used for cross-platform compatibility.

**Implementation Plan:**
1. **Research & Setup**
   - Evaluate: `striprtf`, `pyrtf-ng`, `pyth`
   - Understand RTF control words and groups
   - Handle various RTF versions (1.0 - 1.9.1)

2. **Core Implementation** (`parsers/rtf/`)
   - `parser.py` - Main `parse_rtf()` function
   - `validation.py` - RTF header validation
   - `tokenizer.py` - RTF control word tokenization
   - `content.py` - Text and formatting extraction
   - `metadata.py` - Extract document info
   - `images.py` - Extract embedded images (WMF, EMF, JPEG, PNG)

3. **Features:**
   - [ ] Text extraction with basic formatting
   - [ ] Metadata extraction (author, title, dates)
   - [ ] Image extraction (various formats)
   - [ ] Table support (if present)
   - [ ] Encoding handling (various codepages)

4. **Edge Cases:**
   - Nested groups
   - Unicode escapes
   - Binary data blobs

**Dependencies:** `striprtf` or custom parser

---

### Phase 4: Technical Documentation Formats

#### 4.1 LaTeX Documents (TEX)
**Priority:** Medium
**Extensions:** `.tex`, `.latex`
**Estimated Effort:** High (4-5 days)

**Description:**
Standard format for academic and scientific documents. Complex macro system.

**Implementation Plan:**
1. **Research & Setup**
   - Evaluate: `TexSoup`, `pylatexenc`, `plasTeX`
   - Decide on macro expansion depth
   - Handle common packages (amsmath, graphicx, hyperref)

2. **Core Implementation** (`parsers/latex/`)
   - `parser.py` - Main `parse_latex()` function
   - `validation.py` - Basic syntax validation
   - `preprocessor.py` - Handle `\input`, `\include` directives
   - `commands.py` - Parse common LaTeX commands
   - `environments.py` - Handle environments (document, figure, table, etc.)
   - `math.py` - Extract/convert math expressions
   - `bibliography.py` - Parse `\cite` and bibliography
   - `metadata.py` - Extract from `\title`, `\author`, `\date`

3. **Features:**
   - [ ] Section-based chapter detection (`\section`, `\chapter`)
   - [ ] Math equation handling (as text or image)
   - [ ] Figure/table extraction with captions
   - [ ] Bibliography/citation handling
   - [ ] Cross-reference resolution
   - [ ] Basic macro expansion

4. **Limitations:**
   - Complex custom macros may not expand correctly
   - Some packages may not be fully supported
   - Focus on common document structures

**Dependencies:** `TexSoup` or `pylatexenc`

---

#### 4.2 reStructuredText (RST)
**Priority:** Low
**Extensions:** `.rst`
**Estimated Effort:** Low (1-2 days)

**Description:**
Python documentation standard. Used by Sphinx for technical documentation.

**Implementation Plan:**
1. **Research & Setup**
   - Use `docutils` (official implementation)
   - Understand directive system
   - Handle Sphinx-specific extensions

2. **Core Implementation** (`parsers/rst/`)
   - `parser.py` - Main `parse_rst()` function using docutils
   - `validation.py` - RST syntax validation
   - `metadata.py` - Extract from field lists and docinfo
   - `content.py` - Convert to markdown
   - `directives.py` - Handle common directives

3. **Features:**
   - [ ] Heading-based chapter structure
   - [ ] Code block extraction with language hints
   - [ ] Cross-reference handling
   - [ ] Image and figure directives
   - [ ] Admonition conversion (note, warning, etc.)
   - [ ] Table conversion

**Dependencies:** `docutils`

---

### Phase 5: Data & Notebook Formats

#### 5.1 Jupyter Notebooks (IPYNB)
**Priority:** High
**Extensions:** `.ipynb`
**Estimated Effort:** Low (1-2 days)

**Description:**
Interactive data science notebooks combining code, markdown, and outputs.

**Implementation Plan:**
1. **Research & Setup**
   - Use `nbformat` (official Jupyter library)
   - Handle different notebook versions (v3, v4)
   - Decide on output handling (include/exclude)

2. **Core Implementation** (`parsers/jupyter/`)
   - `parser.py` - Main `parse_jupyter()` function
   - `validation.py` - Notebook version validation
   - `metadata.py` - Extract notebook metadata
   - `cells.py` - Process code, markdown, raw cells
   - `outputs.py` - Handle cell outputs (text, images, HTML)

3. **Features:**
   - [ ] Code cell extraction with syntax highlighting markers
   - [ ] Markdown cell rendering
   - [ ] Output extraction (text, error, display_data)
   - [ ] Image output handling
   - [ ] Execution order tracking
   - [ ] Kernel info as metadata

4. **Output Options:**
   - `include_outputs`: Include cell execution outputs
   - `include_code`: Include code cells
   - `execution_count`: Show execution order

**Dependencies:** `nbformat`

---

#### 5.2 Structured Data (JSON/YAML)
**Priority:** Medium
**Extensions:** `.json`, `.yaml`, `.yml`
**Estimated Effort:** Low (1-2 days)

**Description:**
Convert structured data to readable markdown representation.

**Implementation Plan:**
1. **Core Implementation** (`parsers/structured/`)
   - `parser.py` - Main `parse_structured()` function
   - `json_parser.py` - JSON-specific handling
   - `yaml_parser.py` - YAML-specific handling
   - `renderer.py` - Convert to markdown representation
   - `schema.py` - Optional JSON Schema detection

2. **Features:**
   - [ ] Nested structure rendering with indentation
   - [ ] Array-to-table conversion (for uniform objects)
   - [ ] Type-aware formatting (dates, URLs, etc.)
   - [ ] Large file handling (streaming for big files)
   - [ ] Schema detection and description

3. **Rendering Options:**
   - `max_depth`: Maximum nesting depth to render
   - `array_as_table`: Convert arrays of objects to tables
   - `code_block`: Wrap in code block vs expand

**Dependencies:** `pyyaml` (already installed)

---

#### 5.3 Tabular Data (CSV/TSV)
**Priority:** Medium
**Extensions:** `.csv`, `.tsv`
**Estimated Effort:** Low (1 day)

**Description:**
Convert tabular data to markdown tables with intelligent formatting.

**Implementation Plan:**
1. **Core Implementation** (`parsers/csv/`)
   - `parser.py` - Main `parse_csv()` function
   - `detection.py` - Delimiter and encoding detection
   - `renderer.py` - Markdown table generation
   - `statistics.py` - Column statistics and types

2. **Features:**
   - [ ] Auto-detect delimiter (comma, tab, semicolon, pipe)
   - [ ] Header row detection
   - [ ] Encoding detection (UTF-8, Latin-1, etc.)
   - [ ] Large file sampling (first N rows)
   - [ ] Column type inference
   - [ ] Basic statistics in metadata

3. **Options:**
   - `max_rows`: Maximum rows to include (default: 1000)
   - `include_stats`: Add column statistics
   - `detect_header`: Auto-detect header row

**Dependencies:** Standard library `csv`

---

### Phase 6: Microsoft Office Formats

#### 6.1 Excel Spreadsheets (XLSX/XLS)
**Priority:** High
**Extensions:** `.xlsx`, `.xls`, `.xlsm`, `.xlsb`
**Estimated Effort:** Medium (2-3 days)

**Description:**
Microsoft Excel spreadsheet parsing with multi-sheet support.

**Implementation Plan:**
1. **Research & Setup**
   - Use `openpyxl` for XLSX (modern format)
   - Use `xlrd` for legacy XLS format
   - Handle formulas, charts, pivot tables

2. **Core Implementation** (`parsers/excel/`)
   - `parser.py` - Main `parse_excel()` function
   - `validation.py` - File format validation
   - `metadata.py` - Workbook properties
   - `sheets.py` - Sheet processing
   - `cells.py` - Cell value extraction
   - `formulas.py` - Formula handling (values vs formulas)
   - `charts.py` - Chart extraction as images
   - `tables.py` - Named table/range extraction

3. **Features:**
   - [ ] Multi-sheet handling (each sheet as chapter)
   - [ ] Cell value extraction (with formatting)
   - [ ] Formula evaluation (show values by default)
   - [ ] Named range extraction
   - [ ] Table/range to markdown conversion
   - [ ] Chart extraction as images
   - [ ] Metadata (author, dates, custom properties)

4. **Options:**
   - `sheets`: List of sheets to include (default: all)
   - `include_formulas`: Show formulas vs values
   - `max_rows`: Row limit per sheet
   - `extract_charts`: Extract charts as images

**Dependencies:** `openpyxl`, `xlrd` (for legacy)

---

#### 6.2 PowerPoint Presentations (PPTX/PPT)
**Priority:** High
**Extensions:** `.pptx`, `.ppt`, `.ppsx`, `.pps`
**Estimated Effort:** Medium (2-3 days)

**Description:**
Microsoft PowerPoint presentation parsing with slide-by-slide extraction.

**Implementation Plan:**
1. **Research & Setup**
   - Use `python-pptx` for PPTX format
   - Evaluate legacy PPT support options
   - Handle slide layouts, masters, themes

2. **Core Implementation** (`parsers/powerpoint/`)
   - `parser.py` - Main `parse_powerpoint()` function
   - `validation.py` - File format validation
   - `metadata.py` - Presentation properties
   - `slides.py` - Slide-by-slide processing
   - `shapes.py` - Shape content extraction
   - `text.py` - Text frame extraction
   - `images.py` - Image and chart extraction
   - `notes.py` - Speaker notes extraction
   - `tables.py` - Table extraction

3. **Features:**
   - [ ] Slide-by-slide extraction (each slide as chapter)
   - [ ] Text from all shapes (textboxes, titles, etc.)
   - [ ] Speaker notes as additional content
   - [ ] Image extraction with positions
   - [ ] Table extraction as markdown
   - [ ] SmartArt text extraction
   - [ ] Slide numbers and titles

4. **Options:**
   - `include_notes`: Include speaker notes
   - `extract_images`: Extract slide images
   - `slides`: Specific slide numbers to extract

**Dependencies:** `python-pptx`

---

### Phase 7: Audio Transcription

#### 7.1 Audio Transcription (MP3/WAV/M4A)
**Priority:** Medium
**Extensions:** `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.wma`
**Estimated Effort:** High (3-4 days)

**Description:**
Speech-to-text transcription using NVIDIA Parakeet TDT model (600M parameters).
This feature requires optional heavy dependencies and should be truly optional.

**Model:** `nvidia/parakeet-tdt-0.6b-v2`
- 600M parameter model
- Excellent accuracy for English
- Supports timestamps and punctuation
- ~1.2GB model download

**Implementation Plan:**
1. **Dependency Strategy (CRITICAL)**
   - Create optional dependency group: `pip install omniparser[audio]`
   - Lazy import all audio dependencies
   - Graceful degradation with clear error message
   - Consider Docker image with pre-installed deps

2. **Core Implementation** (`parsers/audio/`)
   - `parser.py` - Main `parse_audio()` function
   - `validation.py` - Audio file validation
   - `metadata.py` - Extract audio metadata (duration, bitrate, etc.)
   - `transcriber.py` - Parakeet model wrapper
   - `timestamps.py` - Timestamp formatting
   - `segmentation.py` - Chapter detection from silence gaps
   - `diarization.py` - Optional speaker diarization

3. **Features:**
   - [ ] Automatic speech recognition
   - [ ] Timestamp generation (word or sentence level)
   - [ ] Punctuation and capitalization
   - [ ] Chapter detection from long silences
   - [ ] Audio metadata (duration, sample rate, channels)
   - [ ] Progress callbacks for long files

4. **Optional Features (Future):**
   - [ ] Speaker diarization (who said what)
   - [ ] Language detection
   - [ ] Multi-language support

5. **Configuration:**
   ```python
   options = {
       "include_timestamps": True,  # Add timestamps
       "timestamp_level": "sentence",  # "word" or "sentence"
       "detect_chapters": True,  # Split on long silences
       "silence_threshold": 2.0,  # Seconds of silence for chapter split
       "device": "cuda",  # or "cpu"
   }
   ```

6. **Optional Dependency Setup (pyproject.toml):**
   ```toml
   [project.optional-dependencies]
   audio = [
       "nemo_toolkit[asr]>=1.20.0",
       "torch>=2.0.0",
       "torchaudio>=2.0.0",
       "pydub>=0.25.0",
       "librosa>=0.10.0",
   ]
   ```

**Dependencies:**
- `nemo_toolkit[asr]` (NVIDIA NeMo for Parakeet)
- `torch`, `torchaudio`
- `pydub` (audio format handling)
- `librosa` (audio analysis)

**Hardware Requirements:**
- Minimum: 8GB RAM, CPU (slow but works)
- Recommended: NVIDIA GPU with 4GB+ VRAM
- Optimal: NVIDIA GPU with 8GB+ VRAM (faster processing)

---

### Phase 8: Email Formats

#### 8.1 Email Messages (EML/MSG)
**Priority:** Medium
**Extensions:** `.eml`, `.msg`
**Estimated Effort:** Medium (2-3 days)

**Description:**
Email message parsing with attachment extraction and thread detection.

**Implementation Plan:**
1. **Research & Setup**
   - Use `email` (stdlib) for EML format
   - Use `extract-msg` for Outlook MSG format
   - Handle multipart messages, encodings

2. **Core Implementation** (`parsers/email/`)
   - `parser.py` - Main `parse_email()` function
   - `eml_parser.py` - EML format handling
   - `msg_parser.py` - MSG format handling
   - `metadata.py` - Headers extraction
   - `body.py` - Body extraction (plain/HTML)
   - `attachments.py` - Attachment extraction
   - `threading.py` - Email thread detection

3. **Features:**
   - [ ] Header extraction (From, To, Subject, Date, etc.)
   - [ ] Body extraction (prefer plain text, fallback HTML)
   - [ ] Attachment listing and optional extraction
   - [ ] Thread/conversation detection (In-Reply-To, References)
   - [ ] MIME type handling
   - [ ] Encoding detection and conversion

4. **Metadata Fields:**
   - `from`, `to`, `cc`, `bcc`
   - `subject`, `date`
   - `message_id`, `in_reply_to`
   - `attachments` (list with names and sizes)

**Dependencies:** `extract-msg` (for Outlook MSG)

---

## Completed

- [x] **BaseProject integration** - Added AgentUsage/, updated CLAUDE.md, installed git hooks
- [x] **QR code detection** - Implemented in PDF parser with URL fetching
- [x] **All 7 parsers implemented** - EPUB, HTML, PDF, DOCX, Markdown, Text, Photo
- [x] **PhotoParser wrapper class** - Added for API consistency
- [x] **ParserRegistry** - Added dynamic format registration system
- [x] **Lazy imports** - Improved startup performance in parser.py

---

## Implementation Notes for Future Agents

### Adding a New Parser

1. **Create parser directory:** `src/omniparser/parsers/{format}/`
2. **Implement core modules:**
   - `parser.py` - Main `parse_{format}()` function
   - `validation.py` - File validation
   - `metadata.py` - Metadata extraction
   - `__init__.py` - Exports
3. **Create wrapper class** (optional, for consistency):
   - `{Format}Parser(BaseParser)` in `__init__.py`
4. **Register in registry:**
   - Add to `base/registry.py:register_builtin_parsers()`
5. **Add lazy import helper:**
   - Add `_parse_{format}()` to `parser.py`
6. **Update format detection:**
   - Add extension to `parser.py` routing
   - Update `get_supported_formats()`
7. **Write tests:**
   - Unit tests for each module
   - Integration tests with sample files
8. **Update documentation:**
   - Add to README supported formats
   - Update this TODOS.md

### Code Patterns to Follow

- Use functional style for new parsers (see `FUNCTIONAL_PATTERNS.md`)
- Follow existing module structure (validation, metadata, content, etc.)
- Accumulate warnings instead of failing on non-critical errors
- Use the `Document` model for all output
- Add comprehensive docstrings (Google style)
- Type hints everywhere

---

*Last updated: 2025-12-02*
