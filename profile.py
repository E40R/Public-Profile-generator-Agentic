from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CareerTimelineItem(BaseModel):
    year: str = Field(description="Year or period (e.g., '1992' or '2014-Present')")
    event: str = Field(description="Role, appointment, or major career milestone")


class ReferenceItem(BaseModel):
    source: str = Field(description="Name of the source (e.g., 'Wikipedia', 'Forbes', 'CNBC')")
    url: str = Field(description="URL to the source")


class SourceExtract(BaseModel):
    """Structured extraction from a single raw source chunk/article."""
    source_name: str = Field(description="Name of the source platform or website")
    source_url: str = Field(description="URL of the source")
    full_name: Optional[str] = Field(default=None, description="Full name mentioned in this source")
    nationality: Optional[str] = Field(default=None, description="Nationality mentioned in this source")
    current_role: Optional[str] = Field(default=None, description="Current occupation or title")
    industry: Optional[str] = Field(default=None, description="Industry sector")
    current_city_country: Optional[str] = Field(default=None, description="Current city/region and country of residence/office")
    biography_summary: Optional[str] = Field(default=None, description="Biographical summary extracted from this source")
    career_timeline: List[str] = Field(default_factory=list, description="List of career timeline events with dates found in this source")
    education: List[str] = Field(default_factory=list, description="Degrees, universities, or education background")
    interests: List[str] = Field(default_factory=list, description="Personal interests, hobbies, philanthropy, or focus areas")
    estimated_net_worth: Optional[str] = Field(default=None, description="Estimated net worth figure if explicitly mentioned (e.g., 'US$1.5 – 2.0 Billion')")
    net_worth_date: Optional[str] = Field(default=None, description="Date or year of the net worth estimate")
    recent_news: List[str] = Field(default_factory=list, description="Recent public activities, news items, or achievements")
    photo_url: Optional[str] = Field(default=None, description="Image or photo URL if found")
    missing_info_notes: List[str] = Field(default_factory=list, description="Notes on any information that was looked for but explicitly not found in this chunk")


class FinalProfile(BaseModel):
    """Synthesized and verified final executive profile combining all sources."""
    full_name: str = Field(description="Verified full name")
    photo_url: Optional[str] = Field(default=None, description="URL of the person's portrait or main image")
    nationality: str = Field(description="Verified nationality (e.g. 'American (born in India)')")
    current_role: str = Field(description="Current role and organization (e.g. 'Chairman & Chief Executive Officer, Microsoft')")
    industry: str = Field(description="Industry (e.g. 'Technology')")
    current_city_country: str = Field(description="Current city/state and country (e.g. 'Bellevue, Washington, United States')")
    executive_summary: str = Field(description="Concise 2-3 sentence executive summary of the leader's impact and background")
    biography: str = Field(description="Detailed biographical summary highlighting career progression and achievements")
    career_timeline: List[CareerTimelineItem] = Field(default_factory=list, description="Chronological career milestones")
    education: List[str] = Field(default_factory=list, description="Educational qualifications and institutions")
    interests: List[str] = Field(default_factory=list, description="Key professional and personal interests, hobbies, or philanthropy")
    estimated_net_worth: str = Field(description="Estimated net worth range with date/source context (e.g. 'US$1.5 – 2.0 Billion (Public estimates as of 2025)')")
    net_worth_details_or_conflicts: Optional[str] = Field(
        default=None, 
        description="Explanation of net worth sources, variations, or discrepancies across reports (e.g., 'Forbes reported $1.8B while Wikipedia/Bloomberg cited $2.0B')"
    )
    recent_news: List[str] = Field(default_factory=list, description="Recent public activities, keynotes, or strategic moves")
    references: List[ReferenceItem] = Field(default_factory=list, description="List of all unique references and source URLs used")
    missing_or_conflicting_info: List[str] = Field(
        default_factory=list, 
        description="Explicit documentation of any missing data or conflicting statements across public sources"
    )
