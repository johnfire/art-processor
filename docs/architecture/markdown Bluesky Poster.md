markdown# Bluesky Poster Module — Claude Code Briefing
## Project: Theo-van-Gogh Social Media Automation System

---

## 1. Context & Purpose

This module is one component of a larger system called **Theo-van-Gogh**, an
AI-powered automation system for an artist's social media marketing workflow.
The overall system generates content packages (image + text/caption/hashtags/metadata)
and distributes them to multiple social platforms.

This specific module handles posting to **Bluesky** via the official AT Protocol API.

Overall architecture:
```
Theo-van-Gogh (content generation)
        |
        v
Content Package (image path + metadata)
        |
        v
OpenClaw Orchestrator
        |
        |---> bluesky_poster.py          <- THIS MODULE
        |---> mastodon_poster.py
        |---> pixelfed_poster.py
        |---> postforme_poster.py        (Instagram, TikTok, Facebook, Threads)
        |---> cara_poster.py
```

---

## 2. Platform: Bluesky / AT Protocol

- **Platform:** Bluesky Social (bsky.social)
- **Protocol:** AT Protocol (atproto)
- **API type:** Open REST API — no approval process, no paid tiers
- **Docs:** https://docs.bsky.app
- **AT Protocol spec:** https://atproto.com
- **Python SDK docs:** https://atproto.blue
- **GitHub SDK:** https://github.com/MarshalX/atproto

---

## 3. Python SDK
```bash
pip install atproto
```

Auto-generated from AT Protocol lexicons. Type-hinted and well documented.
Use the **synchronous** client (not async).

---

## 4. Authentication

- Use an **app password**, NOT the main account password
- Create in Bluesky: Settings -> Privacy and Security -> App Passwords
- Store in environment variables / `.env`, never hardcoded
- `accessJwt` token expires quickly but SDK Client handles refresh automatically
  if you keep the client instance alive
```python
from atproto import Client
client = Client()
client.login('your-handle.bsky.social', 'your-app-password')
```

---

## 5. Core Functionality

### Primary use case: post text + image

The flow is always:
1. Strip EXIF metadata from image (privacy + official recommendation)
2. Upload image as blob, get blob reference back
3. Create post with text + embedded blob
```python
from atproto import Client, models
from PIL import Image
import io

def strip_exif(image_path: str) -> bytes:
    """Strip EXIF metadata from image before upload."""
    img = Image.open(image_path)
    buffer = io.BytesIO()
    img.save(buffer, format=img.format or 'JPEG')
    return buffer.getvalue()


def post_image_to_bluesky(
    client: Client,
    image_path: str,
    alt_text: str,
    post_text: str
) -> dict:
    """Post an image with caption text to Bluesky."""

    # Step 1: strip EXIF
    img_data = strip_exif(image_path)

    # Step 2: upload blob — returns a blob reference
    upload_response = client.upload_blob(img_data)

    # Step 3: build image embed
    embed = models.AppBskyEmbedImages.Main(
        images=[
            models.AppBskyEmbedImages.Image(
                alt=alt_text,
                image=upload_response.blob
            )
        ]
    )

    # Step 4: send post with text and embedded image
    post = client.send_post(text=post_text, embed=embed)

    return {'uri': post.uri, 'cid': post.cid}
```

### Multiple images (up to 4 per post)
```python
embed = models.AppBskyEmbedImages.Main(
    images=[
        models.AppBskyEmbedImages.Image(alt=alt_1, image=blob_1),
        models.AppBskyEmbedImages.Image(alt=alt_2, image=blob_2),
    ]
)
```

---

## 6. Content Package Interface
```python
content_package = {
    'image_path': '/path/to/painting.jpg',
    'alt_text': 'Description of the artwork',
    'caption': 'Post text / caption',
    'hashtags': ['#art', '#watercolour'],
    'platform': 'bluesky'
}
```

Append hashtags to caption before posting.
Respect the 300 character limit.

---

## 7. Module Design Requirements

### File structure
```
posters/
    bluesky_poster.py
    __init__.py
```

### Code style
- Max ~500 lines per module
- Clean, simple code
- Inline comments throughout
- No hardcoded credentials
- Centralised config via settings.py or .env (match existing project pattern)

### Error handling
- Wrap all API calls in try/except
- Log failures clearly
- Return structured success/failure dict for orchestrator

### Return structure
```python
# success
{'success': True, 'platform': 'bluesky', 'uri': 'at://...', 'cid': 'bafy...', 'error': None}

# failure
{'success': False, 'platform': 'bluesky', 'uri': None, 'cid': None, 'error': 'message'}
```

---

## 8. Environment Variables
```env
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

---

## 9. Dependencies
```
atproto        # Bluesky / AT Protocol SDK
Pillow         # Image processing + EXIF stripping
python-dotenv  # Env variable loading (if not already in project)
```

---

## 10. Character Limit

**300 characters maximum.** Enforce this — truncate with ellipsis or raise,
but never silently post truncated content without logging.

---

## 11. Gotchas

- Fully open API — no app review, no business account needed
- EXIF stripping is officially recommended, may be enforced server-side in future
- Keep same Client instance alive — SDK handles token refresh automatically
- Two-step pattern is mandatory: upload blob first, get reference, then post
- Up to 4 images per post
- Store returned `uri` and `cid` if you need to track or delete posts later
- bsky.app may resize images for display, but original blob is stored intact

---

## 12. Reference Links

- Bluesky API docs:        https://docs.bsky.app
- Quickstart:              https://docs.bsky.app/docs/get-started
- Creating posts guide:    https://docs.bsky.app/docs/tutorials/creating-a-post
- Full HTTP API reference: https://docs.bsky.app/docs/api/at-protocol-xrpc-api
- Python SDK docs:         https://atproto.blue
- Python SDK GitHub:       https://github.com/MarshalX/atproto
- AT Protocol spec:        https://atproto.com
