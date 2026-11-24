import asyncio
import json
from app.services.prospect_service import prospect_service

TEST_QUERIES = [
    "Football lovers in Washington DC in USA",
    "Digital marketing agency owners in New York USA",
    "Startup founders in London UK",
    "Cricket lovers in Ahmedabad India",
    "Restaurant owners in Dubai UAE"
]


async def run_demos():
    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n==========================================")
        print(f"[{idx}/5] Executing Discovery Query: {query}")
        print(f"==========================================")
        try:
            res = await prospect_service.discover_prospects(query)
            print(f"Success: {res.success}")
            print(f"Total Discovered Prospects: {res.total_prospects}")
            print(json.dumps(res.model_dump(), indent=2))
        except Exception as e:
            print(f"Error on query '{query}': {e}")


if __name__ == "__main__":
    asyncio.run(run_demos())
