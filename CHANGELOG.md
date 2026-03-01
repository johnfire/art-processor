# Theo-van-Gogh Changelog

## v9 - Modular Architecture & Centralized Paths (2025-02-10)

### Major Architectural Changes

**Centralized Path Configuration**
All file paths now managed in `config/settings.py` for maximum modularity and easy configuration.

### New Path Structure

**Base Paths (User Configurable):**
- `PAINTINGS_BIG_PATH` = `~/ai-workzone/my-paintings-big`
- `PAINTINGS_INSTAGRAM_PATH` = `~/ai-workzone/my-paintings-instagram`
- `METADATA_OUTPUT_PATH` = `~/ai-workzone/processed-metadata`

**Derived Paths (Auto-Generated):**
- `UPLOAD_TRACKER_PATH` = `~/ai-workzone/processed-metadata/upload_status.json`
- `COOKIES_DIR` = `~/.config/theo-van-gogh/cookies/`
- `FASO_COOKIES_PATH` = `~/.config/theo-van-gogh/cookies/faso_cookies.json`
- `INSTAGRAM_COOKIES_PATH` = `~/.config/theo-van-gogh/cookies/instagram_cookies.json`
- `SCREENSHOTS_DIR` = `~/.config/theo-van-gogh/debug/screenshots/`
- `LOGS_DIR` = `~/.config/theo-van-gogh/debug/logs/`

### File Migrations

**Moved for Better Organization:**
- `upload_status.json`: Project root → metadata folder
- `faso_cookies.json`: Project root → cookies folder
- Debug screenshots: Project root → screenshots folder

### Updated Modules

**All modules now use centralized paths:**
- ✅ `config/settings.py` - Added path configuration section
- ✅ `src/upload_tracker.py` - Uses UPLOAD_TRACKER_PATH
- ✅ `src/faso_client.py` - Uses FASO_COOKIES_PATH and SCREENSHOTS_DIR
- ✅ `main.py` - Uses UPLOAD_TRACKER_PATH
- ✅ `manual_login.py` - Uses FASO_COOKIES_PATH

### New Documentation

**Added:**
- `ARCHITECTURE.md` - Complete architectural documentation
  - Modular design principles
  - Path hierarchy
  - Adding new modules guide
  - Configuration examples

### Benefits

**For Development:**
- ✅ Add new modules without changing existing code
- ✅ All paths in one file
- ✅ No hardcoded paths anywhere
- ✅ Easy to test with different configurations

**For Users:**
- ✅ Customize all paths via .env
- ✅ Better file organization
- ✅ Easy backup/restore
- ✅ Clear separation of data/config/debug

**For Future:**
- ✅ Instagram module ready to plug in
- ✅ Email module ready to plug in
- ✅ Any new platform follows same pattern

### Migration Notes

**Automatic Directory Creation:**
All new directories are created automatically on first run.

**Backward Compatible:**
Old files in project root won't break anything. New system uses new locations.

**Manual Migration (Optional):**
```bash
# Move existing files to new locations
mv upload_status.json ~/ai-workzone/processed-metadata/
mv faso_cookies.json ~/.config/theo-van-gogh/cookies/
```

### Configuration Override

**Via .env (Recommended):**
```bash
PAINTINGS_BIG_PATH=/your/custom/path
COOKIES_DIR=/your/custom/cookies
DEBUG_DIR=/your/custom/debug
```

**Via settings.py:**
Edit defaults directly in `config/settings.py`

---

## v8 - FASO Login & Navigation (2025-02-08)
- Browser automation for FASO
- Cloudflare handling
- Cookie persistence

## v7 - Testing Infrastructure (2025-02-08)
- pytest framework
- GitHub Actions CI/CD
- 26 initial tests

## v6 - File Organization & Upload Tracking (2025-02-08)
- Collection-based organization
- Upload status tracking
- Platform management

## v5 - Admin Mode (2025-02-08)
- Configuration management UI

## v4 - Instagram Analysis (2025-02-08)
- 5MB limit workaround

## v3 - Simplified Workflow (2025-02-08)
- Hard-coded new-paintings

## v2 - Extended Metadata (2025-02-08)
- Manual dimensions
- Extended fields

## v1 - Initial Release (2025-02-07)
- AI processing
- Metadata generation
