import streamlit as st
import os
from utils import parse_env_content, save_config_to_session, load_env_from_file


def render_settings_tab():
    """Render the Settings tab"""
    st.markdown("## ⚙️ Configuration Settings")

    # Check if we have configuration loaded in session state
    if hasattr(st.session_state, 'config_settings') and st.session_state.config_settings:
        config = st.session_state.config_settings
        is_cloud = getattr(st.session_state, 'is_cloud_deployment', False)

        # Show deployment type
        if is_cloud:
            st.info(
                "🌐 **Streamlit Cloud Deployment** - Configuration loaded from secrets")
        else:
            st.info("💻 **Local Development** - Configuration loaded from .env file")

        # Show API key status
        if config.get('OPENAI_API_KEY'):
            st.success("✅ OpenAI API Key is configured")
        else:
            st.warning("⚠️ OpenAI API Key not found")

        # Display loaded variables
        st.markdown("### 📊 Loaded Configuration")
        for key, value in config.items():
            if any(s in key.upper() for s in ["KEY", "SECRET", "API"]):
                display_value = "***" + value[-4:] if len(value) > 4 else "***"
            else:
                display_value = value
            st.text(f"{key}: {display_value}")

        # Show configuration summary
        st.markdown("---")
        st.markdown("### 📋 Configuration Summary")
        st.json({
            "Deployment": "Streamlit Cloud" if is_cloud else "Local Development",
            "API Key": "✅ Configured" if config.get('OPENAI_API_KEY') else "❌ Not Set",
            "Model": config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            "Max Tokens": config.get('MAX_TOKENS', '1000'),
            "Temperature": config.get('TEMPERATURE', '0.7'),
            "Total Variables": len(config)
        })

    else:
        # No configuration found
        st.warning("⚠️ No configuration found")

        # Check if we're likely on Streamlit Cloud
        try:
            # Try to access secrets to determine environment
            if hasattr(st, 'secrets'):
                try:
                    # Try to access secrets - this will fail if no secrets.toml exists
                    secrets_dict = dict(st.secrets)
                    if secrets_dict:
                        st.markdown("### 🌐 Streamlit Cloud Deployment")
                        st.info(
                            "**For Streamlit Cloud:** Add your credentials as secrets in the Streamlit Cloud dashboard.")
                        st.markdown("""
                        **Steps to configure secrets:**
                        1. Go to your app in Streamlit Cloud
                        2. Click on "Settings" → "Secrets"
                        3. Add the following secrets:
                           ```
                           OPENAI_API_KEY = "sk-your-openai-api-key-here"
                           OPENAI_MODEL = "gpt-3.5-turbo"
                           MAX_TOKENS = "1000"
                           TEMPERATURE = "0.7"
                           ```
                        4. Save and redeploy your app
                        """)
                    else:
                        # Secrets exists but is empty - treat as local development
                        raise Exception("No secrets found")
                except:
                    # No secrets.toml or empty secrets - treat as local development
                    raise Exception("Local development mode")
            else:
                # No st.secrets - definitely local development
                raise Exception("Local development mode")
        except:
            # Local development mode
            st.markdown("### 💻 Local Development")
            st.info(
                "**For local development:** Create a `.env` file in your project root.")

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
