# EPUB Test Fixtures

This directory contains EPUB files used for integration testing.

## ⚠️ Important: Copyright Notice

**EPUB files are NOT included in this repository due to copyright restrictions.**

The `.gitignore` file is configured to exclude all `.epub` files from version control to prevent accidental commits of copyrighted material.

## Adding Your Own Test EPUBs

To run the integration tests, you'll need to add your own EPUB files to this directory:

1. **Find or Create Test EPUBs**
   - Use your own EPUB files
   - Download public domain EPUBs from [Project Gutenberg](https://www.gutenberg.org/)
   - Download free/open EPUBs from [Standard Ebooks](https://standardebooks.org/)
   - Create sample EPUBs using tools like [Calibre](https://calibre-ebook.com/)

2. **Place EPUBs in This Directory**
   ```bash
   # Copy your EPUB files here
   cp ~/Downloads/book.epub tests/fixtures/epub/
   ```

3. **Update Test Files**
   - The integration tests in `tests/integration/test_epub_parsing.py` reference specific EPUB files
   - Update the file paths to match your EPUB files
   - Or name your test EPUB to match the expected filename

## Recommended Test EPUBs

For comprehensive testing, we recommend having EPUBs with these characteristics:

### Simple EPUB
- 1-5 chapters
- Basic structure
- Minimal metadata
- ~1-2 MB size

### Complex EPUB
- 20+ chapters
- Nested table of contents (3+ levels)
- Rich metadata (author, publisher, ISBN, etc.)
- Multiple images
- ~5-10 MB size

### Edge Cases
- **No TOC**: EPUB without table of contents (tests spine-based fallback)
- **Image-heavy**: EPUB with 50+ images
- **Unicode**: Non-English content (tests encoding handling)
- **Minimal metadata**: EPUB with incomplete metadata

## Public Domain Sources

Safe sources for test EPUBs (no copyright issues):

1. **Project Gutenberg** - https://www.gutenberg.org/
   - 70,000+ free eBooks
   - Public domain works
   - Available in EPUB format

2. **Standard Ebooks** - https://standardebooks.org/
   - High-quality, beautifully formatted public domain eBooks
   - Free and open source
   - EPUB 3 format

3. **Open Library** - https://openlibrary.org/
   - Many public domain books
   - Multiple formats including EPUB

## Example: Download from Project Gutenberg

```bash
# Example: Download "Alice's Adventures in Wonderland"
curl -o tests/fixtures/epub/alice.epub \
  https://www.gutenberg.org/ebooks/11.epub3.images

# Example: Download "Pride and Prejudice"
curl -o tests/fixtures/epub/pride-and-prejudice.epub \
  https://www.gutenberg.org/ebooks/1342.epub3.images
```

## Running Tests Without EPUBs

If you don't have test EPUBs:

```bash
# Run only unit tests (no integration tests)
pytest tests/unit/

# Skip integration tests
pytest -m "not integration"
```

## Current Test Files

The integration tests expect these files (you need to provide them):

- `A System for Writing.epub` - Used in `test_epub_parsing.py`
  - You can use any EPUB file and update the test expectations
  - Or rename your test file to match

## Contributing

When contributing test cases:
- **Never commit actual EPUB files** to the repository
- Include instructions for obtaining test files
- Provide sample metadata/structure expectations
- Test with public domain EPUBs when possible

---

*For more information, see the [OmniParser documentation](../../README.md)*
