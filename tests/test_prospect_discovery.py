import pytest
from app.schemas import QueryUnderstanding, LocationInfo, SocialLink, Prospect
from app.utils.validators import extract_emails, extract_phones, extract_whatsapp_links, clean_url
from app.utils.normalizers import clean_prospect_name, calculate_name_similarity
from app.services.deduplication_service import deduplication_service
from app.services.llm_service import llm_service
from app.platforms import SUPPORTED_PLATFORMS, PLATFORM_BY_NAME


def test_clean_prospect_name():
    assert clean_prospect_name("John Smith - Founder & CEO | LinkedIn") == "John Smith"
    assert clean_prospect_name("Michael Johnson (@mjohnson) • Instagram photos and videos") == "Michael Johnson"
    assert clean_prospect_name("David Miller - Washington DC | X") == "David Miller"


def test_validators_email_extraction():
    text = "Contact me at john.smith@agency.com or support@company.org for inquiries."
    emails = extract_emails(text)
    assert "john.smith@agency.com" in emails
    assert "support@company.org" in emails


def test_validators_phone_and_whatsapp():
    text = "Call +1-202-555-0199 or message on https://wa.me/12025550199"
    wa_links = extract_whatsapp_links(text)
    assert "https://wa.me/12025550199" in wa_links


def test_clean_url():
    dirty = "https://www.linkedin.com/in/johnsmith?utm_source=share&utm_medium=member_desktop"
    cleaned = clean_url(dirty)
    assert "utm_source" not in cleaned
    assert cleaned == "https://www.linkedin.com/in/johnsmith"


def test_platform_query_generation():
    query_info = QueryUnderstanding(
        interest="Football",
        audience="Football lovers",
        location=LocationInfo(city="Washington DC", state="District of Columbia", country="USA")
    )
    linkedin = PLATFORM_BY_NAME["linkedin"]
    query = linkedin.build_search_query(query_info)
    assert "site:linkedin.com/in/" in query
    assert "Football" in query
    assert "Washington DC" in query


def test_heuristic_query_understanding():
    parsed = llm_service._heuristic_parse("Football lovers in Washington DC in USA")
    assert "football" in parsed.interest.lower()
    assert parsed.location.city == "Washington DC"
    assert parsed.location.country == "USA"


def test_deduplication_consolidation():
    raw_candidates = [
        {
            "name": "John Smith",
            "location": "Washington DC, USA",
            "social_links": [
                SocialLink(platform="LinkedIn", link="https://linkedin.com/in/johnsmith")
            ],
            "source_snippet": "Football coach in Washington DC"
        },
        {
            "name": "John Smith",
            "location": "Washington DC",
            "social_links": [
                SocialLink(platform="Instagram", link="https://instagram.com/johnsmith"),
                SocialLink(platform="Email", link="mailto:john@smith.com")
            ],
            "source_snippet": "Passionate football enthusiast"
        }
    ]
    consolidated = deduplication_service.consolidate(raw_candidates)
    assert len(consolidated) == 1
    prospect = consolidated[0]
    assert prospect.name == "John Smith"
    platforms = [sl.platform for sl in prospect.social_link]
    assert "LinkedIn" in platforms
    assert "Instagram" in platforms
    assert "Email" in platforms
