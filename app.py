import streamlit as st
from utils import initialize_session_state, load_env_from_file
from company_analysis_tab import render_company_analysis_tab
from validation_tab import render_validation_tab
from settings_tab import render_settings_tab

# Configure page
st.set_page_config(
    page_title="Company Analysis Tool",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define allowed users (static list)
ALLOWED_USERS = [
    "avshesh.teqno"
]


def check_user_authentication():
    """Check if user is authenticated"""
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""

    return st.session_state.user_authenticated


def show_login_popup():
    """Show login popup for user authentication"""
    st.markdown("---")
    st.markdown("## 🔐 User Authentication Required")
    st.warning("⚠️ Please enter your username to access the application")

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Login")

            username = st.text_input(
                "Username:",
                placeholder="Enter your username",
                key="login_username"
            )

            if st.button("🚀 Login", type="primary"):
                if username.strip():
                    if username.strip().lower() in [user.lower() for user in ALLOWED_USERS]:
                        st.session_state.user_authenticated = True
                        st.session_state.username = username.strip()
                        st.success(f"✅ Welcome, {username}! Access granted.")
                        st.rerun()
                    else:
                        st.error(
                            "❌ Access denied. Username not found in allowed users list.")
                else:
                    st.error("❌ Please enter a username.")

            st.markdown("---")
            # st.info("**Allowed Users:** " + ", ".join(ALLOWED_USERS))

    # Initialize session state
    initialize_session_state()


# Check authentication
if not check_user_authentication():
    show_login_popup()
    st.stop()

# User is authenticated, proceed with normal app
st.success(f"👋 Welcome, {st.session_state.username}!")

# Initialize session state
initialize_session_state()

# Header with tabs
tab1, validation_tab, settings_tab = st.tabs(
    ["Company Analysis", "Result Validation", "Settings"])

# Tab 1 - Company Analysis
with tab1:
    render_company_analysis_tab()

# Result Validation Tab
with validation_tab:
    render_validation_tab()

# Settings Tab
with settings_tab:
    render_settings_tab()

# Footer
st.markdown("---")
