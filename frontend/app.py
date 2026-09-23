"""Main application entry point: page config, login, sidebar and routing."""

import streamlit as st
from dotenv import load_dotenv
from auth import check_password
from visual_components import theme
from visual_components.components import sidebar
from visual_components.views import (
    claim_verification,
    claims_analytics,
    disproven_claims,
    outlet_analytics,
    verification_logs,
)

# Load environment variables from .env file
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Verifact",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Theme Rules
theme.inject_custom_theme()

if not check_password():
    st.stop()

# Sidebar label -> function that renders that page.
# To add a page: create a file in visual_components/views/ and add one line here.
VIEWS = {
    "Claim Verification": claim_verification.render,
    "Latest Disproven Claims": disproven_claims.render,
    "Verification Logs": verification_logs.render,
    "Outlet Analytics": outlet_analytics.render,
    "Claims Analytics": claims_analytics.render,
}

sidebar.render_sidebar_logo()
selected_view = st.sidebar.radio(
    "Navigation", list(VIEWS), label_visibility="collapsed")
sidebar.render_system_status()

VIEWS[selected_view]()
