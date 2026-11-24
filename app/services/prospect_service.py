import asyncio
import logging
from typing import List, Dict, Any
from app.config import settings
from app.schemas import ProspectDiscoveryResponse, QueryUnderstanding
from app.services.query_service import query_service
from app.services.search_service import search_service
from app.services.profile_extractor import profile_extractor
from app.services.relevance_service import relevance_service
from app.services.deduplication_service import deduplication_service
from app.platforms import SUPPORTED_PLATFORMS

logger = logging.getLogger("prospect_service")


class ProspectService:
    async def discover_prospects(self, query: str) -> ProspectDiscoveryResponse:
        """
        Full end-to-end multi-platform prospect discovery pipeline.
        """
        # Step 1: Query Understanding (LLM)
        query_info: QueryUnderstanding = await query_service.process_query(query)
        logger.info(f"Analyzed query: interest='{query_info.interest}', location='{query_info.location.to_location_string()}'")

        # Step 2: Generate platform-specific search dork queries
        platform_queries = query_service.generate_platform_queries(query_info)

        # Step 3: Execute discovery with controlled concurrency to prevent search engine rate limits
        raw_candidates: List[Dict[str, Any]] = []
        semaphore = asyncio.Semaphore(4)

        async def fetch_platform(platform):
            dork = platform_queries.get(platform.name)
            if not dork:
                return platform, []
            async with semaphore:
                try:
                    res = await asyncio.wait_for(
                        search_service.search(dork, max_results=settings.MAX_RESULTS_PER_PLATFORM),
                        timeout=6.0
                    )
                    return platform, res
                except Exception:
                    return platform, []

        fetch_tasks = [fetch_platform(p) for p in SUPPORTED_PLATFORMS]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        location_fallback = query_info.location.to_display_location()
        if location_fallback == "Unknown":
            location_fallback = None

        # Step 4: Extract profile data and public contacts
        for item_res in results:
            if isinstance(item_res, Exception):
                continue
            platform, res = item_res
            for item in res:
                validated_data = platform.extract_profile_data(item)
                if validated_data:
                    extracted = profile_extractor.extract(
                        item=validated_data,
                        platform_name=platform.name,
                        fallback_location=location_fallback
                    )
                    if extracted:
                        raw_candidates.append(extracted)

        logger.info(f"Discovered {len(raw_candidates)} raw profile candidates across platforms")

        # Step 5: Relevance filtering
        relevant_candidates = relevance_service.filter_relevant_candidates(raw_candidates, query_info)
        logger.info(f"{len(relevant_candidates)} candidates passed relevance evaluation")

        # Step 6: Deduplication & Entity Consolidation
        consolidated_prospects = deduplication_service.consolidate(relevant_candidates)
        logger.info(f"Consolidated into {len(consolidated_prospects)} unique prospects")

        return ProspectDiscoveryResponse(
            success=True,
            query=query,
            total_prospects=len(consolidated_prospects),
            prospects=consolidated_prospects
        )


prospect_service = ProspectService()
