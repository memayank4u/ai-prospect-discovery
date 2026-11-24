import re
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class ThreadsPlatform(BasePlatform):
    name = "Threads"
    domain = "threads.net"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc_str = query_info.location.to_location_string()
        loc_clause = f'"{loc_str}"' if loc_str != "Unknown" else ""
        interest_clause = f'"{query_info.interest}"' if query_info.interest else ""
        return f'site:threads.net/@ {interest_clause} {loc_clause}'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        # Matches threads.net/@username (excluding /post/)
        if "/post/" in url:
            return False
        return bool(re.search(r"threads\.net\/@[A-Za-z0-9_.-]+", url, re.IGNORECASE))
