# Changelog Automation

This document explains how the automated changelog generation works in the OmniParser project.

## Overview

The project uses **[git-cliff](https://git-cliff.org/)** to automatically generate and update `CHANGELOG.md` based on [conventional commits](https://www.conventionalcommits.org/).

### Key Features

- ✅ **Automatic Updates**: CHANGELOG.md is updated on every push to main/develop branches
- ✅ **Conventional Commits**: Parses commit messages following the conventional format
- ✅ **Keep a Changelog Format**: Maintains the existing changelog structure
- ✅ **Semantic Versioning**: Compatible with semver for version bumping
- ✅ **Customizable**: Fully configurable via `cliff.toml`

## How It Works

### Workflow Trigger

The GitHub Action (`.github/workflows/changelog.yml`) runs when:
- Code is pushed to `main`, `master`, `develop`, or `claude/**` branches
- Workflow is manually triggered via GitHub Actions UI
- **Excludes**: Changes to `CHANGELOG.md` itself (prevents infinite loops)

### Commit Parsing

git-cliff reads all commits and groups them by type:

| Commit Type | Changelog Section | Example |
|-------------|-------------------|---------|
| `feat:` | Added | `feat: Add PDF parser support` |
| `fix:` | Fixed | `fix: Resolve encoding issue in EPUB` |
| `docs:` | Documentation | `docs: Update API reference` |
| `perf:` | Performance | `perf: Optimize text extraction` |
| `refactor:` | Refactored | `refactor: Simplify parser logic` |
| `test:` | Testing | `test: Add integration tests` |
| `chore:` | Miscellaneous | `chore: Update dependencies` |
| `revert:` | Revert | `revert: Undo previous changes` |

### Commit Format Requirements

**Standard Format:**
```
<type>: <description>

[optional body]

[optional footer]
```

**Examples:**

✅ **Good:**
```bash
feat: Add EPUB parser with TOC detection
fix: Resolve memory leak in image extraction
docs: Add usage examples for PDF parser
```

❌ **Bad (will be filtered out):**
```bash
WIP changes
Update stuff
Fixed it
```

## Configuration

### cliff.toml

The `cliff.toml` file controls changelog generation:

```toml
[changelog]
header = "# Changelog\n\n..."  # Changelog header
body = "{% if version %}..."    # Template for entries
footer = "..."                  # Footer text

[git]
conventional_commits = true     # Parse conventional commits
filter_unconventional = true    # Skip non-conventional commits
commit_parsers = [...]          # Define commit type mappings
```

**Key Settings:**

- **`conventional_commits = true`**: Only parse conventional commits
- **`filter_unconventional = true`**: Ignore commits that don't follow the format
- **`commit_parsers`**: Maps commit types to changelog sections
- **`tag_pattern`**: Regex for matching version tags (e.g., `v0.1.0`)

### Customizing Sections

To add or modify sections, edit `commit_parsers` in `cliff.toml`:

```toml
commit_parsers = [
  { message = "^feat", group = "<!-- 0 -->Added" },
  { message = "^fix", group = "<!-- 1 -->Fixed" },
  { message = "^security", group = "<!-- 2 -->Security" },  # Custom section
  # ... more parsers
]
```

The `<!-- N -->` prefix controls sort order (lower numbers appear first).

## Manual Changelog Generation

### Prerequisites

Install git-cliff:

```bash
# macOS (Homebrew)
brew install git-cliff

# Linux (cargo)
cargo install git-cliff

# Or download from: https://github.com/orhun/git-cliff/releases
```

### Generate Changelog

```bash
# Generate for all commits
git-cliff --output CHANGELOG.md

# Generate for a specific version range
git-cliff --tag v0.2.0 --output CHANGELOG.md

# Preview without writing
git-cliff

# Include unreleased changes
git-cliff --unreleased --output CHANGELOG.md

# Generate since last tag
git-cliff --latest --output CHANGELOG.md
```

### Common Use Cases

**1. Before a Release:**
```bash
# Update changelog with all changes since last release
git-cliff --unreleased --tag v0.2.0 --output CHANGELOG.md
git add CHANGELOG.md
git commit -m "docs: Update changelog for v0.2.0"
git tag v0.2.0
git push --tags
```

**2. Preview Next Release:**
```bash
# See what will be in the next changelog
git-cliff --unreleased
```

**3. Regenerate Entire Changelog:**
```bash
# Rebuild from scratch (use with caution!)
git-cliff --output CHANGELOG.md
```

## Versioning

### Semantic Versioning

The project follows [semver](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features (`feat:` commits)
- **PATCH** (1.0.0 → 1.0.1): Bug fixes (`fix:` commits)

### Version Bumping

**Manual Versioning:**

1. Update `pyproject.toml`:
   ```toml
   [project]
   version = "0.2.0"
   ```

2. Generate changelog:
   ```bash
   git-cliff --tag v0.2.0 --output CHANGELOG.md
   ```

3. Commit and tag:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: Bump version to 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

**Automated Versioning (Future Enhancement):**

Consider adding `release-please` or `semantic-release` for fully automated version bumping and releases.

## Troubleshooting

### Changelog Not Updating

**Problem:** CHANGELOG.md doesn't update after pushing commits.

**Solutions:**
1. Check that commits follow conventional format
2. Verify workflow ran: Go to GitHub Actions tab
3. Check workflow permissions: Ensure `contents: write` is set
4. Review workflow logs for errors

### Missing Commits in Changelog

**Problem:** Some commits don't appear in CHANGELOG.md.

**Causes:**
- Commits don't follow conventional format
- Commits match skip patterns in `cliff.toml`
- Commits are dependency updates (`chore(deps)`)

**Solution:**
```bash
# Test locally to see what's included
git-cliff --verbose

# Check if specific commit is parsed
git log --oneline | grep "<commit-message>"
```

### Duplicate Entries

**Problem:** Changelog has duplicate entries.

**Solution:**
```bash
# Regenerate from scratch
git-cliff --output CHANGELOG.md

# Or manually edit CHANGELOG.md and commit
```

### Workflow Infinite Loop

**Problem:** Workflow keeps triggering itself.

**Prevention:**
- The workflow has `paths-ignore: CHANGELOG.md` to prevent this
- Bot commits use `github-actions[bot]` which can be filtered

**If it happens:**
1. Disable the workflow in GitHub Settings
2. Fix the issue
3. Re-enable workflow

## Best Practices

### Writing Good Commit Messages

✅ **DO:**
- Use conventional commit format
- Write clear, descriptive messages
- Reference issues when applicable
- Keep subject under 50 characters

❌ **DON'T:**
- Use vague messages ("fix stuff", "update code")
- Skip the commit type prefix
- Make commits too granular (combine related changes)

### Examples

**Good:**
```bash
feat: Add support for password-protected PDFs
fix: Resolve Unicode encoding error in HTML parser
docs: Add architecture diagrams to README
test: Add unit tests for metadata extraction
refactor: Extract chapter detection to separate module
perf: Optimize image extraction for large EPUBs
```

**Bad:**
```bash
WIP
Fixed bug
Update
Changes
asdf
```

### Commit Hygiene

1. **One logical change per commit**: Each commit should represent a single logical change
2. **Working code**: Don't commit broken code
3. **Descriptive messages**: Future you will thank you
4. **Reference issues**: Link commits to GitHub issues when relevant

## Advanced Usage

### Custom Sections

Add custom changelog sections by editing `cliff.toml`:

```toml
commit_parsers = [
  { message = "^feat", group = "<!-- 0 -->Added" },
  { message = "^deprecated", group = "<!-- 1 -->Deprecated" },  # Custom
  { message = "^removed", group = "<!-- 2 -->Removed" },        # Custom
  { message = "^fix", group = "<!-- 3 -->Fixed" },
  # ...
]
```

### Filtering Commits

**Skip certain commits:**
```toml
commit_parsers = [
  { message = "^chore\\(release\\)", skip = true },
  { message = "^WIP", skip = true },
  # ...
]
```

**Filter by author:**
```toml
[git]
commit_preprocessors = [
  { pattern = 'Author: dependabot.*', skip = true },
]
```

### Release Notes

Generate release notes for GitHub Releases:

```bash
# Get changes for latest tag
git-cliff --latest --strip header

# Get changes between two tags
git-cliff v0.1.0..v0.2.0 --strip header
```

## Integration with Other Tools

### Pre-commit Hooks

Validate commit messages before committing:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v2.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

### Release Automation

Combine with GitHub Releases:

```yaml
# .github/workflows/release.yml
- name: Generate Release Notes
  run: |
    git-cliff --latest --strip header > RELEASE_NOTES.md

- name: Create GitHub Release
  uses: softprops/action-gh-release@v1
  with:
    body_path: RELEASE_NOTES.md
    files: dist/*
```

## Resources

- **git-cliff Documentation**: https://git-cliff.org/docs/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Keep a Changelog**: https://keepachangelog.com/
- **Semantic Versioning**: https://semver.org/
- **Project Commit Guide**: `GIT_COMMIT_STYLE_GUIDE.md` (in this repo)

## Support

For issues with changelog automation:

1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Test locally with `git-cliff --verbose`
4. Open an issue on GitHub

---

**Remember**: Good commit messages lead to good changelogs! 🚀
