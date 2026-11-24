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
        name = candidate.get("name", "")
        cand_loc = candidate.get("location", "")
        snippet = candidate.get("source_snippet", "")
        text = f"{name} {snippet}".lower()
        full_loc_text = f"{cand_loc} {text}".lower()

        # 1. Reject generic media headlines, sports scores, and aggregate websites
        bad_keywords = [
            "latest news", "scores & fixtures", "scores,", "highlights",
            "nfl.com", "espn", "bbc sport", "premier league", "championship"
        ]
        if any(bw in name.lower() or bw in cand_loc.lower() for bw in bad_keywords):
            return 0.0

        # 2. Candidate must match the core domain interest (e.g. Football)
        if interest_keywords:
            if not any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in interest_keywords):
                return 0.0

        # 3. Candidate must match target location when location is specified in query
        if location_keywords:
            # Must mention target location in snippet or location field
            if not any(kw in full_loc_text for kw in location_keywords):
                return 0.0

            # If an explicit location was parsed (e.g. "Chicago"), and it conflicts with target location, reject!
            if cand_loc and not any(kw in cand_loc.lower() for kw in location_keywords):
                return 0.0

        return 0.8


relevance_service = RelevanceService()
