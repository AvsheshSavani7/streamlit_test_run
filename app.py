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
