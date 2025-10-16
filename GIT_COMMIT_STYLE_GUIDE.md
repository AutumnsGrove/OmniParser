# Git Commit Style Guide

This document describes the commit message style used in this project. It's based on [Conventional Commits](https://www.conventionalcommits.org/) but simplified for clarity and ease of use.

## Format

```
<type>: <description>

[optional body]

[optional footer]
```

## Commit Types

Use these prefixes to categorize your commits:

### **feat**: New Features
Introduces new functionality or capabilities.

```
feat: Add diagram caching system
feat: Implement watch mode for auto-regeneration
feat: Add support for custom Mermaid themes
```

### **fix**: Bug Fixes
Fixes a bug or resolves an issue.

```
fix: Correct line number tracking in extractor
fix: Handle unicode characters in filenames
fix: Prevent crash when output directory is read-only
```

### **docs**: Documentation
Changes to documentation only (README, comments, guides).

```
docs: Add comprehensive README
docs: Update installation instructions
docs: Add API documentation for file_handler module
```

### **style**: Code Style/Formatting
Changes that don't affect code behavior (formatting, whitespace, etc.).

```
style: Format code with Black
style: Fix indentation in generator.py
style: Reorganize imports alphabetically
```

### **refactor**: Code Refactoring
Restructuring code without changing functionality.

```
refactor: Extract validation logic into separate function
refactor: Simplify error handling in generator
refactor: Rename variables for clarity
```

### **test**: Tests
Adding, modifying, or fixing tests.

```
test: Add integration tests for core functionality
test: Add edge case tests for extractor
test: Fix mocking in generator tests
```

### **chore**: Maintenance/Tooling
Routine tasks, dependency updates, build configuration, etc.

```
chore: Add .gitignore for Python/UV project
chore: Add project dependencies
chore: Update requirements.txt versions
chore: Add pre-commit hooks
```

### **perf**: Performance Improvements
Changes that improve performance.

```
perf: Optimize markdown file scanning
perf: Add caching for repeated extractions
perf: Use multiprocessing for batch generation
```

### **build**: Build System
Changes to build configuration or dependencies.

```
build: Update build script for production
build: Add Docker configuration
build: Configure CI/CD pipeline
```

### **ci**: Continuous Integration
Changes to CI/CD configuration.

```
ci: Add GitHub Actions workflow
ci: Configure automated testing
ci: Add code coverage reporting
```

## Guidelines

### 1. **Keep The Subject Line Short**
- Aim for 50 characters or less
- Be concise but descriptive
- Use imperative mood: "Add feature" not "Added feature"

✅ **Good:**
```
feat: Add SVG output support
```

❌ **Bad:**
```
feat: I added support for generating diagrams in SVG format which allows for scalable vector graphics
```

### 2. **Use Imperative Mood**
Write as if giving a command or instruction.

✅ **Good:**
```
fix: Correct timezone handling
refactor: Extract helper function
docs: Update README with examples
```

❌ **Bad:**
```
fix: Corrected timezone handling
refactor: Extracted helper function
docs: Updated README with examples
```

### 3. **Don't End with a Period**
The subject line is a title, not a sentence.

✅ **Good:**
```
feat: Add configuration file support
```

❌ **Bad:**
```
feat: Add configuration file support.
```

### 4. **Body Is Optional but Helpful**
Use the body to explain *why* and *what*, not *how*.

```
feat: Add diagram caching system

Implements a caching mechanism to skip regeneration of unchanged
diagrams. This significantly improves performance for large
documentation projects where only a few files change.

The cache uses file modification timestamps and content hashes
to detect changes.
```

### 5. **Use Body for Breaking Changes**
If introducing breaking changes, explain them clearly.

```
refactor: Change CLI argument format

BREAKING CHANGE: The --output flag now requires a directory path
instead of a filename pattern. Update your scripts accordingly.

Old: --output "diagrams/*.png"
New: --output "diagrams" --format png
```

## Examples from This Project

Here are real commits from MermaidVisualizer:

### ✅ Excellent Examples

```
feat: Implement core modules (extractor, generator, file_handler, cli) and comprehensive test suite
```
- Clear type
- Describes what was added
- Mentions all major components

```
docs: Add comprehensive README
```
- Simple and clear
- Type matches content perfectly

```
style: Format code with Black
```
- Specific tool mentioned
- Action is clear

```
test: Add integration tests for core functionality
```
- Specifies test type (integration)
- Clear scope

```
chore: Add .gitignore for Python/UV project
```
- Maintenance task
- Mentions project type for context

### ❌ Examples to Avoid

```
Update stuff
```
- No type prefix
- Vague description
- Not helpful for history

```
fix: fixed the bug
```
- Wrong mood (past tense)
- Doesn't describe what bug
- Not actionable

```
feat: Add the ability to generate diagrams from markdown files and also update the documentation and fix some bugs
```
- Too long
- Multiple concerns in one commit
- Should be split into separate commits

```
WIP
```
- Not descriptive
- Doesn't follow format
- Avoid committing WIP when possible

## Type Decision Tree

Not sure which type to use? Follow this tree:

```
Does it add new functionality?
├─ Yes → feat
└─ No
   └─ Does it fix a bug?
      ├─ Yes → fix
      └─ No
         └─ Is it documentation only?
            ├─ Yes → docs
            └─ No
               └─ Is it formatting/style only?
                  ├─ Yes → style
                  └─ No
                     └─ Does it change code structure?
                        ├─ Yes → refactor
                        └─ No
                           └─ Is it tests?
                              ├─ Yes → test
                              └─ No → chore
```

## Special Cases

### Multiple Files, One Purpose

If changes span multiple files but serve one purpose, use one commit:

```
feat: Add user authentication

- Add login endpoint
- Create user model
- Add JWT token generation
- Update documentation
```

### Dependent Changes

If changes must go together, keep them in one commit:

```
refactor: Rename function for clarity

Updated all call sites and tests to use new name.
```

### Configuration Changes

```
chore: Update project configuration

- Add prettier config
- Update tsconfig.json
- Add ESLint rules
```

## Anti-Patterns to Avoid

### ❌ Vague Commits
```
Update files
Fix things
Changes
```

### ❌ Too Many Concerns
```
feat: Add feature X, fix bug Y, update docs, refactor module Z
```
**Fix:** Split into 4 commits with appropriate types

### ❌ Wrong Type
```
feat: Fix typo in README
```
**Fix:** Should be `docs: Fix typo in README`

### ❌ Mixing Types
```
feat: Add new feature and fix bugs
```
**Fix:** Separate into `feat` and `fix` commits

### ❌ Work-in-Progress Commits
```
WIP
wip: trying something
temp commit
```
**Fix:** Finish the work or use branches

## Benefits of This Style

1. **Scannable History**: Quickly understand what changed
2. **Automated Changelogs**: Tools can generate release notes automatically
3. **Semantic Versioning**: Types map to version bumps (feat→minor, fix→patch)
4. **Better Collaboration**: Team members understand changes at a glance
5. **Git Tools**: Many tools parse these formats for enhanced features

## Tools & Automation

### Commitizen
Helps write conventional commits interactively:
```bash
npm install -g commitizen
git cz  # Instead of git commit
```

### Commitlint
Validates commit messages:
```bash
npm install --save-dev @commitlint/cli @commitlint/config-conventional
```

### Pre-commit Hooks
Enforce style automatically:
```bash
# .git/hooks/commit-msg
#!/bin/bash
commit_msg=$(cat $1)
pattern='^(feat|fix|docs|style|refactor|test|chore|perf|build|ci):.+$'

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "Error: Commit message doesn't follow conventional format"
    echo "Format: <type>: <description>"
    echo "Types: feat, fix, docs, style, refactor, test, chore, perf, build, ci"
    exit 1
fi
```

## Quick Reference

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: Add dark mode` |
| `fix` | Bug fix | `fix: Resolve memory leak` |
| `docs` | Documentation | `docs: Update API guide` |
| `style` | Formatting | `style: Format with Black` |
| `refactor` | Code restructuring | `refactor: Extract helper` |
| `test` | Tests | `test: Add unit tests` |
| `chore` | Maintenance | `chore: Update dependencies` |
| `perf` | Performance | `perf: Optimize queries` |
| `build` | Build system | `build: Update webpack` |
| `ci` | CI/CD | `ci: Add GitHub Actions` |

## Commit Message Template

Save this as `.gitmessage` and configure Git to use it:

```
# <type>: <subject> (Max 50 chars)

# <body> (Wrap at 72 chars)

# <footer>

# Type can be:
#   feat:     New feature
#   fix:      Bug fix
#   docs:     Documentation changes
#   style:    Code style/formatting
#   refactor: Code refactoring
#   test:     Tests
#   chore:    Maintenance
#   perf:     Performance improvements
#   build:    Build system changes
#   ci:       CI/CD changes
#
# Subject line: Use imperative mood ("Add" not "Added")
# Body: Explain what and why vs. how
# Footer: Reference issues, breaking changes
```

Configure Git to use it:
```bash
git config --global commit.template ~/.gitmessage
```

## Summary

**The Golden Rules:**
1. Use a type prefix
2. Keep subject under 50 chars
3. Use imperative mood
4. Don't end with period
5. Add body for complex changes
6. One logical change per commit

Following this style makes your Git history a powerful tool for understanding project evolution, debugging issues, and collaborating effectively.
