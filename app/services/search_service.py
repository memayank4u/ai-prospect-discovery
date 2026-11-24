import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("search_service")


class SearchService:
    def __init__(self):
        self.timeout = settings.TIMEOUT_SECONDS

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes search across the configured search provider.
        Falls back automatically if the primary provider fails.
        """
        results = []

        # 1. SerpAPI (if key is set)
        if settings.SERPAPI_API_KEY:
            try:
                results = await self._search_serpapi(query, max_results)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"SerpAPI failed: {e}. Trying fallback.")

        # 2. Google Custom Search (if keys set)
        if settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_ID:
            try:
                results = await self._search_google_cse(query, max_results)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Google CSE failed: {e}. Trying fallback.")

        # 3. DuckDuckGo Search (Default / Zero-cost)
        try:
            results = await self._search_duckduckgo(query, max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}. Trying public HTTP search.")

        # 4. Fallback direct HTTP public search
        try:
            results = await self._search_public_fallback(query, max_results)
        except Exception as e:
            logger.error(f"All search providers failed for query '{query}': {e}")

        return results

    async def _search_serpapi(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": settings.SERPAPI_API_KEY,
            "num": max_results,
            "engine": "google"
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            organic = data.get("organic_results", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in organic[:max_results]
            ]

    async def _search_google_cse(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": settings.GOOGLE_CSE_API_KEY,
            "cx": settings.GOOGLE_CSE_ID,
            "q": query,
            "num": min(max_results, 10)
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in items[:max_results]
            ]

    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Executes DuckDuckGo search using ddgs / duckduckgo_search library in a thread."""
        def run_sync_ddg():
            try:
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS

                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))
            except Exception as ex:
                logger.debug(f"DDGS run error: {ex}")
                return []

        raw_results = await asyncio.to_thread(run_sync_ddg)
        formatted = []
        for item in raw_results:
            formatted.append({
                "title": item.get("title", ""),
                "url": item.get("href") or item.get("link", ""),
                "snippet": item.get("body") or item.get("snippet", "")
            })
        return formatted

    async def _search_public_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Direct fallback search using HTML parsing when APIs are rate limited."""
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.post(url, data={"q": query}, headers=headers)
            if resp.status_code != 200:
                return []

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for r in soup.select(".result"):
                title_elem = r.select_one(".result__title a")
                snippet_elem = r.select_one(".result__snippet")
                if title_elem and title_elem.get("href"):
                    raw_href = title_elem["href"]
                    # Extract target URL from DDG redirect link if needed
                    actual_url = raw_href
                    if "uddg=" in raw_href:
                        from urllib.parse import parse_qs, urlparse, unquote
                        parsed_qs = parse_qs(urlparse(raw_href).query)
                        if "uddg" in parsed_qs:
                            actual_url = unquote(parsed_qs["uddg"][0])

                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": actual_url,
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                    })
                    if len(results) >= max_results:
                        break
            return results


search_service = SearchService()
