"""Models that configure LLM output for claim extraction."""
from typing import Literal
from pydantic import BaseModel, Field

TOPIC_TAGS = [
    "Politics UK", "Politics USA", "Politics International", "Elections US", "Elections UK",
    "Elections International", "War/Conflict", "Military", "Terrorism", "Abortion", "Immigration",
    "Economy Finance", "Trade Tariffs", "Healthcare", "Public Health Pandemic", "Vaccines",
    "Medicine Treatment", "Science General", "Climate Change", "Environment", "Energy",
    "Technology", "Artificial Intelligence", "Social Media Platforms", "Cybersecurity", "Education",
    "Religion", "Race Ethnicity", "Gender Sexuality", "Crime Law Enforcement", "Judiciary Legal",
    "Government Corruption", "Media Journalism", "Celebrity Entertainment", "Sports",
    "Natural Disaster", "Conspiracy Theory", "History Revisionism", "Business Corporate",
    "Labor Employment", "Foreign Interference", "Public Figure Statement", "Europe", "Asia",
    "Africa", "Americas", "Middle East", "Oceania", "Other"
]

TopicTag = Literal[tuple(TOPIC_TAGS)]

TECHNIQUE_TAGS = [
    "AI Generated Content", "Manipulated Media", "Deepfake", "Misleading Context",
    "Miscaptioned", "Satire Mistaken As Real", "Statistical Distortion", "Cherry Picking",
    "Outdated Content", "Unverified Claim", "Opinion Stated As Fact", "Pseudoscience",
    "Conspiracy Narrative", "Astroturfing", "Bot Amplification", "None"
]

TechniqueTag = Literal[tuple(TECHNIQUE_TAGS)]


class Claim(BaseModel):
    """A single claim extracted from user-provided text."""
    text: str = Field(
        description="The claim stated in a single, self-contained, checkable sentence")
    claim_type: Literal["event", "statistic", "promise", "opinion", "other"] = Field(
        description=(
            "event: something that happened (a speech, a vote, an action). "
            "statistic: a specific number, set of numbers, or measurable fact - a fact or figure that should be externally verifiable. "
            "promise: a future commitment that cannot yet be true or false. "
            "opinion: a subjective statement reflecting personal beliefs or views that cannot be objectively verified. Eg. 'I think this policy is unfair.' , 'X is an idiot.'"
            "other: vague narrative/editorial framing with no specific verifiable content."
        ))
    verification_method: Literal["external_search", "context_only", "not_verifiable"] = Field(
        description=(
            "external_search: requires checking outside sources."
            "context_only: contextual information that is given in the article itself and can be verified without external sources, and would not need to be fact checked. e.g. 'x gave a speech on Sunday.', 'x raised concerns'"
            "not_verifiable: opinion, future promise, or too vague to check — skip entirely."
        )

    )
    entities: list[str] = Field(
        description="People, organizations, or places named in the claim")

    tags: list[TopicTag] = Field(  # type: ignore[valid-type]
        description=f"Topic tags for the claim. Choose up to 2 from the allowed list only: {TOPIC_TAGS}",
        min_length=1,
        max_length=2
    )


class InputAnalysis(BaseModel):
    """Analysis of the input text, including extracted claims, topic tags, and a summary."""
    claims: list[Claim]
    tags: list[TopicTag] = Field(  # type: ignore[valid-type]
        description=f"Topic tags for the article. Choose from the allowed list only: {TOPIC_TAGS}",
        min_length=1,
        max_length=2
    )
    summary: str = Field(
        description="One-sentence summary of what the article is about")
