# Git Hook Examples and Advanced Usage

## Overview

This guide provides additional useful hook examples and introduces the pre-commit framework for managing hooks across projects.

---

## Other Useful Hooks

### pre-push Hook
Run tests before pushing to remote:
```bash
#!/bin/bash
echo "Running tests before push..."
pytest tests/ || exit 1
```

### post-checkout Hook
Install dependencies after switching branches:
```bash
#!/bin/bash
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
```

### post-merge Hook
Run database migrations after merging:
```bash
#!/bin/bash
echo "Checking for pending migrations..."
python manage.py migrate --check || python manage.py migrate
```

---

## Testing Hook Example

Complete pre-push hook that runs pytest:

```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Running test suite before push..."
echo "================================"

# Run pytest with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Capture exit code
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Tests failed! Push aborted."
    echo "Fix failing tests before pushing."
    exit 1
fi

echo ""
echo "✅ All tests passed! Proceeding with push."
exit 0
```

---

## Secrets Scanning Hook

Pre-commit hook that blocks commits containing API keys:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Scanning for secrets..."

# Patterns to detect
PATTERNS=(
    "sk-ant-api[0-9a-zA-Z-]+"          # Anthropic keys
    "sk-[a-zA-Z0-9]{32,}"              # OpenAI keys
    "AIza[0-9A-Za-z-_]{35}"            # Google API keys
    "AKIA[0-9A-Z]{16}"                 # AWS Access Keys
    "[a-f0-9]{32}"                     # Generic API tokens
)

# Check staged files
for pattern in "${PATTERNS[@]}"; do
    if git diff --cached | grep -E "$pattern" > /dev/null; then
        echo ""
        echo "❌ SECURITY WARNING: Possible API key detected!"
        echo "Pattern matched: $pattern"
        echo ""
        echo "Please remove secrets and use secrets.json instead."
        exit 1
    fi
done

echo "✅ No secrets detected"
exit 0
```

---

## TODO Tracking Hook

Automatically update TODOS.md based on code comments:

```bash
#!/bin/bash
# .git/hooks/post-commit

echo "Updating TODOS.md from code comments..."

# Find all TODO comments
git grep -n "TODO:" > /tmp/todos.txt 2>/dev/null

if [ -s /tmp/todos.txt ]; then
    echo "" >> TODOS.md
    echo "## Code TODOs (Auto-generated)" >> TODOS.md
    echo "" >> TODOS.md

    while IFS=: read -r file line content; do
        echo "- [ ] $file:$line - $content" >> TODOS.md
    done < /tmp/todos.txt

    echo "✅ TODOS.md updated"
else
    echo "No TODO comments found"
fi

rm -f /tmp/todos.txt
```

---

## Using the pre-commit Framework

### What is pre-commit?

Pre-commit is a Python package that manages git hooks using a configuration file. It provides:
- Centralized hook configuration
- Easy sharing across projects
- Access to community hooks
- Automatic updates

### Installation

```bash
# Using uv (recommended)
uv add --dev pre-commit

# Or using pip
pip install pre-commit

# Install hooks
pre-commit install
```

### Basic Commands

```bash
# Install hooks for the first time
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Update hook versions
pre-commit autoupdate
```

---

## pre-commit Config Example

Complete `.pre-commit-config.yaml`:

```yaml
# .pre-commit-config.yaml
repos:
  # Python code formatting with Black
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  # Python linting with Ruff
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace      # Remove trailing whitespace
      - id: end-of-file-fixer        # Ensure files end with newline
      - id: check-yaml                # Validate YAML syntax
      - id: check-json                # Validate JSON syntax
      - id: check-added-large-files  # Prevent large files
        args: [--maxkb=1000]
      - id: mixed-line-ending        # Prevent mixed line endings
        args: [--fix=lf]

  # Type checking with mypy
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## When to Use Framework vs Custom Scripts

### Use pre-commit Framework When:
- Working with Python projects
- Need standard code quality tools (Black, Ruff, mypy)
- Want to share configuration across projects
- Team collaboration is important
- Need automatic tool updates

### Use Custom Scripts When:
- Project-specific logic required
- Non-standard workflows
- Language-specific tools not in framework
- Simple, one-off hooks
- Want complete control

### Hybrid Approach:
Combine both! Use pre-commit for standard tools, custom scripts for project-specific needs:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  # Custom local hook
  - repo: local
    hooks:
      - id: custom-check
        name: Custom validation
        entry: ./scripts/custom_hook.sh
        language: system
```

---

## Custom Hook Patterns

### Common Structure

```bash
#!/bin/bash
# Hook name and description

# 1. Print what you're doing
echo "Running [hook name]..."

# 2. Perform checks/operations
# ... your logic here ...

# 3. Exit with appropriate code
if [ $? -eq 0 ]; then
    echo "✅ Success message"
    exit 0
else
    echo "❌ Error message"
    echo "Instructions to fix"
    exit 1
fi
```

### Best Practices

1. **Fast execution**: Hooks run frequently, keep them quick
2. **Clear output**: Users should understand what's happening
3. **Actionable errors**: Tell users how to fix issues
4. **Fail gracefully**: Handle missing dependencies
5. **Document behavior**: Add comments explaining logic

### Template

```bash
#!/bin/bash
# Description: [What this hook does]
# When it runs: [pre-commit, pre-push, etc.]

set -e  # Exit on error

HOOK_NAME="[Your Hook Name]"

echo "Running $HOOK_NAME..."

# Main logic
function main() {
    # Your checks here

    if [[ -z "$REQUIRED_VAR" ]]; then
        echo "❌ Error: Missing required configuration"
        return 1
    fi

    # Success
    echo "✅ $HOOK_NAME passed"
    return 0
}

# Run and capture result
main
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Fix the issues above and try again."
fi

exit $EXIT_CODE
```

---

## Related Guides

- [Setup Guide](setup_guide.md) - Initial hook installation
- [Code Quality Guide](code_quality.md) - Code formatting hooks
- [Testing Strategies](testing_strategies.md) - Test-related hooks
