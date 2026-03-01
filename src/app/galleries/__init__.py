"""
Art gallery website platform registry.
Maps gallery names to their implementation classes.
"""

from src.app.galleries.base import GalleryPlatform


# Gallery registry: name -> module path + class name
_GALLERY_REGISTRY = {
    "faso": ("src.app.galleries.faso", "FASOGallery"),
}


def get_gallery(name: str) -> GalleryPlatform:
    """
    Get an instance of a gallery platform by name.

    Args:
        name: Gallery name (e.g. "faso").

    Returns:
        GalleryPlatform instance.

    Raises:
        KeyError: If gallery name is not registered.
    """
    if name not in _GALLERY_REGISTRY:
        raise KeyError(f"Unknown gallery platform: {name}")

    module_path, class_name = _GALLERY_REGISTRY[name]
    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()


def get_all_gallery_names() -> list:
    """Get all registered gallery names."""
    return list(_GALLERY_REGISTRY.keys())
