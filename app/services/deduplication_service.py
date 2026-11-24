import re
from typing import List, Dict, Any
from urllib.parse import urlparse
from app.schemas import Prospect, SocialLink
from app.utils.normalizers import normalize_string, calculate_name_similarity


class DeduplicationService:
    def consolidate(self, raw_prospects: List[Dict[str, Any]]) -> List[Prospect]:
        """
        Consolidates multiple profiles belonging to the same individual into single prospect records.
        Deduplicates based on normalized name, location, and social handle signals.
        """
        if not raw_prospects:
            return []

        consolidated: List[Dict[str, Any]] = []

        for candidate in raw_prospects:
            cand_name = candidate["name"]
            cand_location = candidate.get("location")
            cand_links = candidate.get("social_links", [])
            cand_handle = self._extract_handle(cand_links)

            matched_idx = -1
            best_score = 0.0

            for idx, existing in enumerate(consolidated):
                ex_name = existing["name"]
                ex_location = existing.get("location")
                ex_handle = existing.get("handle")

                sim = calculate_name_similarity(cand_name, ex_name)

                # Strong match condition:
                # 1. Exact name match
                # 2. Or high name similarity (>0.8) and matching location or matching handle
                is_match = False
                if sim >= 0.95:
                    is_match = True
                elif sim >= 0.75:
                    if cand_handle and ex_handle and cand_handle == ex_handle:
                        is_match = True
                    elif cand_location and ex_location and normalize_string(cand_location) == normalize_string(ex_location):
                        is_match = True

                if is_match and sim > best_score:
                    best_score = sim
                    matched_idx = idx

            if matched_idx >= 0:
                # Merge into existing prospect
                target = consolidated[matched_idx]
                
                # Combine social links without duplicate URLs
                existing_urls = {l.link for l in target["social_links"]}
                for link in cand_links:
                    if link.link not in existing_urls:
                        target["social_links"].append(link)
                        existing_urls.add(link.link)

                # Prefer the more specific location
                if not target.get("location") and cand_location:
                    target["location"] = cand_location
                elif cand_location and len(cand_location) > len(target.get("location", "")):
                    target["location"] = cand_location

                # Record handle if missing
                if not target.get("handle") and cand_handle:
                    target["handle"] = cand_handle
            else:
                # Add new prospect entry
                consolidated.append({
                    "name": cand_name,
                    "location": cand_location,
                    "social_links": list(cand_links),
                    "handle": cand_handle
                })

        # Convert to strict Pydantic Prospect objects
        output: List[Prospect] = []
        for item in consolidated:
            # Sort social links deterministically by platform name
            sorted_links = sorted(item["social_links"], key=lambda x: x.platform)
            output.append(Prospect(
                name=item["name"],
                location=item.get("location"),
                social_link=sorted_links
            ))

        return output

    def _extract_handle(self, links: List[SocialLink]) -> str:
        """Extracts username handle from social link URL (e.g. instagram.com/johnsmith -> johnsmith)."""
        for l in links:
            if l.platform in ["X", "Instagram", "Threads", "YouTube"]:
                try:
                    path = urlparse(l.link).path.strip("/@")
                    if path and "/" not in path:
                        return path.lower()
                except Exception:
                    pass
        return ""


deduplication_service = DeduplicationService()
