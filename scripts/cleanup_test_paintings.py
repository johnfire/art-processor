"""
Remove all test paintings and metadata created by generate_test_paintings.py.

Deletes:
  - Images in:   ~/ai-workzone/my-paintings-big/test-paintings/
  - Metadata in: ~/ai-workzone/processed-metadata/test-paintings/

Run from the project root:
    source venv/bin/activate
    python testing-scripts/cleanup_test_paintings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import PAINTINGS_BIG_PATH, METADATA_OUTPUT_PATH

CATEGORY = "test-paintings"

TEST_FILENAMES = [
    "test_painting_1",
    "test_painting_2",
    "test_painting_3",
]


def remove_file(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"  removed : {path}")
    else:
        print(f"  missing : {path}")


def remove_dir_if_empty(path: Path) -> None:
    if path.exists() and not any(path.iterdir()):
        path.rmdir()
        print(f"  removed dir : {path}")


def main() -> None:
    images_dir = PAINTINGS_BIG_PATH / CATEGORY
    metadata_dir = METADATA_OUTPUT_PATH / CATEGORY

    print(f"\nCleaning up test paintings...\n")

    for name in TEST_FILENAMES:
        print(f"  [{name}]")
        remove_file(images_dir / f"{name}.jpg")
        remove_file(metadata_dir / f"{name}.json")
        remove_file(metadata_dir / f"{name}.txt")

    # Remove directories if now empty
    remove_dir_if_empty(images_dir)
    remove_dir_if_empty(metadata_dir)

    print(f"\nDone.\n")


if __name__ == "__main__":
    main()
