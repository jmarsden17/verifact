"""Fixed design elements for the app."""
import streamlit as st

# Custom Brand Colours
COLOUR_APP_BG = "#F3F4F6"
COLOUR_SIDEBAR_BG = "#FFFFFF"
COLOUR_CARD_BG = "#FFFFFF"
COLOUR_BORDER = "#E2E8F0"
COLOUR_TEXT_MAIN = "#0F172A"
COLOUR_TEXT_MUTED = "#64748B"

# Accent colour - buttons, active nav, key numbers, links.
# Change these to re-skin the app.
COLOUR_PRIMARY = "#2563EB"
COLOUR_PRIMARY_HOVER = "#1D4ED8"
COLOUR_PRIMARY_DARK = "#1E3A8A"
COLOUR_PRIMARY_SOFT = "#DBEAFE"
COLOUR_PRIMARY_RGB = "37, 99, 235"

# Semantic Colours
COLOUR_SUCCESS_BG = "#E6F4EA"
COLOUR_SUCCESS_FG = "#10B981"

COLOUR_DANGER_BG = "#FFE6E6"
COLOUR_DANGER_FG = "#F43F5E"

COLOUR_WARNING_BG = "#FFFBEB"
COLOUR_WARNING_FG = "#F59E0B"

COLOUR_UNCLEAR_BG = "#F1F5F9"
COLOUR_UNCLEAR_FG = "#64748B"

# Gradient bar colours
GRADIENT_HIGH_SCORE = "#112459"
GRADIENT_MID_SCORE = "#3C71E6"
GRADIENT_LOW_SCORE = "#C3DDFA"

# Verdict lookups - single source of truth shared by badges and charts
VERDICT_ORDER = ["Supported", "Contradicted", "Missing Context", "Unclear"]

# Solid colour per verdict (charts)
VERDICT_CHART_COLOURS = {
    "Supported": COLOUR_SUCCESS_FG,
    "Contradicted": COLOUR_DANGER_FG,
    "Missing Context": COLOUR_WARNING_FG,
    "Unclear": COLOUR_UNCLEAR_FG,
}

# Per verdict badges
VERDICT_BADGES = {
    "Contradicted": (COLOUR_DANGER_BG, COLOUR_DANGER_FG, "❌"),
    "Supported": (COLOUR_SUCCESS_BG, COLOUR_SUCCESS_FG, "✅"),
    "Missing Context": (COLOUR_WARNING_BG, COLOUR_WARNING_FG, "⚠️"),
    "Unclear": (COLOUR_APP_BG, COLOUR_TEXT_MAIN, "❓"),
}
VERDICT_BADGE_DEFAULT = (COLOUR_APP_BG, COLOUR_TEXT_MAIN, "ℹ️")


def inject_custom_theme():
    """Inject global CSS rules for custom palette and UI scaffolding."""
    custom_css = f"""
    <style>
        /* Global Reset */
        .stApp {{
            background-color: {COLOUR_APP_BG};
            color: {COLOUR_TEXT_MAIN};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: {COLOUR_SIDEBAR_BG} !important;
            border-right: 1px solid {COLOUR_BORDER} !important;
        }}

        [data-testid="stSidebar"] * {{
            color: {COLOUR_TEXT_MAIN} !important;
        }}

        /* Collapsed Sidebar Chevron Pill (Dark Navy Icon on Light Grey Pill) */
        [data-testid="stSidebarCollapsedControl"],
        button[data-testid="baseButton-header"] {{
            background-color: #E2E8F0 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
            padding: 6px !important;
            visibility: visible !important;
            opacity: 1 !important;
        }}

        [data-testid="stSidebarCollapsedControl"] svg,
        button[data-testid="baseButton-header"] svg,
        [data-testid="stSidebarHeader"] svg {{
            fill: {COLOUR_TEXT_MAIN} !important;
            color: {COLOUR_TEXT_MAIN} !important;
            stroke: {COLOUR_TEXT_MAIN} !important;
        }}

        /* Radio Navigation Label Styling */
        [data-testid="stSidebar"] div[role="radiogroup"] label span {{
            color: {COLOUR_TEXT_MAIN} !important;
            font-size: 15px !important;
            font-weight: 500 !important;
        }}

        /* Active navigation item */
        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background-color: {COLOUR_PRIMARY_SOFT};
            border-radius: 8px;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span {{
            color: {COLOUR_PRIMARY_DARK} !important;
            font-weight: 700 !important;
        }}

        /* Inputs & Textareas */
        .stTextArea textarea, .stTextInput input {{
            border-radius: 8px !important;
            border: 1px solid {COLOUR_BORDER} !important;
            background-color: #FFFFFF !important;
            color: {COLOUR_TEXT_MAIN} !important;
            padding: 10px 12px !important;
            font-size: 15px !important;
        }}

        .stTextArea textarea:focus, .stTextInput input:focus {{
            border-color: {COLOUR_PRIMARY} !important;
            box-shadow: 0 0 0 1px {COLOUR_PRIMARY} !important;
        }}

        .stTextArea textarea::placeholder, .stTextInput input::placeholder {{
            color: #94A3B8 !important;
            opacity: 1 !important;
        }}

        /* Primary Form Action Buttons */
        div.stButton > button, div.stFormSubmitButton > button {{
            background-color: {COLOUR_PRIMARY} !important;
            color: #FFFFFF !important;
            height: 44px !important;
            border-radius: 8px !important;
            padding: 0px 20px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba({COLOUR_PRIMARY_RGB}, 0.30) !important;
        }}

        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background-color: {COLOUR_PRIMARY_HOVER} !important;
        }}

        [data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
        }}

        /* Key numbers draw the eye */
        [data-testid="stMetricValue"] {{
            color: {COLOUR_PRIMARY_DARK} !important;
            font-weight: 800 !important;
        }}

        /* Claim heading (the statement being checked) */
        .claim-label {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            color: {COLOUR_TEXT_MUTED};
            margin-bottom: 4px;
        }}

        .claim-statement {{
            font-size: 20px;
            font-weight: 700;
            line-height: 1.35;
            color: {COLOUR_TEXT_MAIN};
            margin-bottom: 14px;
        }}

        /* Big verdict banner: --banner-bg / --banner-fg are set per verdict */
        .verdict-banner {{
            display: flex;
            align-items: center;
            gap: 12px;
            background-color: var(--banner-bg);
            border-left: 3px solid var(--banner-border);
            border-radius: 8px;
            padding: 10px 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
        }}

        .verdict-banner, .verdict-banner * {{
            color: var(--banner-fg) !important;
        }}

        .verdict-banner .verdict-banner__icon {{
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: var(--banner-fg);
            color: var(--banner-bg) !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 800;
            line-height: 1;
        }}

        .verdict-banner__label {{
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
        }}

        .verdict-banner__verdict {{
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.3px;
            line-height: 1.2;
        }}

        .verdict-banner__text {{
            margin-top: 1px;
            font-size: 13px;
            font-weight: 500;
        }}

        /* Chips (small labels and links) */
        .chip {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            border: 1px solid {COLOUR_BORDER};
            background-color: #FFFFFF;
            color: {COLOUR_TEXT_MAIN};
        }}

        .chip-accent {{
            background-color: {COLOUR_PRIMARY_SOFT};
            border-color: {COLOUR_PRIMARY_SOFT};
            color: {COLOUR_PRIMARY_DARK};
        }}

        a.chip-link {{
            color: {COLOUR_PRIMARY} !important;
            text-decoration: none !important;
        }}

        a.chip-link:hover {{
            background-color: {COLOUR_PRIMARY_SOFT};
            border-color: {COLOUR_PRIMARY};
        }}

        .verdict-pill {{
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            border-radius: 9999px;
            background-color: var(--verdict-bg);
            color: var(--verdict-fg);
        }}

        /* Feed cards (Latest Disproven Claims) */
        .feed-card {{
            background-color: {COLOUR_CARD_BG};
            border: 1px solid {COLOUR_BORDER};
            border-left: 5px solid var(--verdict-fg, {COLOUR_PRIMARY});
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            transition: box-shadow 0.15s ease, transform 0.15s ease;
        }}

        .feed-card:hover {{
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
            transform: translateY(-1px);
        }}

        .feed-card__top {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
        }}

        .feed-card__meta {{
            margin-left: auto;
            font-size: 12px;
            font-weight: 500;
            color: {COLOUR_TEXT_MUTED};
        }}

        .feed-card__claim {{
            font-size: 18px;
            font-weight: 700;
            line-height: 1.35;
            color: {COLOUR_TEXT_MAIN};
        }}

        .feed-card__summary {{
            margin-top: 8px;
            font-size: 14px;
            line-height: 1.5;
            color: {COLOUR_TEXT_MUTED};
        }}

        .feed-card__sources {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }}

        /* Source cards (inside each claim report) */
        .source-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
            margin-bottom: 8px;
        }}

        .source-card {{
            background-color: {COLOUR_APP_BG};
            border-left: 3px solid {COLOUR_PRIMARY};
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            font-size: 14px;
            line-height: 1.5;
        }}

        .source-card__excerpt {{
            margin: 8px 0 10px 0;
        }}

        .ui-card {{
            background-color: {COLOUR_CARD_BG};
            border: 1px solid {COLOUR_BORDER};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }}

        #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
