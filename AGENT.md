# AGENT.md

This file provides guidance to Claude Code when working with code in this repository.

> **Note**: This is the main orchestrator file. For detailed guides, see `AgentUsage/README.md`

---

<!-- BaseProject: Project Overview -->
## Project Overview

**Project:** OmniParser - Universal Document Parser
**Purpose:** Transform any document, web page, or structured data into clean, standardized markdown with comprehensive metadata extraction
**Status:** Phase 2.8 Complete - 6 Parsers + AI Features (v0.3.0)

**Tech Stack:**
- **Language:** Python 3.10+
- **Package Manager:** UV (modern Python package manager)
- **Build System:** Hatchling
- **Key Libraries:** ebooklib (EPUB), PyMuPDF (PDF), python-docx (DOCX), BeautifulSoup4 (HTML parsing), ftfy (text processing)
- **AI Integration:** anthropic SDK (Claude API), OpenRouter support, Vision API integration
- **Testing:** pytest, pytest-cov
- **Code Quality:** Black formatter, mypy type checking

**Architecture:**
- Modular parser architecture with `BaseParser` abstract class
- Format-specific parsers: 6 implemented (EPUB, HTML, PDF, DOCX, Markdown, Text)
- AI processors: 5 modules (summarizer, tagger, quality, image_analyzer, image_describer)
- Universal `Document` data model for consistent output across all formats
- Post-processing components (chapter detection, text cleaning, metadata extraction)

**Key Resources:**
- Full specification: `docs/OMNIPARSER_PROJECT_SPEC.md`
- Architecture plan: `docs/ARCHITECTURE_PLAN.md`
- Implementation reference: `docs/IMPLEMENTATION_REFERENCE.md`

<!-- /BaseProject: Project Overview -->

---

<!-- BaseProject: Essential Instructions -->
## Essential Instructions (Always Follow)

### Core Behavior
- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary for achieving your goal
- ALWAYS prefer editing existing files to creating new ones
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested

### Naming Conventions
- **Directories**: Use CamelCase (e.g., `VideoProcessor`, `AudioTools`, `DataAnalysis`)
- **Date-based paths**: Use skewer-case with YYYY-MM-DD (e.g., `logs-2025-01-15`, `backup-2025-12-31`)
- **No spaces or underscores** in directory names (except date-based paths)

### TODO Management
- **Always check `TODOS.md` first** when starting a task or session
- **Update immediately** when tasks are completed, added, or changed
- Keep the list current and manageable

<!-- /BaseProject: Essential Instructions -->

---

## Git Workflow

### Conventional Commits Format
```bash
<type>: <brief description>

<optional body>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`, `style`

**Examples:**
```bash
feat: Add EPUB parser with TOC-based chapter detection
fix: Resolve encoding issue in text extraction
docs: Update API documentation
test: Add unit tests for BaseParser interface
chore: Add python-magic dependency
```

**Guidelines:**
1. Keep subject under 50 characters
2. Use imperative mood ("Add feature" not "Added feature")
3. Don't end with period
4. Reference issues when relevant

**For complete details:** See `AgentUsage/git_guide.md`

---

## Package Management

This project uses **UV** for Python package management.

### Always Use `uv run`
```bash
uv run pytest              # Run tests
uv run black src/ tests/   # Format code
uv run mypy src/           # Type check
uv build                   # Build package
```

**DO NOT use bare `python` or `pytest` commands** - they will fail because the environment is managed by UV.

---

## Code Standards

### Python Style
- **Formatter:** Black (line length 88)
- **Type checking:** mypy with strict mode
- **Docstrings:** Google style
- **Import order:** stdlib, third-party, local

### Key Guidelines
- Use type hints everywhere
- Write comprehensive docstrings
- Keep functions focused (max ~50 lines)
- Handle errors gracefully

### Functional Patterns (For New Code)
- **`FUNCTIONAL_PATTERNS.md`** - Comprehensive guide with examples
- **`PATTERNS_QUICK_REF.md`** - Quick reference card

---

## Testing Requirements

### Test Coverage Target
- **Unit tests:** >90% coverage
- **Integration tests:** All parsers with real files
- **Edge cases:** Error handling, malformed inputs

### Running Tests
```bash
uv run pytest                                    # All tests
uv run pytest --cov=omniparser --cov-report=html # With coverage
uv run pytest tests/unit/test_models.py          # Specific file
```

---

## Development Workflow

### Before Committing
```bash
uv run black src/ tests/   # Format code
uv run mypy src/           # Check types
uv run pytest              # Run tests
git add .
git commit -m "type: description"
```

---

## File Organization

```
src/omniparser/
├── __init__.py          # Package exports
├── parser.py            # Main parse_document() function
├── models.py            # Data models
├── exceptions.py        # Custom exceptions
├── base/                # Abstract base classes
├── parsers/             # Format-specific parsers
│   ├── epub/
│   ├── pdf/
│   ├── docx/
│   ├── html/
│   ├── markdown/
│   └── text/
├── processors/          # Post-processing & AI
└── utils/               # Utilities
```

---

<!-- BaseProject: AgentUsage Guide Index -->
## When to Read Specific Guides

**The `AgentUsage/` directory contains comprehensive workflow guides. Read the full guide when you encounter these situations:**

### Secrets & API Keys
- **When managing API keys or secrets** → Read `AgentUsage/secrets_management.md`
- **Before implementing secrets loading** → Read `AgentUsage/secrets_management.md`
- **For advanced security patterns** → Read `AgentUsage/secrets_advanced.md`

### Package Management
- **When using UV package manager** → Read `AgentUsage/uv_usage.md`
- **Before creating/modifying pyproject.toml** → Read `AgentUsage/uv_usage.md`
- **When managing Python dependencies** → Read `AgentUsage/uv_usage.md`

### Version Control
- **For detailed git workflow** → Read `AgentUsage/git_guide.md`
- **For commit message best practices** → Read `AgentUsage/git_guide.md`

### Search & Research
- **When searching across 20+ files** → Read `AgentUsage/house_agents.md`
- **When finding patterns in codebase** → Read `AgentUsage/house_agents.md`
- **For complex multi-step research** → Read `AgentUsage/research_workflow.md`

### Testing
- **Before writing tests** → Read `AgentUsage/testing_strategies.md`
- **When implementing test coverage** → Read `AgentUsage/testing_strategies.md`
- **For test organization patterns** → Read `AgentUsage/testing_strategies.md`

### Code Quality
- **When refactoring code** → Read `AgentUsage/code_style_guide.md`
- **Before major code changes** → Read `AgentUsage/code_quality.md`
- **For documentation standards** → Read `AgentUsage/documentation_standards.md`

### Project Setup & Structure
- **When setting up new components** → Read `AgentUsage/project_setup.md`
- **For directory structure patterns** → Read `AgentUsage/project_structure.md`
- **Setting up CI/CD** → Read `AgentUsage/ci_cd_patterns.md`

### Docker & Deployment
- **When containerizing the application** → Read `AgentUsage/docker_guide.md`
- **For multi-stage Docker builds** → Read `AgentUsage/docker_guide.md`

**Complete Guide Index:** See `AgentUsage/README.md` for full documentation index

<!-- /BaseProject: AgentUsage Guide Index -->

---

<!-- BaseProject: House Agents Integration -->
## House Agents - Specialized Claude Subagents

**House Agents** are specialized sub-agents that handle heavy operations in separate context windows, dramatically reducing token usage.

### What Are House Agents?
- **house-research** - Search 70k+ tokens across files, return 3k summary (95% token savings)
- **house-git** - Analyze 43k token diffs, return 500 token summary (98% token savings)
- **house-bash** - Process 21k+ command output, return 700 token summary (97% token savings)

### When to Use House Agents
- **house-bash**: Running commands with verbose output (test suites, builds, package installs)
- **house-research**: Searching across 20+ files for patterns, TODOs, or function definitions
- **house-git**: Analyzing large diffs, reviewing changes before commits, branch comparisons

**Installation & Usage:** See `AgentUsage/house_agents.md` for detailed setup and examples

<!-- /BaseProject: House Agents Integration -->

---

## Quick Reference

**Essential Commands:**
```bash
uv run pytest             # Run tests
uv run black .            # Format code
uv run mypy src/          # Type check
uv build                  # Build package
```

**Before Every Commit:**
1. Format: `uv run black .`
2. Test: `uv run pytest`
3. Commit with conventional format

---

**Remember: Quality over speed. Write code that future you will thank you for!**
