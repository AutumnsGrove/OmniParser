# OmniParser Examples

This directory contains practical examples demonstrating OmniParser's capabilities.

## Available Examples

### 1. EPUB to Markdown Converter (`epub_to_markdown.py`)

**Blazingly fast EPUB to Markdown conversion** - Converts EPUB files to clean, well-formatted Markdown documents with proper headers, metadata, and navigation.

#### Features:
- ⚡ **Lightning Fast**: Parses 5MB EPUBs in ~0.25 seconds
- 📋 **YAML Frontmatter**: Includes title, author, publisher, publication date, word count, reading time
- 📑 **Table of Contents**: Auto-generated with working anchor links
- 📖 **Chapter Hierarchy**: Preserves heading levels from original EPUB
- 📊 **Statistics Footer**: Document stats (chapters, words, images, reading time)
- ✨ **Clean Formatting**: Properly formatted Markdown with separation between chapters

#### Usage:

```bash
# Basic usage (output to same name with .md extension)
uv run python examples/epub_to_markdown.py book.epub

# Specify output file
uv run python examples/epub_to_markdown.py book.epub output.md

# Example with test file
uv run python examples/epub_to_markdown.py "tests/fixtures/epub/A System for Writing.epub" output.md
```

#### Output Format:

```markdown
---
title: Book Title
author: Author Name
publisher: Publisher Name
published: 2024-01-15
language: en
word_count: 45,000
reading_time: 200 minutes
converted: 2025-01-20 14:14:12
source: book.epub
---

# Book Title

**Author:** Author Name

## Table of Contents

1. [Chapter 1](#chapter-1)
2. [Chapter 2](#chapter-2)
...

---

## Chapter 1

[Chapter content here...]

---

## Chapter 2

[Chapter content here...]

---

## Document Statistics

- **Total Chapters:** 12
- **Total Words:** 45,000
- **Estimated Reading Time:** 200 minutes
...
```

#### Performance:

Real-world test with "A System for Writing" EPUB:
- **File size:** 4.8 MB
- **Parse time:** 0.24 seconds 🚀
- **Output size:** 241 KB
- **Chapters:** 13
- **Words:** 40,633
- **Images:** 64 (extracted but not embedded in markdown)

#### Requirements:

```bash
# Install OmniParser
pip install omniparser

# Or with UV
uv pip install omniparser
```

#### Notes:

- Images are extracted during parsing but not embedded in the Markdown output
- The script preserves chapter hierarchy (h2 for main chapters, h3 for subsections, etc.)
- Table of contents links use GitHub-flavored Markdown anchors
- All text is cleaned and formatted for readability

---

## Coming Soon

- **epub_analyzer.py** - Analyze EPUB structure and metadata
- **batch_converter.py** - Convert multiple EPUBs at once
- **epub_validator.py** - Validate EPUB files and check for issues
- **compare_chapters.py** - Compare chapter detection across different options

---

## Usage Tips

### Running Examples

All examples can be run with UV (recommended) or standard Python:

```bash
# With UV (recommended - manages dependencies)
uv run python examples/epub_to_markdown.py book.epub

# With standard Python (requires OmniParser installed)
python examples/epub_to_markdown.py book.epub
```

### Custom Options

Most examples support custom parsing options. Check each script's help:

```bash
python examples/epub_to_markdown.py --help
```

---

## Contributing Examples

Have a cool use case for OmniParser? Contributions welcome!

Examples should:
- Be self-contained and runnable
- Include clear docstrings
- Handle errors gracefully
- Print progress information
- Be well-commented

---

*For more information, see the main [README](../README.md) and [API documentation](../docs/)*
