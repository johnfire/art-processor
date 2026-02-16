"""
Generate Instagram-sized images from big originals.

For each metadata file that has a big image but no instagram image:
  - Portrait (height >= width)  → 1080 × 1350 px  (4:5 ratio)
  - Landscape (width > height)  → 1080 ×  566 px  (~1.91:1 ratio)

Images are crop-filled to the target dimensions (centred crop, no distortion).
Output goes to the matching subfolder inside my-paintings-instagram/.
The metadata file is updated with the new instagram path.

Usage:
  python src/generate_instagram_images.py           # dry run
  python src/generate_instagram_images.py --apply   # write images + update metadata
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

# Instagram target dimensions
PORTRAIT_SIZE  = (1080, 1350)   # 4:5 — for vertical paintings
LANDSCAPE_SIZE = (1080, 566)    # ~1.91:1 — for horizontal paintings

JPEG_QUALITY = 90   # good quality, typically 600 KB – 1.2 MB at these dimensions

INSTAGRAM_DIR  = Path("~/ai-workzone/my-paintings-instagram").expanduser()
METADATA_DIR   = Path("~/ai-workzone/processed-metadata").expanduser()


def _get_big_path(files: dict) -> Path | None:
    """Return the big image path, handling both string and list formats."""
    big = files.get("big")
    if not big:
        return None
    if isinstance(big, list):
        big = big[0] if big else None
    if not big:
        return None
    p = Path(big)
    return p if p.exists() else None


def _target_size(img: Image.Image) -> tuple[int, int]:
    """Choose portrait or landscape target based on the source image orientation."""
    w, h = img.size
    return PORTRAIT_SIZE if h >= w else LANDSCAPE_SIZE


def _generate(big_path: Path, out_path: Path, apply: bool) -> bool:
    """
    Resize and crop big_path to Instagram size, save to out_path.
    Returns True on success (or would-succeed in dry-run).
    """
    try:
        with Image.open(big_path) as img:
            target = _target_size(img)
            if apply:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                resized = ImageOps.fit(img.convert("RGB"), target, Image.LANCZOS)
                resized.save(out_path, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    apply = "--apply" in sys.argv

    metadata_files = sorted(METADATA_DIR.rglob("*.json"))
    created = 0
    skipped = 0
    errors  = 0

    for meta_path in metadata_files:
        with open(meta_path) as f:
            data = json.load(f)

        files = data.get("files", {})

        # Skip if instagram already set and the file actually exists
        existing_ig = files.get("instagram")
        if existing_ig and Path(existing_ig).exists():
            skipped += 1
            continue

        big_path = _get_big_path(files)
        if not big_path:
            skipped += 1
            continue

        # Derive output path: same subfolder + filename under instagram dir
        category = big_path.parent.name
        out_path = INSTAGRAM_DIR / category / big_path.name

        # Determine what size we'd produce
        try:
            with Image.open(big_path) as img:
                target = _target_size(img)
                orientation = "portrait" if target == PORTRAIT_SIZE else "landscape"
        except Exception as e:
            print(f"  SKIP (can't open): {big_path.name} — {e}")
            errors += 1
            continue

        label = "  CREATE" if apply else "WOULD CREATE"
        print(f"{label}  {category}/{out_path.name}  →  {target[0]}×{target[1]} ({orientation})")

        ok = _generate(big_path, out_path, apply)
        if not ok:
            errors += 1
            continue

        if apply:
            data["files"]["instagram"] = str(out_path)
            with open(meta_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")

        created += 1

    print(f"\n{'Created' if apply else 'Would create'}: {created}")
    print(f"Already done / no big image: {skipped}")
    if errors:
        print(f"Errors: {errors}")
    if not apply:
        print("\nRun with --apply to generate images and update metadata.")


if __name__ == "__main__":
    main()
