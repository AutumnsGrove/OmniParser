# Git Commit Message Guide

## Overview

Well-crafted commit messages tell the story of **what** changed and **why**, making project history a powerful tool for understanding code evolution and debugging issues.

This guide focuses on the **Custom Format** optimized for Claude Code collaboration.

**For Conventional Commits**: See [git_conventional_commits.md](git_conventional_commits.md) for the industry-standard format used in open source projects.

---

## Quick Reference

### Custom Format Template

```
[Action] [Brief description of what was changed]

- [Specific change 1 with technical detail]
- [Specific change 2 with technical detail]
- [Specific change 3 with technical detail]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Action Verbs

- **Add** - New features, files, or functionality
- **Update** - Improvements to existing features
- **Fix** - Bug fixes and error corrections
- **Refactor** - Code structure improvements (no functionality changes)
- **Remove** - Deletion of features, files, or deprecated code
- **Enhance** - Performance or user experience improvements

---

## Action Verbs Explained

### Add - New Features

Use when creating something new.

```
Add real-time progress tracking and file verification

- Implement progress bar with percentage display
- Add file hash verification for integrity checks
- Create logging system for tracking operations
- Include timestamp tracking for all operations

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Update - Improvements

Use when enhancing existing features.

```
Update API key management with fallback mechanisms

- Enhance secrets.json loading with error handling
- Add environment variable fallback support
- Improve error messages for missing keys
- Update documentation with new loading pattern

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Fix - Bug Fixes

Use when correcting errors or unexpected behavior.

```
Fix path handling issues in video compression pipeline

- Resolve Unicode character handling in filenames
- Correct absolute path resolution on Windows
- Fix directory creation race conditions
- Handle spaces in file paths properly

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Refactor - Code Restructuring

Use when improving code structure without changing behavior.

```
Refactor logging system for improved performance

- Extract logging configuration to separate module
- Replace print statements with structured logging
- Consolidate duplicate logging code
- Improve log level handling and filtering

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## When to Use Each Action

```
What did you change?

Created something new?
├─ New feature → Add
├─ New file/module → Add
└─ New configuration → Add

Modified existing code?
├─ Fixed a bug → Fix
├─ Improved feature → Update
├─ Better performance → Enhance
└─ Better UX → Enhance

Changed structure without new behavior?
└─ Refactor

Removed something?
└─ Remove
```

---

## Best Practices

### 1. Subject Line (First Line)

- **Keep under 60 characters**
- **Start with action verb**
- **Be specific but concise**
- **Use imperative mood** ("Add" not "Added")

```bash
# Good
Add user authentication system
Fix memory leak in image processor
Update database connection pooling

# Bad
added new feature
bug fixes
updates
```

### 2. Detail Bullets

- **Use hyphens** for bullet points
- **Be specific** with technical details
- **Explain what and why**
- **Include file/module names** when relevant
- **Group related changes** together

```
Add database migration system

- Implement forward migration using Alembic
- Add automatic rollback on migration failure
- Create migration versioning and tracking system
- Include comprehensive error logging
- Add database backup before migrations

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3. Attribution Footer

- **Always include** the Claude Code attribution
- **Maintains clear co-authorship** record
- **Helpful for tracking** AI-assisted development

---

## Universal Guidelines

These principles apply to all commit messages:

### Atomic Commits

Each commit should represent **one logical change**.

**Good - Single Purpose:**
```
Add user authentication

- Create login endpoint
- Add JWT token generation
- Implement password hashing
- Add user session management
```

**Bad - Multiple Concerns:**
```
Add authentication, fix bug in parser, update docs, refactor utils
```

**Fix:** Split into 4 separate commits.

### Descriptive but Concise

**Good:**
```
Fix memory leak in image processing pipeline
```

**Bad:**
```
Fix bug
Fix the memory leak that was occurring in the image processing pipeline when processing large batches
```

### Imperative Mood

Write as if giving a command:

**Good:**
- Add feature
- Fix bug
- Update docs

**Bad:**
- Added feature
- Fixed bug
- Updated docs

### Context in Body

Use bullets to explain **why** and **what**, not **how**:

```
Refactor configuration loader for better testability

- Previous implementation tightly coupled to file I/O
- New version uses dependency injection
- Allows mock configs in tests
- Separates concerns between loading and parsing

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Anti-Patterns to Avoid

### ❌ Vague Messages

```
Update files
Fix things
Changes
WIP
```

**Why bad**: Provides no information.
**Fix**: Be specific about what and why.

### ❌ Too Many Concerns

```
Add feature X, fix bug Y, update docs, refactor module Z
```

**Why bad**: Makes git bisect useless, hard to revert.
**Fix**: Split into 4 separate commits.

### ❌ Wrong Action

```
Add typo fix in README  # Should be "Fix"
Fix new authentication  # Should be "Add"
```

**Why bad**: Misleading about the change type.
**Fix**: Use correct action verb.

### ❌ Past Tense

```
Added new feature
Fixed the bug
Updated documentation
```

**Why bad**: Not standard imperative mood.
**Fix**: Use imperative: "Add", "Fix", "Update"

### ❌ No Context

```
Update config
```

**Why bad**: Which config? What changed? Why?

**Fix:**
```
Update database connection pooling configuration

- Increase max connections from 10 to 50
- Add connection timeout of 30 seconds
- Enable connection recycling to prevent leaks

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Tools & Automation

### Git Commit Template

Save as `~/.gitmessage`:

```
# [Action] Brief description
#
# Body - explain what and why (optional)
#
# Footer (optional)
# 🤖 Generated with [Claude Code](https://claude.ai/code)
# Co-Authored-By: Claude <noreply@anthropic.com>
#
# --- Action Verbs ---
# Add:      New features, files, functionality
# Update:   Improvements to existing features
# Fix:      Bug fixes and corrections
# Refactor: Code structure improvements
# Remove:   Deletion of features/files
# Enhance:  Performance or UX improvements
```

Configure Git:
```bash
git config --global commit.template ~/.gitmessage
```

### Pre-commit Hook

Basic hook (`.git/hooks/commit-msg`):

```bash
#!/bin/bash
commit_msg=$(cat $1)

# Check for custom format
pattern='^(Add|Update|Fix|Refactor|Remove|Enhance) .+$'

if echo "$commit_msg" | grep -qE "$pattern"; then
    exit 0
else
    echo "Error: Commit message must start with action verb"
    echo "Use: Add, Update, Fix, Refactor, Remove, or Enhance"
    exit 1
fi
```

See `ClaudeUsage/pre_commit_hooks/` for more examples.

---

## When to Commit

**Commit changes immediately after:**

- ✅ Completing a significant feature or bug fix
- ✅ Adding new functionality that works correctly
- ✅ Making configuration or structural improvements
- ✅ Implementing user-requested features
- ✅ Fixing critical errors or security issues

**Don't commit:**

- ❌ Broken code that doesn't compile/run
- ❌ Incomplete features (use feature branches)
- ❌ Debug code or commented-out experiments
- ❌ Secrets, API keys, or sensitive data

---

## Benefits of Good Commit Messages

### Clear Communication
- Team members understand changes immediately
- Code reviewers grasp intent without reading all code
- Future developers (including yourself) know why changes were made

### Better Debugging
- `git bisect` becomes a powerful debugging tool
- Easy to find when bugs were introduced
- Simple to understand what each commit changed

### Project Documentation
- Commit history tells the project's story
- Evolution of features is traceable
- Design decisions are preserved

### Collaboration
- Clear handoffs between developers
- Easy to review pull requests
- Reduces back-and-forth communication

---

## Real-World Examples

### Feature Addition

```
Add user authentication system

- Implement JWT-based token generation
- Create login and logout endpoints
- Add password hashing with bcrypt
- Implement session management with Redis
- Add authentication middleware for protected routes
- Include token refresh mechanism

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Bug Fix

```
Fix memory leak in background job processor

- Release database connections after job completion
- Clear job data from memory after processing
- Implement connection pooling with max limits
- Add memory monitoring to job logs

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Refactoring

```
Refactor validation logic into reusable module

- Extract common validation functions from controllers
- Create ValidationError custom exception class
- Centralize error message formatting
- Add type hints for better IDE support
- No functional changes to validation behavior

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Documentation

```
Update API documentation with authentication examples

- Add authentication flow diagrams
- Include example requests with tokens
- Document error responses for auth failures
- Add troubleshooting section for common issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Related Documentation

- **[git_conventional_commits.md](git_conventional_commits.md)** - Industry standard format for open source
- **[git_workflow.md](git_workflow.md)** - Complete Git workflow with examples
- **[pre_commit_hooks/](pre_commit_hooks/)** - Automated commit validation

---

## Summary: The Golden Rules

1. ✅ **One logical change per commit**
2. ✅ **Descriptive subject line (under 60 chars)**
3. ✅ **Use imperative mood**
4. ✅ **Don't end subject with period**
5. ✅ **Add detailed bullets for complex changes**
6. ✅ **Be specific, not vague**
7. ✅ **Include Claude Code attribution**

**Following these guidelines makes your Git history a powerful tool for understanding project evolution, debugging issues, and collaborating effectively.**

---

*Last updated: 2025-10-19*
