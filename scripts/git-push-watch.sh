#!/bin/bash
# Push to GitHub, then watch the CI run and fire a desktop notification
# with the result (pass or fail).
#
# Usage (from project root):
#   bash testing-scripts/git-push-watch.sh              # push current branch
#   bash testing-scripts/git-push-watch.sh origin main  # push specific ref
#
# Requires: gh CLI authenticated (GH_TOKEN env var set)

DISPLAY="${DISPLAY:-:0}"

# ── Push ──────────────────────────────────────────────────────────────────────
git push "$@"
PUSH_EXIT=$?

if [ $PUSH_EXIT -ne 0 ]; then
    echo ""
    echo "✗  Push failed — not watching CI."
    exit $PUSH_EXIT
fi

# ── Wait for Actions to register the run ─────────────────────────────────────
echo ""
echo "⏳ Waiting for GitHub Actions to start…"
sleep 6

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "⚠  Could not determine repo name. Is GH_TOKEN set?"
    exit 1
fi

echo "👀 Watching CI for $REPO…"
echo "   (Ctrl-C to stop watching — CI will still run on GitHub)"
echo ""

# ── Get the latest run ID (retry up to 10s for it to register) ───────────────
RUN_ID=""
for i in $(seq 1 5); do
    RUN_ID=$(gh run list --repo "$REPO" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null)
    [ -n "$RUN_ID" ] && break
    sleep 2
done

if [ -z "$RUN_ID" ]; then
    echo "⚠  Could not get run ID from GitHub. Check manually: gh run list"
    exit 1
fi

# ── Watch and notify ─────────────────────────────────────────────────────────
gh run watch "$RUN_ID" --exit-status
CI_EXIT=$?

echo ""

if [ $CI_EXIT -eq 0 ]; then
    notify-send -u normal -i dialog-ok \
        "Theo-van-Gogh CI ✓" "All checks passed on GitHub." 2>/dev/null || true
    echo "✓  CI passed."
else
    notify-send -u critical -i dialog-error \
        "Theo-van-Gogh CI ✗" "CI FAILED on GitHub — check the Actions tab." 2>/dev/null || true
    echo "✗  CI failed. Check: gh run view --web"
fi

exit $CI_EXIT
