# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Git Commit Standards

**CRITICAL:** All commits in this repository MUST follow the conventional commit style documented in `GIT_COMMIT_STYLE_GUIDE.md`.

### Required Reading
Before making ANY commits, read:
- **`GIT_COMMIT_STYLE_GUIDE.md`** - Complete guide to commit message format

### Commit Format
```
<type>: <description>

[optional body]

[optional footer]
```

### Valid Commit Types
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring (no feature changes)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config)
- `perf`: Performance improvements
- `build`: Build system changes
- `ci`: CI/CD configuration

### Commit Guidelines
1. **Keep subject under 50 characters**
2. **Use imperative mood** ("Add feature" not "Added feature")
3. **Don't end with period**
4. **Be specific and descriptive**
5. **Reference issues when relevant**

### Examples

✅ **Good:**
```bash
feat: Add EPUB parser with TOC-based chapter detection
fix: Resolve encoding issue in text extraction
docs: Add API documentation for Document class
test: Add unit tests for BaseParser interface
chore: Add python-magic dependency
refactor: Extract validation logic to separate module
```

❌ **Bad:**
```bash
Update code
Fixed bug
Added stuff
WIP
Changes
```

---

## Subagent Commit Requirements

**MANDATORY:** All subagents MUST commit their changes before completing their task.

### Subagent Commit Pattern
1. **Complete the assigned task**
2. **Stage changes:** `git add .`
3. **Create commit** following conventional commit style
4. **Include completion summary in commit body**

### Subagent Commit Template
```bash
git commit -m "<type>: <subagent-task-summary>

Completed by: <subagent-name>
Phase: <phase-number>
Task: <task-description>

Changes:
- <change-1>
- <change-2>
- <change-3>

Deliverables:
- <file-1>
- <file-2>
"
```

### Example Subagent Commits
```bash
# Research Phase
docs: Complete ebooklib_processor.py analysis

Completed by: house-research Agent 1
Phase: Phase 1 - Research
Task: Analyze ebooklib_processor.py (963 lines)

Changes:
- Documented all classes and methods
- Extracted EPUB processing workflow
- Identified dependencies
- Documented integration points

Deliverables:
- research/ebooklib_analysis.md

---

# Development Phase
feat: Implement core data models

Completed by: general-purpose Agent 2.1
Phase: Phase 2.1 - Foundation
Task: Implement Document, Chapter, Metadata models

Changes:
- Created src/omniparser/models.py
- Implemented 5 dataclasses with type hints
- Added serialization methods (to_dict, from_dict, save_json, load_json)
- Comprehensive docstrings on all classes

Deliverables:
- src/omniparser/models.py
- tests/unit/test_models.py

---

# Testing Phase
test: Add integration tests for EPUB parser

Completed by: general-purpose Agent 3.1
Phase: Phase 3 - Testing
Task: Create integration tests for EPUBParser

Changes:
- Created tests/integration/test_epub_parser.py
- Added test fixtures (simple.epub, complex.epub)
- Tested TOC-based chapter detection
- Verified metadata extraction

Deliverables:
- tests/integration/test_epub_parser.py
- tests/fixtures/epub/simple.epub
- tests/fixtures/epub/complex.epub
```

---

## Package Management

This project uses **UV** for Python package management.

### Always Use `uv run`
```bash
# Run Python scripts
uv run python -m omniparser.cli

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/

# Build package
uv build
```

**DO NOT use bare `python` or `pytest` commands** - they will fail because the environment is managed by UV.

---

## Code Standards

### Python Style
- **Formatter:** Black (line length 88)
- **Type checking:** mypy with strict mode
- **Docstrings:** Google style
- **Import order:** stdlib, third-party, local

### Code Quality Rules
1. **Use type hints everywhere**
   ```python
   def parse_document(file_path: Path) -> Document:
       """Parse document and return structured output."""
       ...
   ```

2. **Write comprehensive docstrings**
   ```python
   class EPUBParser(BaseParser):
       """
       Parser for EPUB files using EbookLib.

       Features:
       - TOC-based chapter detection
       - Image extraction
       - Metadata from OPF
       - HTML to Markdown conversion

       Example:
           >>> parser = EPUBParser()
           >>> doc = parser.parse(Path("book.epub"))
           >>> print(doc.metadata.title)
       """
   ```

3. **Keep functions focused**
   - Single responsibility principle
   - Max ~50 lines per function
   - Extract helpers when needed

4. **Handle errors gracefully**
   ```python
   try:
       document = parse_document(path)
   except UnsupportedFormatError as e:
       logger.error(f"Format not supported: {e}")
   except ParsingError as e:
       logger.error(f"Parsing failed: {e}")
   ```

---

## Testing Requirements

### Test Every Component
Each module must have corresponding tests:
```
src/omniparser/models.py → tests/unit/test_models.py
src/omniparser/parsers/epub_parser.py → tests/unit/test_epub_parser.py
```

### Test Coverage Target
- **Unit tests:** >90% coverage
- **Integration tests:** All parsers with real files
- **Edge cases:** Error handling, malformed inputs

### Running Tests
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=omniparser --cov-report=html

# Specific test file
uv run pytest tests/unit/test_models.py

# Specific test function
uv run pytest tests/unit/test_models.py::test_document_serialization
```

---

## Development Workflow

### Standard Development Process
1. **Read architecture plan** (ARCHITECTURE_PLAN.md)
2. **Implement component** following specs
3. **Write unit tests** for new code
4. **Format code** with Black
5. **Type check** with mypy
6. **Run tests** ensure all pass
7. **Commit changes** following conventional commit style
8. **Update documentation** if needed

### Before Committing
```bash
# Format code
uv run black src/ tests/

# Check types
uv run mypy src/

# Run tests
uv run pytest

# Review changes
git status
git diff

# Commit with proper message
git add .
git commit -m "feat: Add EPUB parser implementation"
```

---

## File Organization

### Source Layout
```
src/omniparser/
├── __init__.py          # Package exports
├── parser.py            # Main parse_document() function
├── models.py            # Data models
├── exceptions.py        # Custom exceptions
├── base/                # Abstract base classes
│   └── base_parser.py
├── parsers/             # Format-specific parsers
│   ├── epub_parser.py
│   ├── pdf_parser.py
│   └── ...
├── processors/          # Post-processing
│   ├── chapter_detector.py
│   ├── text_cleaner.py
│   └── ...
└── utils/               # Utilities
    ├── format_detector.py
    ├── encoding.py
    └── validators.py
```

### Documentation Layout
```
docs/
├── README.md            # Main documentation
├── api.md              # API reference
├── parsers.md          # Parser implementation guide
└── contributing.md     # Contribution guidelines
```

---

## Code References

When referencing specific code locations, use the format:
```
file_path:line_number
```

**Example:**
```
The EPUB parser implements TOC extraction in:
src/omniparser/parsers/epub_parser.py:245
```

This allows easy navigation in IDEs.

---

## Common Commands

### Project Setup
```bash
# Initialize project
cd /Users/autumn/Documents/Projects/OmniParser
uv init

# Install dependencies
uv sync

# Install dev dependencies
uv sync --dev
```

### Development
```bash
# Run tests with coverage
uv run pytest --cov=omniparser --cov-report=html

# Format all code
uv run black .

# Type check
uv run mypy src/

# Build package
uv build

# Install locally for testing
uv add --editable .
```

### Git Operations
```bash
# Check status
git status

# View changes
git diff

# Stage changes
git add .

# Commit (follow GIT_COMMIT_STYLE_GUIDE.md)
git commit -m "feat: Add new parser"

# View history
git log --oneline

# Check commit message format
git log -1 --pretty=%B
```

---

## Important Notes

### 1. Architecture First
Always reference ARCHITECTURE_PLAN.md before implementing features. Don't deviate without good reason.

### 2. Test-Driven Development
Write tests alongside code. Don't defer testing to the end.

### 3. Documentation as Code
Keep documentation in sync with code. Update docs when changing APIs.

### 4. Semantic Versioning
- `feat` commits → minor version bump (1.0.0 → 1.1.0)
- `fix` commits → patch version bump (1.0.0 → 1.0.1)
- Breaking changes → major version bump (1.0.0 → 2.0.0)

### 5. Commit Hygiene
- **One logical change per commit**
- **Commit working code** (tests should pass)
- **Write descriptive messages**
- **Reference issues when relevant**

---

## Troubleshooting

### UV Issues
```bash
# Reinstall dependencies
rm -rf .venv uv.lock
uv sync

# Update UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Test Failures
```bash
# Run with verbose output
uv run pytest -vv

# Run specific test
uv run pytest tests/unit/test_models.py -k test_document_creation

# Show print statements
uv run pytest -s
```

### Import Errors
```bash
# Ensure package is installed
uv sync

# Check PYTHONPATH
echo $PYTHONPATH

# Install in editable mode
uv add --editable .
```

---

## Quick Reference

**Essential Commands:**
```bash
uv run pytest             # Run tests
black .                   # Format code
uv run mypy src/          # Type check
uv build                  # Build package
git commit -m "type: msg" # Commit (follow style guide!)
```

**Before Every Commit:**
1. Format: `uv run black .`
2. Test: `uv run pytest`
3. Check commit message format (see GIT_COMMIT_STYLE_GUIDE.md)

---

**Remember: Quality over speed. Write code that future you will thank you for!**
