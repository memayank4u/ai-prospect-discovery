import re
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class LinkedInPlatform(BasePlatform):
    name = "LinkedIn"
    domain = "linkedin.com"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc = query_info.location.to_location_string()
        loc_str = f'"{loc}"' if loc != "Unknown" else ""
        interest_str = f'"{query_info.interest}"' if query_info.interest else ""
        return f'site:linkedin.com/in/ {interest_str} {loc_str}'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        return bool(re.search(r"linkedin\.com\/in\/[A-Za-z0-9_-]+", url, re.IGNORECASE))
