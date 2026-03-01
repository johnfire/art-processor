# Tech Stack — Theo-van-Gogh

## Runtime

| Component | Choice | Version | Rationale |
|-----------|--------|---------|-----------|
| Language | Python | 3.12 | Type hints, match/case, pathlib |
| CLI framework | Click | 8.x | Composable commands, auto help |
| Terminal UI | Rich | 13.x | Tables, prompts, progress bars |
| AI API | Anthropic Claude | claude-sonnet-4-20250514 | Vision + text, best quality |
| Browser automation | Playwright | async API | FASO + future gallery sites |
| HTTP (social) | stdlib urllib.request | — | No external deps for API calls |
| OAuth signing | stdlib hmac + hashlib | — | Flickr OAuth 1.0a |

## Testing

| Component | Choice |
|-----------|--------|
| Test runner | pytest |
| Mocking | pytest-mock |
| BDD | pytest-bdd (Gherkin .feature files) |
| Coverage | pytest-cov (threshold: 40%) |

## Key Config Variables (`config/settings.py`, loaded from `.env`)

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=2000

# Gallery sites
FASO_EMAIL=your@email.com
FASO_PASSWORD=your-password

# Social platforms (implemented)
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=...
BLUESKY_HANDLE=user.bsky.social
BLUESKY_APP_PASSWORD=...
PIXELFED_INSTANCE_URL=https://pixelfed.social
PIXELFED_ACCESS_TOKEN=...
FLICKR_API_KEY=...
FLICKR_API_SECRET=...
FLICKR_OAUTH_TOKEN=...
FLICKR_OAUTH_SECRET=...

# Paths (defaults shown)
PAINTINGS_BIG_PATH=~/ai-workzone/my-paintings-big
PAINTINGS_INSTAGRAM_PATH=~/ai-workzone/my-paintings-instagram
METADATA_OUTPUT_PATH=~/ai-workzone/processed-metadata
VIDEOS_PATH=~/ai-workzone/videos
```

## Logs

All logs go to `~/logs/app.log` (global rule — never project-local `logs/`).
Logger: `src/core/logger.py` — `get_logger("name")` returns child of `theo.*` hierarchy.
