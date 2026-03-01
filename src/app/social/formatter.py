"""
Post text formatter for social media platforms.
Produces a consistent post format across all platforms.

Format:
    Painting Title

    Short description (~75 words max)

    #art #artforsale #subject
    artbychristopherrehm.com
"""

import re
from typing import Dict, Any


WEBSITE_URL = "artbychristopherrehm.com"


def format_post_text(metadata: Dict[str, Any], max_words: int = 75) -> str:
    """
    Build the full post text from painting metadata.

    Args:
        metadata: Painting metadata dict.
        max_words: Maximum words for the description portion.

    Returns:
        Formatted post text string.
    """
    title = metadata.get("title", {}).get("selected", "Untitled")
    description = metadata.get("description") or ""
    subject = metadata.get("subject") or ""

    short_desc = truncate_description(description, max_words)
    hashtags = build_hashtags(subject)

    parts = [title]
    if short_desc:
        parts.append(short_desc)
    parts.append(f"{hashtags}\n{WEBSITE_URL}")

    return "\n\n".join(parts)


def truncate_description(text: str, max_words: int = 75) -> str:
    """
    Truncate text to at most max_words words.
    Strips markdown formatting (**bold**, *italic*).

    Args:
        text: The full description text.
        max_words: Maximum number of words to keep.

    Returns:
        Truncated plain text.
    """
    if not text:
        return ""

    # Strip markdown bold/italic markers
    plain = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text)
    # Collapse whitespace
    plain = re.sub(r'\s+', ' ', plain).strip()

    words = plain.split()
    if len(words) <= max_words:
        return plain

    return " ".join(words[:max_words]) + "..."


def subject_to_hashtag(subject: str) -> str:
    """
    Convert a subject string to a hashtag.
    "Sea Beasties on Titan" -> "#seabeastiesontitan"

    Args:
        subject: The subject string.

    Returns:
        Hashtag string (lowercase, no spaces).
    """
    if not subject:
        return ""
    # Remove non-alphanumeric chars, collapse, lowercase
    tag = re.sub(r'[^a-zA-Z0-9]', '', subject).lower()
    return f"#{tag}" if tag else ""


def build_hashtags(subject: str) -> str:
    """
    Build the hashtag line: #art #artforsale #subject

    Args:
        subject: The painting subject.

    Returns:
        Hashtag string.
    """
    tags = ["#art", "#artforsale"]
    subject_tag = subject_to_hashtag(subject)
    if subject_tag and subject_tag not in tags:
        tags.append(subject_tag)
    return " ".join(tags)
