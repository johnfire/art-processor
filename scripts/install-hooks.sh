#!/bin/bash
# Install git hooks from git-hooks/ into .git/hooks/ as symlinks.
# Re-running this script is safe — it will overwrite existing hooks.
#
# Run from the project root:
#   bash testing-scripts/install-hooks.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_SOURCE="$REPO_ROOT/git-hooks"
HOOKS_TARGET="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_SOURCE" ]; then
    echo "Error: git-hooks/ directory not found at $HOOKS_SOURCE"
    exit 1
fi

echo "Installing git hooks..."
echo "  Source : $HOOKS_SOURCE"
echo "  Target : $HOOKS_TARGET"
echo ""

for hook in "$HOOKS_SOURCE"/*; do
    name=$(basename "$hook")
    target="$HOOKS_TARGET/$name"

    chmod +x "$hook"
    ln -sf "$hook" "$target"
    echo "  ✓  $name"
done

echo ""
echo "Done. Hooks are now active for this repository."
echo "To uninstall, delete the symlinks in .git/hooks/"
