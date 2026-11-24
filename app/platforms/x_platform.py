import re
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class XPlatform(BasePlatform):
    name = "X"
    domain = "x.com"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc_str = query_info.location.to_location_string()
        loc_clause = f'"{loc_str}"' if loc_str != "Unknown" else ""
        interest_clause = f'"{query_info.interest}"' if query_info.interest else ""
        return f'(site:x.com OR site:twitter.com) {interest_clause} {loc_clause}'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        # Excludes /status/, /home, /explore, /search, /intent, /hashtag, etc.
        if any(bad in url.lower() for bad in ["/status/", "/home", "/explore", "/search", "/intent", "/hashtag/", "/i/"]):
            return False
        pattern = r"(?:twitter\.com|x\.com)\/[A-Za-z0-9_]{1,30}\/?$"
        return bool(re.search(pattern, url, re.IGNORECASE))
