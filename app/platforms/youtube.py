import re
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class YouTubePlatform(BasePlatform):
    name = "YouTube"
    domain = "youtube.com"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc_str = query_info.location.to_location_string()
        loc_clause = f'"{loc_str}"' if loc_str != "Unknown" else ""
        interest_clause = f'"{query_info.interest}"' if query_info.interest else ""
        return f'site:youtube.com/@ {interest_clause} {loc_clause}'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        # Matches youtube.com/@channel or youtube.com/channel/UC... or youtube.com/c/name
        # Excludes /watch?v=, /shorts/, /feed/
        if any(bad in url for bad in ["/watch", "/shorts", "/feed", "/playlist"]):
            return False
        return bool(re.search(r"youtube\.com\/(?:@|channel\/|c\/|user\/)[A-Za-z0-9_.-]+", url, re.IGNORECASE))
