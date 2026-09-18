"""Clean and validate claim/verdict records before load."""

import logging
from collections import Counter
import pandas as pd

logger = logging.getLogger(__name__)

TOPIC_TAGS = [
    "Politics UK", "Politics USA", "Politics International", "Elections US", "Elections UK", "Elections International", "War/Conflict",
    "Military", "Terrorism", "Abortion", "Immigration", "Economy Finance", "Trade Tariffs", "Healthcare", "Public Health Pandemic", "Vaccines",
    "Medicine Treatment", "Science General", "Climate Change", "Environment", "Energy", "Technology", "Artificial Intelligence", "Social Media Platforms",
    "Cybersecurity", "Education", "Religion", "Race Ethnicity", "Gender Sexuality", "Crime Law Enforcement", "Judiciary Legal",
    "Government Corruption", "Media Journalism", "Celebrity Entertainment", "Sports", "Natural Disaster", "Conspiracy Theory",
    "History Revisionism", "Business Corporate", "Labor Employment", "Foreign Interference", "Public Figure Statement",
    "Europe", "Asia", "Africa", "Americas", "Middle East", "Oceania", "Other"
]

TECHNIQUE_TAGS = [
    "AI Generated Content", "Manipulated Media", "Deepfake", "Misleading Context", "Miscaptioned", "Satire Mistaken As Real",
    "Statistical Distortion", "Cherry Picking", "Outdated Content", "Unverified Claim", "Opinion Stated As Fact", "Pseudoscience",
    "Conspiracy Narrative", "Astroturfing", "Bot Amplification", "None"
]

VERDICTS = ["supported", "contradicted", "mixed / missing context", "unclear / not enough evidence"]


def clean_list_value(value):
    """Return value if it's a list, else an empty list."""
    return value if isinstance(value, list) else []


def clean_text_value(value):
    """Return a stripped string, or "" if not a string."""
    return value.strip() if isinstance(value, str) else ""


def clean_float_value(value):
    """Return value if it's a real number, else None."""
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def filter_tags(tags: list[str], exclude: list[str] = None, max_tags: int = 5) -> list[str]:
    """Remove excluded tags and cap the result at max_tags."""
    exclude = exclude if exclude is not None else []
    excluded_lower = {e.lower() for e in exclude}
    filtered = [tag for tag in tags if tag.lower() not in excluded_lower]
    return filtered[:max_tags]


def clean_categorical_value(value, allowed: list[str]) -> str:
    """Return the lowercased value if it's in allowed, else "unknown"."""
    allowed_lower = {a.lower() for a in allowed}
    if isinstance(value, str) and value.lower() in allowed_lower:
        return value.lower()
    logger.warning("Unrecognised categorical value %r, falling back to 'unknown'", value)
    return "unknown"


def clean_categorical_list(values, allowed: list[str]) -> list[str]:
    """Like clean_categorical_value, but for a list: drops any value not in allowed."""
    allowed_lower = {a.lower() for a in allowed}
    cleaned = clean_list_value(values)
    dropped = [v for v in cleaned if not (isinstance(v, str) and v.lower() in allowed_lower)]
    if dropped:
        logger.warning("Dropping unrecognised values %r", dropped)
    return [v for v in cleaned if isinstance(v, str) and v.lower() in allowed_lower]


def dedupe_list(values: list[str]) -> list[str]:
    """Remove case-insensitive duplicates, preserving first-seen order."""
    seen = set()
    result = []
    for value in values:
        key = value.lower()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def sort_tags(tags: list[str]) -> list[str]:
    """Return tags sorted alphabetically, case-insensitive."""
    return sorted(tags, key=str.lower)


def clean_tag_list(tags, exclude: list[str] = None) -> list[str]:
    """Clean, dedupe, filter against TOPIC_TAGS, and alphabetically sort."""
    valid = clean_categorical_list(tags, TOPIC_TAGS)
    deduped = dedupe_list(valid)
    filtered = filter_tags(deduped, exclude=exclude)
    return sort_tags(filtered)


def clean_verdict(verdict: dict) -> dict:
    """Clean one individual per-source verdict dict."""
    return {
        "claim": clean_text_value(verdict.get("claim")),
        "verdict": clean_categorical_value(verdict.get("verdict"), VERDICTS),
        "reasoning": clean_text_value(verdict.get("reasoning")),
        "technique": clean_categorical_value(
            verdict.get("misinformation_type") or verdict.get("technique"), TECHNIQUE_TAGS
        ),
        "entities": dedupe_list(clean_list_value(verdict.get("entities"))),
        "tags": clean_tag_list(verdict.get("tags"), exclude=["fact-checking"]),
        "sources": clean_list_value(verdict.get("sources")),
        "source_name": clean_text_value(verdict.get("source_name")),
    }


def resolve_overall_verdict(cleaned_verdicts: list[dict]) -> str:
    """Majority vote across individual verdicts; falls back on tie or no data."""
    votes = [v["verdict"] for v in cleaned_verdicts if v["verdict"] != "unknown"]
    if not votes:
        return "unclear / not enough evidence"
    counts = Counter(votes)
    top_count = max(counts.values())
    winners = [v for v, c in counts.items() if c == top_count]
    if len(winners) > 1:
        return "unclear / not enough evidence"
    return winners[0]


def transform(combined: dict) -> pd.DataFrame:
    """Clean handler_collate_results.py's claim-keyed output into one row per claim."""
    logger.info("Transforming %d claims", len(combined))
    if not combined:
        logger.warning("No claims to transform")
        return pd.DataFrame()

    rows = []
    for claim_text, data in combined.items():
        raw_verdicts = clean_list_value(data.get("verdicts"))
        cleaned_verdicts = [clean_verdict(v) for v in raw_verdicts]
        summary = data.get("summary") or {}

        rows.append({
            "claim": clean_text_value(claim_text),
            "verdict": resolve_overall_verdict(cleaned_verdicts),
            "summary": clean_text_value(summary.get("summary")),
            "confidence_score": clean_float_value(summary.get("confidence_score")),
            "technique": clean_categorical_value(summary.get("misinformation_type"), TECHNIQUE_TAGS),
            "entities": tuple(dedupe_list(clean_list_value(summary.get("entities")))),
            "tags": tuple(clean_tag_list(summary.get("tags"), exclude=["fact-checking"])),
            "sources": tuple(clean_list_value(summary.get("sources"))),
            "individual_verdicts": cleaned_verdicts,
        })

    df = pd.DataFrame(rows)
    logger.info("Finished transforming %d claims", len(df))
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_combined = {
        "The Eiffel Tower was built in 1822.": {
            "verdicts": [
                {"claim": "The Eiffel Tower was built in 1822.", "verdict": "Contradicted",
                 "reasoning": "It was completed in 1889.", "misinformation_type": "None",
                 "entities": ["Eiffel Tower"], "tags": ["History"], "sources": ["https://fullfact.org/x"],
                 "source_name": "Full Fact"},
            ],
            "summary": {
                "summary": "Sources agree it was 1889, not 1822.",
                "confidence_score": 0.95,
                "misinformation_type": "None",
                "entities": ["Eiffel Tower"],
                "tags": ["History Revisionism"],
                "sources": ["https://fullfact.org/x"],
            },
        }
    }
    print(transform(demo_combined).to_string())