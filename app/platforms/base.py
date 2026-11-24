from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.schemas import QueryUnderstanding
from app.utils.validators import clean_url, is_valid_url


class BasePlatform(ABC):
    """Abstract base class for all prospect discovery platforms."""
    
    name: str = "Base"
    domain: str = ""

    @abstractmethod
    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        """Constructs an optimized search/dork query for this platform."""
        pass

    @abstractmethod
    def validate_profile_url(self, url: str) -> bool:
        """Validates if a URL actually belongs to a public profile/channel/page on this platform."""
        pass

    def extract_profile_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extracts structured profile details from a search engine result item.
        Returns None if the result is invalid or not a valid profile.
        """
        raw_url = item.get("url") or item.get("link") or ""
        cleaned = clean_url(raw_url)
        if not cleaned or not self.validate_profile_url(cleaned):
            return None

        title = item.get("title", "")
        snippet = item.get("snippet") or item.get("body") or ""

        return {
            "platform": self.name,
            "url": cleaned,
            "title": title,
            "snippet": snippet,
        }
