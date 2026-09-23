"""Input widgets for the Claim Verification page."""

import streamlit as st
from .. import theme

DEMO_PARAGRAPH = (
    "Viral social media posts claim that drinking warm lemon water daily completely cures type 2 diabetes. "
    "Meanwhile, policy reports suggest the government is removing all EV purchase tax credits starting next month, "
    "and leaked internal memos claim the central bank is planning an emergency 200 basis point rate cut."
)
DEMO_URL = "https://example-newsroom.com/analysis/multi-claim-report"


def render_demo_presets():
    """Render a button demonstrating multi-claim extraction."""

    st.markdown("**Try a Multi-Claim Newsroom Paragraph:**")

    if st.button("Test Multi-Claim Paragraph Audit", width="stretch"):
        st.session_state.input_claim = DEMO_PARAGRAPH
        st.session_state.input_url = DEMO_URL
        st.rerun()

    st.markdown("---")


def render_verification_form():
    """Render statement input form and return (submitted, claim_text, url)."""

    with st.form("claim_input_form", clear_on_submit=False):
        claim_input = st.text_area(
            "Statements or Headline Text:",
            value=st.session_state.get("input_claim", ""),
            placeholder="e.g., 'Viral post claims drinking lemon water completely reverses diabetes.'",
            height=100
        )
        url_input = st.text_input(
            "URL:",
            value=st.session_state.get("input_url", ""),
            type="url"
        )

        st.markdown(
            """
            <div style="
                background-color: {theme.GRADIENT_LOW_SCORE}; 
                border-left: 4px solid {theme.GRADIENT_MID_SCORE}; 
                padding: 6px 12px; 
                border-radius: 4px; 
                font-size: 13px; 
                color: #1a535c; 
                margin-top: -8px; 
                margin-bottom: 12px;">
                <b>Note:</b> If both text and a URL are provided, the URL will be omitted.
            </div>
            """.format(theme=theme),
            unsafe_allow_html=True
        )

        submit = st.form_submit_button("Verify Claim")

    return submit, claim_input, url_input
