"""
Generate 3 fake test paintings with dummy metadata for FASO uploader testing.

Creates:
  - Small JPEG images (solid colour + bold "TEST N" label) in:
      ~/ai-workzone/my-paintings-big/test-paintings/
  - Matching metadata JSON + TXT files in:
      ~/ai-workzone/processed-metadata/test-paintings/

Run from the project root:
    source venv/bin/activate
    python testing-scripts/generate_test_paintings.py
"""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config.settings import PAINTINGS_BIG_PATH, METADATA_OUTPUT_PATH
from src.metadata_manager import MetadataManager

# ── Configuration ─────────────────────────────────────────────────────────────

CATEGORY = "test-paintings"

TEST_PAINTINGS = [
    {
        "filename_base": "test_painting_1",
        "title": "Test Painting One",
        "colour": (180, 100, 100),   # muted red
        "description": "This is dummy test data for painting one. It contains placeholder text to simulate a real gallery description. The painting depicts nothing in particular and is used solely for automated testing of the upload pipeline.",
        "subject": "Abstract",
        "style": "Abstract",
        "collection": "Oil Paintings",
        "substrate": "Canvas",
        "medium": "Oil",
        "width": 60.0,
        "height": 80.0,
        "price_eur": 100.0,
    },
    {
        "filename_base": "test_painting_2",
        "title": "Test Painting Two",
        "colour": (100, 150, 180),   # muted blue
        "description": "This is dummy test data for painting two. It contains placeholder text to simulate a real gallery description. The work explores imaginary concepts for the purpose of testing the upload and metadata pipeline.",
        "subject": "Landscape",
        "style": "Impressionism",
        "collection": "Landscapes and Cityscapes, Real Places",
        "substrate": "Linen",
        "medium": "Acrylic",
        "width": 40.0,
        "height": 50.0,
        "price_eur": 150.0,
    },
    {
        "filename_base": "test_painting_3",
        "title": "Test Painting Three",
        "colour": (120, 170, 120),   # muted green
        "description": "This is dummy test data for painting three. It contains placeholder text to simulate a real gallery description. This piece is entirely fictional and exists only to validate the end-to-end upload workflow.",
        "subject": "Still Life",
        "style": "Realism",
        "collection": "Other Paintings",
        "substrate": "Panel",
        "medium": "Oil",
        "width": 30.0,
        "height": 30.0,
        "price_eur": 75.0,
    },
]

# ── Image generation ───────────────────────────────────────────────────────────

def make_test_image(path: Path, label: str, colour: tuple) -> None:
    """Create a small solid-colour JPEG with a bold label."""
    img = Image.new("RGB", (400, 300), colour)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default(size=36)
    except TypeError:
        # Pillow < 10.1 fallback
        font = ImageFont.load_default()

    # Centre the text
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (400 - text_w) // 2
    y = (300 - text_h) // 2

    # Shadow for readability
    draw.text((x + 2, y + 2), label, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), label, fill=(255, 255, 255), font=font)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=60)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    images_dir = PAINTINGS_BIG_PATH / CATEGORY
    manager = MetadataManager()

    print(f"\nGenerating test paintings...")
    print(f"  Images  → {images_dir}")
    print(f"  Metadata → {METADATA_OUTPUT_PATH / CATEGORY}\n")

    for p in TEST_PAINTINGS:
        image_path = images_dir / f"{p['filename_base']}.jpg"

        # 1. Generate image
        make_test_image(image_path, p["title"], p["colour"])

        # 2. Build metadata
        unit = "cm"
        metadata = manager.create_metadata(
            filename_base=p["filename_base"],
            category=CATEGORY,
            big_file_path=image_path,
            instagram_file_path=None,
            selected_title=p["title"],
            all_titles=[p["title"], f"Alternate Title for {p['title']}"],
            description=p["description"],
            width=p["width"],
            height=p["height"],
            depth=None,
            dimension_unit=unit,
            dimensions_formatted=f"{p['width']:.0f}{unit} x {p['height']:.0f}{unit}",
            substrate=p["substrate"],
            medium=p["medium"],
            subject=p["subject"],
            style=p["style"],
            collection=p["collection"],
            price_eur=p["price_eur"],
            creation_date=datetime.now().strftime("%Y-%m-%d"),
            analyzed_from="big",
        )

        # 3. Save JSON + TXT
        json_path = manager.save_metadata_json(metadata, CATEGORY)
        txt_path = manager.save_metadata_text(metadata, CATEGORY)

        size_kb = image_path.stat().st_size // 1024
        print(f"  ✓ {p['filename_base']}")
        print(f"      image    : {image_path} ({size_kb}kb)")
        print(f"      metadata : {json_path}")
        print(f"      text     : {txt_path}")

    print(f"\nDone. Run the FASO uploader to test:\n  python main.py upload-faso\n")
    print(f"To clean up afterwards:\n  python testing-scripts/cleanup_test_paintings.py\n")


if __name__ == "__main__":
    main()
