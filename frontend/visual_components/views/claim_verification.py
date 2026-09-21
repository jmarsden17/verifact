"""Claim Verification page: submit text, see per-claim verdicts."""

import streamlit as st
from database_conns import fetch_data as fn
from ..components.audit_summary import render_audit_summary
from ..components.claim_form import render_demo_presets, render_verification_form
from ..components.claim_report import render_claim_reports
from ..components.header import render_page_header
from ..components.scroll import render_anchor, scroll_to

RESULTS_ANCHOR = "verification-results"


def _init_form_state():
    """Initialise the session state for the claim verification form."""

    st.session_state.setdefault("input_claim", "")
    st.session_state.setdefault("input_url", "")


def _render_results(results: list):
    """Render the verification results section."""

    render_anchor(RESULTS_ANCHOR)
    st.markdown("---")
    render_audit_summary(results)
    st.markdown("---")
    render_claim_reports(results)
    scroll_to(RESULTS_ANCHOR)


def render():
    """Main Verification Workspace."""

    render_page_header(
        "Claim Verification Workspace",
        "Submit headlines, quotes, or social media statements to check against primary fact-checking records."
    )

    _init_form_state()
    render_demo_presets()
    submit, claim_input, url_input = render_verification_form()

    if submit:
        results = fn.verify_claim(claim_input, url_input)
        if not results:
            st.warning(
                "Please select a sample claim above or enter text to verify.")
            return

        _render_results(results)
