"""Fixed design elements for the app."""
import streamlit as st

# Custom Brand Colours
COLOUR_APP_BG = "#F3F4F6"
COLOUR_SIDEBAR_BG = "#FFFFFF"
COLOUR_CARD_BG = "#FFFFFF"
COLOUR_BORDER = "#E2E8F0"
COLOUR_TEXT_MAIN = "#0F172A"
COLOUR_TEXT_MUTED = "#64748B"
COLOUR_PRIMARY = "#6A8EAE"
COLOUR_PRIMARY_HOVER = "#4A6E91"

# Semantic Colours - good/bad/warning
COLOUR_SUCCESS_BG = "#DCFCE7"
COLOUR_SUCCESS_FG = "#166534"

COLOUR_DANGER_BG = "#FEE2E2"
COLOUR_DANGER_FG = "#991B1B"

COLOUR_WARNING_BG = "#FEF3C7"
COLOUR_WARNING_FG = "#92400E"


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

        /* Inputs & Textareas */
        .stTextArea textarea, .stTextInput input {{
            border-radius: 8px !important;
            border: 1px solid {COLOUR_BORDER} !important;
            background-color: #FFFFFF !important;
            color: {COLOUR_TEXT_MAIN} !important;
            padding: 10px 12px !important;
            font-size: 15px !important;
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
        }}

        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background-color: {COLOUR_PRIMARY_HOVER} !important;
        }}

        [data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
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
