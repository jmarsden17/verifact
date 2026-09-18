"""Clean and validate claim/verdict records before they are loaded to the database."""

import logging
import pandas as pd
from models import TOPIC_TAGS, TECHNIQUE_TAGS

logger = logging.getLogger(__name__)

VERDICTS = ["supported", "contradicted", "mixed / missing context", "unclear / not enough evidence"]


def clean_list_value(value):
    """Return value if it's a list, else an empty list."""
    return value if isinstance(value, list) else []


def clean_text_value(value):
    """Return a stripped string, or "" if not a string."""
    return value.strip() if isinstance(value, str) else ""


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


def transform(records: list[dict]) -> pd.DataFrame:
    """Clean every column of a list of raw handler_verify_claim.py records."""
    logger.info("Transforming %d records", len(records))
    df = pd.DataFrame(records)
    if df.empty:
        logger.warning("No records to transform")
        return df

    for column in ["claim", "reasoning"]:
        if column not in df.columns:
            logger.warning("Column %r missing from records, defaulting to ''", column)
            df[column] = ""
        df[column] = df[column].apply(clean_text_value)

    if "entities" not in df.columns:
        logger.warning("Column 'entities' missing from records, defaulting to []")
        df["entities"] = [[] for _ in range(len(df))]
    df["entities"] = df["entities"].apply(clean_list_value).apply(dedupe_list)

    if "verdict" not in df.columns:
        logger.warning("Column 'verdict' missing from records, defaulting to None")
        df["verdict"] = None
    df["verdict"] = df["verdict"].apply(lambda v: clean_categorical_value(v, VERDICTS))

    if "misinformation_type" not in df.columns:
        logger.warning("Column 'misinformation_type' missing from records, defaulting to None")
        df["misinformation_type"] = None
    df["misinformation_type"] = df["misinformation_type"].apply(
        lambda v: clean_categorical_value(v, TECHNIQUE_TAGS)
    )

    if "tags" not in df.columns:
        logger.warning("Column 'tags' missing from records, defaulting to []")
        df["tags"] = [[] for _ in range(len(df))]
    df["tags"] = df["tags"].apply(lambda t: clean_tag_list(t, exclude=["fact-checking"]))

    if "sources" not in df.columns:
        logger.warning("Column 'sources' missing from records, defaulting to []")
        df["sources"] = [[] for _ in range(len(df))]
    df["sources"] = df["sources"].apply(clean_list_value)

    logger.info("Finished transforming %d records", len(df))
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_records = [{"claim": "Example claim.", "verdict": "Supported",
                      "reasoning": "Example.", "entities": [],
                      "misinformation_type": "None", "tags": [],
                      "sources": [], "source_name": "Example Source"}]
    print(transform(demo_records))