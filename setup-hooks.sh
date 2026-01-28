#!/bin/bash

# Define paths
HOOK_DIR=".git/hooks"
PRE_COMMIT_HOOK="$HOOK_DIR/pre-commit"
SOURCE_HOOK="backend/hooks/pre_commit.py"

# Ensure .git/hooks exists
if [ ! -d "$HOOK_DIR" ]; then
    echo "❌ Error: .git directory not found. Are you in the repo root?"
    exit 1
fi

# Check if pre-commit already exists
if [ -f "$PRE_COMMIT_HOOK" ]; then
    echo "⚠️  A pre-commit hook already exists. Backing it up to pre-commit.bak"
    mv "$PRE_COMMIT_HOOK" "$PRE_COMMIT_HOOK.bak"
fi

# Copy the python script to .git/hooks/pre-commit
cp "$SOURCE_HOOK" "$PRE_COMMIT_HOOK"

# Make it executable
chmod +x "$PRE_COMMIT_HOOK"

echo "✅ Guardrails pre-commit hook installed successfully!"
echo "   Try committing a file with a secret (e.g. 'password = \"123\"') to test it."
