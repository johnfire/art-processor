# CLAUDE.md — AI Coding Guide for Theo-van-Gogh

Art management automation system for working artists. See `.claude/context/` for deep-dive docs.

## Quick Orientation

- **Entry point:** `main.py` at project root (Click CLI)
- **All paths:** `config/settings.py` — never hardcode paths elsewhere
- **Metadata schema:** `src/app/services/metadata_manager.py` — source of truth for JSON structure
- **Logger:** `from src.core.logger import get_logger` — always use this, never bare `logging`
- **Tests:** `tests/` — run with `source venv/bin/activate && pytest`
- **Context docs:** `.claude/context/architecture.md`, `decisions.md`, `stack.md`, `gotchas.md`

## Running Things

Always activate the virtualenv first:
```bash
source venv/bin/activate
pytest                              # full suite
pytest tests/unit/ -v               # unit tests only
pytest tests/e2e/test_bdd_*.py --no-cov -v  # BDD only
python main.py --help               # CLI commands
```

## Key Import Paths (post-refactor)

```python
from src.app.services.image_analyzer import ImageAnalyzer
from src.app.services.metadata_manager import MetadataManager
from src.app.galleries.browser_uploader import BaseBrowserUploader
from src.app.social.base import SocialPlatform
from src.core.logger import get_logger
from config.settings import METADATA_OUTPUT_PATH
```

## Key Conventions

- **Platform stubs** in `src/app/social/` raise `NotImplementedError` — don't implement until dev account ready
- **URL checks** use `urlparse().hostname ==` (not `in` substring) — CodeQL enforces this
- **Gallery sites** track `last_uploaded` (one-time). **Social media** tracks `last_posted` + `post_count` (can repeat)
- **No external HTTP deps** — social platforms use stdlib `urllib.request` only
- **Lazy platform loading** — import classes on demand via registry, not at module level
- **Logs** go to `~/logs/` — never a project-local `logs/` dir

## Adding a New Social Platform

1. Create `src/app/social/newplatform.py` implementing `SocialPlatform` ABC
2. Register it in `src/app/social/__init__.py`
3. Add to `SOCIAL_MEDIA_PLATFORMS` list in `src/app/social/base.py`
4. Add credentials to `config/settings.py` + `.env.example`

CLI, scheduler, and metadata tracking work automatically after step 4.

## Adding a New Gallery Site

1. Subclass `BaseBrowserUploader` in `src/app/galleries/newsite.py`
2. Implement: `name`, `profile_dir`, `dashboard_url`, `upload_painting(metadata)`
3. Register in `src/app/galleries/__init__.py`
4. Add credentials to `config/settings.py` + `.env.example`

Note: Saatchi, ArtPal, Jose need a live DevTools session to map selectors first.

## FASO Browser Automation

- Persistent Chromium profile: `~/.config/theo-van-gogh/cookies/faso_browser_profile`
- Login: `data.fineartstudioonline.com/login/`
- Always sets Availability to "Available"; uses fuzzy dropdown matching
- Profile marker `.logged_in` must exist before browser start

## GitHub Workflow

```bash
gh issue list --repo johnfire/theo-van-gogh
gh issue view <number> --repo johnfire/theo-van-gogh --json title,body,labels
gh issue close <number> --repo johnfire/theo-van-gogh --comment "Fixed in commit ..."
```

Label `claude code should fix` marks issues ready for AI implementation.

## Testing Notes

- Coverage threshold 40% — running a single file will fail coverage, that's expected
- BDD tests use `ctx` dict fixture to flow state between Given/When/Then steps
- Security tests: `urlparse().hostname ==` not substring `in` (CodeQL rule)
