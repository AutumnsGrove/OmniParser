# Conventional Commits Guide

## Overview

Conventional Commits is a standardized commit message format used widely in open source projects. It enables automated changelog generation, semantic versioning, and better tooling integration.

**When to Use:**
- Open source contributions
- Projects using automated changelog tools
- Teams requiring semantic versioning automation
- Projects with established Conventional Commits workflow

**For Claude Code Projects**: See [git_commit_guide.md](git_commit_guide.md) for the custom format optimized for AI collaboration.

---

## Quick Reference

### Format

```
<type>: <description>

[optional body]

[optional footer]
```

### Common Types

```bash
feat: Add dark mode toggle
fix: Resolve timezone handling bug
docs: Update API documentation
style: Format code with Black
refactor: Extract helper function
test: Add integration tests
chore: Update dependencies
perf: Optimize database queries
```

---

## Commit Types

| Type | Purpose | Changelog | Example |
|------|---------|-----------|---------|
| `feat` | New feature | Yes | `feat: Add user authentication` |
| `fix` | Bug fix | Yes | `fix: Correct password validation` |
| `docs` | Documentation only | No | `docs: Update README` |
| `style` | Code formatting | No | `style: Run Black formatter` |
| `refactor` | Code restructure | No | `refactor: Simplify validation logic` |
| `test` | Add/modify tests | No | `test: Add auth tests` |
| `chore` | Maintenance | No | `chore: Update dependencies` |
| `perf` | Performance | Yes | `perf: Optimize query speed` |
| `build` | Build system | No | `build: Update webpack config` |
| `ci` | CI/CD changes | No | `ci: Add GitHub Actions` |

---

## Type Details and Examples

### feat: New Features

Use when adding new functionality or capabilities.

```
feat: Add diagram caching system

Implements a caching mechanism to skip regeneration of unchanged
diagrams. This significantly improves performance for large
documentation projects where only a few files change.

The cache uses file modification timestamps and content hashes
to detect changes.
```

**Triggers version bump**: Minor (1.0.0 → 1.1.0)

### fix: Bug Fixes

Use when correcting errors or unexpected behavior.

```
fix: Correct line number tracking in extractor

Fixes an off-by-one error that caused incorrect line numbers
in error messages when processing multi-line code blocks.

Closes #123
```

**Triggers version bump**: Patch (1.0.0 → 1.0.1)

### docs: Documentation

Use for documentation-only changes (code comments, READMEs, guides).

```
docs: Add API documentation for file_handler module

Includes docstrings for all public functions and usage examples.
Updates README with new module information.
```

**No version bump**

### refactor: Code Restructuring

Use when changing code structure without affecting behavior.

```
refactor: Extract validation logic into separate function

No functional changes, just improves code organization and
makes the validator reusable across modules.
```

**No version bump**

### perf: Performance Improvements

Use when optimizing code for speed or resource usage.

```
perf: Optimize markdown file scanning

Use os.scandir instead of os.walk for 3x faster directory
traversal on large projects.

Benchmarks:
- Before: 2.3s for 1000 files
- After: 0.7s for 1000 files
```

**Triggers version bump**: Patch (1.0.0 → 1.0.1)

### test: Tests

Use when adding or modifying tests.

```
test: Add comprehensive unit tests for authentication

Covers:
- Token generation and validation
- Password hashing verification
- Edge cases for expired tokens
- Invalid credentials handling

Test coverage increased from 67% to 94%
```

**No version bump**

### chore: Maintenance Tasks

Use for maintenance tasks that don't modify source code.

```
chore: Update Python dependencies

- Upgrade pytest to 8.0.0
- Update black to 24.1.0
- Pin anthropic SDK to 0.8.0
```

**No version bump**

---

## Breaking Changes

When introducing breaking changes, use the `BREAKING CHANGE:` footer or add `!` after type.

### Method 1: Footer

```
refactor: Change CLI argument format

BREAKING CHANGE: The --output flag now requires a directory path
instead of a filename pattern. Update your scripts accordingly.

Migration:
  Old: --output "diagrams/*.png"
  New: --output "diagrams" --format png
```

### Method 2: Exclamation Mark

```
feat!: Replace XML config with YAML

Completely removes XML configuration support. All configuration
files must be migrated to YAML format.

See migration guide in docs/migration/xml-to-yaml.md
```

**Triggers version bump**: Major (1.0.0 → 2.0.0)

---

## Guidelines

### 1. Subject Line

- **Keep under 50 characters**
- **Use imperative mood** ("Add" not "Added")
- **Don't end with period**
- **Be specific but concise**

```bash
# Good
feat: Add user session timeout
fix: Prevent memory leak in parser

# Bad
feat: Added new feature
fix: bug fix.
```

### 2. Body (Optional but Recommended)

- **Explain what and why, not how**
- **Wrap at 72 characters**
- **Use bullet points for multiple changes**

```
feat: Implement rate limiting for API

Add configurable rate limiting to prevent API abuse:
- Default: 100 requests per minute
- Configurable per-endpoint
- Returns 429 status when exceeded

Resolves #456
```

### 3. Footer (Optional)

Use for:
- Breaking changes (`BREAKING CHANGE:`)
- Issue references (`Fixes #123`, `Closes #456`)
- Co-authors (`Co-authored-by: Name <email>`)

---

## Real-World Examples

### Feature Addition

```
feat: Add real-time collaboration support

Implements WebSocket-based real-time editing:
- Multiple users can edit simultaneously
- Changes sync in real-time
- Conflict resolution using operational transforms
- Presence indicators for active users

Closes #234, #567
```

### Bug Fix

```
fix: Handle Unicode characters in filenames

Prevents crashes when processing files with non-ASCII characters
by using proper UTF-8 encoding throughout the pipeline.

Before: Crashed on files like "résumé.md"
After: Handles all Unicode filenames correctly

Fixes #789
```

### Documentation

```
docs: Add comprehensive README with examples

Includes:
- Installation instructions for all platforms
- Quick start guide
- Usage examples
- Configuration options
- Troubleshooting section
- Contributing guidelines
```

### Refactoring

```
refactor: Simplify authentication middleware

Extract common auth logic into reusable decorator.
No functional changes, just cleaner code organization.

- Reduces code duplication
- Makes testing easier
- Improves readability
```

### Performance

```
perf: Cache compiled regex patterns

Compile regex patterns once at module load instead of
on every request. Reduces CPU usage by 15% under load.
```

---

## Scopes (Optional)

Add scope to provide additional context:

```
feat(api): Add rate limiting middleware
fix(auth): Correct token expiration check
docs(readme): Update installation instructions
test(parser): Add edge case coverage
```

**Common scopes:**
- Component names: `auth`, `api`, `cli`, `ui`
- Module names: `parser`, `validator`, `renderer`
- File types: `readme`, `config`, `tests`

---

## Tools and Automation

### Commitlint

Enforce conventional commits:

```bash
# Install
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Configure (.commitlintrc.json)
{
  "extends": ["@commitlint/config-conventional"]
}

# Add to package.json
{
  "husky": {
    "hooks": {
      "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
  }
}
```

### Standard Version

Automated changelog and versioning:

```bash
# Install
npm install --save-dev standard-version

# Use
npm run release

# Generates:
# - Updates version in package.json
# - Generates CHANGELOG.md
# - Creates git tag
# - Commits changes
```

### Commitizen

Interactive commit message builder:

```bash
# Install
npm install -g commitizen

# Use instead of git commit
git cz
```

---

## Integration with Semantic Versioning

Conventional Commits maps directly to SemVer:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | Minor | 1.0.0 → 1.1.0 |
| `fix:` | Patch | 1.0.0 → 1.0.1 |
| `perf:` | Patch | 1.0.0 → 1.0.1 |
| `BREAKING CHANGE:` | Major | 1.0.0 → 2.0.0 |
| Others | No bump | - |

---

## Changelog Generation

With conventional commits, changelogs are automatically generated:

```markdown
# Changelog

## [2.0.0] - 2025-10-19

### Breaking Changes
- **api:** Changed authentication from OAuth1 to OAuth2

### Features
- **ui:** Add dark mode support
- **api:** Implement rate limiting

### Bug Fixes
- **parser:** Fix Unicode handling in filenames
- **auth:** Correct token expiration logic

### Performance
- **db:** Optimize query performance with indexing
```

---

## Best Practices

### DO ✅

1. **Use conventional format consistently**
2. **Write clear, specific descriptions**
3. **Include body for complex changes**
4. **Reference issues in footer**
5. **Mark breaking changes explicitly**

### DON'T ❌

1. **Don't mix multiple concerns**
   ```bash
   # Bad
   feat: Add login, fix bug, update docs

   # Good - Split into 3 commits
   feat: Add user login endpoint
   fix: Correct validation error message
   docs: Update API documentation
   ```

2. **Don't use past tense**
   ```bash
   # Bad
   feat: Added new feature

   # Good
   feat: Add user authentication
   ```

3. **Don't be vague**
   ```bash
   # Bad
   fix: Fix bug

   # Good
   fix: Prevent memory leak in file parser
   ```

---

## Comparison with Custom Format

### When to Use Each

**Use Conventional Commits:**
- Open source projects
- Automated tooling required
- Team uses standard-version/semantic-release
- Need automated changelogs

**Use Custom Format** (see git_commit_guide.md):
- Working with Claude Code
- Personal/team projects
- Want detailed implementation notes
- Prefer human-readable without tooling

### Example: Same Change, Both Formats

**Conventional:**
```
feat: Add user authentication system

Implements JWT-based authentication with secure password
hashing and session management. Includes middleware for
protecting routes.

- Uses bcrypt for password hashing
- JWT tokens expire after 24 hours
- Includes login/logout endpoints
```

**Custom:**
```
Add user authentication system

- Implement JWT-based token generation
- Create login and logout endpoints
- Add password hashing with bcrypt
- Implement session management
- Add authentication middleware

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Both are valid! Choose based on your project needs.

---

## Related Documentation

- **[git_commit_guide.md](git_commit_guide.md)** - Custom format for Claude Code
- **[git_workflow.md](git_workflow.md)** - Complete Git workflow
- **Specification**: https://www.conventionalcommits.org/
- **Angular Convention**: https://github.com/angular/angular/blob/main/CONTRIBUTING.md

---

*Last updated: 2025-10-19*
