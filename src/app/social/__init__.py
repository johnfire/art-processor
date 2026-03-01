"""
Social media platform registry.
Maps platform names to their implementation classes.
"""

from src.app.social.base import SocialPlatform


# Platform registry: name -> module path + class name
# Lazily imported to avoid loading all platforms at startup
_PLATFORM_REGISTRY = {
    "mastodon": ("src.app.social.mastodon", "MastodonPlatform"),
    "instagram": ("src.app.social.instagram", "InstagramPlatform"),
    "facebook": ("src.app.social.facebook", "FacebookPlatform"),
    "bluesky": ("src.app.social.bluesky", "BlueskyPlatform"),
    "linkedin": ("src.app.social.linkedin", "LinkedInPlatform"),
    "tiktok": ("src.app.social.tiktok", "TikTokPlatform"),
    "youtube": ("src.app.social.youtube", "YouTubePlatform"),
    "cara": ("src.app.social.cara", "CaraPlatform"),
    "threads": ("src.app.social.threads", "ThreadsPlatform"),
    "pixelfed": ("src.app.social.pixelfed", "PixelfedPlatform"),
    "tumblr": ("src.app.social.tumblr", "TumblrPlatform"),
    "flickr": ("src.app.social.flickr", "FlickrPlatform"),
    "upscrolled": ("src.app.social.upscrolled", "UpScrolledPlatform"),
}


def get_platform(name: str) -> SocialPlatform:
    """
    Get an instance of a social media platform by name.

    Args:
        name: Platform name (e.g. "mastodon").

    Returns:
        SocialPlatform instance.

    Raises:
        KeyError: If platform name is not registered.
    """
    if name not in _PLATFORM_REGISTRY:
        raise KeyError(f"Unknown social media platform: {name}")

    module_path, class_name = _PLATFORM_REGISTRY[name]
    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()


def get_all_platform_names() -> list:
    """Get all registered platform names."""
    return list(_PLATFORM_REGISTRY.keys())


def get_implemented_platforms() -> list:
    """Get names of platforms that have real implementations (not stubs)."""
    implemented = []
    for name in _PLATFORM_REGISTRY:
        try:
            platform = get_platform(name)
            # Try calling is_configured — stubs will work but post methods raise NotImplementedError
            # Check if it has a real post_image (not the stub's)
            if not getattr(platform, '_is_stub', False):
                implemented.append(name)
        except Exception:
            pass
    return implemented
