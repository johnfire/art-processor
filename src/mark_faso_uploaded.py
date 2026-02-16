"""
One-off script: mark all metadata files as already uploaded to FASO.

Use this when paintings were manually uploaded to FASO before the
automated tracking was set up — it stamps last_uploaded so the uploader
won't try to re-upload them.

Usage:
  python src/mark_faso_uploaded.py           # dry run (shows what would change)
  python src/mark_faso_uploaded.py --apply   # write changes to disk
"""

import json
import sys
from pathlib import Path

# Date to use — represents "uploaded before automated tracking began"
STAMP = "2026-01-01T00:00:00.000000"


def main():
    apply = "--apply" in sys.argv

    metadata_dir = Path("~/ai-workzone/processed-metadata").expanduser()
    files = sorted(metadata_dir.rglob("*.json"))

    changed = 0
    skipped = 0

    for path in files:
        with open(path) as f:
            data = json.load(f)

        # Skip files that don't have the gallery_sites/faso structure
        if "gallery_sites" not in data or "faso" not in data.get("gallery_sites", {}):
            skipped += 1
            continue

        faso = data["gallery_sites"]["faso"]
        if faso.get("last_uploaded") is not None:
            skipped += 1
            continue

        print(f"{'  SET' if apply else ' WOULD SET'}  {path.relative_to(metadata_dir)}")

        if apply:
            data["gallery_sites"]["faso"]["last_uploaded"] = STAMP
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")

        changed += 1

    print(f"\n{'Updated' if apply else 'Would update'}: {changed}  |  Already set: {skipped}")
    if not apply:
        print("\nRun with --apply to write changes.")


if __name__ == "__main__":
    main()
