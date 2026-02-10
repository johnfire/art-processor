# v9 Modular Architecture - Installation Guide

## What Changed

**Major architectural improvement:** All file paths are now centralized in `config/settings.py` for maximum modularity.

## Key Changes

### 1. Updated Paths in settings.py
- Base paths use `~/ai-workzone/` instead of `~/Pictures/`
- Added centralized paths for cookies, debug files, screenshots
- All directories auto-created on startup

### 2. Moved Files
- `upload_status.json`: Project root → `~/ai-workzone/processed-metadata/`
- `faso_cookies.json`: Project root → `~/.config/theo-van-gogh/cookies/`
- Screenshots: Project root → `~/.config/theo-van-gogh/debug/screenshots/`

### 3. Updated Modules
All modules now import paths from settings instead of hardcoding:
- `upload_tracker.py`
- `faso_client.py`
- `main.py`
- `manual_login.py`

## Installation

### 1. Backup Current Data (Optional)
```bash
# If you have existing data in project root:
cp upload_status.json upload_status.json.backup
cp faso_cookies.json faso_cookies.json.backup
```

### 2. Install Updated Files
```bash
cd your-Theo-van-Gogh-folder

# Replace configuration
cp v9-modular-architecture/settings.py config/

# Replace updated modules
cp v9-modular-architecture/upload_tracker.py src/
cp v9-modular-architecture/faso_client.py src/
cp v9-modular-architecture/main.py .
cp v9-modular-architecture/manual_login.py .

# Add architecture docs
cp v9-modular-architecture/ARCHITECTURE.md .
```

### 3. Update Your .env File

**Important:** Update paths in `.env` to match new structure:

```bash
# Edit .env
nano .env

# Change these paths:
PAINTINGS_BIG_PATH=~/ai-workzone/my-paintings-big
PAINTINGS_INSTAGRAM_PATH=~/ai-workzone/my-paintings-instagram
METADATA_OUTPUT_PATH=~/ai-workzone/processed-metadata

# You can customize these if needed:
COOKIES_DIR=~/.config/theo-van-gogh/cookies
DEBUG_DIR=~/.config/theo-van-gogh/debug
```

### 4. Run Once to Create Directories
```bash
python main.py --help
```

This will auto-create all the new directories:
- `~/ai-workzone/processed-metadata/`
- `~/.config/theo-van-gogh/cookies/`
- `~/.config/theo-van-gogh/debug/screenshots/`
- `~/.config/theo-van-gogh/debug/logs/`

### 5. Migrate Existing Data (If Needed)

If you have existing data in old locations:

```bash
# Move upload tracker
mv upload_status.json ~/ai-workzone/processed-metadata/

# Move cookies
mkdir -p ~/.config/theo-van-gogh/cookies
mv faso_cookies.json ~/.config/theo-van-gogh/cookies/
```

## What You Get

### Centralized Configuration
All paths in one place (`config/settings.py`)

### Modular Design
- Each platform (FASO, Instagram, etc.) is self-contained
- Adding new modules doesn't break existing code
- Easy to customize paths

### Better Organization
```
~/ai-workzone/
  ├── my-paintings-big/
  ├── my-paintings-instagram/
  └── processed-metadata/
      └── upload_status.json    ← Moved here

~/.config/theo-van-gogh/
  ├── cookies/
  │   └── faso_cookies.json     ← Moved here
  └── debug/
      └── screenshots/          ← Moved here
```

### Future-Proof
When we add Instagram, Facebook, Email modules:
- They import paths from settings
- No changes to existing code needed
- Everything just works

## Customization

Want different paths? Just edit `.env`:

```bash
# Use external drive for paintings
PAINTINGS_BIG_PATH=/mnt/external/paintings

# Custom debug location
DEBUG_DIR=/tmp/debug

# Shared network cookies
COOKIES_DIR=/mnt/network/cookies
```

## Testing

After installation, verify it works:

```bash
# Should show new paths
python main.py verify-config

# Should create files in new location
python main.py process
```

## Files Included

- `settings.py` - Updated configuration with centralized paths
- `upload_tracker.py` - Uses UPLOAD_TRACKER_PATH
- `faso_client.py` - Uses FASO_COOKIES_PATH and SCREENSHOTS_DIR
- `main.py` - Uses UPLOAD_TRACKER_PATH
- `manual_login.py` - Uses FASO_COOKIES_PATH
- `ARCHITECTURE.md` - Complete architecture documentation

## Backward Compatibility

Old files in project root won't cause errors, they just won't be used. The system creates and uses the new locations automatically.

## Need Help?

See `ARCHITECTURE.md` for complete details on:
- Path hierarchy
- Adding new modules
- Configuration examples
- Design principles
