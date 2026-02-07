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
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# File Paths
PAINTINGS_BIG_PATH = Path(os.getenv("PAINTINGS_BIG_PATH", "~/Pictures/my-paintings-big")).expanduser()
PAINTINGS_INSTAGRAM_PATH = Path(os.getenv("PAINTINGS_INSTAGRAM_PATH", "~/Pictures/my-paintings-instagram")).expanduser()
METADATA_OUTPUT_PATH = Path(os.getenv("METADATA_OUTPUT_PATH", "~/Pictures/processed-metadata")).expanduser()

# Extensible Categories
# Add new categories here as needed
CATEGORIES = [
    "abstract",
    "landscapes",
    "cityscapes",
    "fantasy",
    "botanicals",
    "surreal",
    # Add more as needed
]

# Extensible Medium Types
# Add new mediums here as needed
MEDIUMS = [
    "Oil on canvas",
    "Watercolor",
    "Acrylic",
    "Drawing",
    "Woodblock print",
    # Add more as needed
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

# Ensure output directory exists
METADATA_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
