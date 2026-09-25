"""Models that configure LLM output for claim extraction and analysis."""

from typing import Literal
from pydantic import BaseModel, Field

TOPIC_TAGS = [
    "Politics UK", "Politics USA", "Politics International", "Elections US",
    "Elections UK", "Elections International", "War/Conflict",
    "Military", "Terrorism", "Abortion", "Immigration", "Economy Finance",
    "Trade Tariffs", "Healthcare", "Public Health Pandemic", "Vaccines",
    "Medicine Treatment", "Science General", "Climate Change", "Environment",
    "Energy", "Technology", "Artificial Intelligence", "Social Media Platforms",
    "Cybersecurity", "Education", "Religion", "Race Ethnicity", "Gender Sexuality",
    "Crime Law Enforcement", "Judiciary Legal", "Government Corruption",
    "Media Journalism", "Celebrity Entertainment", "Sports", "Natural Disaster",
    "Conspiracy Theory", "History Revisionism", "Business Corporate", "Labor Employment",
    "Foreign Interference", "Public Figure Statement", "Europe", "Asia", "Africa",
    "Americas", "Middle East", "Oceania", "Other"
]

TopicTag = Literal[tuple(TOPIC_TAGS)]

TECHNIQUE_TAGS = [
    "AI Generated Content", "Manipulated Media", "Deepfake", "Misleading Context",
    "Miscaptioned", "Satire Mistaken As Real", "Statistical Distortion",
    "Cherry Picking", "Outdated Content", "Unverified Claim", "Opinion Stated As Fact",
    "Pseudoscience", "Conspiracy Narrative", "Astroturfing", "Bot Amplification", "None"
]

TechniqueTag = Literal[tuple(TECHNIQUE_TAGS)]


class VerdictResult(BaseModel):
    """Result of verifying a single claim against an article."""
    claim: str
    verdict: Literal["Supported", "Contradicted",
                     "Mixed / Missing Context", "Unclear / Not enough evidence"]
    reasoning: str
    misinformation_type: TechniqueTag = Field(  # type: ignore[valid-type]
        description=f"Technique tag for the misinformation. If the claim is supported by the article and is not\
          misleading, assign 'None'. Choose from the allowed list only: {TECHNIQUE_TAGS}."
    )
    entities: list[str] = Field(
        description="People, organizations, or places named in the claim")
    tags: list[TopicTag] = Field(  # type: ignore[valid-type]
        description=f"Topic tags for the verdict. Choose from the allowed list only: {TOPIC_TAGS}",
        min_length=1,
        max_length=2
    )
    sources: list[str] = Field(
        description="Article URL that the verdict is based on.")
