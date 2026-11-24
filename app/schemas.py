from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ProspectDiscoveryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language prospect discovery query",
        json_schema_extra={"example": "Football lovers in Washington DC in USA"}
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        clean = v.strip()
        if not clean or len(clean) < 3:
            raise ValueError("Query must be at least 3 characters long and non-empty.")
        return clean


class SocialLink(BaseModel):
    platform: str = Field(..., description="Platform name, e.g. Google, LinkedIn, X, YouTube, Instagram, WhatsApp, Facebook, Email, Threads")
    link: str = Field(..., description="Verified public profile URL or contact link")


class Prospect(BaseModel):
    name: str = Field(..., description="Prospect's full name")
    location: Optional[str] = Field(None, description="Discovered or verified location")
    social_link: List[SocialLink] = Field(default_factory=list, description="Array of verified profile or contact links")


class ProspectDiscoveryResponse(BaseModel):
    success: bool = Field(True, description="Indicates if the query was processed successfully")
    query: str = Field(..., description="The original search query")
    total_prospects: int = Field(..., description="Total count of unique prospects discovered")
    prospects: List[Prospect] = Field(default_factory=list, description="List of discovered consolidated prospects")


class LocationInfo(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    def to_location_string(self) -> str:
        """Concise location keyword for search queries."""
        if self.city:
            return self.city
        if self.state:
            return self.state
        return self.country or "Unknown"

    def to_display_location(self) -> str:
        """Formatted location for final prospect output."""
        parts = [p for p in [self.city, self.country] if p]
        return ", ".join(parts) if parts else "Unknown"


class QueryUnderstanding(BaseModel):
    interest: str = Field(..., description="Primary interest or industry, e.g., Football, Marketing, Restaurant")
    audience: str = Field(..., description="Target audience description, e.g., Football lovers, Agency owners")
    location: LocationInfo = Field(default_factory=LocationInfo)
    target_type: str = Field("individual", description="individual or business")
    search_keywords: List[str] = Field(default_factory=list, description="Extracted relevant keywords for dorking")
