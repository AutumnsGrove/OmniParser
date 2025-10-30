# Test Fixtures - Public Domain Documents

This directory contains test fixtures for document parsing in multiple formats (PDF, TXT, MD, DOCX). All files are sourced from public domain materials to ensure there are no copyright concerns when including them in this repository.

## 📋 Table of Contents

- [Copyright Status](#copyright-status)
- [Sources](#sources)
- [File Formats](#file-formats)
- [Usage](#usage)
- [Downloading Fixtures](#downloading-fixtures)
- [Attribution](#attribution)

## ⚖️ Copyright Status

**All test fixtures in this directory are in the public domain or licensed for testing.**

### Public Domain Works

The majority of files are sourced from **Project Gutenberg**, which provides books whose copyrights have expired in the United States. These works are:

- Published before 1928 (and thus in the US public domain)
- Free to use, modify, and distribute without restrictions
- Not subject to copyright protection in the United States

### Licensed Test Files

Some markdown test files are sourced from GitHub repositories specifically created for testing purposes and are licensed under permissive licenses (MIT, CC-BY-SA, etc.).

## 📚 Sources

### Primary Source: Project Gutenberg

**Website**: https://www.gutenberg.org/

**About**: Project Gutenberg is a volunteer effort to digitize and archive cultural works. It offers over 70,000 free eBooks, focusing on older works in the public domain.

**Copyright Policy**: 
> "Most books in the Project Gutenberg collection are distributed as public domain under United States copyright law."
> 
> Source: [Project Gutenberg - Wikipedia](https://en.wikipedia.org/wiki/Project_Gutenberg)

**Books Included** (examples):
- *Pride and Prejudice* by Jane Austen (1813)
- *Frankenstein* by Mary Shelley (1818)
- *Alice's Adventures in Wonderland* by Lewis Carroll (1865)
- *Moby Dick* by Herman Melville (1851)
- *A Tale of Two Cities* by Charles Dickens (1859)
- *The Adventures of Sherlock Holmes* by Arthur Conan Doyle (1892)
- *Middlemarch* by George Eliot (1871)
- *The Prince* by Niccolò Machiavelli (1532)
- *War and Peace* by Leo Tolstoy (1869)
- *The Yellow Wallpaper* by Charlotte Perkins Gilman (1892)

### Secondary Sources: GitHub Test Repositories

**Markdown Test Files**:
- [mxstbr/markdown-test-file](https://github.com/mxstbr/markdown-test-file) - Comprehensive markdown syntax tests
- [fullpipe/markdown-test-page](https://github.com/fullpipe/markdown-test-page) - Markdown elements demonstration

**Purpose**: These repositories provide test files specifically designed for testing markdown parsers and renderers.

### Derived Works

**DOCX and additional MD files**: Created by converting Project Gutenberg TXT files to other formats. Since the source material is public domain, these conversions are also public domain.

### Additional Sources
**PDF Test Files**: Pulled from available papers/technical reports listed on the Nasa Archive ntrs.nasa.gov/
**Image Test Files**: Pulled from pixnio.com
**Starting .docx exxample files**: https://sample-files.com/documents/docx/


## 📁 File Formats

This repository includes test fixtures in the following formats:

### PDF (Portable Document Format)
- **Count**: ~8-10 files
- **Source**: Project Gutenberg PDF downloads
- **Use Case**: Testing PDF parsing, text extraction, metadata reading

### TXT (Plain Text)
- **Count**: ~10 files
- **Source**: Project Gutenberg plain text downloads
- **Encoding**: UTF-8
- **Use Case**: Testing basic text parsing, encoding detection

### MD (Markdown)
- **Count**: ~7-10 files
- **Sources**: 
  - GitHub test repositories (syntax examples)
  - Converted from Project Gutenberg TXT files
- **Use Case**: Testing markdown parsing, rendering, frontmatter extraction

### DOCX (Microsoft Word Document)
- **Count**: ~7 files
- **Source**: Created from Project Gutenberg TXT files with basic formatting
- **Use Case**: Testing DOCX parsing, style extraction, document structure

## 🎯 Usage

### Intended Use Cases

These test fixtures are suitable for:

✅ **Software Testing**: Unit tests, integration tests, end-to-end tests  
✅ **Parser Development**: Building and testing document parsers  
✅ **Library Development**: Creating document processing libraries  
✅ **CI/CD Pipelines**: Automated testing in continuous integration  
✅ **Educational Purposes**: Learning document formats and parsing  
✅ **Performance Testing**: Benchmarking document processing speed

### Usage Rights

You may:
- ✅ Use these files in commercial or non-commercial projects
- ✅ Modify, transform, or build upon these files
- ✅ Distribute these files or derivatives
- ✅ Include these files in open source or proprietary software
- ✅ Use for machine learning training data

You do NOT need to:
- ❌ Request permission
- ❌ Pay fees or royalties
- ❌ Provide attribution (though it's appreciated!)

### Important Notes

⚠️ **Jurisdiction**: These files are public domain in the United States. Copyright laws vary by country, and some works may still be under copyright in other jurisdictions.

⚠️ **Verification**: While we've taken care to ensure all files are public domain, you should verify the copyright status for your specific use case if uncertain.

⚠️ **Updates**: Copyright laws and public domain status can change. The status documented here is accurate as of 2025.

## 🔽 Downloading Fixtures

### Automated Download

Use the provided script to download all fixtures:

```bash
# Install dependencies
pip install requests python-docx

# Run the download script
python download_test_fixtures.py
```

This will:
1. Create a `test_fixtures/` directory structure
2. Download PDFs and TXT files from Project Gutenberg
3. Download markdown test files from GitHub
4. Generate DOCX files from TXT sources
5. Create a detailed metadata file

### Manual Download

Alternatively, download files manually from:
- Project Gutenberg: https://www.gutenberg.org/
- GitHub test repositories (see sources above)

## 🙏 Attribution

While not legally required for public domain works, we acknowledge:

### Project Gutenberg
The Project Gutenberg Literary Archive Foundation  
Website: https://www.gutenberg.org/  
Founded by Michael S. Hart in 1971

### Original Authors
We honor the original authors of these literary classics:
- Jane Austen, Mary Shelley, Lewis Carroll, Herman Melville, Charles Dickens, Arthur Conan Doyle, George Eliot, Niccolò Machiavelli, Leo Tolstoy, Charlotte Perkins Gilman, and many others.

### Test File Contributors
Contributors to open source markdown test file repositories on GitHub.

## 📖 References

- [U.S. Copyright Office - Government Works](https://www.copyright.gov/title17/92chap1.html#105)
- [Project Gutenberg](https://www.gutenberg.org/)
- [Copyright Status of Works by the Federal Government (Wikipedia)](https://en.wikipedia.org/wiki/Copyright_status_of_works_by_the_federal_government_of_the_United_States)
- [Public Domain Day](https://publicdomainday.org/)

## 🆘 Questions?

### How do I know these are really public domain?

All Project Gutenberg books included here were published before 1928, which means their copyrights have expired under US law. Additionally, Project Gutenberg only distributes works that are public domain in the US.

### Can I use these commercially?

Yes! Public domain means no restrictions on use, including commercial use.

### Do I need to include this README in my project?

No, but it's good practice to document your test data sources. You can copy relevant sections or create your own documentation.

### What if I need more test files?

Visit Project Gutenberg directly to download more public domain books, or create your own test fixtures using their materials as a base.

### Can I contribute additional test fixtures?

If you're contributing to this repository, please ensure any new test fixtures are also public domain or properly licensed. Document the source clearly in this README.

## 📜 License

The test fixtures themselves are **public domain** or licensed for testing purposes.

Any scripts or documentation in this repository (such as the download script and this README) are provided under [MIT License](../LICENSE) (or your preferred license).

---

**Last Updated**: 2025  
**Fixture Count**: ~35-40 files across 4 formats  
**Repository**: [Your Repository URL]

