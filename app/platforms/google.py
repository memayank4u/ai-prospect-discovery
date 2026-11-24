from urllib.parse import urlparse
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class GooglePlatform(BasePlatform):
    name = "Google"
    domain = "google.com"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc_str = query_info.location.to_location_string()
        loc_clause = f'"{loc_str}"' if loc_str != "Unknown" else ""
        interest_clause = f'"{query_info.interest}"' if query_info.interest else ""
        return f'{interest_clause} {loc_clause} ("about me" OR "founder" OR "official website" OR "contact")'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        # Do not include social platforms here (they are handled by their own platforms)
        # and do not include generic search result URLs or large news aggregators
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        excluded_domains = [
            "google.", "bing.", "yahoo.", "duckduckgo.", "wikipedia.org",
            "linkedin.com", "instagram.com", "twitter.com", "x.com",
            "facebook.com", "youtube.com", "threads.net"
        ]
        if any(bad in netloc for bad in excluded_domains):
            return False
        return len(parsed.path.split("/")) <= 4
