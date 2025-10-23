# Git Workflow Guide

## Overview

A safety-first git workflow emphasizing verification, backups, and clean commit history.

**Core Principles:**
- **Safety First**: Always create backups before major operations
- **Verification**: Confirm changes before committing
- **Clean History**: Write meaningful commit messages (see [git_commit_guide.md](git_commit_guide.md))
- **Containerization**: Safely initialize git repos in existing projects

---

## Quick Reference

```bash
# Check repository status
git status
git diff --stat

# Review history
git log --oneline -5

# Stage and commit
git add .
git commit -m "Message here"

# View changes
git diff                  # Unstaged changes
git diff --cached        # Staged changes

# Undo operations
git restore <file>              # Discard working changes
git restore --staged <file>     # Unstage
git reset HEAD~1                # Undo last commit (keep changes)

# Branch operations
git branch                      # List branches
git checkout -b <new-branch>    # Create and switch
git merge <branch>              # Merge branch

# Stash work
git stash
git stash pop
git stash list
```

---

## Repository Setup

### For Folders WITHOUT Git Repos

#### Step 1: Create Backup

```bash
# Create timestamped backup directory
mkdir ../backup_$(basename $PWD)_$(date +%Y%m%d_%H%M%S)

# Copy all files
cp -r * ../backup_*/

# Verify backup integrity
diff -r . ../backup_*/
```

**Expected**: No output means backup is successful.

#### Step 2: Initialize Git

```bash
git init

# Create .gitignore
cat > .gitignore << 'EOF'
secrets.json
*.log
__pycache__/
.DS_Store
.venv/
EOF

# Stage and commit
git add .
git commit -m "Initial commit: [Project description]"
```

#### Step 3: Clean Up Backup

```bash
# Verify git repo is working
git status
git log --oneline -1

# Remove backup after confirmation
rm -rf ../backup_*
echo "✅ Backup cleaned up"
```

### For Existing Git Repos

```bash
# Check status
git status
git diff --stat

# Review recent commits
git log --oneline -5

# Stage changes
git add .

# Commit (see git_commit_guide.md for message format)
git commit -m "Your message here"

# Verify
git status
git log --oneline -1
```

---

## Commit Message Standards

For detailed formatting, see **[git_commit_guide.md](git_commit_guide.md)**.

**Quick template:**
```
[Action] Brief description

- Specific change 1
- Specific change 2

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Actions**: Add, Update, Fix, Refactor, Remove, Enhance

---

## Branching Strategies

### Feature Branches

```bash
# Create and switch to feature branch
git checkout -b feature/user-auth

# Work and commit
git add .
git commit -m "Add user authentication"

# Switch back to main
git checkout main

# Merge feature
git merge feature/user-auth

# Delete branch
git branch -d feature/user-auth
```

### Branch Naming Conventions

```
feature/feature-name    # New features
fix/bug-description     # Bug fixes
experiment/new-idea     # Experiments
release/v1.0.0         # Releases
```

### Dev/Main Branch Strategy (Optional)

For projects with ongoing development and production releases, consider a two-branch strategy:

**`main` branch** - Production-ready code
- Only receives merges from dev when stable
- Always in deployable state
- Users/clients clone from this branch
- Clean and minimal

**`dev` branch** - Active development
- All development work happens here
- Experimental features and work-in-progress
- Testing and iteration
- Can be messy during active development

**Workflow:**
```bash
# Daily development in dev branch
git checkout dev
git pull origin dev

# Create feature branches off dev
git checkout -b feature/new-feature

# Work and commit
git add .
git commit -m "feat: implement new feature"

# Merge back to dev
git checkout dev
git merge feature/new-feature

# When ready for production
# Test thoroughly, then merge to main
git checkout main
git merge dev
git push origin main

# Continue development in dev
git checkout dev
```

**Benefits:**
- Keeps main clean for users/production
- Development work doesn't clutter production branch
- Can experiment freely in dev
- Clear separation between stable and in-progress work

**When to use:**
- Template repositories (like BaseProject itself)
- Projects with external users cloning the repo
- Applications with production deployments
- Open source projects with stable releases

**When NOT to use:**
- Simple personal projects
- Rapid prototypes
- Single-developer projects without production needs

---

## Handling Merge Conflicts

### Identifying Conflicts

```bash
# Attempt merge
git merge feature-branch

# If conflicts, git shows:
# CONFLICT (content): Merge conflict in file.py

# Check which files conflict
git status
```

### Resolution

**Option 1: Manual resolution**
```bash
# Edit file, resolve conflicts between:
# <<<<<<< HEAD
# Your changes
# =======
# Incoming changes
# >>>>>>> feature-branch

# Stage resolved file
git add file.py

# Complete merge
git commit
```

**Option 2: Accept one side**
```bash
# Accept current branch
git checkout --ours file.py

# Accept incoming branch
git checkout --theirs file.py

# Stage and commit
git add file.py
git commit
```

### Preventing Conflicts

- Pull frequently
- Commit small, focused changes
- Communicate about file ownership
- Keep feature branches short-lived

---

## Stashing Changes

### When to Stash

- Switch branches without committing
- Pull latest changes with uncommitted work
- Quickly test something on clean directory

### Stash Commands

```bash
# Stash current changes
git stash

# Stash with message
git stash push -m "WIP: auth feature"

# List stashes
git stash list

# Apply most recent
git stash pop

# Apply specific stash
git stash apply stash@{1}

# Delete stash
git stash drop stash@{0}
```

---

## Reviewing History

### Git Log

```bash
# Basic log
git log --oneline -10

# Graph view
git log --graph --oneline --all

# Search commits
git log --grep="authentication"

# By author
git log --author="Claude"

# Date range
git log --since="2025-01-01"

# With file changes
git log --stat
```

### Git Diff

```bash
# Working directory changes (unstaged)
git diff

# Staged changes
git diff --cached

# Between commits
git diff abc1234 def5678

# Specific file
git diff file.py

# Summary
git diff --stat
```

### Finding Changes

```bash
# When line was changed
git log -S "function_name" --source --all

# File history
git log --follow -- path/to/file.py

# Who changed each line
git blame file.py
```

---

## Undoing Changes

### Git Restore (Recommended)

```bash
# Discard working changes
git restore file.py

# Discard all changes
git restore .

# Unstage file
git restore --staged file.py

# Restore from specific commit
git restore --source=abc1234 file.py
```

### Git Reset (Use Carefully)

```bash
# Undo last commit, keep changes staged
git reset --soft HEAD~1

# Undo last commit, keep changes unstaged
git reset HEAD~1

# Undo last commit, discard changes (DANGEROUS)
git reset --hard HEAD~1
```

**Warning**: Never use `--hard` on pushed commits.

### Git Revert (Safe for Shared History)

```bash
# Create new commit undoing changes
git revert abc1234

# Revert without committing
git revert --no-commit abc1234
```

---

## Common Workflows

### Daily Development

```bash
# Start of day
git pull origin main

# Create feature branch
git checkout -b feature/today-work

# Work and commit frequently
git add file.py
git commit -m "Add initial structure"

# More work
git add .
git commit -m "Implement core logic"

# Merge back at end of day
git checkout main
git merge feature/today-work
git branch -d feature/today-work
```

### Experimental Changes

```bash
# Save current work
git stash push -m "Current progress"

# Create experiment branch
git checkout -b experiment/new-approach

# Try experimental code
# ...

# If successful, merge
git checkout main
git merge experiment/new-approach

# If failed, discard
git checkout main
git branch -D experiment/new-approach

# Restore original work
git stash pop
```

---

## Troubleshooting

### "Detached HEAD state"

```bash
# Create branch from current state
git checkout -b recovery-branch

# Or return to main
git checkout main
```

### Committed to Wrong Branch

```bash
# Note commit hash
git log --oneline -1  # abc1234

# Switch to correct branch
git checkout correct-branch
git cherry-pick abc1234

# Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1
```

### Committed Secrets

```bash
# If NOT pushed yet
git reset --hard HEAD~1

# If already pushed
# 1. Rotate secrets immediately
# 2. Use BFG Repo-Cleaner or git-filter-branch
# 3. Force push (coordinate with team)
```

### Lost Commits

```bash
# Git keeps deleted commits for ~30 days
git reflog

# Find lost commit
# abc1234 HEAD@{5}: commit: My lost work

# Recover
git checkout abc1234
git checkout -b recovery-branch
```

---

## Repository Publishing

**Note**: The user handles `git push` operations. Claude focuses on local commits and version control.

```bash
# Typical push workflow (user-managed)
git push origin main
git push origin feature-branch
git push --tags
```

---

## Related Guides

- **[git_commit_guide.md](git_commit_guide.md)** - Commit message formatting
- **[git_conventional_commits.md](git_conventional_commits.md)** - Conventional Commits format
- **[house_agents.md](house_agents.md)** - Using house-git for large operations
- **[secrets_management.md](secrets_management.md)** - Keeping secrets out of version control

---

*Last updated: 2025-10-19*
