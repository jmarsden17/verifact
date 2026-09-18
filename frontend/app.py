"""Main Application Routing."""

import os
import streamlit as st
from dotenv import load_dotenv
from visual_components import ui, theme, visuals
from database_conns import connection, fetch_data
# Load environment variables from .env file
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Disinformation Verifier",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Theme Rules
theme.inject_custom_theme()


def check_password() -> bool:
    """Returns True if user is authenticated, otherwise renders login gate."""

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("## 🔒 Dashboard Authentication Required")
    st.markdown(
        "Please enter the password to access the verification workspace.")

    with st.form("login_form"):
        user_password = st.text_input("Password", type="password")
        submit_btn = st.form_submit_button("Log In")

        if submit_btn:
            # Reads DASHBOARD_PASSWORD from .env, fallback to "disinformation"
            expected_password = os.environ.get(
                "DASHBOARD_PASSWORD", "disinformation").strip()
            clean_input = user_password.strip() if user_password else ""

            if clean_input == expected_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

    return False


if not check_password():
    st.stop()


ui.render_sidebar_logo()

view = st.sidebar.radio(
    "Navigation",
    ["Claim Verification", "Top Disproven Claims",
        "Verification Logs", "Outlet Analytics"],
    label_visibility="collapsed"
)

ui.render_system_status()

# Routing Logic
if view == "Claim Verification":
    ui.render_claim_verification_view()
elif view == "Top Disproven Claims":
    ui.render_top_disproven_claims_view()
elif view == "Verification Logs":
    ui.render_verification_logs_view()
elif view == "Outlet Analytics":
    ui.render_outlet_credibility_view()
