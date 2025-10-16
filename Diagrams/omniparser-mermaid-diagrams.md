# OmniParser Architecture Diagrams (Mermaid)
**Visual reference for OmniParser architecture**

---

## System Context Diagram

```mermaid
graph TB
    subgraph External["External Systems"]
        epub2tts["epub2tts<br/>(Audio)"]
        cli["CLI<br/>Tools"]
        web["Web<br/>Apps"]
        other["Other<br/>Apps"]
    end
    
    subgraph OmniParser["OmniParser - Universal Document Parser"]
        main["parse_document()<br/>Input: File path (EPUB/PDF/DOCX/HTML/URL/MD/TXT)<br/>Output: Document object (markdown + metadata + structure)"]
    end
    
    subgraph Libraries["External Libraries"]
        libs["ebooklib | PyMuPDF | python-docx<br/>trafilatura | beautifulsoup4<br/>tesseract | chardet | python-magic<br/>ftfy | readability-lxml"]
    end
    
    epub2tts --> main
    cli --> main
    web --> main
    other --> main
    main --> libs
    
    style OmniParser fill:#e1f5ff
    style External fill:#fff4e1
    style Libraries fill:#f0f0f0
```

---

## Layered Architecture

```mermaid
graph TB
    subgraph Application["APPLICATION LAYER"]
        app["parse_document(file_path, options...) → Document<br/>• Entry point for all parsing operations<br/>• Format detection, validation, error handling"]
    end
    
    subgraph Parser["PARSER LAYER"]
        epub["EPUB<br/>Parser"]
        pdf["PDF<br/>Parser"]
        docx["DOCX<br/>Parser"]
        html["HTML<br/>Parser"]
        md["Markdown<br/>Parser"]
        txt["Text<br/>Parser"]
        base["BaseParser<br/>(Abstract)"]
        
        epub -.inherits.-> base
        pdf -.inherits.-> base
        docx -.inherits.-> base
        html -.inherits.-> base
        md -.inherits.-> base
        txt -.inherits.-> base
    end
    
    subgraph Processor["PROCESSOR LAYER"]
        chapter["Chapter<br/>Detector"]
        metadata["Metadata<br/>Extractor"]
        cleaner["Text<br/>Cleaner"]
        converter["Markdown Converter<br/>(HTML → MD)"]
    end
    
    subgraph Base["BASE LAYER"]
        models["Data Models<br/>Document | Chapter | Metadata | ImageReference"]
        exceptions["Exceptions"]
        utilities["Utilities"]
        format["Format Detection"]
    end
    
    app --> epub & pdf & docx & html & md & txt
    epub & pdf & docx & html & md & txt --> chapter & metadata & cleaner & converter
    chapter & metadata & cleaner & converter --> models & exceptions & utilities & format
    
    style Application fill:#e8f5e9
    style Parser fill:#fff3e0
    style Processor fill:#e1f5fe
    style Base fill:#f3e5f5
```

---

## Parser Flow Diagram

```mermaid
flowchart TD
    Start([User calls<br/>parse_document<br/>file.epub])
    
    Validate{Validate File<br/>• Exists?<br/>• Readable?<br/>• Size OK?}
    
    Detect[Detect Format<br/>• Magic bytes<br/>• Extension<br/>Result: 'epub']
    
    Select[Select Parser<br/>EPUBParser]
    
    subgraph Parse["EPUBParser.parse()"]
        Load[1. Load with ebooklib]
        Meta[2. Extract metadata<br/>title, author, etc]
        TOC[3. Parse TOC structure<br/>chapter boundaries]
        Content[4. Extract chapter content<br/>HTML → text]
        Images[5. Extract images<br/>if enabled]
        Clean[6. Clean text<br/>if enabled]
        Build[7. Build Document object]
        
        Load --> Meta --> TOC --> Content --> Images --> Clean --> Build
    end
    
    Return([Return Document<br/>• content markdown<br/>• chapters List<br/>• images List<br/>• metadata Metadata<br/>• processing_info])
    
    Start --> Validate
    Validate -->|Valid| Detect
    Validate -->|Invalid| Error1([FileReadError])
    Detect --> Select
    Select --> Parse
    Build --> Return
    
    style Start fill:#e8f5e9
    style Return fill:#e8f5e9
    style Error1 fill:#ffebee
    style Parse fill:#e3f2fd
```

---

## Document Object Structure

```mermaid
graph TD
    Doc[Document]
    
    Doc --> id["document_id: uuid-1234-5678"]
    Doc --> content["content: Full text as markdown..."]
    Doc --> wc["word_count: 50000"]
    Doc --> time["estimated_reading_time: 250 min"]
    
    Doc --> Chapters[chapters: List]
    Chapters --> Ch0[Chapter 0]
    Chapters --> Ch1[Chapter 1]
    Chapters --> ChN[Chapter N...]
    
    Ch0 --> ch0id["chapter_id: 0"]
    Ch0 --> ch0title["title: Prologue"]
    Ch0 --> ch0content["content: Chapter text..."]
    Ch0 --> ch0start["start_position: 0"]
    Ch0 --> ch0end["end_position: 500"]
    Ch0 --> ch0wc["word_count: 100"]
    Ch0 --> ch0level["level: 1"]
    Ch0 --> ch0meta["metadata: {}"]
    
    Doc --> Images[images: List]
    Images --> Img0[ImageReference 0]
    Images --> ImgN[ImageReference N...]
    
    Img0 --> imgid["image_id: img_001"]
    Img0 --> imgpos["position: 1500"]
    Img0 --> imgpath["file_path: /path/to/image.jpg"]
    Img0 --> imgalt["alt_text: Description"]
    Img0 --> imgsize["size: 800, 600"]
    Img0 --> imgfmt["format: jpg"]
    
    Doc --> Metadata[metadata: Metadata]
    Metadata --> mtitle["title: Book Title"]
    Metadata --> mauthor["author: Author Name"]
    Metadata --> mauthors["authors: [Author 1, Author 2]"]
    Metadata --> mpub["publisher: Publisher Inc."]
    Metadata --> mdate["publication_date: 2024-01-01"]
    Metadata --> mlang["language: en"]
    Metadata --> misbn["isbn: 978-0-123456-78-9"]
    Metadata --> mdesc["description: Book description..."]
    Metadata --> mtags["tags: [fiction, fantasy]"]
    Metadata --> mfmt["original_format: epub"]
    Metadata --> msize["file_size: 2048000"]
    Metadata --> mcustom["custom_fields: {}"]
    
    Doc --> Processing[processing_info: ProcessingInfo]
    Processing --> pparser["parser_used: epub"]
    Processing --> pver["parser_version: 1.0.0"]
    Processing --> ptime["processing_time: 2.5s"]
    Processing --> pts["timestamp: 2025-10-16 12:00:00"]
    Processing --> pwarn["warnings: []"]
    Processing --> popts["options_used: {extract_images: true}"]
    
    style Doc fill:#e1f5fe
    style Chapters fill:#fff3e0
    style Images fill:#f3e5f5
    style Metadata fill:#e8f5e9
    style Processing fill:#fce4ec
```

---

## EPUB Parser Internal Flow

```mermaid
flowchart TD
    Start([EPUBParser.parse<br/>book.epub])
    
    Load[Load EPUB<br/>ebooklib.read_epub]
    
    subgraph ExtractMeta["Extract Metadata"]
        Meta1[get_metadata DC, title]
        Meta2[get_metadata DC, creator]
        Meta3[get_metadata DC, publisher]
        MetaRet[Return Metadata object]
        Meta1 --> Meta2 --> Meta3 --> MetaRet
    end
    
    subgraph ExtractTOC["Extract TOC Structure"]
        TOC1[book.toc Table of Contents]
        TOC2[Recursive processing]
        TOC3[epub.Link → TocEntry]
        TOC4[epub.Section → TocEntry with children]
        TOC5[Build hierarchy]
        TOCRet[Return List TocEntry]
        TOC1 --> TOC2 --> TOC3 --> TOC4 --> TOC5 --> TOCRet
    end
    
    subgraph ExtractChap["Extract Chapters"]
        ChapTOC["For each TOC entry:<br/>• Find item by href<br/>• Extract HTML content<br/>• Parse with BeautifulSoup<br/>• Extract text<br/>• Create Chapter object"]
        ChapFallback["Fallback no TOC:<br/>• Iterate spine items<br/>• Each spine item = chapter"]
        ChapRet[Return List Chapter]
        ChapTOC --> ChapRet
        ChapFallback --> ChapRet
    end
    
    subgraph ExtractImg["Extract Images (optional)"]
        Img1["For each ITEM_IMAGE:<br/>• Extract binary data<br/>• Save to temp location<br/>• Create ImageReference"]
        ImgRet[Return List ImageReference]
        Img1 --> ImgRet
    end
    
    BuildContent[Build Full Content<br/>Join chapter.content<br/>Markdown format]
    
    CleanText[Clean Text optional<br/>• Fix encoding ftfy<br/>• Normalize whitespace<br/>• Normalize quotes]
    
    ReturnDoc([Return Document<br/>content, chapters,<br/>images, metadata, ...])
    
    Start --> Load
    Load --> ExtractMeta
    ExtractMeta --> ExtractTOC
    ExtractTOC --> ExtractChap
    ExtractChap --> ExtractImg
    ExtractImg --> BuildContent
    BuildContent --> CleanText
    CleanText --> ReturnDoc
    
    style Start fill:#e8f5e9
    style ReturnDoc fill:#e8f5e9
    style ExtractMeta fill:#e3f2fd
    style ExtractTOC fill:#fff3e0
    style ExtractChap fill:#f3e5f5
    style ExtractImg fill:#fce4ec
```

---

## Parser Inheritance Hierarchy

```mermaid
classDiagram
    class BaseParser {
        <<abstract>>
        +parse()* Document
        +supports_format()* bool
        +extract_images() List~ImageReference~
        +clean_text() str
    }
    
    class EPUBParser {
        +parse() Document
        +supports_format() bool
        -Uses: ebooklib, BeautifulSoup
        -Supports: .epub
        -Features: TOC-based chapters, images, metadata
    }
    
    class PDFParser {
        +parse() Document
        +supports_format() bool
        -Uses: PyMuPDF, Tesseract
        -Supports: .pdf
        -Features: OCR, table extraction, font-based headings
    }
    
    class DOCXParser {
        +parse() Document
        +supports_format() bool
        -Uses: python-docx
        -Supports: .docx, .doc
        -Features: Style-based headings, images, tables
    }
    
    class HTMLParser {
        +parse() Document
        +supports_format() bool
        -Uses: Trafilatura, Readability, requests
        -Supports: .html, .htm, URLs
        -Features: Main content extraction, URL fetching
    }
    
    class MarkdownParser {
        +parse() Document
        +supports_format() bool
        -Uses: PyYAML
        -Supports: .md, .markdown
        -Features: Frontmatter, heading detection
    }
    
    class TextParser {
        +parse() Document
        +supports_format() bool
        -Uses: chardet
        -Supports: .txt
        -Features: Encoding detection, normalization
    }
    
    BaseParser <|-- EPUBParser
    BaseParser <|-- PDFParser
    BaseParser <|-- DOCXParser
    BaseParser <|-- HTMLParser
    BaseParser <|-- MarkdownParser
    BaseParser <|-- TextParser
```

---

## Data Flow: epub2tts Integration

```mermaid
sequenceDiagram
    participant User
    participant epub2tts as epub2tts Application
    participant processor as epub2tts.core.epub_processor
    participant omni as OmniParser (External Package)
    participant tts as TTS Pipeline
    participant output as Audiobook Output
    
    User->>epub2tts: Upload book.epub
    epub2tts->>processor: process_epub(epub_path)
    
    rect rgb(230, 245, 255)
        Note over processor: Parse with OmniParser
        processor->>omni: parse_document(epub_path)
        
        Note over omni: • Format detection<br/>• EPUBParser selected<br/>• Parse EPUB structure<br/>• Extract chapters, metadata, images
        
        omni-->>processor: Return Document object
    end
    
    rect rgb(255, 243, 224)
        Note over processor: Convert to epub2tts format
        processor->>processor: ProcessingResult(<br/>text_content=doc.content,<br/>chapters=_convert_chapters(),<br/>metadata=_convert_metadata()<br/>)
        
        Note over processor: Apply TTS-specific processing
        processor->>processor: tts_cleaner.add_pauses(<br/>result.text_content<br/>)
    end
    
    processor-->>epub2tts: Return ProcessingResult
    
    epub2tts->>tts: Process with TTS Pipeline
    
    rect rgb(232, 245, 233)
        Note over tts: • Text chunking (respects chapters)<br/>• Voice synthesis (Kokoro TTS)<br/>• Audio stitching<br/>• M4B/M4A output
    end
    
    tts-->>output: Generate audiobook
    output-->>User: Audiobook ready
```

---

## Error Handling Flow

```mermaid
flowchart TD
    Start([parse_document path])
    
    Validate{Validate Input<br/>File exists?<br/>File readable?<br/>File size OK?}
    
    DetectFormat[Detect Format<br/>• Magic bytes check<br/>• Extension fallback]
    
    FormatCheck{Format<br/>Supported?}
    
    CreateParser[Create Parser<br/>e.g., EPUBParser]
    
    ParseAttempt{Parser.parse<br/>Success?}
    
    ReturnDoc([Return Document])
    
    ErrFile([FileReadError])
    ErrValidation([ValidationError])
    ErrUnsupported([UnsupportedFormatError<br/>Format not supported: ...])
    ErrParsing([ParsingError<br/>with original_error preserved])
    ErrNetwork([NetworkError<br/>if URL])
    ErrIO([FileReadError<br/>if IO issue])
    
    Start --> Validate
    
    Validate -->|File exists| ValidateReadable{Readable?}
    Validate -->|Not exists| ErrFile
    
    ValidateReadable -->|Yes| ValidateSize{Size OK?}
    ValidateReadable -->|No| ErrFile
    
    ValidateSize -->|Yes| DetectFormat
    ValidateSize -->|No| ErrValidation
    
    DetectFormat --> FormatCheck
    
    FormatCheck -->|Supported| CreateParser
    FormatCheck -->|Unsupported| ErrUnsupported
    
    CreateParser --> ParseAttempt
    
    ParseAttempt -->|Success| ReturnDoc
    ParseAttempt -->|Parse Error| ErrParsing
    ParseAttempt -->|Network Error| ErrNetwork
    ParseAttempt -->|IO Error| ErrIO
    
    style Start fill:#e8f5e9
    style ReturnDoc fill:#e8f5e9
    style ErrFile fill:#ffebee
    style ErrValidation fill:#ffebee
    style ErrUnsupported fill:#ffebee
    style ErrParsing fill:#ffebee
    style ErrNetwork fill:#ffebee
    style ErrIO fill:#ffebee
```

---

## Testing Structure

```mermaid
graph TD
    Tests[tests/]
    
    Tests --> Unit[unit/<br/>Unit tests - fast, isolated]
    Tests --> Integration[integration/<br/>Integration tests - slower, end-to-end]
    Tests --> Fixtures[fixtures/<br/>Test data]
    
    Unit --> UnitModels[test_models.py<br/>Data model tests]
    Unit --> UnitEPUB[test_epub_parser.py<br/>EPUB parser tests]
    Unit --> UnitPDF[test_pdf_parser.py<br/>PDF parser tests]
    Unit --> UnitDOCX[test_docx_parser.py<br/>DOCX parser tests]
    Unit --> UnitHTML[test_html_parser.py<br/>HTML parser tests]
    Unit --> UnitMD[test_markdown_parser.py<br/>Markdown parser tests]
    Unit --> UnitText[test_text_parser.py<br/>Text parser tests]
    Unit --> UnitFormat[test_format_detector.py<br/>Format detection tests]
    Unit --> UnitCleaner[test_text_cleaner.py<br/>Text cleaning tests]
    Unit --> UnitChapter[test_chapter_detector.py<br/>Chapter detection tests]
    Unit --> UnitExcept[test_exceptions.py<br/>Exception tests]
    
    UnitModels --> M1[test_document_creation]
    UnitModels --> M2[test_document_serialization]
    UnitModels --> M3[test_chapter_helpers]
    UnitModels --> M4[test_metadata_fields]
    
    UnitEPUB --> E1[test_parse_valid_epub]
    UnitEPUB --> E2[test_parse_no_toc]
    UnitEPUB --> E3[test_metadata_extraction]
    UnitEPUB --> E4[test_chapter_detection]
    UnitEPUB --> E5[test_image_extraction]
    
    Integration --> IPipeline[test_full_pipeline.py<br/>parse_document with all formats]
    Integration --> IFormat[test_format_detection.py<br/>Format detection integration]
    Integration --> IError[test_error_handling.py<br/>Error scenarios]
    Integration --> ISerial[test_serialization.py<br/>JSON save/load tests]
    
    Fixtures --> F1[sample.epub - Valid EPUB]
    Fixtures --> F2[no_toc.epub - EPUB without TOC]
    Fixtures --> F3[images.epub - EPUB with images]
    Fixtures --> F4[sample.pdf - Text-based PDF]
    Fixtures --> F5[scanned.pdf - OCR PDF]
    Fixtures --> F6[sample.docx - DOCX with formatting]
    Fixtures --> F7[sample.html - HTML article]
    Fixtures --> F8[sample.md - Markdown with frontmatter]
    Fixtures --> F9[sample.txt - Plain text]
    
    style Tests fill:#e1f5fe
    style Unit fill:#fff3e0
    style Integration fill:#f3e5f5
    style Fixtures fill:#e8f5e9
```

---

## Package Structure

```mermaid
graph TD
    Root[omniparser/]
    
    Root --> Config[pyproject.toml<br/>UV package configuration]
    Root --> README[README.md<br/>User-facing documentation]
    Root --> LICENSE[LICENSE<br/>MIT License]
    Root --> CHANGELOG[CHANGELOG.md<br/>Version history]
    Root --> GitIgnore[.gitignore<br/>Git ignore rules]
    
    Root --> Src[src/]
    Src --> Package[omniparser/]
    
    Package --> Init[__init__.py<br/>Exports: parse_document,<br/>Document, exceptions]
    Package --> Parser[parser.py<br/>Main parse_document function<br/>Entry point, format detection]
    Package --> Models[models.py<br/>Document, Chapter, Metadata,<br/>ImageReference, ProcessingInfo]
    Package --> Exceptions[exceptions.py<br/>OmniparserError, ParsingError, etc.]
    
    Package --> BaseDir[base/]
    BaseDir --> BaseInit[__init__.py]
    BaseDir --> BaseParser[base_parser.py<br/>BaseParser ABC]
    
    Package --> ParsersDir[parsers/]
    ParsersDir --> ParsersInit[__init__.py]
    ParsersDir --> EPUB[epub_parser.py<br/>EPUBParser ported from epub2tts]
    ParsersDir --> PDF[pdf_parser.py<br/>PDFParser PyMuPDF + OCR]
    ParsersDir --> DOCX[docx_parser.py<br/>DOCXParser python-docx]
    ParsersDir --> HTML[html_parser.py<br/>HTMLParser Trafilatura]
    ParsersDir --> MD[markdown_parser.py<br/>MarkdownParser]
    ParsersDir --> Text[text_parser.py<br/>TextParser chardet]
    
    Package --> ProcessorsDir[processors/]
    ProcessorsDir --> ProcessorsInit[__init__.py]
    ProcessorsDir --> ChapterDet[chapter_detector.py<br/>Heading-based detection]
    ProcessorsDir --> MetaExt[metadata_extractor.py<br/>Metadata extraction]
    ProcessorsDir --> MDConv[markdown_converter.py<br/>HTML → Markdown]
    ProcessorsDir --> TextClean[text_cleaner.py<br/>Text normalization]
    
    Package --> UtilsDir[utils/]
    UtilsDir --> UtilsInit[__init__.py]
    UtilsDir --> FormatDet[format_detector.py<br/>Magic bytes detection]
    UtilsDir --> Encoding[encoding.py<br/>Encoding utilities]
    UtilsDir --> Validators[validators.py<br/>Input validation]
    
    Root --> TestsDir[tests/]
    TestsDir --> TestsInit[__init__.py]
    TestsDir --> Conftest[conftest.py<br/>Pytest configuration]
    TestsDir --> UnitTests[unit/<br/>Unit tests]
    TestsDir --> IntTests[integration/<br/>Integration tests]
    TestsDir --> TestFixtures[fixtures/<br/>Test data files]
    
    Root --> DocsDir[docs/]
    DocsDir --> DocsIndex[index.md<br/>Main docs]
    DocsDir --> DocsAPI[api.md<br/>API reference]
    DocsDir --> DocsParsers[parsers.md<br/>Parser implementation guide]
    DocsDir --> DocsContrib[contributing.md<br/>Contribution guide]
    
    Root --> ExamplesDir[examples/]
    ExamplesDir --> ExBasic[basic_usage.py<br/>Simple example]
    ExamplesDir --> ExBatch[batch_processing.py<br/>Process directory]
    ExamplesDir --> ExCustom[custom_parser.py<br/>Custom parser implementation]
    
    style Root fill:#e1f5fe
    style Src fill:#fff3e0
    style Package fill:#e8f5e9
    style BaseDir fill:#f3e5f5
    style ParsersDir fill:#fce4ec
    style ProcessorsDir fill:#fff9c4
    style UtilsDir fill:#e0f2f1
    style TestsDir fill:#fce4ec
    style DocsDir fill:#f3e5f5
    style ExamplesDir fill:#fff3e0
```

---

## Version 1.0 Scope

```mermaid
mindmap
  root((OmniParser v1.0))
    Included ✅
      Parsers
        EPUB parser
          Ported from epub2tts
        PDF parser
          PyMuPDF + Tesseract OCR
        DOCX parser
          python-docx
        HTML/URL parser
          Trafilatura + Readability
        Markdown parser
          frontmatter + headings
        Text parser
          chardet + encoding
      Features
        Chapter detection
          heading-based
        Metadata extraction
          format-agnostic
        Image extraction
          all formats
        Text cleaning
          basic, non-TTS
      Quality
        Comprehensive tests
          >80% coverage
        Professional documentation
        PyPI package
    Future ❌
      Parsers
        RTF parser
        ODT parser
      Features
        AI-powered chapter detection
        JavaScript rendering for URLs
        Plugin system
        Streaming API
        Multi-document archives
```

---

## Deployment Pipeline

```mermaid
flowchart TD
    Dev[Development]
    
    Dev --> Write[Write code<br/>src/omniparser/]
    Dev --> WriteTests[Write tests<br/>tests/]
    Dev --> RunTests[Run tests locally<br/>uv run pytest]
    Dev --> Format[Format code<br/>uv run black .]
    Dev --> TypeCheck[Type check<br/>uv run mypy src/]
    
    TypeCheck --> AllPass{All pass?}
    AllPass -->|No| Fix[Fix issues] --> Write
    AllPass -->|Yes| PreRelease
    
    subgraph PreRelease["Pre-release Validation"]
        V1[✓ All tests pass]
        V2[✓ Coverage >80%]
        V3[✓ Documentation complete]
        V4[✓ Examples work]
        V5[✓ CHANGELOG updated]
    end
    
    PreRelease --> Build[Build Package<br/>uv build<br/>Creates .tar.gz<br/>Creates .whl]
    
    Build --> TestLocal[Test Local Install<br/>uv add ./dist/...<br/>Import works?]
    
    TestLocal --> LocalSuccess{Success?}
    LocalSuccess -->|No| Debug[Debug] --> Write
    LocalSuccess -->|Yes| Publish
    
    Publish[Publish to PyPI<br/>uv publish]
    
    Publish --> Tag[Tag Release<br/>git tag v1.0.0<br/>git push --tags]
    
    Tag --> Update[Update epub2tts<br/>Add omniparser dependency<br/>Test integration<br/>Deploy]
    
    style Dev fill:#e8f5e9
    style PreRelease fill:#e3f2fd
    style Publish fill:#fff3e0
    style Update fill:#f3e5f5
```

---

**Last Updated:** October 16, 2025  
**Status:** Mermaid Conversion Complete  
**Original Source:** ARCHITECTURE_DIAGRAMS.md
