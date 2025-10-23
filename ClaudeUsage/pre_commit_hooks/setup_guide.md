# Git Pre-Commit Hooks Setup Guide

## Overview

Git hooks are scripts that automatically run at specific points in your Git workflow. They help maintain code quality, enforce standards, and catch issues before they enter your repository. This guide covers installing and using the pre-commit hooks provided in this template.

## Quick Reference

```bash
# Copy hooks to your project
cp ClaudeUsage/pre_commit_hooks/commit-msg .git/hooks/
cp ClaudeUsage/pre_commit_hooks/pre-commit .git/hooks/

# Make them executable
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit

# Test without committing
.git/hooks/pre-commit
```

## What Are Git Hooks

Git hooks are executable scripts that Git runs automatically when certain events occur:

- **pre-commit**: Runs before a commit is created (code quality checks)
- **commit-msg**: Validates commit message format
- **pre-push**: Runs before pushing to remote (comprehensive tests)
- **post-commit**: Runs after a commit is created (notifications)

Hooks live in `.git/hooks/` and must be executable. They exit with code 0 (success) or non-zero (failure) to allow or block the Git operation.

## Installation and Activation

### Approach 1: Manual Installation

```bash
# Navigate to your project root
cd /path/to/your/project

# Copy hook scripts
cp /path/to/hook-script .git/hooks/hook-name

# Make executable
chmod +x .git/hooks/hook-name
```

### Approach 2: Using This Template

```bash
# From your project root
# Copy all hooks at once
cp ClaudeUsage/pre_commit_hooks/commit-msg .git/hooks/
cp ClaudeUsage/pre_commit_hooks/pre-commit .git/hooks/

# Make them executable
chmod +x .git/hooks/*

# Verify installation
ls -l .git/hooks/
```

### Testing Your Installation

```bash
# Test pre-commit hook directly
.git/hooks/pre-commit

# Test commit-msg hook with sample message
echo "test commit message" | .git/hooks/commit-msg .git/COMMIT_EDITMSG

# Make a test commit to verify
git add .
git commit -m "Test: verify hooks are working"
```

## Available Hooks in This Template

### commit-msg Hook
Validates commit message format according to project standards:
- Checks for proper action verbs (Add, Update, Fix, etc.)
- Validates message structure
- Ensures Co-Authored-By line is present

### pre-commit Hook
Runs code quality checks before allowing commit:
- **Black**: Python code formatting
- **Ruff**: Fast Python linting
- Automatically formats code when possible
- Blocks commit if critical issues found

See `examples.md` for more hook examples and customization options.

## Hook Execution Order

When you run `git commit`:

1. **pre-commit** runs first
   - Checks staged files
   - Runs formatters/linters
   - Exits if critical issues found

2. **commit-msg** runs next
   - Validates commit message
   - Checks format and structure
   - Can modify message automatically

3. **post-commit** runs last (if present)
   - Runs after commit succeeds
   - Cannot prevent commit
   - Used for notifications

## Testing Hooks

### Run Hooks Manually

```bash
# Test pre-commit on staged files
.git/hooks/pre-commit

# Test commit-msg validation
echo "Invalid message" > test_msg.txt
.git/hooks/commit-msg test_msg.txt
rm test_msg.txt
```

### Test Full Workflow

```bash
# Stage a Python file with issues
echo "x=1+2" > test.py
git add test.py

# Try to commit (pre-commit should format it)
git commit -m "Test: checking pre-commit hook"

# Check if file was formatted
cat test.py  # Should show: x = 1 + 2
```

### Bypass Hooks (Use Sparingly)

```bash
# Skip all hooks for this commit
git commit --no-verify -m "Emergency fix"

# Only use when:
# - Emergency production fixes needed
# - Hook is malfunctioning
# - Intentional policy override
```

## Troubleshooting

### Hook Not Running

```bash
# Check if hook exists
ls -l .git/hooks/

# Verify it's executable
chmod +x .git/hooks/pre-commit

# Check for syntax errors
bash -n .git/hooks/pre-commit
```

### Permission Denied

```bash
# Fix permissions
chmod +x .git/hooks/*

# Verify
ls -l .git/hooks/
```

### Hook Fails Unexpectedly

```bash
# Run with debug output
bash -x .git/hooks/pre-commit

# Check Python/UV availability
which python3
which uv
which black
which ruff
```

### Failed Quality Checks

```bash
# Run tools manually to see full output
black --check .
ruff check .

# Fix issues
black .
ruff check --fix .

# Try commit again
git commit -m "Your message"
```

## Integration with UV and Python Projects

### Using UV in Hooks

```bash
# Install tools via UV
uv pip install black ruff

# Or use UV run in hooks
uv run black .
uv run ruff check .
```

### Environment Considerations

Hooks run in Git's environment, not your shell's:
- May not have your virtualenv active
- PATH might be limited
- Use absolute paths or UV for reliability

```bash
# Good: Uses UV to ensure tools available
uv run black "$file"

# Good: Absolute path
/usr/local/bin/black "$file"

# Risky: Depends on PATH
black "$file"
```

## Related Guides

- **git_commit_guide.md**: Commit message standards and workflow
- **code_quality.md**: Code quality tools and standards
- **examples.md**: Additional hook examples and customization
