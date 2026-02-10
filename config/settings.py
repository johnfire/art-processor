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
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "xxxxxxx-xxxxxxx")

# FASO Configuration
FASO_EMAIL = os.getenv("FASO_EMAIL", "xxxx")
FASO_PASSWORD = os.getenv("FASO_PASSWORD", "xxxx")

# File Paths
PAINTINGS_BIG_PATH = Path(os.getenv("PAINTINGS_BIG_PATH", "~/ai-workzone/my-paintings-big")).expanduser()
PAINTINGS_INSTAGRAM_PATH = Path(os.getenv("PAINTINGS_INSTAGRAM_PATH", "~/ai-workzone/my-paintings-instagram")).expanduser()
METADATA_OUTPUT_PATH = Path(os.getenv("METADATA_OUTPUT_PATH", "~/ai-workzone/processed-metadata")).expanduser()

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
    "Fachwerkhäuser",
    "Imaginary Places",
    "Surreal Botanicals",
    "Drawings",
    "Wood Block Prints",
    "Oil Paintings",
    "Other Paintings",
    "Photography",
    "Coloring Book Drawings and Finished Works",
    "Abstract Works, Stand Alones",
    "Abstracts, Quantum Cubes Collection",
    "Abstracts, Tiny Life, Biologic Abstract Art",
    "Abstracts, Inspired by my life in Central America",
    "Meditations"
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
