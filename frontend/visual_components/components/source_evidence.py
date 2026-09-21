"""Source details for a claim, shown in a dropdown under the claim overview."""

import re

import streamlit as st

from .html_utils import esc, safe_url
from .. import theme

# Word boundaries avoid substring matches like "EVidence"
HIGHLIGHT_KEYWORDS = [r"\bEV\b", r"\blemon water\b",
                      r"\bdiabetes\b", r"\brate cut\b", r"\bcentral bank\b"]


def _highlight_keywords(text: str) -> str:
    """Wrap known keywords in a <mark> tag. Expects already-escaped text."""

    mark_open = (
        f"<mark style='background-color: {theme.COLOUR_WARNING_BG}; "
        f"color: {theme.COLOUR_WARNING_FG}; padding: 2px 4px; "
        "border-radius: 4px; font-weight: 600;'>"
    )
    for keyword in HIGHLIGHT_KEYWORDS:
        text = re.sub(keyword, f"{mark_open}\\g<0></mark>", text,
                      flags=re.IGNORECASE)
    return text


def _source_card(src: dict) -> str:
    """HTML for one source: outlet, matched excerpt, optional link."""

    name = esc(src.get("name") or "Verified Source")
    excerpt = _highlight_keywords(esc(src.get("snippet", "")))
    url = safe_url(src.get("url"))

    link = (
        f'<a class="chip chip-link" href="{esc(url)}" target="_blank" '
        f'rel="noopener noreferrer">Read source ↗</a>'
        if url else ""
    )

    return (
        '<div class="source-card">'
        f'<span class="chip chip-accent">📌 {name}</span>'
        f'<div class="source-card__excerpt">“{excerpt}”</div>'
        f'{link}'
        '</div>'
    )


def _outlet_names(sources: list) -> list:
    """Unique outlet names, in the order they first appear."""

    names = [s.get("name") or "Verified Source" for s in sources]
    return list(dict.fromkeys(names))


def render_source_evidence(sources: list):
    """One dropdown per claim holding a card for every source."""

    outlets = _outlet_names(sources)

    with st.expander(f"📚 Source details ({len(sources)}) — {', '.join(outlets)}",
                     expanded=False):
        # One HTML block with no blank lines so Markdown doesn't break it up
        cards = "".join(_source_card(src) for src in sources)
        st.markdown(f'<div class="source-grid">{cards}</div>',
                    unsafe_allow_html=True)
