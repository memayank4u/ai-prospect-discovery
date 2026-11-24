import json
import logging
import re
from typing import Optional, Dict, Any
from app.config import settings
from app.schemas import QueryUnderstanding, LocationInfo

logger = logging.getLogger("llm_service")

# Prompt template optimized for minimal token usage
SYSTEM_PROMPT = """You are an AI Prospect Query Analyzer.
Extract structured search parameters from the natural language query.
Return pure JSON matching this exact structure:
{
  "interest": "string (core topic/industry)",
  "audience": "string (target profile)",
  "location": {
    "city": "string or null",
    "state": "string or null",
    "country": "string or null"
  },
  "target_type": "individual or business",
  "search_keywords": ["keyword1", "keyword2"]
}
Do not include any explanation or markdown tags outside the JSON."""


class LLMService:
    def __init__(self):
        self._cache: Dict[str, QueryUnderstanding] = {}
        self.gemini_client = None
        self.openai_client = None

        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    async def analyze_query(self, query: str) -> QueryUnderstanding:
        """Analyzes query using LLM with caching and heuristic fallback."""
        cache_key = query.strip().lower()
        if settings.ENABLE_CACHE and cache_key in self._cache:
            logger.info(f"Query understanding cache hit for: '{query}'")
            return self._cache[cache_key]

        result: Optional[QueryUnderstanding] = None

        # Try Gemini if configured
        if settings.LLM_PROVIDER == "gemini" and self.gemini_client:
            result = await self._call_gemini(query)

        # Try OpenAI if configured or as fallback
        if not result and (settings.LLM_PROVIDER == "openai" or self.openai_client):
            result = await self._call_openai(query)

        # Fallback to intelligent deterministic heuristic parser
        if not result:
            logger.info("Using deterministic NLP parser (no API key or provider unavailable)")
            result = self._heuristic_parse(query)

        if settings.ENABLE_CACHE and result:
            self._cache[cache_key] = result

        return result

    async def _call_gemini(self, query: str) -> Optional[QueryUnderstanding]:
        try:
            prompt = f"{SYSTEM_PROMPT}\n\nQuery: {query}"
            response = self.gemini_client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            raw_text = response.text
            parsed = self._extract_json(raw_text)
            if parsed:
                return QueryUnderstanding(**parsed)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
        return None

    async def _call_openai(self, query: str) -> Optional[QueryUnderstanding]:
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content
            parsed = json.loads(raw_text)
            return QueryUnderstanding(**parsed)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            clean = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean.strip(), flags=re.MULTILINE)
            return json.loads(clean)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None

    def _heuristic_parse(self, query: str) -> QueryUnderstanding:
        """
        Deterministic NLP extractor for zero-cost, instant-response query understanding.
        Extracts interest, audience, and geographical locations (city, state, country).
        """
        lower = query.lower()
        words = query.split()

        # Known country mappings
        country_aliases = {
            "usa": "USA", "united states": "USA", "us": "USA", "america": "USA",
            "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK",
            "india": "India", "uae": "UAE", "united arab emirates": "UAE", "dubai": "UAE",
            "canada": "Canada", "australia": "Australia", "germany": "Germany"
        }

        detected_country = None
        for alias, country in country_aliases.items():
            if re.search(r"\b" + re.escape(alias) + r"\b", lower):
                detected_country = country
                break

        # Known city mappings
        city_state_map = {
            "washington dc": ("Washington DC", "District of Columbia", "USA"),
            "new york": ("New York", "New York", "USA"),
            "london": ("London", None, "UK"),
            "ahmedabad": ("Ahmedabad", "Gujarat", "India"),
            "dubai": ("Dubai", "Dubai", "UAE"),
            "san francisco": ("San Francisco", "California", "USA"),
            "los angeles": ("Los Angeles", "California", "USA"),
            "chicago": ("Chicago", "Illinois", "USA"),
            "toronto": ("Toronto", "Ontario", "Canada"),
            "mumbai": ("Mumbai", "Maharashtra", "India"),
            "delhi": ("Delhi", "Delhi", "India"),
            "bangalore": ("Bangalore", "Karnataka", "India")
        }

        detected_city = None
        detected_state = None
        for city_key, (c, s, ctry) in city_state_map.items():
            if city_key in lower:
                detected_city = c
                detected_state = s
                if not detected_country:
                    detected_country = ctry
                break

        # Extract audience & interest
        # Patterns like: "<Audience> in <Location>"
        target_audience = query
        interest = query

        in_split = re.split(r"\s+in\s+", query, flags=re.IGNORECASE)
        if len(in_split) > 1:
            target_audience = in_split[0].strip()
            # If location was not found by dictionary, take the parts after 'in'
            if not detected_city and not detected_country:
                loc_candidate = in_split[1].strip()
                detected_city = loc_candidate

        # Extract core interest from audience (e.g. "Football lovers" -> "Football", "Digital marketing agency owners" -> "Digital Marketing")
        interest_clean = target_audience
        for noise in ["lovers", "enthusiasts", "owners", "founders", "fans", "directors", "specialists", "managers"]:
            interest_clean = re.sub(r"\b" + noise + r"\b", "", interest_clean, flags=re.IGNORECASE).strip()

        target_type = "business" if any(b in lower for b in ["agency", "restaurant", "company", "store", "business"]) else "individual"

        return QueryUnderstanding(
            interest=interest_clean or target_audience,
            audience=target_audience,
            location=LocationInfo(
                city=detected_city,
                state=detected_state,
                country=detected_country
            ),
            target_type=target_type,
            search_keywords=[w for w in words if len(w) > 3 and w.lower() not in ["lovers", "owners", "from", "with"]]
        )


llm_service = LLMService()
