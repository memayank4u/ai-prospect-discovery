import re
from typing import List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
)

PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
)

WHATSAPP_LINK_REGEX = re.compile(
    r"https?:\/\/(?:api\.whatsapp\.com\/send\?phone=|wa\.me\/)(\d+)",
    re.IGNORECASE
)


def extract_emails(text: str) -> List[str]:
    """Extract valid email addresses from text, excluding false positives (like image names)."""
    if not text:
        return []
    matches = EMAIL_REGEX.findall(text)
    valid_emails = []
    ignored_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".css", ".js")
    for email in matches:
        email_clean = email.strip().lower()
        if not any(email_clean.endswith(ext) for ext in ignored_extensions):
            if email_clean not in valid_emails:
                valid_emails.append(email_clean)
    return valid_emails


def extract_phones(text: str) -> List[str]:
    """Extract and validate phone numbers from text."""
    if not text:
        return []
    raw_matches = PHONE_REGEX.findall(text)
    valid_phones = []
    for raw in raw_matches:
        cleaned = re.sub(r"[^\d+]", "", raw)
        # Phone numbers should have between 7 and 15 digits
        digits_only = re.sub(r"\D", "", cleaned)
        if 7 <= len(digits_only) <= 15:
            # Avoid matching year numbers like 2024 or zip codes
            if len(digits_only) not in (4, 5):
                if raw.strip() not in valid_phones:
                    valid_phones.append(raw.strip())
    return valid_phones


def extract_whatsapp_links(text: str) -> List[str]:
    """Extract WhatsApp direct links from text or generate from phone numbers if explicit."""
    if not text:
        return []
    matches = WHATSAPP_LINK_REGEX.findall(text)
    links = []
    for num in matches:
        link = f"https://wa.me/{num}"
        if link not in links:
            links.append(link)
    return links


def clean_url(url: str) -> str:
    """Remove tracking parameters (utm_*, ref, igshid, etc.) from profile URLs."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Filter query params
        tracked_keys = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "igshid", "fbclid", "ref", "s", "t"}
        query_pairs = parse_qsl(parsed.query)
        cleaned_pairs = [(k, v) for k, v in query_pairs if k.lower() not in tracked_keys]
        new_query = urlencode(cleaned_pairs)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), parsed.params, new_query, parsed.fragment))
    except Exception:
        return url.strip()


def is_valid_url(url: str) -> bool:
    """Verify if a string is a valid HTTP/HTTPS URL."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False
