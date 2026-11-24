import re
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class FacebookPlatform(BasePlatform):
    name = "Facebook"
    domain = "facebook.com"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc_str = query_info.location.to_location_string()
        loc_clause = f'"{loc_str}"' if loc_str != "Unknown" else ""
        interest_clause = f'"{query_info.interest}"' if query_info.interest else ""
        return f'site:facebook.com {interest_clause} {loc_clause}'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        # Excludes /sharer, /groups, /watch, /events, /policies, /help, /login
        if any(bad in url for bad in ["/sharer", "/groups/", "/watch", "/events/", "/policies", "/help", "/login", "/photo.php"]):
            return False
        return bool(re.search(r"facebook\.com\/(?:people\/[A-Za-z0-9_.-]+\/\d+|[A-Za-z0-9_.-]{3,50})\/?$", url, re.IGNORECASE))
