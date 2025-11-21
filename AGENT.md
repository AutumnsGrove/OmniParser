# AGENT.md

> Main orchestrator for Claude agents. For detailed guides, see `AgentUsage/README.md`

---

## Project Overview

**Project:** OmniParser - Universal Document Parser
**Purpose:** Transform documents into clean markdown with metadata extraction
**Version:** 0.3.0

**Tech Stack:** Python 3.10+ | UV | Hatchling | pytest | Black | mypy

**Detailed Specs:** See `CLAUDE.md` for comprehensive project documentation

---

## Essential Instructions

### Core Behavior
- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary
- ALWAYS prefer editing existing files to creating new ones
- NEVER proactively create documentation unless requested

### Before Any Task
1. Check `TODOS.md` for current priorities
2. Read relevant sections of `CLAUDE.md` for project context
3. Update `TODOS.md` when tasks are completed

### Git Workflow
```bash
# Conventional commits required
<type>: <description>

# Types: feat, fix, docs, refactor, test, chore, perf
```

**Always run before committing:**
```bash
uv run black src/ tests/   # Format
uv run pytest              # Test
```

---

## Quick Reference

### Commands
```bash
uv run pytest              # Run tests
uv run black .             # Format code
uv run mypy src/           # Type check
uv build                   # Build package
```

### Key Files
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Detailed project docs, code standards, architecture |
| `TODOS.md` | Task tracking |
| `AgentUsage/` | Workflow guides (git, secrets, testing, etc.) |

---

## When to Read Guides

| Situation | Guide |
|-----------|-------|
| Managing secrets/API keys | `AgentUsage/secrets_management.md` |
| Git workflow questions | `AgentUsage/git_guide.md` |
| Writing tests | `AgentUsage/testing_strategies.md` |
| Using UV package manager | `AgentUsage/uv_usage.md` |
| Searching 20+ files | `AgentUsage/house_agents.md` |

**Full index:** `AgentUsage/README.md`

---

## Project-Specific Notes

- **Use `uv run`** for all commands (not bare `python` or `pytest`)
- **Follow patterns** in `FUNCTIONAL_PATTERNS.md` for new code
- **Test coverage target:** >90%
- **Parsers:** EPUB, HTML, PDF, DOCX, Markdown, Text

---

*For comprehensive details: `CLAUDE.md` | For workflows: `AgentUsage/`*
