# Architecture Decision Records — Theo-van-Gogh

## ADR-001: Tracking in metadata files, not a central DB
**Date:** 2025-01-01
**Status:** Accepted
**Reason:** Each painting's JSON is the single source of truth for its upload/post history. Eliminates sync issues between a DB and the file system. Works offline, no DB dependency.
**Consequence:** No cross-painting queries; iterate files to build aggregate views.

## ADR-002: No external HTTP dependencies for social platforms
**Date:** 2025-01-01
**Status:** Accepted
**Reason:** Mastodon, Flickr, Bluesky implemented with stdlib `urllib.request` + `hmac`/`hashlib`. Keeps dependency footprint minimal and auditable.
**Consequence:** More boilerplate per platform; no auto-retry or connection pooling from a library.

## ADR-003: Platform stubs raise NotImplementedError
**Date:** 2025-01-01
**Status:** Accepted
**Reason:** All 13 social platforms + future gallery sites are registered from day one. Unimplemented ones raise `NotImplementedError` with a clear message rather than silently failing.
**Consequence:** Registry is always complete; users see informative errors if they select an unready platform.

## ADR-004: Lazy platform loading via registry dicts
**Date:** 2025-01-01
**Status:** Accepted
**Reason:** Importing all platform modules at startup would pull in Playwright, atproto, etc. even when unused. Registry maps `name → (module_path, class_name)`; importlib loads on demand.
**Consequence:** Faster startup; harder to statically analyse all platform imports.

## ADR-005: Persistent Chromium profile for FASO
**Date:** 2025-01-01
**Status:** Accepted
**Reason:** FASO uses Cloudflare protection that blocks headless browsers mid-session. Persistent profile survives sessions and keeps Cloudflare cookies valid after a one-time manual login.
**Consequence:** User must run `python manual_login.py` once to seed the profile; profile path is `~/.config/theo-van-gogh/cookies/faso_browser_profile`.

## ADR-006: Cron-based scheduling, no daemon
**Date:** 2025-01-01
**Status:** Accepted
**Reason:** `python main.py check-schedule` runs every 5 min via cron. Simple, reliable, no persistent process to manage or monitor.
**Consequence:** Scheduling granularity is 5 minutes; posts may run up to 5 min late.

## ADR-007: CAR standard project structure (src/app/services/, src/core/)
**Date:** 2026-03-01
**Status:** Accepted
**Reason:** Adopted `car-standard-project-structure.md` to improve navigability and Claude Code integration. Entry point (`main.py`) stays at root; business logic moves to `src/app/services/`; gallery/social frameworks in their own subdirs; logger extracted to `src/core/`.
**Consequence:** All imports changed from `src.X` to `src.app.services.X` etc. Worth the one-time churn for long-term clarity.

## ADR-008: BaseBrowserUploader ABC for all gallery sites
**Date:** 2026-02-21
**Status:** Accepted
**Reason:** FASO + future gallery sites (Saatchi, ArtPal, Jose) share Playwright launch, session check, form helpers. Extracted to `src/app/galleries/browser_uploader.py`.
**Consequence:** Each new gallery site subclasses `BaseBrowserUploader` and implements only site-specific selectors.
