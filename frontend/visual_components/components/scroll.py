"""Helpers to jump the page to a section after Streamlit re-renders."""

import time
import streamlit as st

_SCROLL_SCRIPT = """
<script>
    setTimeout(function() {
        var target = window.parent.document.getElementById("__ANCHOR_ID__");
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 150);
</script>
"""


def render_anchor(anchor_id: str):
    """Drop an invisible marker that scroll_to() can jump to."""

    st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)


def scroll_to(anchor_id: str):
    """Smooth-scroll the page to the marker created by render_anchor()."""

    script = _SCROLL_SCRIPT.replace("__ANCHOR_ID__", anchor_id)
    # forces a fresh iframe each call, so the script re-runs every time
    nonce = time.time_ns()
    st.components.v1.html(f"{script}<!-- {nonce} -->", height=0)
