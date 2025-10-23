# Claude Usage Guide Index

This directory contains comprehensive guides for working with Claude on development projects. Each guide is self-contained and focused on specific workflows or technologies.

## Quick Reference

### Core Workflows

| Guide | Description | When to Use |
|-------|-------------|-------------|
| [git_workflow.md](git_workflow.md) | Git operations, commits, branching | Every session with code changes |
| [git_conventional_commits.md](git_conventional_commits.md) | Conventional commit message standards | Writing standardized commit messages |
| [secrets_management.md](secrets_management.md) | API key handling, security patterns | Setting up projects with external APIs |
| [secrets_advanced.md](secrets_advanced.md) | Advanced secrets patterns, rotation, auditing | Enterprise-grade security implementations |
| [house_agents.md](house_agents.md) | Specialized agent usage (research, coding) | Complex searches or multi-file refactoring |
| [subagent_usage.md](subagent_usage.md) | Creating focused task agents | Breaking down large tasks into subtasks |
| [research_workflow.md](research_workflow.md) | Codebase analysis patterns | Understanding unfamiliar codebases |

### Development

| Guide | Description | When to Use |
|-------|-------------|-------------|
| [uv_usage.md](uv_usage.md) | UV package manager workflows | Python dependency management |
| [testing_strategies.md](testing_strategies.md) | Test patterns and frameworks | Writing or debugging tests |
| [code_quality.md](code_quality.md) | Linting, formatting, standards | Setting up quality checks |
| [code_style_guide.md](code_style_guide.md) | General code style principles | Writing clean, maintainable code |
| [project_structure.md](project_structure.md) | Directory layouts, file organization | Starting new projects |
| [project_setup.md](project_setup.md) | Project initialization patterns | Setting up new projects from template |

### Documentation

| Guide | Description | When to Use |
|-------|-------------|-------------|
| [documentation_standards.md](documentation_standards.md) | Writing style, formats, templates | Creating or updating documentation |

### Infrastructure

| Guide | Description | When to Use |
|-------|-------------|-------------|
| [docker_guide.md](docker_guide.md) | Container setup and workflows | Dockerizing applications |
| [ci_cd_patterns.md](ci_cd_patterns.md) | GitHub Actions, automation | Setting up CI/CD pipelines |
| [database_setup.md](database_setup.md) | Database configuration patterns | Working with databases |

### Multi-Language Support

| Guide | Description | When to Use |
|-------|-------------|-------------|
| [multi_language_guide.md](multi_language_guide.md) | Patterns for Python, JavaScript, Go, Rust | Multi-language projects or new languages |

### Pre-commit Hooks

| Guide | Description | When to Use |
|-------|-------------|-------------|
| [pre_commit_hooks/setup_guide.md](pre_commit_hooks/setup_guide.md) | Hook setup and configuration | Enforcing code quality on commit |
| [pre_commit_hooks/examples.md](pre_commit_hooks/examples.md) | Language-specific hook patterns | Configuring hooks for specific tech stacks |

## How to Use These Guides

1. **On-Demand Reference**: Read guides when you need specific knowledge
2. **Self-Contained**: Each guide stands alone with complete information
3. **Cross-Referenced**: Related topics link to each other
4. **Start with TEMPLATE_CLAUDE.md**: Check parent directory for trigger patterns

## Guide Structure

All guides follow a consistent format:

- **Overview**: What the guide covers
- **When to Use**: Specific triggers and scenarios
- **Core Concepts**: Key principles and patterns
- **Practical Examples**: Real-world code and commands
- **Common Pitfalls**: What to avoid
- **Related Guides**: Cross-references to other relevant guides

## Contributing to Guides

When updating guides:
- Keep examples current and tested
- Maintain the scannable format
- Update cross-references when adding new guides
- Follow documentation standards from documentation_standards.md

## Quick Start Checklist

For new projects, reference these guides in order:

1. **project_setup.md** - Initialize project from template
2. **project_structure.md** - Set up directory layout
3. **git_workflow.md** - Initialize version control
4. **git_conventional_commits.md** - Learn commit message standards
5. **secrets_management.md** - Configure API keys
6. **uv_usage.md** (Python) or relevant language guide
7. **pre_commit_hooks/setup_guide.md** - Set up quality checks
8. **testing_strategies.md** - Add test framework
9. **docker_guide.md** (if needed) - Containerize application

---

*Last updated: 2025-10-19*
*Total guides: 18*
