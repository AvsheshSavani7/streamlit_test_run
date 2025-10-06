import streamlit as st
from openai import OpenAI
import json
import os
import hashlib
from datetime import datetime
from typing import Dict


def parse_env_content(env_content: str) -> Dict[str, str]:
    """Parse .env file content and return key-value pairs"""
    env_vars = {}
    for line in env_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env_vars[key] = value
    return env_vars


def clean_json_syntax(text: str) -> str:
    """Clean up JSON syntax issues in prompts"""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if '//' in line:
            comment_index = line.find('//')
            if comment_index > 0:
                cleaned_line = line[:comment_index].rstrip()
                cleaned_lines.append(cleaned_line)
            else:
                continue
        else:
            cleaned_lines.append(line)

    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = cleaned_text.replace('{', '{{').replace('}', '}}')
    cleaned_text = cleaned_text.replace('{{company_name}}', '{company_name}')

    return cleaned_text


def parse_analysis_json(analysis_text: str):
    """Parse analysis text and return formatted JSON if possible"""
    try:
        parsed_json = json.loads(analysis_text)
        return json.dumps(parsed_json, indent=2)
    except json.JSONDecodeError:
        return analysis_text


def display_analysis_result(analysis_data, company_name: str = ""):
    """Display analysis result with proper JSON formatting"""
    if isinstance(analysis_data, dict):
        st.json(analysis_data)
    elif isinstance(analysis_data, str):
        try:
            parsed_json = json.loads(analysis_data)
            st.json(parsed_json)
        except json.JSONDecodeError:
            st.text_area(f"Analysis for {company_name}",
                         value=analysis_data, height=200, disabled=True)
    else:
        st.text_area(f"Analysis for {company_name}",
                     value=str(analysis_data), height=200, disabled=True)


def save_config_to_session(config: Dict[str, str]):
    """Save configuration to session state and user storage"""
    st.session_state.config_settings = config
    if 'OPENAI_API_KEY' in config:
        st.session_state.openai_api_key = config['OPENAI_API_KEY']
        st.session_state.openai_client = OpenAI(
            api_key=config['OPENAI_API_KEY'])

    # Save to user settings (localStorage equivalent)
    user_settings = {
        'config_settings': config,
        'openai_api_key': config.get('OPENAI_API_KEY', ''),
        'last_saved': datetime.now().isoformat()
    }
    save_user_settings(user_settings)


def load_env_from_file():
    """Load environment variables from .env file if it exists"""
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, 'r') as f:
                content = f.read()
                env_vars = parse_env_content(content)
                save_config_to_session(env_vars)
                return content
        except Exception as e:
            st.error(f"Error reading .env file: {str(e)}")
    return ""


def get_user_id():
    """Generate a unique user ID based on browser info"""
    # Use Streamlit's session info to create a unique identifier
    try:
        # Get session info from Streamlit
        session_info = st.get_option("server.headless")
        # Create a hash from session info for user identification
        user_string = f"user_{hash(str(session_info))}"
        return hashlib.md5(user_string.encode()).hexdigest()[:16]
    except:
        # Fallback to a default user ID
        return "default_user"


def load_user_settings():
    """Load user settings from browser storage (simulated with file)"""
    user_id = get_user_id()
    settings_file = f".user_settings_{user_id}.json"

    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_user_settings(settings):
    """Save user settings to browser storage (simulated with file)"""
    user_id = get_user_id()
    settings_file = f".user_settings_{user_id}.json"

    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f)
        return True
    except:
        return False


def initialize_session_state():
    """Initialize all session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = get_user_id()

    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'generated_output' not in st.session_state:
        st.session_state.generated_output = ""
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    if 'output_file' not in st.session_state:
        st.session_state.output_file = None
    if 'config_settings' not in st.session_state:
        # Load from user settings first
        user_settings = load_user_settings()
        st.session_state.config_settings = user_settings.get(
            'config_settings', {})
        if user_settings.get('openai_api_key'):
            st.session_state.openai_api_key = user_settings['openai_api_key']
            st.session_state.openai_client = OpenAI(
                api_key=user_settings['openai_api_key'])
    if 'env_file_content' not in st.session_state:
        st.session_state.env_file_content = ""
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = None
    # Validation tab session state
    if 'validation_input_json' not in st.session_state:
        st.session_state.validation_input_json = None
    if 'validation_expected_json' not in st.session_state:
        st.session_state.validation_expected_json = None
    if 'validation_actual_json' not in st.session_state:
        st.session_state.validation_actual_json = None
