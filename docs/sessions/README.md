# Claude Code Session Prompts - Quick Reference

This directory contains individual session prompts for autonomous Claude Code execution. Each prompt is designed to be **copy-pasted directly** into a new Claude Code session.

**🎉 NEW: All sessions now use PR/branch workflow!** Each session creates a feature branch and submits a Pull Request for review.

---

## 📋 Available Sessions

### OmniParser Refactoring Sessions

These should be run **sequentially** in the OmniParser project. Each creates its own feature branch and PR.

1. **`SESSION_1_PDF_PARSER_REFACTOR.md`**
   - **Project:** OmniParser
   - **Branch:** `refactor/pdf-parser-modular`
   - **Duration:** 4-5 hours
   - **Target:** Refactor PDF parser (1,052 lines → 6 modules)
   - **Prerequisites:** None
   - **Deliverables:** Pull Request with modular PDF parser

2. **`SESSION_2_DOCX_PARSER_REFACTOR.md`**
   - **Project:** OmniParser
   - **Branch:** `refactor/docx-parser-modular`
   - **Duration:** 3-4 hours
   - **Target:** Refactor DOCX parser (755 lines → 5-6 modules) + complete beta features
   - **Prerequisites:** Session 1 PR merged
   - **Deliverables:** Pull Request with production DOCX parser (lists + hyperlinks)

3. **`SESSION_3_MARKDOWN_TEXT_REFACTOR.md`**
   - **Project:** OmniParser
   - **Branch:** `refactor/markdown-text-parsers`
   - **Duration:** 3-4 hours
   - **Target:** Refactor Markdown (741 lines → 4 modules) + Text (580 lines → 4 modules)
   - **Prerequisites:** Session 2 PR merged
   - **Deliverables:** Pull Request with both parsers modular

4. **`SESSION_4_EPUB_PARSER_REFACTOR.md`**
   - **Project:** OmniParser
   - **Branch:** `refactor/epub-parser-modular`
   - **Duration:** 4-5 hours
   - **Target:** Refactor EPUB parser (1,053 lines → 7 modules)
   - **Prerequisites:** Session 3 PR merged
   - **Deliverables:** Pull Request with modular EPUB parser

5. **`SESSION_5_HTML_PARSER_REFACTOR.md`**
   - **Project:** OmniParser
   - **Branch:** `refactor/html-parser-modular`
   - **Duration:** 3-4 hours
   - **Target:** Refactor HTML parser (686 lines → 5-6 modules)
   - **Prerequisites:** Session 4 PR merged
   - **Deliverables:** Pull Request with modular HTML parser

### epub2tts Migration Session

This runs **independently** in the epub2tts project:

6. **`SESSION_EPUB2TTS_MIGRATION.md`**
   - **Project:** epub2tts
   - **Branch:** `feat/integrate-omniparser`
   - **Duration:** 6-8 hours
   - **Target:** Migrate from internal EPUB processing to OmniParser dependency
   - **Prerequisites:** OmniParser v0.1.0+ available
   - **Deliverables:** Pull Request for epub2tts v0.2.0 using OmniParser

---

## 🚀 Quick Start

### For Refactoring (OmniParser)

**Run these sequentially, one at a time. Each creates a PR:**

```bash
# Session 1: PDF Parser
cat docs/sessions/SESSION_1_PDF_PARSER_REFACTOR.md
# Copy → Paste into Claude Code → Creates PR on branch refactor/pdf-parser-modular
# Review PR → Merge → Continue to Session 2

# Session 2: DOCX Parser
cat docs/sessions/SESSION_2_DOCX_PARSER_REFACTOR.md
# Copy → Paste into Claude Code → Creates PR on branch refactor/docx-parser-modular
# Review PR → Merge → Continue to Session 3

# Session 3: Markdown & Text
cat docs/sessions/SESSION_3_MARKDOWN_TEXT_REFACTOR.md
# Copy → Paste into Claude Code → Creates PR on branch refactor/markdown-text-parsers
# Review PR → Merge → Continue to Session 4

# Session 4: EPUB Parser
cat docs/sessions/SESSION_4_EPUB_PARSER_REFACTOR.md
# Copy → Paste into Claude Code → Creates PR on branch refactor/epub-parser-modular
# Review PR → Merge → Continue to Session 5

# Session 5: HTML Parser
cat docs/sessions/SESSION_5_HTML_PARSER_REFACTOR.md
# Copy → Paste into Claude Code → Creates PR on branch refactor/html-parser-modular
# Review PR → Merge → All parsers refactored! 🎉
```

### For Migration (epub2tts)

**This can run independently:**

```bash
# epub2tts Migration (can run anytime after OmniParser v0.1.0 released)
cd /Users/mini/Documents/GitHub/epub2tts
cat docs/sessions/SESSION_EPUB2TTS_MIGRATION.md
# Copy → Paste into Claude Code → Creates PR on branch feat/integrate-omniparser
# Review PR → Merge → Migration complete!
```

---

## 📊 Session Overview

| Session | Project | Branch | Duration | Lines Changed | PR Deliverable |
|---------|---------|--------|----------|---------------|----------------|
| 1. PDF | OmniParser | `refactor/pdf-parser-modular` | 4-5h | 1,052 → ~600 | Modular PDF parser |
| 2. DOCX | OmniParser | `refactor/docx-parser-modular` | 3-4h | 755 → ~580 | Production DOCX + features |
| 3. Markdown/Text | OmniParser | `refactor/markdown-text-parsers` | 3-4h | 1,321 → ~920 | Both parsers modular |
| 4. EPUB | OmniParser | `refactor/epub-parser-modular` | 4-5h | 1,053 → ~750 | Modular EPUB parser |
| 5. HTML | OmniParser | `refactor/html-parser-modular` | 3-4h | 686 → ~500 | Modular HTML parser |
| 6. epub2tts | epub2tts | `feat/integrate-omniparser` | 6-8h | -965 lines | OmniParser integration |
| **TOTAL** | Both | **6 PRs** | **24-32h** | **-1,312 lines** | All parsers refactored |

---

## ✅ Success Criteria

### After All Refactoring Sessions (1-5)
- ✅ All parser files ≤200 lines
- ✅ All modules 50-200 lines
- ✅ All tests passing (no regressions)
- ✅ DOCX parser production-ready
- ✅ Functional patterns followed
- ✅ **6 Pull Requests created and reviewed**
- ✅ Documentation updated

### After Migration Session (6)
- ✅ epub2tts uses OmniParser (>=0.1.0)
- ✅ 965 lines removed
- ✅ All tests passing
- ✅ Full TTS pipeline tested
- ✅ Version bumped to v0.2.0
- ✅ **Pull Request created and reviewed**
- ✅ Documentation updated

---

## 🎯 Execution Strategy

### Sequential Refactoring (Recommended)
Run Sessions 1 → 2 → 3 → 4 → 5 sequentially in OmniParser. Each session:
1. Creates feature branch
2. Makes modular changes
3. Runs tests
4. Creates Pull Request
5. **You review and merge PR**
6. Next session starts from merged main

**Why sequential with PRs?**
- Each PR gets reviewed before merging
- GitHub bot reviews code automatically
- Main branch stays stable
- Easy to rollback if issues found
- Session patterns improve over time

### Parallel Execution (Advanced)
Session 6 (epub2tts migration) can run **in parallel** with refactoring sessions since it's in a different project.

**Example timeline:**
```
Day 1:  Session 1 (PDF) → PR created → Review & merge
Day 2:  Session 2 (DOCX) → PR created → Review & merge
        Session 6 (epub2tts) started in parallel → PR created
Day 3:  Session 3 (Markdown/Text) → PR created → Review & merge
        Session 6 (epub2tts) → Review & merge
Day 4:  Session 4 (EPUB) → PR created → Review & merge
Day 5:  Session 5 (HTML) → PR created → Review & merge
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
Claude Code will:
- Create feature branch
- Make changes and commit frequently
- Push to remote after every commit
- Run tests after each change
- Create Pull Request when complete
- Report progress throughout

### Step 7: Review Pull Request
When session completes:
- Check PR URL provided by Claude Code
- Review changes on GitHub
- Let GitHub bot review (automatic)
- Approve and merge PR
- Move to next session

---

## 🔄 PR Workflow

### Each Session Follows This Pattern:

1. **Branch Creation**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b [branch-name]
   git push -u origin [branch-name]
   ```

2. **Iterative Development**
   - Make changes
   - Run tests
   - Commit with conventional commit format
   - Push to remote branch
   - Repeat

3. **PR Creation**
   ```bash
   gh pr create \
     --title "[conventional-commit-style-title]" \
     --body "[standardized PR body]" \
     --base main \
     --head [branch-name]
   ```

4. **Review & Merge**
   - You review PR on GitHub
   - GitHub bot reviews automatically
   - Merge when approved
   - Delete branch after merge

---

## 🚨 Troubleshooting

### Session Fails Mid-Execution
1. Check error message in Claude Code output
2. Review last successful commit: `git log --oneline -5`
3. Check which branch you're on: `git branch --show-current`
4. If needed, restart from last known good state
5. Or manually complete remaining steps and create PR

### Tests Fail After Refactoring
1. Check test output: `uv run pytest tests/ -v --tb=short`
2. Review recent changes: `git diff HEAD~1`
3. Fix failing tests (usually import or data structure issues)
4. Commit fix: `git commit -m "fix: <description>"`
5. Push: `git push origin [branch-name]`

### PR Creation Fails
If `gh pr create` fails:
1. Create PR manually on GitHub
2. Use the PR body template from the session file
3. Set base to `main`, head to `[branch-name]`

### Branch Conflicts
If branch has conflicts with main:
```bash
git checkout [branch-name]
git fetch origin
git merge origin/main
# Resolve conflicts
git add .
git commit -m "merge: Resolve conflicts with main"
git push origin [branch-name]
```

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

**Each session:**
- ✅ Creates its own feature branch
- ✅ Makes atomic commits with git push
- ✅ Runs tests continuously
- ✅ Creates Pull Request automatically
- ✅ Ready for your review!

**After each PR is merged, move to the next session!**

---

**Last Updated:** 2025-10-29
**Version:** 2.0 (PR/Branch Workflow)
**Mode:** YOLO (Auto-approve) execution
**Workflow:** Feature branches → Pull Requests → Review → Merge
