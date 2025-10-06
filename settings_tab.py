import streamlit as st
import json
from utils import parse_env_content, save_config_to_session, load_user_settings, save_user_settings, get_user_id


def render_settings_tab():
    """Render the Settings tab"""
    st.markdown("## ⚙️ Configuration Settings")

    # Show user info and localStorage status
    user_id = get_user_id()
    user_settings = load_user_settings()

    st.info(
        f"👤 **User ID:** `{user_id}` | 💾 **Settings stored in:** Browser localStorage (simulated)")

    if user_settings.get('last_saved'):
        st.success(f"✅ **Last saved:** {user_settings['last_saved']}")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🔧 Environment Variables")
        st.markdown("Configure individual environment variables:")

        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value="",  # Never show the actual key
            placeholder="Enter your OpenAI API key",
            help="Your OpenAI API key for generating company analysis"
        )

        # Show if API key is configured without revealing it
        if st.session_state.config_settings.get('OPENAI_API_KEY'):
            st.success("✅ API Key is configured")
        else:
            st.warning("⚠️ API Key not configured")

        model_name = st.text_input(
            "OpenAI Model",
            value=st.session_state.config_settings.get(
                'OPENAI_MODEL', 'gpt-3.5-turbo'),
            help="OpenAI model to use (default: gpt-3.5-turbo)"
        )

        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=int(st.session_state.config_settings.get(
                'MAX_TOKENS', 1000)),
            help="Maximum tokens for API response"
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=float(st.session_state.config_settings.get(
                'TEMPERATURE', 0.7)),
            step=0.1,
            help="Controls randomness in AI responses"
        )

        if st.button("💾 Save Individual Settings", key="save_individual"):
            config = {
                'OPENAI_MODEL': model_name,
                'MAX_TOKENS': str(max_tokens),
                'TEMPERATURE': str(temperature)
            }

            # Only update API key if user provided a new one
            if openai_key.strip():
                config['OPENAI_API_KEY'] = openai_key
                st.success("✅ Individual settings saved with new API key!")
            else:
                # Keep existing API key if no new one provided
                if st.session_state.config_settings.get('OPENAI_API_KEY'):
                    config['OPENAI_API_KEY'] = st.session_state.config_settings['OPENAI_API_KEY']
                st.success("✅ Individual settings saved!")

            save_config_to_session(config)

    with col2:
        st.markdown("### 📄 .env File Configuration")
        st.markdown("Paste your entire .env file content here:")

        env_content = st.text_area(
            ".env File Content",
            value=st.session_state.env_file_content,
            height=300,
            placeholder="OPENAI_API_KEY=your_key_here\nOPENAI_MODEL=gpt-3.5-turbo\nMAX_TOKENS=1000\nTEMPERATURE=0.7\n# Add more variables as needed",
            help="Paste your complete .env file content. Each line should be in KEY=VALUE format."
        )

        if st.button("🔄 Load from .env Content", key="load_env_content"):
            if env_content.strip():
                try:
                    env_vars = parse_env_content(env_content)
                    if env_vars:
                        save_config_to_session(env_vars)
                        st.session_state.env_file_content = env_content
                        st.success(
                            f"✅ Loaded {len(env_vars)} environment variables!")

                        st.markdown("**Loaded Variables:**")
                        for key, value in env_vars.items():
                            if 'KEY' in key.upper() or 'SECRET' in key.upper() or 'API' in key.upper():
                                display_value = "***" + \
                                    value[-4:] if len(value) > 4 else "***"
                            else:
                                display_value = value
                            st.text(f"{key}: {display_value}")
                    else:
                        st.warning(
                            "⚠️ No valid environment variables found in the content")
                except Exception as e:
                    st.error(f"❌ Error parsing .env content: {str(e)}")
            else:
                st.warning("⚠️ Please enter .env file content")

        if st.button("💾 Save .env to File", key="save_env_file"):
            if env_content.strip():
                try:
                    with open('.env', 'w') as f:
                        f.write(env_content)
                    st.success("✅ .env file saved to disk!")
                except Exception as e:
                    st.error(f"❌ Error saving .env file: {str(e)}")
            else:
                st.warning("⚠️ No content to save")

    # Current Configuration Status
    st.markdown("---")
    st.markdown("### 📊 Current Configuration Status")

    if st.session_state.config_settings:
        st.success("✅ Configuration is active")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**API Configuration:**")
            api_key_status = "✅ Set" if st.session_state.config_settings.get(
                'OPENAI_API_KEY') else "❌ Not Set"
            model_status = st.session_state.config_settings.get(
                'OPENAI_MODEL', 'gpt-3.5-turbo')
            st.text(f"API Key: {api_key_status}")
            st.text(f"Model: {model_status}")

            # Show masked API key if available
            if st.session_state.config_settings.get('OPENAI_API_KEY'):
                masked_key = "sk-***" + \
                    st.session_state.config_settings['OPENAI_API_KEY'][-4:]
                st.text(f"Key Preview: {masked_key}")

        with col2:
            st.markdown("**Generation Settings:**")
            max_tokens = st.session_state.config_settings.get(
                'MAX_TOKENS', '1000')
            temperature = st.session_state.config_settings.get(
                'TEMPERATURE', '0.7')
            st.text(f"Max Tokens: {max_tokens}")
            st.text(f"Temperature: {temperature}")

        with col3:
            st.markdown("**Total Variables:**")
            total_vars = len(st.session_state.config_settings)
            st.text(f"Loaded: {total_vars}")

            col_clear1, col_clear2 = st.columns(2)

            with col_clear1:
                if st.button("🗑️ Clear Configuration", key="clear_config"):
                    st.session_state.config_settings = {}
                    st.session_state.env_file_content = ""
                    st.session_state.openai_api_key = ""
                    st.session_state.openai_client = None
                    # Clear localStorage as well
                    save_user_settings({})
                    st.rerun()

            with col_clear2:
                if st.button("🔑 Clear API Key Only", key="clear_api_key"):
                    if 'OPENAI_API_KEY' in st.session_state.config_settings:
                        del st.session_state.config_settings['OPENAI_API_KEY']
                    st.session_state.openai_api_key = ""
                    st.session_state.openai_client = None
                    # Also clear from localStorage
                    user_settings = load_user_settings()
                    if 'openai_api_key' in user_settings:
                        del user_settings['openai_api_key']
                    if 'config_settings' in user_settings and 'OPENAI_API_KEY' in user_settings['config_settings']:
                        del user_settings['config_settings']['OPENAI_API_KEY']
                    save_user_settings(user_settings)
                    st.rerun()
    else:
        st.info(
            "ℹ️ No configuration loaded. Use the options above to configure your environment variables.")

    # Example .env file
    st.markdown("---")
    with st.expander("📝 Example .env File Format"):
        st.markdown("""
        ```env
        # OpenAI Configuration
        OPENAI_API_KEY=sk-your-openai-api-key-here
        OPENAI_MODEL=gpt-3.5-turbo
        MAX_TOKENS=1000
        TEMPERATURE=0.7
        
        # Optional: Other API configurations
        # ANTHROPIC_API_KEY=your-anthropic-key
        # GOOGLE_API_KEY=your-google-key
        
        # Application settings
        # DEBUG=false
        # LOG_LEVEL=info
        ```
        
        **Instructions:**
        1. Copy the above template
        2. Replace the placeholder values with your actual API keys
        3. Paste the entire content in the text area above
        4. Click "Load from .env Content" to apply the settings
        """)

    # localStorage Management Section
    st.markdown("---")
    st.markdown("### 💾 Browser localStorage Management")

    col_local1, col_local2 = st.columns(2)

    with col_local1:
        st.markdown("**Current localStorage Status:**")
        if user_settings:
            st.success("✅ Settings stored in browser")
            st.json({
                "user_id": user_id,
                "has_api_key": bool(user_settings.get('openai_api_key')),
                "config_count": len(user_settings.get('config_settings', {})),
                "last_saved": user_settings.get('last_saved', 'Never')
            })
        else:
            st.info("ℹ️ No settings in localStorage")

    with col_local2:
        st.markdown("**localStorage Actions:**")
        if st.button("📥 Export Settings", key="export_settings"):
            if user_settings:
                settings_json = json.dumps(user_settings, indent=2)
                st.download_button(
                    label="💾 Download Settings",
                    data=settings_json,
                    file_name=f"user_settings_{user_id}.json",
                    mime="application/json"
                )
            else:
                st.warning("No settings to export")

        if st.button("🗑️ Clear localStorage", key="clear_localStorage"):
            save_user_settings({})
            st.session_state.config_settings = {}
            st.session_state.openai_api_key = ""
            st.session_state.openai_client = None
            st.success("localStorage cleared!")
            st.rerun()
