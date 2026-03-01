# Theo-van-Gogh Architecture

## Overview

Art management automation system for artists. Generates AI-powered metadata for paintings, uploads artwork to gallery websites, and posts to social media platforms with scheduling support.

**Stack:** Python 3.12, Click CLI, Rich terminal UI, Anthropic Claude API, Playwright browser automation

## Three-Phase Design

- **Phase 1 (complete):** AI metadata generation — Claude vision analyzes paintings, generates titles and descriptions
- **Phase 2 (complete):** Gallery uploads — automated FASO website uploads via browser
- **Phase 3 (current):** Social media management — post to multiple platforms with scheduling

## Project Structure

```
theo-van-gogh/
├── main.py                          # CLI entry point (Click commands)
├── config/
│   ├── settings.py                  # All paths, credentials, extensible lists
│   └── prompts.py                   # AI prompt templates
├── src/
│   ├── image_analyzer.py            # Claude vision API (titles + descriptions)
│   ├── file_manager.py              # File pairing, renaming, EXIF extraction
│   ├── metadata_manager.py          # JSON + text metadata creation/loading
│   ├── file_organizer.py            # Move files to collection folders
│   ├── cli_interface.py             # Rich-based interactive prompts
│   ├── admin_mode.py                # Interactive settings editor (16 options)
│   ├── collection_folder_manager.py # Collection folder sync
│   ├── skeleton_metadata_generator.py # Stub metadata for existing paintings
│   ├── metadata_editor.py           # Interactive metadata editing
│   ├── instagram_folder_sync.py     # Sync instagram folder structure
│   ├── upload_tracker.py            # Legacy tracker (being replaced)
│   ├── faso_client.py               # FASO session/API handling
│   ├── faso_uploader.py             # FASO browser automation + form filling
│   ├── migrate_tracking.py          # Migration: upload_status.json → metadata
│   ├── social/                      # Social media platform framework
│   │   ├── __init__.py              # Platform registry (lazy loading)
│   │   ├── base.py                  # SocialPlatform ABC, PostResult
│   │   ├── formatter.py             # Universal post text builder
│   │   ├── scheduler.py             # Scheduled post management + cron
│   │   ├── cli.py                   # Interactive posting/scheduling CLI
│   │   ├── mastodon.py              # Mastodon API (implemented)
│   │   ├── instagram.py             # stub
│   │   ├── facebook.py              # stub
│   │   ├── bluesky.py               # stub
│   │   ├── linkedin.py              # stub
│   │   ├── tiktok.py                # stub
│   │   ├── youtube.py               # stub
│   │   ├── cara.py                  # stub
│   │   ├── threads.py               # stub
│   │   └── pixelfed.py              # stub
│   └── galleries/                   # Gallery website framework
│       ├── __init__.py              # Gallery registry
│       ├── base.py                  # GalleryPlatform ABC, UploadResult
│       └── faso.py                  # FASO gallery wrapper
├── tests/                           # pytest (189 tests, >40% coverage)
├── manual_login.py                  # One-time FASO browser login helper
└── explore_faso.py                  # FASO form field discovery tool
```

## Data Layout

```
~/ai-workzone/
├── my-paintings-big/                # Full-resolution paintings
│   ├── new-paintings/               # Unprocessed (input)
│   ├── oil-paintings/               # Organized by collection
│   ├── abstracts-quantum-cubes/
│   └── ...
├── my-paintings-instagram/          # Social-sized paintings (same structure)
├── processed-metadata/              # Metadata JSON + text files
│   ├── schedule.json                # Scheduled social media posts
│   ├── upload_status.json           # Legacy tracker (deprecated)
│   ├── oil-paintings/
│   │   ├── painting_name.json       # Per-painting metadata
│   │   └── painting_name.txt
│   └── ...
└── videos/                          # Short videos (<2 min, future)

~/.config/theo-van-gogh/
├── cookies/
│   ├── faso_browser_profile/        # Persistent Chromium profile for FASO
│   └── faso_cookies.json
└── debug/
    ├── screenshots/
    └── logs/
```

## Painting Metadata Schema

Each painting has a JSON file in `processed-metadata/<collection>/`:

```json
{
  "filename_base": "chromatic_entropy",
  "category": "fire-stars",
  "files": {
    "big": "/path/to/big/chromatic_entropy.jpg",
    "instagram": "/path/to/instagram/chromatic_entropy.jpg"
  },
  "title": {
    "selected": "Chromatic Entropy",
    "all_options": ["Option 1", "Option 2", "..."]
  },
  "description": "AI-generated gallery description...",
  "dimensions": { "width": 60.0, "height": 80.0, "depth": null, "unit": "cm", "formatted": "60cm x 80cm" },
  "substrate": "canvas",
  "medium": "oil",
  "subject": "abstract",
  "style": "abstract",
  "collection": "Fire Stars",
  "price_eur": 500.0,
  "creation_date": "2025-07-20",
  "processed_date": "2025-07-20T14:30:00",
  "analyzed_from": "instagram",
  "gallery_sites": {
    "faso": { "last_uploaded": "2026-02-10T10:00:00", "url": null }
  },
  "social_media": {
    "mastodon":  { "last_posted": null, "post_url": null, "post_count": 0 },
    "instagram": { "last_posted": null, "post_url": null, "post_count": 0 },
    "facebook":  { "last_posted": null, "post_url": null, "post_count": 0 },
    "bluesky":   { "last_posted": null, "post_url": null, "post_count": 0 },
    "linkedin":  { "last_posted": null, "post_url": null, "post_count": 0 },
    "tiktok":    { "last_posted": null, "post_url": null, "post_count": 0 },
    "youtube":   { "last_posted": null, "post_url": null, "post_count": 0 },
    "cara":      { "last_posted": null, "post_url": null, "post_count": 0 },
    "threads":   { "last_posted": null, "post_url": null, "post_count": 0 },
    "pixelfed":  { "last_posted": null, "post_url": null, "post_count": 0 }
  }
}
```

## Two Platform Categories

### Gallery Sites (`src/app/galleries/`)
Full portfolio/sales websites where artwork is displayed and managed.

- **Purpose:** Display all art, handle sales, detailed listings
- **Tracking:** `gallery_sites` in metadata — `last_uploaded` timestamp (one-time uploads)
- **Current:** FASO (browser automation via Playwright)
- **Future:** Singular Art, WordPress

```python
class GalleryPlatform(ABC):
    def upload_artwork(self, metadata) -> UploadResult
    def is_configured(self) -> bool
```

### Social Media (`src/social/`)
Promotional platforms for audience engagement and driving traffic.

- **Purpose:** Promotion, sharing, audience building
- **Tracking:** `social_media` in metadata — `last_posted` + `post_count` (can re-post)
- **Current:** Mastodon (REST API, no external dependencies)
- **Future:** Instagram, Facebook, Bluesky, LinkedIn, TikTok, YouTube, Cara, Threads, Pixelfed

```python
class SocialPlatform(ABC):
    def post_image(self, image_path, text, alt_text) -> PostResult
    def post_video(self, video_path, text) -> PostResult
    def verify_credentials(self) -> bool
    def is_configured(self) -> bool
```

### Adding a New Platform

1. Create `src/app/social/newplatform.py` implementing `SocialPlatform`
2. Add to registry in `src/app/social/__init__.py`
3. Add platform name to `SOCIAL_MEDIA_PLATFORMS` list in `src/app/social/base.py`
4. Add credentials to `config/settings.py` + `.env`

That's it — the CLI, scheduler, and metadata tracking work automatically.

## Social Media Post Format

Same format across all platforms:

```
Painting Title

Short description (~75 words max)

#art #artforsale #subject
artbychristopherrehm.com
```

Built by `src/social/formatter.py`. Uses instagram-sized image (smaller, optimized for social).

## Scheduling System

**Schedule file:** `~/ai-workzone/processed-metadata/schedule.json`

```json
{
  "scheduled_posts": [
    {
      "id": "a1b2c3",
      "content_type": "painting",
      "content_id": "chromatic_entropy",
      "metadata_path": "/path/to/metadata.json",
      "platform": "mastodon",
      "scheduled_time": "2026-02-15T10:00:00",
      "status": "pending",
      "post_url": null,
      "error": null,
      "created_at": "2026-02-11T15:00:00"
    }
  ]
}
```

**Cron integration:** `python main.py check-schedule` runs every 5 minutes, executes due posts, updates metadata tracking.

## CLI Commands

```
python main.py                  # Interactive startup (admin mode prompt)
python main.py process          # Process new paintings (Phase 1)
python main.py admin            # Admin mode menu (16 options)
python main.py upload-faso      # Upload to FASO gallery
python main.py post-social      # Post to social media
python main.py schedule-post    # Schedule a future post
python main.py check-schedule   # Execute due scheduled posts (cron)
python main.py verify-config    # Check configuration
python main.py list-categories  # Show painting categories
```

## Admin Menu Options

```
 1. Edit Anthropic API Key
 2. Edit File Paths
 3. Edit Dimension Unit (cm/in)
 4. Add to Lists (Substrates, Mediums, etc.)
 5. Manage Social Media Platforms
 6. Sync Collection Folders
 7. View Current Settings
 8. Generate Skeleton Metadata
 9. Edit Metadata
10. Sync Instagram Folders
11. Upload to FASO
12. Find Painting
13. Post to Social Media
14. Schedule Posts
15. View Schedule
16. Migrate Tracking Data
```

## Configuration

All in `config/settings.py`, loaded from `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Gallery sites
FASO_EMAIL=your@email.com
FASO_PASSWORD=your-password

# Social media
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=yourtoken

# Paths (defaults shown, override as needed)
PAINTINGS_BIG_PATH=~/ai-workzone/my-paintings-big
PAINTINGS_INSTAGRAM_PATH=~/ai-workzone/my-paintings-instagram
METADATA_OUTPUT_PATH=~/ai-workzone/processed-metadata
VIDEOS_PATH=~/ai-workzone/videos
```

## Key Design Decisions

- **No external HTTP dependencies** — Mastodon client uses `urllib.request` (stdlib)
- **Tracking in metadata files** — each painting's JSON is the source of truth for upload/post history
- **Platform stubs** — unimplemented platforms are visible in the system, raise `NotImplementedError`
- **Lazy platform loading** — platform classes imported on demand, not at startup
- **Persistent browser profiles** — FASO uses Chromium persistent context (survives Cloudflare)
- **Same post format everywhere** — one formatter, consistent branding across all social media
- **Post count tracking** — social media posts can be repeated for promotion
- **Cron-based scheduling** — simple, reliable, no daemon process needed
