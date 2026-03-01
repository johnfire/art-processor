# Known Traps and Gotchas — Theo-van-Gogh

## Import Conventions (post CAR refactor, 2026-03-01)

After the directory restructure, import paths are:
- Business logic: `from src.app.services.X import Y`
- Gallery framework: `from src.app.galleries.X import Y`
- Social framework: `from src.app.social.X import Y`
- Logger: `from src.core.logger import get_logger, configure_logging`
- Config: `from config.settings import X` (unchanged)

Never use old flat paths like `from src.image_analyzer import ...` — those modules no longer exist.

## URL Security (CodeQL rule)

Always use `urlparse().hostname ==` for URL validation, never `url in "..."` or `"domain" in url`:

```python
# CORRECT
from urllib.parse import urlparse
assert urlparse(url).hostname == "mastodon.social"

# WRONG — CodeQL will flag this
assert "mastodon.social" in url
```

## Platform Stubs

`src/app/social/` has 9 stub platforms (instagram, facebook, linkedin, tiktok, youtube, cara, threads, tumblr, upscrolled). They all raise `NotImplementedError`. Do not implement until the dev account is set up. UpScrolled has no public API yet — check support around 2026-04-22.

## Playwright / HeadlessUI (Cara, future sites)

- Scope selectors inside `[role="dialog"]` not `#headlessui-portal-root` (avoids hidden focus guards)
- `locator.wait_for()` only accepts `attached/detached/visible/hidden` — NOT `enabled`
- Wait for enabled: `from playwright.async_api import expect; await expect(btn).to_be_enabled(timeout=...)`
- HeadlessUI outer dialog div has no size → Playwright sees it as hidden; skip `wait_for` or use `state="attached"`
- Multiple matches: add `.first` to the locator
- Hit-testing inside dialogs: use `force=True` on clicks
- File pickers via SVG icon buttons: use `expect_file_chooser()` pattern

## FASO Specifics

- Dashboard URL: `data.fineartstudioonline.com/cfgeditwebsite.asp?new_login=y&faso_com_auth=y`
- Profile marker: `~/.config/theo-van-gogh/cookies/faso_browser_profile/.logged_in` must exist
- Always sets Availability to "Available"
- Upload button: `a.tb_link:has(img[src*="upload_2"])`
- Save button: `input[value*="Save Changes"]`
- Uses fuzzy dropdown matching (`_select_dropdown_fuzzy`)

## BDD Tests

- Feature files live at `tests/e2e/features/*.feature`
- Step definitions at `tests/e2e/test_bdd_*.py`
- `scenarios("features/X.feature")` resolves relative to the test file — path stays correct
- State flows via `ctx` dict fixture between Given/When/Then steps
- Run BDD only: `pytest tests/e2e/test_bdd_*.py --no-cov -v`

## Gallery vs Social Media

| | Gallery sites | Social media |
|--|--|--|
| Purpose | Portfolio / sales | Promotion |
| Tracking field | `gallery_sites` | `social_media` |
| Key | `last_uploaded` + `url` | `last_posted` + `post_count` |
| Re-post? | No (one-time) | Yes (can repeat) |
| Image used | Big (full res) | Instagram (optimised) |

## Flickr OAuth

- Upload endpoint: `https://up.flickr.com/services/upload/` — all OAuth params in multipart body (not Authorization header)
- REST endpoint: `https://www.flickr.com/services/rest/` — for `flickr.test.login`

## Logs

All logs go to `~/logs/` (global rule). Never create a project-local `logs/` directory.

## Gallery Sites Needing DevTools Before Implementation

Saatchi Art, ArtPal, Jose Art Gallery — none have APIs, all need Playwright. Must do a live DevTools session to map CSS selectors before implementing. Do not guess selectors.
