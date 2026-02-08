# v4 Update Instructions

## Files Changed in v4

Only 2 files changed:
1. `main.py` - Now analyzes Instagram version instead of big version
2. `src/metadata_manager.py` - Added analyzed_from parameter

## How to Update

### Option 1: Using these individual files

```bash
# Navigate to your existing art-processor folder
cd /path/to/your/art-processor

# Copy the two changed files (adjust paths as needed)
cp ~/Downloads/main.py .
cp ~/Downloads/metadata_manager.py src/

# Optional: add changelog
cp ~/Downloads/CHANGELOG.md .
```

Your `.env`, `venv/`, and all other files remain unchanged.

### Option 2: Quick test

If you want to verify the files work before replacing:

```bash
# Make backup of current files
cp main.py main.py.backup
cp src/metadata_manager.py src/metadata_manager.py.backup

# Copy new files
cp ~/Downloads/main.py .
cp ~/Downloads/metadata_manager.py src/

# Test it
python main.py process

# If something goes wrong, restore:
cp main.py.backup main.py
cp src/metadata_manager.py.backup src/metadata_manager.py
```

## What Changed

**main.py:**
- Lines 139-148: Added logic to prefer Instagram version for AI analysis
- Lines 176-182: Uses `analyze_file` instead of `big_file`
- Line 221: Passes `analyzed_from` parameter to metadata

**src/metadata_manager.py:**
- Line 43: Added `analyzed_from` parameter
- Line 98: Uses parameter instead of hardcoded "big"
- Updated docstring

## Verification

After updating, run:
```bash
python main.py verify-config
```

Then test with one painting to confirm it works.
