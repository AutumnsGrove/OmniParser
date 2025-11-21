# TODOS.md

> Task tracking for OmniParser development. Update this file when tasks are completed, added, or changed.

---

## High Priority

- [ ] **Improve test coverage** - Currently at 94.3% (830/880 passing), target 100%
- [ ] **Fix remaining 50 failing tests** - Investigate and resolve test failures
- [ ] **Update DOCX parser status** - Currently marked as beta, evaluate for production readiness

## Medium Priority

- [ ] **Add CLI interface** - Implement `omniparser` command-line tool for direct usage
- [ ] **Create PyPI release workflow** - Automate package publishing with GitHub Actions
- [ ] **Add more AI providers** - Expand beyond Anthropic/OpenAI (e.g., Google Gemini, Cohere)
- [ ] **Performance benchmarks** - Document and track parser performance metrics

## Low Priority

- [ ] **Refactor EPUB parser** - Apply functional patterns from FUNCTIONAL_PATTERNS.md
- [ ] **Add async support** - Implement async versions of parsers for concurrent processing
- [ ] **Create API documentation** - Generate comprehensive API docs with Sphinx or MkDocs
- [ ] **Add more test fixtures** - Expand test coverage with diverse document samples

## Documentation

- [ ] **Update architecture diagrams** - Ensure diagrams reflect current implementation
- [ ] **Add migration guide** - Document upgrading from v0.2.x to v0.3.x
- [ ] **Create contributor guide** - Detailed guide for new contributors

## Completed

- [x] **BaseProject integration** - Added AgentUsage/, updated CLAUDE.md, installed git hooks
- [x] **QR code detection** - Implemented in PDF parser with URL fetching
- [x] **All 6 parsers implemented** - EPUB, HTML, PDF, DOCX, Markdown, Text

---

*Last updated: 2025-11-21*
