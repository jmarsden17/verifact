"""Password gate for the dashboard."""

import os

import streamlit as st

DEFAULT_PASSWORD = "disinformation"


def _expected_password() -> str:
    """Read DASHBOARD_PASSWORD from the environment (.env), else the default."""

    return os.environ.get("DASHBOARD_PASSWORD", DEFAULT_PASSWORD).strip()


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
            clean_input = user_password.strip() if user_password else ""

            if clean_input == _expected_password():
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

    return False
