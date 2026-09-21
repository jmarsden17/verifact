"""Clean and validate claim/verdict records before load."""

import logging
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

VERDICTS = ["Supported", "Contradicted",
            "Mixed / Missing Context", "Unclear / Not enough evidence"]

OUTLETS = ['Reuters Fact Check', 'BBC Verify', 'Full Fact', 'Wikipedia API']


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


def clean_categorical_value(value, allowed: list[str], category: str) -> str:
    """Return the value (in its allowed casing) if it matches allowed, else "unknown"."""
    allowed_by_lower = {a.lower(): a for a in allowed}
    if isinstance(value, str) and value.lower() in allowed_by_lower:
        return allowed_by_lower[value.lower()]
    logger.warning(
        "Unrecognised categorical value %r, falling back to 'unknown'", value)
    if category == "TOPIC_TAGS":
        return 'Other'
    if category == "TECHNIQUE_TAGS":
        return 'None'
    if category == "VERDICT":
        return 'Unclear / Not enough evidence'
    if category == 'OUTLETS':
        return None


def clean_categorical_list(values, allowed: list[str]) -> list[str]:
    """Like clean_categorical_value, but for a list: drops any value not in allowed."""
    allowed_lower = {a.lower() for a in allowed}
    cleaned = clean_list_value(values)
    dropped = [v for v in cleaned if not (
        isinstance(v, str) and v.lower() in allowed_lower)]
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


def ensure_column(df: pd.DataFrame, column: str, default):
    """Add column with default if missing."""
    if column not in df.columns:
        logger.warning(
            "Column %r missing from records, defaulting to %r", column, default)
        df[column] = [default()
                      for _ in range(len(df))] if callable(default) else default
    return df


def transform(records: list[dict]) -> pd.DataFrame:
    """Clean every column of a list of raw handler_verify_claim.py records."""
    logger.info("Transforming %d records", len(records))
    df = pd.DataFrame(records)
    if df.empty:
        logger.warning("No records to transform")
        return df

    if "reasoning" in df.columns:
        df = df.rename(columns={"reasoning": "source_reasoning"})

    if "misinformation_type" in df.columns:
        if "technique" in df.columns:
            df["technique"] = df["technique"].combine_first(
                df["misinformation_type"])
            df = df.drop(columns=["misinformation_type"])
        else:
            df = df.rename(columns={"misinformation_type": "technique"})

    for column in ["claim", "source_reasoning", "summary", "similar_claim"]:
        df = ensure_column(df, column, "")
        df[column] = df[column].apply(clean_text_value)

    df = ensure_column(df, "similarity", None)
    df["similarity"] = df["similarity"].apply(clean_float_value)

    df = ensure_column(df, "entities", list)
    df["entities"] = df["entities"].apply(clean_list_value).apply(dedupe_list)
    df["entities"] = df["entities"].apply(
        lambda e: tuple(e) if isinstance(e, list) else e)

    df = ensure_column(df, "verdict", None)
    df["verdict"] = df["verdict"].apply(
        lambda v: clean_categorical_value(v, VERDICTS, 'VERDICTS'))

    df = ensure_column(df, "technique", None)
    df["technique"] = df["technique"].apply(
        lambda v: clean_categorical_value(v, TECHNIQUE_TAGS, 'TECHNIQUE_TAGS'))

    df = ensure_column(df, "tags", list)
    df["tags"] = df["tags"].apply(
        lambda t: clean_tag_list(t, exclude=["fact-checking"]))
    df["tags"] = df["tags"].apply(
        lambda t: tuple(t) if isinstance(t, list) else t)

    df = ensure_column(df, "sources", list)
    df["sources"] = df["sources"].apply(clean_list_value)
    df["sources"] = df["sources"].apply(lambda s: s[0] if s else None)

    df = ensure_column(df, "source_name", "")
    df["source_name"] = df["source_name"].apply(clean_text_value)
    df["source_name"] = df["source_name"].apply(
        lambda v: clean_categorical_value(v, OUTLETS, 'OUTLETS'))

    df = ensure_column(df, "claim_url", None)
    df["claim_url"] = df["claim_url"].apply(
        lambda v: v if isinstance(v, str) and v.strip() else None)

    df = ensure_column(df, "claim_embedding", None)
    df["claim_embedding"] = df["claim_embedding"].apply(
        lambda v: v if isinstance(v, list) else None)

    df = ensure_column(df, "confidence_score", None)
    df["confidence_score"] = df["confidence_score"].apply(clean_float_value)

    logger.info("Finished transforming %d records", len(df))
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_records = [
        {"claim": "Example claim.", "verdict": "Supported", "reasoning": "Example.",
         "misinformation_type": "None", "entities": [], "tags": [], "sources": ["https://a.com"],
         "source_name": "Full Fact", "confidence_score": 0.8},
        {"claim": "Cached claim.", "similar_claim": "A similar claim.", "similarity": 0.94,
         "verdict": "Contradicted", "summary": "Cached claim-level summary.", "technique": "None"},
    ]
    print(transform(demo_records).to_string())
