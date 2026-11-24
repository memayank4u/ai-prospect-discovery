import re
from typing import Optional


PLATFORM_SUFFIX_PATTERNS = [
    r"\s*[-|–—•]\s*(?:LinkedIn|Instagram|Twitter|X|YouTube|Facebook|Threads|Pinterest|TikTok).*$",
    r"\s*\(?@[A-Za-z0-9_.]+\)?\s*[-|–—•]?\s*.*$",
    r"\s*•\s*Instagram.*$",
    r"\s*[-|–—]\s*Posts\s*&.*$",
    r"\s*\|\s*Professional Profile.*$",
    r"\s*[-|–—]\s*Official Channel.*$",
    r"\s*[-|–—]\s*About\s*\|\s*.*$",
    r"\s*profile\s*\|\s*.*$"
]


def clean_prospect_name(raw_title: str) -> str:
    """
    Extracts a clean person/entity name from a search result title.
    Example:
      'John Smith - Founder & CEO | LinkedIn' -> 'John Smith'
      'Michael Johnson (@mjohnson) • Instagram photos and videos' -> 'Michael Johnson'
    """
    if not raw_title:
        return "Unknown"

    name = raw_title.strip()

    # Remove known platform trailer patterns
    for pat in PLATFORM_SUFFIX_PATTERNS:
        name = re.sub(pat, "", name, flags=re.IGNORECASE)

    # If delimiter like '-' or '|' remains, usually first part is the name
    if " - " in name:
        name = name.split(" - ")[0]
    elif " | " in name:
        name = name.split(" | ")[0]
    elif " • " in name:
        name = name.split(" • ")[0]
    elif " — " in name:
        name = name.split(" — ")[0]
    elif "–" in name:
        name = name.split("–")[0]

    # Remove quotes or brackets
    name = re.sub(r'["\'\(\)\[\]]', "", name).strip()

    # Remove common prefix titles if present (e.g. Dr., Mr., etc.)
    # Keep it clean
    words = name.split()
    if len(words) > 5:
        # If still too long, take the first 2-3 words (likely First and Last name)
        name = " ".join(words[:3])

    return name.title() if name else "Unknown"


def normalize_string(text: Optional[str]) -> str:
    """Normalize string for case-insensitive matching."""
    if not text:
        return ""
    return re.sub(r"[^a-zA-Z0-9\s]", "", text).lower().strip()


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculates Jaccard / Token similarity between two names for entity resolution.
    Returns score between 0.0 and 1.0.
    """
    norm1 = normalize_string(name1)
    norm2 = normalize_string(name2)
    if not norm1 or not norm2:
        return 0.0
    if norm1 == norm2:
        return 1.0

    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)
