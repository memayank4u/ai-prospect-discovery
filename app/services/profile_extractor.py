import re
from typing import Dict, Any, List, Optional
from app.schemas import SocialLink
from app.utils.normalizers import clean_prospect_name
from app.utils.validators import extract_emails, extract_phones, extract_whatsapp_links, clean_url


class ProfileExtractor:
    def extract(self, item: Dict[str, Any], platform_name: str, fallback_location: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Extracts prospect information from a validated search result item.
        Extracts public contact information (Email, Phone, WhatsApp) and associates with the prospect.
        """
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        url = clean_url(item.get("url", ""))

        if not url:
            return None

        # Clean prospect name
        name = clean_prospect_name(title)
        if not name or name.lower() in ["unknown", "profile", "home", "search", "explore"]:
            # Try snippet if title is just generic
            words = snippet.split()
            if len(words) >= 2 and words[0].istitle() and words[1].istitle():
                name = f"{words[0]} {words[1]}"
            else:
                return None

        # Try to detect location from snippet or fallback
        discovered_location = self._detect_location(snippet, title) or fallback_location

        social_links: List[SocialLink] = []

        # 1. Primary platform profile link
        social_links.append(SocialLink(platform=platform_name, link=url))

        # 2. Extract public emails from text
        combined_text = f"{title} {snippet}"
        emails = extract_emails(combined_text)
        for email in emails:
            social_links.append(SocialLink(platform="Email", link=f"mailto:{email}"))

        # 3. Extract public WhatsApp links
        wa_links = extract_whatsapp_links(combined_text)
        for wa in wa_links:
            social_links.append(SocialLink(platform="WhatsApp", link=wa))

        # 4. Extract public phones (can also be mapped to WhatsApp if country code is present)
        phones = extract_phones(combined_text)
        for phone in phones:
            digits = re.sub(r"\D", "", phone)
            if digits and len(digits) >= 10 and not any(l.platform == "WhatsApp" for l in social_links):
                social_links.append(SocialLink(platform="WhatsApp", link=f"https://wa.me/{digits}"))

        return {
            "name": name,
            "location": discovered_location,
            "social_links": social_links,
            "source_snippet": snippet
        }

    def _detect_location(self, snippet: str, title: str) -> Optional[str]:
        """Scans snippet for common location patterns like 'Location: Washington, DC' or 'based in London'."""
        text = f"{title} {snippet}"
        match = re.search(r"(?:based in|located in|living in|from)\s+([A-Za-z\s]+(?:,\s*[A-Za-z\s]+)?)", text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            ignored_locations = {"google", "facebook", "linkedin", "instagram", "twitter", "x", "youtube", "threads", "whatsapp", "website", "online", "the web", "scratch"}
            if candidate.lower() in ignored_locations:
                return None
            # Avoid long sentences
            if len(candidate.split()) <= 4:
                return candidate.title()
        return None


profile_extractor = ProfileExtractor()
