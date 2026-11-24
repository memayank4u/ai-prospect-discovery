from typing import Dict
from app.schemas import QueryUnderstanding
from app.services.llm_service import llm_service
from app.platforms import SUPPORTED_PLATFORMS


class QueryService:
    async def process_query(self, query: str) -> QueryUnderstanding:
        """Parses natural language query into structured understanding."""
        return await llm_service.analyze_query(query)

    def generate_platform_queries(self, query_info: QueryUnderstanding) -> Dict[str, str]:
        """Generates platform-specific search dork queries for each supported platform."""
        queries = {}
        for platform in SUPPORTED_PLATFORMS:
            queries[platform.name] = platform.build_search_query(query_info)
        return queries


query_service = QueryService()
