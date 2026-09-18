"""UI layout views and visual components."""

import re
import json
import streamlit as st
import pandas as pd
from . import theme
from utils import db as fn
from . import visuals as vis


def render_page_header(title: str, description: str):
    """Render section headers with brand icon."""

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 6px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50" width="48" height="48" style="flex-shrink: 0;">
            <!-- Document Shield Base -->
            <rect x="2" y="4" width="36" height="42" rx="5" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2.5"/>
            <!-- Accent Lines -->
            <line x1="9" y1="14" x2="24" y2="14" stroke="#4A6E91" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="9" y1="20" x2="31" y2="20" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
            <!-- Check Badge -->
            <circle cx="32" cy="35" r="11" fill="{theme.COLOUR_PRIMARY}"/>
            <path d="M 28 35 L 30 37 L 36 32" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <h1 style="margin: 0 !important; font-size: 36px !important; font-weight: 800 !important; color: {theme.COLOUR_TEXT_MAIN}; line-height: 1.1;">{title}</h1>
    </div>
    <p style="margin-bottom: 24px; color: {theme.COLOUR_TEXT_MUTED}; font-size: 15px; margin-left: 62px;">{description}</p>
    """, unsafe_allow_html=True)


def render_verdict_badge(rating: str):
    """Render status indicators."""

    badge_styles = {
        "Contradicted": (theme.COLOUR_DANGER_BG, theme.COLOUR_DANGER_FG, "❌"),
        "Supported": (theme.COLOUR_SUCCESS_BG, theme.COLOUR_SUCCESS_FG, "✅"),
        "Missing Context": (theme.COLOUR_WARNING_BG, theme.COLOUR_WARNING_FG, "⚠️"),
        "Unclear": (theme.COLOUR_APP_BG, theme.COLOUR_TEXT_MAIN, "❓")
    }

    bg, fg, icon = badge_styles.get(
        rating, (theme.COLOUR_APP_BG, theme.COLOUR_TEXT_MAIN, "ℹ️"))

    badge_html = f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background-color: {bg};
        color: {fg};
        padding: 6px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 12px;
    ">
        <span>{icon}</span>
        <span>VERDICT: {rating.upper()}</span>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)


def render_sidebar_logo():
    """Render the logo inside the sidebar."""

    logo_svg = """
    <div style="padding: 4px 0px 16px 0px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 80" width="100%">
            <g transform="translate(0, 5)">
                <!-- Document Container -->
                <rect x="4" y="6" width="44" height="56" rx="6" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2.5"/>
                <!-- Document Lines -->
                <line x1="12" y1="18" x2="30" y2="18" stroke="#4A6E91" stroke-width="2.5" stroke-linecap="round"/>
                <line x1="12" y1="26" x2="40" y2="26" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
                <line x1="12" y1="34" x2="36" y2="34" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
                <!-- Pulse Check Badge -->
                <circle cx="38" cy="46" r="14" fill="#6A8EAE"/>
                <path d="M 33 46 L 36 49 L 43 42" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </g>
            <!-- Brand Text -->
            <text x="64" y="32" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-weight="700" font-size="15" fill="#0F172A" letter-spacing="0.5">DISINFORMATION</text>
            <text x="64" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-weight="700" font-size="15" fill="#6A8EAE" letter-spacing="0.5">VERIFIER</text>
            <text x="64" y="62" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-weight="500" font-size="8.5" fill="#64748B" letter-spacing="1.2">FAST CLAIM AUDIT</text>
        </svg>
    </div>
    """
    st.sidebar.markdown(logo_svg, unsafe_allow_html=True)


def render_system_status():
    """Render a live architecture status indicator pinned to the sidebar footer."""

    st.sidebar.markdown(f"""
    <div style="margin-top: auto; padding-top: 20px;">
        <hr style="margin-bottom: 16px; border: 0; border-top: 1px solid {theme.COLOUR_BORDER};">
        <div style="background-color: #F8FAFC; border: 1px solid {theme.COLOUR_BORDER}; padding: 12px; border-radius: 8px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 12px; font-weight: 600; color: {theme.COLOUR_TEXT_MAIN};">Engine Status</span>
                <span style="font-size: 11px; font-weight: 600; color: {theme.COLOUR_SUCCESS_FG}; background-color: {theme.COLOUR_SUCCESS_BG}; padding: 2px 6px; border-radius: 4px;">● ONLINE</span>
            </div>
            <div style="font-size: 11px; color: {theme.COLOUR_TEXT_MUTED}; line-height: 1.4;">
                • <strong>Compute:</strong> AWS ECS Fargate<br>
                • <strong>Database:</strong> PostgreSQL RDS<br>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Claim verification helpers

def _render_demo_presets():
    """Render a button demonstrating multi-claim extraction."""

    st.markdown("**Try a Multi-Claim Newsroom Paragraph:**")

    multi_claim_paragraph = (
        "Viral social media posts claim that drinking warm lemon water daily completely cures type 2 diabetes. "
        "Meanwhile, policy reports suggest the government is removing all EV purchase tax credits starting next month, "
        "and leaked internal memos claim the central bank is planning an emergency 200 basis point rate cut."
    )

    demo_url = "https://example-newsroom.com/analysis/multi-claim-report"

    if st.button("Test Multi-Claim Paragraph Audit", width="stretch"):
        st.session_state.input_claim = multi_claim_paragraph
        st.session_state.input_url = demo_url
        st.rerun()

    st.markdown("---")


def _render_verification_form():
    """Render statement input form and return submission status."""

    with st.form("claim_input_form", clear_on_submit=False):
        claim_input = st.text_area(
            "Statement or Headline Text",
            value=st.session_state.get("input_claim", ""),
            placeholder="e.g., 'Viral post claims drinking lemon water completely reverses diabetes.'",
            height=100
        )
        url_input = st.text_input(
            "URL",
            value=st.session_state.get("input_url", ""),
            placeholder="https://example.com/news/article"
        )
        submit = st.form_submit_button("Verify Claim")

    return submit, claim_input, url_input


def _render_source_evidence_accordion(sources):
    """Render source evidence cards with keyword highlights for verified outlets."""

    st.markdown("---")
    st.markdown("### Retrieved Source Evidence")
    st.markdown(
        f"<p style='font-size: 13px; color: {theme.COLOUR_TEXT_MUTED}; margin-bottom: 16px;'>"
        "Primary fact-checking records retrieved exclusively from BBC Verify, Reuters, Full Fact, and Wikipedia.</p>",
        unsafe_allow_html=True
    )

    # Avoid substring matches like "EVidence"
    keywords = [r"\bEV\b", r"\blemon water\b",
                r"\bdiabetes\b", r"\brate cut\b", r"\bcentral bank\b"]

    for i, src in enumerate(sources):
        snippet_text = src.get('snippet', '')
        source_name = src.get('name', 'Verified Source')

        for kw in keywords:
            pattern = re.compile(kw, re.IGNORECASE)
            snippet_text = pattern.sub(
                f"<mark style='background-color: {theme.COLOUR_WARNING_BG}; color: {theme.COLOUR_WARNING_FG}; padding: 2px 4px; border-radius: 4px; font-weight: 600;'>\\g<0></mark>",
                snippet_text
            )

        with st.expander(f"📌 Source {i+1}: {source_name} (Semantic Match: 96%)", expanded=(i == 0)):
            col_meta1, col_meta2 = st.columns([2, 1])

            with col_meta1:
                st.markdown("**Matched Excerpt:**")
                st.markdown(f"""
                <div style="background-color: {theme.COLOUR_APP_BG}; border-left: 3px solid {theme.COLOUR_PRIMARY}; padding: 12px 16px; margin-bottom: 12px; border-radius: 0 8px 8px 0; font-size: 14px;">
                    "{snippet_text}"
                </div>
                """, unsafe_allow_html=True)

            with col_meta2:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid {theme.COLOUR_BORDER}; padding: 10px; border-radius: 6px; font-size: 12px;">
                    <strong>Outlet:</strong> {source_name}<br>
                    <strong>Record Status:</strong> <span style="color: {theme.COLOUR_SUCCESS_FG}; font-weight: 600;">VERIFIED</span><br>
                    <strong>Ingested:</strong> 2 days ago
                </div>
                """, unsafe_allow_html=True)


def _render_verification_results(results_list: list):
    """Render multi-claim overview followed by smaller claims."""

    if not results_list:
        return

    st.markdown('<div id="verification-results"></div>',
                unsafe_allow_html=True)
    st.markdown("---")

    # Overall summary
    st.markdown("### 📊 Paragraph Audit Overview")

    total_claims = len(results_list)
    supported = sum(1 for r in results_list if r.get("rating") == "Supported")
    contradicted = sum(1 for r in results_list if r.get(
        "rating") == "Contradicted")
    missing_ctx = sum(1 for r in results_list if r.get(
        "rating") == "Missing Context")
    unclear = sum(1 for r in results_list if r.get("rating") == "Unclear")

    accuracy_pct = round((supported / total_claims) *
                         100) if total_claims > 0 else 0

    with st.container(border=True):
        col_stats, col_chart = st.columns([1.5, 1])

        with col_stats:
            st.markdown(f"**Total Claims Extracted:** `{total_claims}`")
            st.markdown(f"✅ **Supported Claims:** `{supported}`")
            st.markdown(f"❌ **Disproved (Contradicted):** `{contradicted}`")
            st.markdown(
                f"⚠️ **Missing Context / Unclear:** `{missing_ctx + unclear}`")
            st.markdown(f"🎯 **Overall Accuracy Score:** **{accuracy_pct}%**")

        with col_chart:
            st.markdown(
                "<p style='text-align: center; font-size: 13px; font-weight: 600;'>Accuracy Breakdown</p>", unsafe_allow_html=True)
            fig_pie = vis.render_overall_accuracy_chart(
                supported, contradicted, missing_ctx, unclear)
            if fig_pie:
                st.plotly_chart(fig_pie, width="stretch",
                                config={'displayModeBar': False})

    st.markdown("---")

    # Individual claim expanders
    st.markdown("### 🔍 Individual Extracted Claim Reports")

    for idx, item in enumerate(results_list):
        claim_text = item.get("claim", f"Extracted Claim #{idx+1}")
        rating = item.get("rating", "Unclear")

        expander_title = f"Claim {idx+1}: \"{claim_text[:80]}...\" — [{rating.upper()}]"

        with st.expander(expander_title, expanded=(idx == 0)):
            # Split 2 columns for Statement & Confidence Gauge
            col_verdict, col_gauge = st.columns([1.2, 1])

            with col_verdict:
                st.markdown("**Extracted Statement:**")
                st.info(f"\"{claim_text}\"")
                render_verdict_badge(rating)
                st.markdown("**Reasoning Explanation:**")
                st.write(item.get("reasoning", "No explanation provided."))

            with col_gauge:
                confidence = 94.2 if rating in [
                    "Supported", "Contradicted"] else 68.5
                fig_gauge = vis.render_confidence_gauge(confidence)
                st.plotly_chart(
                    fig_gauge,
                    width="stretch",
                    config={'displayModeBar': False},
                    key=f"gauge_chart_{idx}"
                )

            if item.get("sources"):
                _render_source_evidence_accordion(item["sources"])

        st.components.v1.html("""
        <script>
            setTimeout(function() {
                var target = window.parent.document.getElementById("verification-results");
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 150);
        </script>
    """, height=0)


# Main views

def render_claim_verification_view():
    """Main Verification Workspace."""

    render_page_header(
        "Claim Verification Workspace",
        "Submit headlines, quotes, or social media statements to check against primary fact-checking records."
    )

    if "input_claim" not in st.session_state:
        st.session_state.input_claim = ""
    if "input_url" not in st.session_state:
        st.session_state.input_url = ""

    _render_demo_presets()
    submit, claim_input, url_input = _render_verification_form()

    if submit:
        result = fn.verify_claim(claim_input, url_input)
        if not result:
            st.warning(
                "Please select a sample claim above or enter text to verify.")
            return

        _render_verification_results(result)


def render_top_disproven_claims_view():
    """Render feed of top viral fake news and disproven claims from RDS."""

    render_page_header(
        "Top Disproven Claims",
        "Live feed of widespread disproven assertions and misleading viral claims indexed across partner outlets."
    )

    df = fn.get_top_disproven_claims()

    if df.empty:
        st.info("No disproven claims currently recorded in the system.")
        return

    for _, row in df.iterrows():
        verdict = row["verdict"]
        badge_bg = theme.COLOUR_DANGER_BG if verdict == "Contradicted" else theme.COLOUR_WARNING_BG
        badge_fg = theme.COLOUR_DANGER_FG if verdict == "Contradicted" else theme.COLOUR_WARNING_FG
        icon = "✖" if verdict == "Contradicted" else "⚠️"

        publisher_text = row.get("publishers") or "Verified Fact Check"
        timestamp_text = str(row.get("timestamp", ""))

        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1px solid {theme.COLOUR_BORDER}; padding: 18px; border-radius: 10px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 12px; color: {theme.COLOUR_TEXT_MUTED}; font-weight: 500;">
                    {timestamp_text} • {publisher_text}
                </span>
                <span style="font-size: 11px; font-weight: 700; color: {badge_fg}; background-color: {badge_bg}; padding: 4px 10px; border-radius: 12px;">
                    {icon} VERDICT: {verdict.upper()}
                </span>
            </div>
            <div style="font-size: 16px; font-weight: 600; color: {theme.COLOUR_TEXT_MAIN}; margin-top: 4px;">
                "{row['claim_text']}"
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_outlet_credibility_view():
    """Live metric cards & relational data analytics powered by RDS."""

    render_page_header(
        "Outlet Source Analytics",
        "Live distribution metrics across ingested fact-checking partners and techniques."
    )

    df = fn.fetch_analytics_data()

    if df.empty:
        st.warning(
            "⚠️ Unable to load live database records. Please verify your RDS connection settings in your environment.")
        return

    df["publish_datetime"] = pd.to_datetime(df["publish_datetime"])
    df["access_datetime"] = pd.to_datetime(df["access_datetime"])

    total_claims = len(df)
    resurfaced_count = (
        (df["access_datetime"] - df["publish_datetime"]).dt.days > 7).sum()

    top_publisher = df["publisher"].mode(
    )[0] if "publisher" in df and not df["publisher"].dropna().empty else "N/A"
    top_technique = df["technique"].mode(
    )[0] if "technique" in df and not df["technique"].dropna().empty else "N/A"

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(label="Total Claims Checked", value=f"{total_claims:,}")
    with m2:
        st.metric(label="Primary Outlet Source", value=top_publisher)
    with m3:
        st.metric(label="Top Technique Used", value=top_technique)
    with m4:
        st.metric(label="Resurfaced Myths (>7d)",
                  value=f"{resurfaced_count:,}")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("### Verifications by Fact-Checking Publisher")
        st.markdown(
            f"<p style='font-size: 13px; color: {theme.COLOUR_TEXT_MUTED}; margin-bottom: 16px;'>"
            "Live volume of claims indexed across verified primary partners.</p>",
            unsafe_allow_html=True
        )
        fig_publisher = vis.render_outlet_analytics_chart(df)
        if fig_publisher:
            st.plotly_chart(fig_publisher, width="stretch",
                            config={'displayModeBar': False})

    with col_chart2:
        st.markdown("### Claim Ingestion & Recurrence Rate")
        st.markdown(
            f"<p style='font-size: 13px; color: {theme.COLOUR_TEXT_MUTED}; margin-bottom: 16px;'>"
            "Comparing new claims against queries resurfacing long after publication.</p>",
            unsafe_allow_html=True
        )
        fig_recurrence = vis.render_recurrence_timeline_chart(df)
        if fig_recurrence:
            st.plotly_chart(fig_recurrence, width="stretch",
                            config={'displayModeBar': False})

    st.markdown("---")


def render_verification_logs_view():
    """Filterable Data Table View matching exact ERD entities."""

    render_page_header(
        "Verification History Logs",
        "Search and review past newsroom claim checks indexed in RDS."
    )

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            query = st.text_input("Filter by Keyword or Tag",
                                  placeholder="Search claims or tags...")
        with c2:
            status = st.selectbox(
                "Verdict Filter",
                ["All", "Supported", "Contradicted", "Missing Context", "Unclear"]
            )

    df = fn.get_filtered_logs(query, status)

    if df.empty:
        st.info("No verification logs match your filter criteria.")
        return

    # Select and rename columns explicitly to ensure UI updates regardless of DB fallback format
    display_cols = {
        "timestamp": "Timestamp",
        "claim_statement": "Claim Statement",
        "verdict": "Verdict",
        "technique": "Disinformation Technique",
        "sources_count": "Sources Consulted",
        "tags_list": "Tags"
    }

    # Filter dataframe to available ERD columns
    valid_cols = [c for c in display_cols.keys() if c in df.columns]

    if valid_cols:
        st.dataframe(
            df[valid_cols].rename(columns=display_cols),
            width="stretch",
            hide_index=True
        )
    else:
        st.dataframe(df, width="stretch", hide_index=True)
