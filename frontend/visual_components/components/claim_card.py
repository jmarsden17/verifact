"""Card used in the Latest Disproven Claims feed."""

import json
import pandas as pd
import streamlit as st
from .. import theme
from .html_utils import domain_of, esc, safe_url

VERDICT_STYLES = {
    "Contradicted": (theme.COLOUR_DANGER_BG, theme.COLOUR_DANGER_FG, "✖"),
    "Missing Context": (theme.COLOUR_WARNING_BG, theme.COLOUR_WARNING_FG, "⚠️"),
}
SUMMARY_MAX_CHARS = 240
RECENT_DAYS = 14  # show "3 days ago" up to this many days, then a full date afterwards


def _clean(value):
    """None for NaN / NaT / empty values, otherwise the value unchanged."""

    if value is None:
        return None
    if isinstance(value, (list, dict, str)):
        return value or None
    try:
        return None if pd.isna(value) else value
    except (TypeError, ValueError):
        return value


def _relative_date(value) -> str | None:
    """'today', '3 days ago', or '18 Sep 2026' for older dates."""

    value = _clean(value)
    if value is None:
        return None

    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return str(value)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)

    days = (pd.Timestamp.now().normalize() - ts.normalize()).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < RECENT_DAYS:
        return f"{days} days ago"
    return ts.strftime("%d %b %Y")


def _as_link_list(value) -> list:
    """Source_links arrives as a list of {'outlet', 'url'} (or a JSON string)."""

    value = _clean(value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def _sources_html(source_links, publishers) -> str:
    """Link chips for each source; plain chips if we only know outlet names."""

    chips = []
    for link in _as_link_list(source_links):
        url = safe_url(link.get("url"))
        if not url:
            continue
        label = link.get("outlet") or domain_of(url)
        chips.append(
            f'<a class="chip chip-link" href="{esc(url)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label)} ↗</a>'
        )

    if not chips and _clean(publishers):
        chips = [f'<span class="chip">{esc(name.strip())}</span>'
                 for name in str(publishers).split(",")]

    return "".join(chips)


def _meta_text(row) -> str:
    """Generate meta text for a claim."""

    parts = []

    published = _relative_date(row.get("publish_datetime"))
    if published:
        parts.append(f"Published {published}")

    checked = _clean(row.get("access_amount"))
    if checked is not None:
        times = int(checked)
        parts.append(f"Checked {times} time{'s' if times != 1 else ''}")

    return " · ".join(parts)


def render_disproven_claim_card(row):
    """Render one disproven / misleading claim from a DataFrame row."""

    verdict = str(row["verdict"])
    bg, fg, icon = VERDICT_STYLES.get(
        verdict, (theme.COLOUR_WARNING_BG, theme.COLOUR_WARNING_FG, "⚠️"))

    technique = _clean(row.get("technique"))
    technique_html = (
        f'<span class="chip chip-accent" title="Disinformation technique">{esc(technique)}</span>'
        if technique else ""
    )

    summary = _clean(row.get("summary"))
    if summary and len(summary) > SUMMARY_MAX_CHARS:
        summary = summary[:SUMMARY_MAX_CHARS].rstrip() + "..."
    summary_html = (
        f'<div class="feed-card__summary">{esc(summary)}</div>' if summary else ""
    )

    sources_html = _sources_html(
        row.get("source_links"), row.get("publishers"))
    sources_block = (
        f'<div class="feed-card__sources">{sources_html}</div>' if sources_html else ""
    )

    st.markdown(
        f'<div class="feed-card" style="--verdict-bg: {bg}; --verdict-fg: {fg};">'
        '<div class="feed-card__top">'
        f'<span class="verdict-pill">{icon} {esc(verdict.upper())}</span>'
        f'{technique_html}'
        f'<span class="feed-card__meta">{esc(_meta_text(row))}</span>'
        '</div>'
        f'<div class="feed-card__claim">“{esc(row["claim_text"])}”</div>'
        f'{summary_html}'
        f'{sources_block}'
        '</div>',
        unsafe_allow_html=True,
    )
