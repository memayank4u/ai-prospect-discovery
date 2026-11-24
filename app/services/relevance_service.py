import re
from typing import List, Dict, Any
from app.schemas import QueryUnderstanding


class RelevanceService:
    def filter_relevant_candidates(
        self,
        raw_candidates: List[Dict[str, Any]],
        query_info: QueryUnderstanding
    ) -> List[Dict[str, Any]]:
        """
        Filters candidate profiles based on interest, audience, and geographical relevance.
        Rejects false positives and non-matching profiles.
        """
        if not raw_candidates:
            return []

        interest_keywords = [
            k.lower() for k in [query_info.interest, query_info.audience] + query_info.search_keywords
            if k and len(k) > 2
        ]

        loc = query_info.location
        location_keywords = [
            loc_val.lower() for loc_val in [loc.city, loc.state, loc.country]
            if loc_val and len(loc_val) > 2
        ]

        relevant = []
        for cand in raw_candidates:
            score = self._compute_relevance_score(
                candidate=cand,
                interest_keywords=interest_keywords,
                location_keywords=location_keywords
            )
            # Accept if score is >= 0.5 (or if there are direct platform matches with the dork query)
            if score >= 0.5:
                cand["relevance_score"] = score
                relevant.append(cand)

        return relevant

    def _compute_relevance_score(
        self,
        candidate: Dict[str, Any],
        interest_keywords: List[str],
        location_keywords: List[str]
    ) -> float:
        text = f"{candidate.get('name', '')} {candidate.get('location', '')} {candidate.get('source_snippet', '')}".lower()

        score = 0.4  # baseline for search-dork matched results

        # Interest relevance (+0.4)
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in interest_keywords):
            score += 0.4

        # Location relevance (+0.2)
        if location_keywords and any(kw in text for kw in location_keywords):
            score += 0.2

        return min(score, 1.0)


relevance_service = RelevanceService()
