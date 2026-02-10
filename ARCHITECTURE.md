# Theo-van-Gogh Modular Architecture

## Overview
All file paths are centralized in `config/settings.py` for easy configuration and maximum modularity.

## Path Configuration Hierarchy

### Base Paths (User-Configurable via .env)
```python
PAINTINGS_BIG_PATH = ~/ai-workzone/my-paintings-big
PAINTINGS_INSTAGRAM_PATH = ~/ai-workzone/my-paintings-instagram
METADATA_OUTPUT_PATH = ~/ai-workzone/processed-metadata
```

### Derived Paths (Automatically Generated)
```python
# Upload tracking
UPLOAD_TRACKER_PATH = ~/ai-workzone/processed-metadata/upload_status.json

# Browser cookies
COOKIES_DIR = ~/.config/theo-van-gogh/cookies/
FASO_COOKIES_PATH = ~/.config/theo-van-gogh/cookies/faso_cookies.json
INSTAGRAM_COOKIES_PATH = ~/.config/theo-van-gogh/cookies/instagram_cookies.json

# Debug files
DEBUG_DIR = ~/.config/theo-van-gogh/debug/
SCREENSHOTS_DIR = ~/.config/theo-van-gogh/debug/screenshots/
LOGS_DIR = ~/.config/theo-van-gogh/debug/logs/
```

## Modular Design Principles

### 1. Single Source of Truth
All paths come from `config/settings.py`. No hardcoded paths anywhere else.

### 2. Module Independence
Each module (FASO, Instagram, Email) is self-contained:
```python
# Example module structure
from config.settings import FASO_COOKIES_PATH, SCREENSHOTS_DIR

class FASOUploader:
    def __init__(self):
        # Uses paths from settings
        self.cookies_file = FASO_COOKIES_PATH
        # No hardcoded paths!
```

### 3. Easy Configuration
Change any path in one place (`settings.py` or `.env`):
```bash
# .env file
PAINTINGS_BIG_PATH=~/my-custom-location/big
COOKIES_DIR=~/my-custom-location/cookies
```

### 4. No Path Breaking Changes
Adding new modules doesn't require changing existing code:
- Instagram module imports settings, works immediately
- Email module imports settings, works immediately
- Existing modules continue working unchanged

## File Organization

```
Project Structure:
~/ai-workzone/
├── my-paintings-big/
│   ├── new-paintings/           # Unprocessed
│   ├── oil-paintings/           # Organized by collection
│   ├── abstracts/
│   └── ...
├── my-paintings-instagram/
│   └── (same structure)
└── processed-metadata/
    ├── upload_status.json       # MOVED HERE (was in project root)
    ├── new-paintings/
    ├── oil-paintings/
    └── ...

~/.config/theo-van-gogh/
├── cookies/
│   ├── faso_cookies.json
│   └── instagram_cookies.json
└── debug/
    ├── screenshots/
    │   ├── debug_after_login.png
    │   ├── add_artwork_form.png
    │   └── ...
    └── logs/
        └── (future log files)
```

## Updated Modules

### ✅ Modified for Centralized Paths:
1. **config/settings.py** - Added all derived paths
2. **src/upload_tracker.py** - Uses UPLOAD_TRACKER_PATH
3. **src/faso_client.py** - Uses FASO_COOKIES_PATH, SCREENSHOTS_DIR
4. **main.py** - Uses UPLOAD_TRACKER_PATH
5. **manual_login.py** - Uses FASO_COOKIES_PATH

### 📝 Future Modules (Already Compatible):
- **src/instagram_uploader.py** - Will use INSTAGRAM_COOKIES_PATH
- **src/facebook_uploader.py** - Will use paths from settings
- **src/email_sender.py** - Will use paths from settings

## Benefits

### For Development:
- ✅ Add new modules without touching existing code
- ✅ Change paths in one place
- ✅ Test with different configurations easily
- ✅ Debug files organized in one location

### For Users:
- ✅ Customize paths via .env file
- ✅ Backup/restore just the data folders
- ✅ Clear separation of data, config, and debug files

### For Maintenance:
- ✅ Find all paths in one file
- ✅ No scattered hardcoded paths
- ✅ Easy to add new path types
- ✅ Version control friendly (.env not committed)

## Migration Notes

### What Changed:
- `upload_status.json`: Project root → `~/ai-workzone/processed-metadata/`
- `faso_cookies.json`: Project root → `~/.config/theo-van-gogh/cookies/`
- Screenshots: Project root → `~/.config/theo-van-gogh/debug/screenshots/`

### Backward Compatibility:
Old files in project root won't break anything, they just won't be used. The new system creates and uses the new locations.

## Adding New Modules

### Template for New Upload Module:
```python
# src/new_platform_uploader.py

from config.settings import (
    METADATA_OUTPUT_PATH,
    UPLOAD_TRACKER_PATH,
    COOKIES_DIR,
    SCREENSHOTS_DIR
)

class NewPlatformUploader:
    def __init__(self):
        # All paths from settings
        self.cookies_file = COOKIES_DIR / "newplatform_cookies.json"
        self.screenshot_dir = SCREENSHOTS_DIR
        # No hardcoded paths!
    
    def upload(self, painting_metadata):
        # Implementation...
        pass
```

That's it! No other files need to change.

## Configuration Override Examples

### Via .env:
```bash
# Custom painting location
PAINTINGS_BIG_PATH=/mnt/external-drive/paintings

# Custom debug location
DEBUG_DIR=/tmp/theo-van-gogh-debug

# Custom cookies location (for shared network drive)
COOKIES_DIR=/mnt/network-drive/cookies
```

### Via settings.py:
Just edit the defaults in `config/settings.py`.

## Next Steps

When adding new features:
1. Add any new paths to `settings.py`
2. Import paths in your module
3. Use the imported paths
4. Done! No other changes needed.
