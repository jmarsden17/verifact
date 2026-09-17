"""Clean and validate claim/verdict records before they are loaded to the database."""

import pandas as pd

VERDICTS = ["supported", "contradicted", "missing/mixed context", "unclear"]

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
    return "unknown"


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
    """Clean, dedupe, filter, and alphabetically sort a tag list in one step."""
    cleaned = clean_list_value(tags)
    deduped = dedupe_list(cleaned)
    filtered = filter_tags(deduped, exclude=exclude)
    return sort_tags(filtered)


def transform(records: list[dict]) -> pd.DataFrame:
    """Clean every column of a list of raw handler_verify_claim.py records."""
    df = pd.DataFrame(records)
    if df.empty:
        return df

    for column in ["claim", "reasoning"]:
        df[column] = df[column].apply(clean_text_value)

    df["entities"] = df["entities"].apply(clean_list_value).apply(dedupe_list)
    df["verdict"] = df["verdict"].apply(lambda v: clean_categorical_value(v, VERDICTS))
    df["tags"] = df["tags"].apply(lambda t: clean_tag_list(t, exclude=["fact-checking"]))
    df["sources"] = df["sources"].apply(clean_list_value)
    return df


if __name__ == "__main__":
    demo_records = [{"claim": "Example claim.", "verdict": "Supported",
                      "reasoning": "Example.", "entities": [], "tags": [],
                      "sources": [], "source_name": "Example Source"}]
    print(transform(demo_records))