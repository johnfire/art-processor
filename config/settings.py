"""
Configuration settings for the art processor.
All extensible lists are defined here for easy modification.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "xxx")

# FASO Configuration
FASO_EMAIL = os.getenv("FASO_EMAIL", "xxx")
FASO_PASSWORD = os.getenv("FASO_PASSWORD", "xxx")

# Mastodon Configuration
MASTODON_INSTANCE_URL = os.getenv("MASTODON_INSTANCE_URL", "")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN", "")

# Bluesky Configuration
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")

# Pixelfed Configuration
PIXELFED_INSTANCE_URL = os.getenv("PIXELFED_INSTANCE_URL", "")
PIXELFED_ACCESS_TOKEN = os.getenv("PIXELFED_ACCESS_TOKEN", "")
PIXELFED_MAX_CAPTION_LENGTH = 2000   # safe default; varies by instance

# Social Media
SOCIAL_MEDIA_WEBSITE = "artbychristopherrehm.com"

# ============================================================================
# BASE FILE PATHS
# ============================================================================
PAINTINGS_BIG_PATH = Path(os.getenv("PAINTINGS_BIG_PATH", "~/ai-workzone/my-paintings-big")).expanduser()
PAINTINGS_INSTAGRAM_PATH = Path(os.getenv("PAINTINGS_INSTAGRAM_PATH", "~/ai-workzone/my-paintings-instagram")).expanduser()
METADATA_OUTPUT_PATH = Path(os.getenv("METADATA_OUTPUT_PATH", "~/ai-workzone/processed-metadata")).expanduser()

# ============================================================================
# DERIVED FILE PATHS
# All specific file locations derived from base paths above
# Centralized here for easy configuration and modularity
# ============================================================================

# Upload tracking
UPLOAD_TRACKER_PATH = METADATA_OUTPUT_PATH / "upload_status.json"

# Schedule file for social media posts
SCHEDULE_PATH = METADATA_OUTPUT_PATH / "schedule.json"

# Videos
VIDEOS_PATH = Path(os.getenv("VIDEOS_PATH", "~/ai-workzone/videos")).expanduser()

# Browser cookies and session files
COOKIES_DIR = Path(os.getenv("COOKIES_DIR", "~/.config/theo-van-gogh/cookies")).expanduser()
FASO_COOKIES_PATH = COOKIES_DIR / "faso_cookies.json"
INSTAGRAM_COOKIES_PATH = COOKIES_DIR / "instagram_cookies.json"

# Debug and temporary files
DEBUG_DIR = Path(os.getenv("DEBUG_DIR", "~/.config/theo-van-gogh/debug")).expanduser()
SCREENSHOTS_DIR = DEBUG_DIR / "screenshots"
LOGS_DIR = DEBUG_DIR / "logs"

# Ensure all directories exist
for directory in [METADATA_OUTPUT_PATH, COOKIES_DIR, DEBUG_DIR, SCREENSHOTS_DIR, LOGS_DIR, VIDEOS_PATH]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# MEASUREMENT UNITS
# ============================================================================
# Default unit for dimensions
# Options: "cm" for centimeters or "in" for inches
DIMENSION_UNIT = "cm"

# ============================================================================
# EXTENSIBLE ARTWORK METADATA FIELDS
# Add new options to any of these lists as needed
# ============================================================================

# Substrate options
SUBSTRATES = [
    "Canvas",
    "Linen",
    "Panel",
    "Paper",
]

# Medium options
MEDIUMS = [
    "Acrylic",
    "markers and Pens",
    "Oil",
    "Watercolor",
    "Pen and Ink",
    "Pencil",
    "Photography",
    "Wood Block Print"
]

# Subject options
SUBJECTS = [
    "Abstract",
    "Architecture",
    "Cityscape",
    "Domestic Animals",
    "Fantasy",
    "Figurative",
    "Genre",
    "Interior",
    "Landscape",
    "Portrait",
    "Sea Beasties on Titan",
    "Seascape",
    "Still Life",
    "surreal botanical",
    "Wildlife",
]

# Style options
STYLES = [
    "Abstract",
    "Impressionism",
    "Realism",
    "surreal",
    "surrealism"
]

# Collection options
COLLECTIONS = [
    "Sea Beasties from Titan",
    "Landscapes and Cityscapes, Real Places",
    "Fachwerkh\u00e4user",
    "Imaginary Places",
    "Surreal Botanicals",
    "Drawings",
    "Wood Block Prints",
    "Oil Paintings",
    "Other Paintings",
    "Photography",
    "Coloring Book Drawings and Finished Works",
    "Abstract Works, Stand Alones",
    "Abstracts - Quantum Cubes Collection",
    "Abstracts - Tiny Life, Biologic Abstract Art",
    "Abstracts - Inspired by my life in Central America",
    "Meditations",
    "Fire Stars"
]

# Image Processing Settings
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png"]
MAX_IMAGE_SIZE_MB = 100  # Maximum file size for processing

# AI Configuration
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2000

# File Naming
SANITIZE_RULES = {
    " ": "_",
    ":": "",
    ";": "",
    "?": "",
    "!": "",
    "/": "_",
    "\\": "_",
    "*": "",
    '"': "",
    "'": "",
    "<": "",
    ">": "",
    "|": "",
}
