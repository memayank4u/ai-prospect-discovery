from app.platforms.linkedin import LinkedInPlatform
from app.platforms.x_platform import XPlatform
from app.platforms.youtube import YouTubePlatform
from app.platforms.instagram import InstagramPlatform
from app.platforms.facebook import FacebookPlatform
from app.platforms.threads import ThreadsPlatform
from app.platforms.whatsapp import WhatsAppPlatform
from app.platforms.google import GooglePlatform

SUPPORTED_PLATFORMS = [
    LinkedInPlatform(),
    XPlatform(),
    YouTubePlatform(),
    InstagramPlatform(),
    FacebookPlatform(),
    ThreadsPlatform(),
    WhatsAppPlatform(),
    GooglePlatform(),
]

PLATFORM_BY_NAME = {p.name.lower(): p for p in SUPPORTED_PLATFORMS}
