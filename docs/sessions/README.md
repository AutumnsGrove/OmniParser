# Claude Code Session Prompts - Quick Reference

This directory contains individual session prompts for autonomous Claude Code execution. Each prompt is designed to be **copy-pasted directly** into a new Claude Code session.

---

## 📋 Available Sessions

### OmniParser Refactoring Sessions

These should be run **sequentially** in the OmniParser project:

1. **`SESSION_1_PDF_PARSER_REFACTOR.md`**
   - **Project:** OmniParser
   - **Duration:** 4-5 hours
   - **Target:** Refactor PDF parser (1,052 lines → 6 modules)
   - **Prerequisites:** None
   - **Deliverables:** Modular PDF parser, all tests passing

2. **`SESSION_2_DOCX_PARSER_REFACTOR.md`**
   - **Project:** OmniParser
   - **Duration:** 3-4 hours
   - **Target:** Refactor DOCX parser (755 lines → 5-6 modules) + complete beta features
   - **Prerequisites:** Session 1 complete
   - **Deliverables:** Modular DOCX parser with lists + hyperlinks, promoted to production

3. **`SESSION_3_MARKDOWN_TEXT_REFACTOR.md`**
   - **Project:** OmniParser
   - **Duration:** 3-4 hours
   - **Target:** Refactor Markdown (741 lines → 4 modules) + Text (580 lines → 4 modules)
   - **Prerequisites:** Sessions 1 & 2 complete
   - **Deliverables:** Both parsers modular, all tests passing

### epub2tts Migration Session

This runs **independently** in the epub2tts project:

4. **`SESSION_EPUB2TTS_MIGRATION.md`**
   - **Project:** epub2tts
   - **Duration:** 6-8 hours
   - **Target:** Migrate from internal EPUB processing to OmniParser dependency
   - **Prerequisites:** OmniParser v0.1.0+ available
   - **Deliverables:** epub2tts v0.2.0 using OmniParser, 965 lines removed

---

## 🚀 Quick Start

### For Refactoring (OmniParser)

**Run these sequentially, one at a time:**

```bash
# Session 1: PDF Parser
# Copy docs/sessions/SESSION_1_PDF_PARSER_REFACTOR.md
# Paste into new Claude Code session in OmniParser directory
# Wait for completion

# Session 2: DOCX Parser
# Copy docs/sessions/SESSION_2_DOCX_PARSER_REFACTOR.md
# Paste into new Claude Code session in OmniParser directory
# Wait for completion

# Session 3: Markdown & Text Parsers
# Copy docs/sessions/SESSION_3_MARKDOWN_TEXT_REFACTOR.md
# Paste into new Claude Code session in OmniParser directory
# Wait for completion
```

### For Migration (epub2tts)

**This can run in parallel with refactoring sessions:**

```bash
# epub2tts Migration
# Copy docs/sessions/SESSION_EPUB2TTS_MIGRATION.md
# Paste into new Claude Code session in epub2tts directory
# Wait for completion
```

---

## 📊 Session Overview

| Session | Project | Duration | Lines Changed | Deliverable |
|---------|---------|----------|---------------|-------------|
| 1. PDF Refactor | OmniParser | 4-5h | 1,052 → ~700 (6 modules) | Modular PDF parser |
| 2. DOCX Refactor | OmniParser | 3-4h | 755 → ~580 (5-6 modules) | Production DOCX parser |
| 3. Markdown/Text | OmniParser | 3-4h | 1,321 → ~920 (8 modules) | Both parsers modular |
| 4. epub2tts Migration | epub2tts | 6-8h | -965 lines | v0.2.0 with OmniParser |
| **TOTAL** | Both | **16-21h** | **-815 lines** | All parsers refactored + migration complete |

---

## ✅ Success Criteria

### After All Refactoring Sessions (1-3)
- ✅ All parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ All tests passing (no regressions)
- ✅ DOCX parser production-ready
- ✅ Functional patterns followed
- ✅ Documentation updated

### After Migration Session (4)
- ✅ epub2tts uses OmniParser (>=0.1.0)
- ✅ 965 lines removed
- ✅ All tests passing
- ✅ Full TTS pipeline tested
- ✅ Version bumped to v0.2.0
- ✅ Documentation updated

---

## 🎯 Execution Strategy

### Sequential Refactoring (Recommended)
Run Sessions 1 → 2 → 3 sequentially in OmniParser. Each session learns from the previous one's patterns.

**Why sequential?**
- Session 1 establishes refactoring patterns
- Session 2 applies and refines patterns
- Session 3 solidifies patterns across all parsers

### Parallel Execution (Advanced)
Session 4 (epub2tts migration) can run **in parallel** with refactoring sessions since they're in different projects.

**Example timeline:**
```
Day 1:  Session 1 (PDF) running
Day 2:  Session 2 (DOCX) running + Session 4 (epub2tts) started in parallel
Day 3:  Session 3 (Markdown/Text) running + Session 4 completing
```

---

## 📝 How to Use

### Step 1: Choose a Session
Pick the session you want to run (start with Session 1 for refactoring).

### Step 2: Open the Session File
```bash
# In OmniParser repo
cat docs/sessions/SESSION_1_PDF_PARSER_REFACTOR.md
```

### Step 3: Copy Entire Content
Select all text from the session file (Cmd+A / Ctrl+A).

### Step 4: Start New Claude Code Session
- Open Claude Code
- Start a new conversation
- Set to YOLO mode (auto-approve)

### Step 5: Paste and Execute
Paste the entire session prompt and let Claude Code run autonomously.

### Step 6: Monitor Progress
Claude Code will report after each phase:
- Phase completed
- Test status
- Commits created
- What's next

### Step 7: Verify Completion
When session completes:
- Check all tests pass
- Review commits
- Read completion report
- Move to next session

---

## 🚨 Troubleshooting

### Session Fails Mid-Execution
1. Check error message in Claude Code output
2. Review last successful commit: `git log --oneline -5`
3. If needed, restart from last known good state
4. Or manually complete remaining steps

### Tests Fail After Refactoring
1. Check test output: `uv run pytest tests/ -v --tb=short`
2. Review recent changes: `git diff HEAD~1`
3. Fix failing tests (usually import or data structure issues)
4. Commit fix and continue

### Context Overflow
If Claude Code reports token limit:
1. Session prompt was too verbose
2. Ask Claude Code to summarize and continue
3. Split remaining work into smaller tasks

---

## 📚 Related Documentation

### Full Guides (Reference)
- `docs/CLAUDE_CODE_REFACTORING_GUIDE.md` - Complete refactoring guide (all phases)
- `docs/CLAUDE_CODE_EPUB2TTS_MIGRATION_GUIDE.md` - Complete migration guide

### Patterns & Standards
- `PATTERNS_QUICK_REF.md` - Quick patterns reference (keep open!)
- `FUNCTIONAL_PATTERNS.md` - Detailed functional patterns
- `GIT_COMMIT_STYLE_GUIDE.md` - Commit message format

### Project Documentation
- `TODOS.md` - Track overall project progress
- `CLAUDE.md` - Project-specific instructions
- `CHANGELOG.md` - Version history

---

## 🎬 Ready to Execute?

**For Refactoring:** Start with `SESSION_1_PDF_PARSER_REFACTOR.md`

**For Migration:** Use `SESSION_EPUB2TTS_MIGRATION.md`

**Each session is self-contained and ready to copy-paste!**

---

**Last Updated:** 2025-10-29
**Version:** 1.0
**Mode:** YOLO (Auto-approve) execution
