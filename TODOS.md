# TODOS - OmniParser

**Last Updated:** 2025-10-23
**Current Phase:** Phase 2.3 Complete - EPUB Parser Production-Ready (v0.1.0)

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

### Alternative: Phase 2.4 - PDF Parser Implementation
- [ ] Implement PDFParser with PyMuPDF
  - [ ] Basic PDF text extraction
  - [ ] Heading-based chapter detection
  - [ ] Metadata extraction from PDF properties
  - [ ] Image extraction from PDFs
- [ ] Add OCR support for scanned PDFs (pytesseract)
- [ ] Write comprehensive PDF unit tests
- [ ] Add PDF integration tests with real files
- [ ] Update documentation for PDF support

---

## BaseProject Integration Follow-up

### Completed
- [x] Clone BaseProject template
- [x] Copy ClaudeUsage/ workflow guides to project
- [x] Merge CLAUDE.md with BaseProject sections
- [x] Enhance .gitignore with BaseProject patterns
- [x] Analyze commit style (95% already following conventional commits!)

### Optional Enhancements
- [ ] Install house-agents for context-efficient research (see ClaudeUsage/house_agents.md)
  - Install project-level: `git clone https://github.com/houseworthe/house-agents.git /tmp/house-agents && cp -r /tmp/house-agents/.claude .`
  - Or user-wide: `mkdir -p ~/.claude/agents && cp /tmp/house-agents/.claude/agents/*.md ~/.claude/agents/`
- [ ] Set up pre-commit hooks from ClaudeUsage/pre_commit_hooks/ (optional)
  - Commit message validation
  - Secrets detection
  - Code formatting checks
- [ ] Create secrets_template.json if API keys are needed
- [ ] Review ClaudeUsage/ guides for relevant workflows

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
- [ ] Phase 2.5: DOCX Parser (1 week)
- [ ] Phase 2.5: HTML/URL Parser (1-2 weeks)
- [ ] Phase 2.6: Markdown Parser (3-5 days)
- [ ] Phase 2.6: Text Parser (3-5 days)

### Advanced Features (v1.1+)
- [ ] Web & Social: Twitter/X, Reddit, LinkedIn, Medium, RSS/Atom
- [ ] Cloud Platforms: Google Docs, Notion, Confluence, Dropbox Paper
- [ ] Structured Data: JSON, XML, CSV, YAML parsing
- [ ] Archives: ZIP/TAR support with batch processing
- [ ] Technical: Jupyter notebooks, code documentation, API specs

### epub2tts Integration (Phase 4)
- [ ] Make OmniParser a dependency in epub2tts
- [ ] Update epub2tts to use OmniParser for document parsing
- [ ] Run epub2tts test suite with OmniParser
- [ ] Verify no performance regression >20%
- [ ] Update epub2tts documentation

---

## Notes

### Current Strengths
- ✅ Excellent test coverage (357 tests, 100% passing)
- ✅ Well-documented codebase with comprehensive docstrings
- ✅ Already following conventional commit style (95% adherence)
- ✅ Strong architecture with modular design
- ✅ Performance exceeds targets (0.25s vs 5s goal for EPUB)

### Development Resources
- **Workflow Guides:** See `ClaudeUsage/` directory for comprehensive development workflows
- **Architecture:** See `ARCHITECTURE_PLAN.md` for complete implementation plan
- **Specification:** See `OMNIPARSER_PROJECT_SPEC.md` for technical details
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
