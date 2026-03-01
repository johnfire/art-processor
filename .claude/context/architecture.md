# System Architecture — Theo-van-Gogh

Art management automation system for working artists. Three-phase design:

- **Phase 1 (complete):** AI metadata generation — Claude vision analyzes paintings, generates titles and descriptions
- **Phase 2 (complete):** Gallery uploads — automated FASO website uploads via Playwright
- **Phase 3 (current):** Social media management — post to multiple platforms with scheduling

## Project Layout

```
theo-van-gogh/
├── main.py                          # CLI entry point (Click commands) — stays at root
├── manual_login.py                  # One-time FASO browser login helper
├── explore_faso.py                  # FASO form field discovery tool
├── config/
│   ├── settings.py                  # All paths, credentials, extensible lists
│   └── prompts.py                   # AI prompt templates
├── src/
│   ├── core/
│   │   └── logger.py                # Centralised logger factory (get_logger, configure_logging)
│   ├── app/
│   │   ├── services/                # Core business logic
│   │   │   ├── image_analyzer.py    # Claude vision API (titles + descriptions)
│   │   │   ├── metadata_manager.py  # JSON + text metadata creation/loading
│   │   │   ├── metadata_editor.py   # Interactive metadata editing
│   │   │   ├── skeleton_metadata_generator.py
│   │   │   ├── file_manager.py      # File pairing, renaming, EXIF extraction
│   │   │   ├── file_organizer.py    # Move files to collection folders
│   │   │   ├── cli_interface.py     # Rich-based interactive prompts
│   │   │   ├── admin_mode.py        # Interactive settings editor (17 options)
│   │   │   ├── collection_folder_manager.py
│   │   │   ├── instagram_folder_sync.py
│   │   │   ├── upload_tracker.py    # Legacy tracker
│   │   │   ├── migrate_tracking.py  # upload_status.json → metadata migration
│   │   │   ├── activity_log.py
│   │   │   └── login_tracker.py
│   │   ├── galleries/               # Gallery platform framework + implementations
│   │   │   ├── __init__.py          # Gallery registry (lazy loading)
│   │   │   ├── base.py              # GalleryPlatform ABC, UploadResult
│   │   │   ├── browser_uploader.py  # BaseBrowserUploader ABC (shared Playwright)
│   │   │   ├── faso.py              # FASO registry wrapper
│   │   │   ├── faso_uploader.py     # FASO browser automation + form filling
│   │   │   └── faso_client.py       # FASO session handling
│   │   └── social/                  # Social platform framework + implementations
│   │       ├── __init__.py          # Platform registry (lazy loading)
│   │       ├── base.py              # SocialPlatform ABC, PostResult
│   │       ├── formatter.py         # Universal post text builder
│   │       ├── scheduler.py         # Scheduled post management
│   │       ├── cli.py               # Interactive posting/scheduling CLI
│   │       ├── post_logger.py
│   │       ├── daily_poster.py
│   │       ├── mastodon.py          # implemented
│   │       ├── bluesky.py           # implemented
│   │       ├── pixelfed.py          # implemented
│   │       ├── cara.py              # implemented
│   │       ├── flickr.py            # implemented
│   │       ├── upscrolled.py        # stub (no API yet, check ~2026-04-22)
│   │       └── [9 other stubs]
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/                        # Isolated, no I/O
│   ├── integration/                 # Cross-module / real file tests
│   └── e2e/                         # BDD scenarios (pytest-bdd)
│       └── features/                # Gherkin .feature files
├── scripts/                         # Dev utilities
├── docs/
│   ├── architecture/                # System design docs
│   ├── deployment/                  # Setup + operations runbooks
│   ├── guides/                      # How-to guides
│   └── changelog/
└── .claude/                         # Claude Code context
    ├── CLAUDE.md                    # Primary AI guide
    ├── context/                     # This directory
    └── commands/                    # Custom slash commands
```

## Data Layout

```
~/ai-workzone/
├── my-paintings-big/                # Full-resolution paintings
│   ├── new-paintings/               # Unprocessed input
│   └── <collection>/               # Organised by collection
├── my-paintings-instagram/          # Social-sized (same structure)
├── processed-metadata/              # JSON + txt files per painting
│   └── <collection>/painting.json
└── videos/

~/.config/theo-van-gogh/
├── cookies/faso_browser_profile/    # Persistent Chromium profile
└── debug/screenshots/
```

## Two Platform Categories

**Gallery sites** (`gallery_sites` in metadata): one-time uploads, track `last_uploaded`
**Social media** (`social_media` in metadata): repeating posts, track `last_posted` + `post_count`
