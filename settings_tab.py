import streamlit as st
import os
from utils import parse_env_content, save_config_to_session, load_env_from_file


def render_settings_tab():
    """Render the Settings tab"""
    st.markdown("## ⚙️ Configuration Settings")

    # Logout button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.user_authenticated = False
            st.session_state.username = ""
            st.rerun()

    # Load configuration from .env file
    env_file_path = '.env'

    # Check if .env file exists
    if os.path.exists(env_file_path):

        # Load and parse the .env file
        try:
            with open(env_file_path, 'r') as f:
                env_content = f.read()

            env_vars = parse_env_content(env_content)

            if env_vars:
                # Save to session state
                save_config_to_session(env_vars)

                # Show API key status
                if env_vars.get('OPENAI_API_KEY'):
                    st.success("✅ API Key is configured")
                else:
                    st.warning("⚠️ API Key not found in .env file")

                # Display loaded variables
                st.markdown("### 📊 Loaded Configuration")
                for key, value in env_vars.items():
                    if any(s in key.upper() for s in ["KEY", "SECRET", "API"]):
                        display_value = "***" + \
                            value[-4:] if len(value) > 4 else "***"
                    else:
                        display_value = value
                    st.text(f"{key}: {display_value}")

                # Show configuration summary
                st.markdown("---")
                st.markdown("### 📋 Configuration Summary")
                st.json({
                    "API Key": "✅ Configured" if env_vars.get('OPENAI_API_KEY') else "❌ Not Set",
                    "Model": env_vars.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                    "Max Tokens": env_vars.get('MAX_TOKENS', '1000'),
                    "Temperature": env_vars.get('TEMPERATURE', '0.7'),
                    "Total Variables": len(env_vars)
                })

            else:
                st.warning(
                    "⚠️ No valid environment variables found in .env file")

        except Exception as e:
            st.error(f"❌ Error reading .env file: {str(e)}")

    else:
        st.warning("⚠️ .env file not found")
        st.info(
            "Please create a `.env` file in the project root with your configuration.")

        # Show example .env content
        st.markdown("### 📝 Create .env File")
        st.markdown(
            "Create a file named `.env` in your project root with the following content:")

        example_content = """# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=1000
TEMPERATURE=0.7

# Optional: Other APIs
# ANTHROPIC_API_KEY=your-anthropic-key
# GOOGLE_API_KEY=your-google-key"""

        st.code(example_content, language="env")

        st.markdown("**Instructions:**")
        st.markdown(
            "1. Create a file named `.env` in the same directory as `app.py`")
        st.markdown("2. Copy the above template into the `.env` file")
        st.markdown(
            "3. Replace `sk-your-openai-api-key-here` with your actual OpenAI API key")
        st.markdown("4. Save the file and refresh this page")
        st.markdown("5. ⚠️ Never share your API key with others!")

        # Refresh button
        if st.button("🔄 Refresh Configuration", key="refresh_config"):
            st.rerun()
