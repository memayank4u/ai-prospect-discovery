import re
from app.platforms.base import BasePlatform
from app.schemas import QueryUnderstanding


class WhatsAppPlatform(BasePlatform):
    name = "WhatsApp"
    domain = "wa.me"

    def build_search_query(self, query_info: QueryUnderstanding) -> str:
        loc = query_info.location.to_location_string()
        loc_str = f'"{loc}"' if loc != "Unknown" else ""
        interest_str = f'"{query_info.interest}"' if query_info.interest else ""
        return f'("wa.me" OR "chat.whatsapp.com") {interest_str} {loc_str}'.strip()

    def validate_profile_url(self, url: str) -> bool:
        if not url:
            return False
        return bool(re.search(r"(?:wa\.me\/\d+|api\.whatsapp\.com\/send\?phone=\d+|chat\.whatsapp\.com\/[A-Za-z0-9_-]+)", url, re.IGNORECASE))
