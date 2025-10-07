import streamlit as st
from openai import OpenAI
import json
import os
from datetime import datetime
from typing import Dict

from streamlit_js_eval import streamlit_js_eval


def save_login(username: str):
    """Save username into browser localStorage"""
    try:
        streamlit_js_eval(
            js_expressions=f"localStorage.setItem('APP_USERNAME', '{username}')",
            key="set_username"
        )
        return True
    except Exception as e:
        print(f"Error saving login: {e}")
        return False


def load_login():
    """Load username from browser localStorage"""
    try:
        username = streamlit_js_eval(
            js_expressions="localStorage.getItem('APP_USERNAME')",
            key="get_username"
        )
        return username if username else None
    except Exception as e:
        print(f"Error loading login: {e}")
        return None


def clear_login():
    """Clear saved username from browser localStorage"""
    try:
        streamlit_js_eval(
            js_expressions="localStorage.removeItem('APP_USERNAME')",
            key="clear_username"
        )
    except Exception as e:
        print(f"Error clearing login: {e}")


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
    """Save configuration to session state"""
    st.session_state.config_settings = config
    if 'OPENAI_API_KEY' in config:
        st.session_state.openai_api_key = config['OPENAI_API_KEY']
        st.session_state.openai_client = OpenAI(
            api_key=config['OPENAI_API_KEY'])


def load_env_from_file():
    """Load environment variables from .env file if it exists"""
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, 'r') as f:
                content = f.read()
                return content
        except Exception as e:
            st.error(f"Error reading .env file: {str(e)}")
    return ""


def initialize_session_state():
    """Initialize all session state variables"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'generated_output' not in st.session_state:
        st.session_state.generated_output = ""
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    if 'output_file' not in st.session_state:
        st.session_state.output_file = None
    if 'config_settings' not in st.session_state:
        # Try to load from .env file
        env_content = load_env_from_file()
        if env_content:
            env_vars = parse_env_content(env_content)
            st.session_state.config_settings = env_vars
            if env_vars.get('OPENAI_API_KEY'):
                st.session_state.openai_api_key = env_vars['OPENAI_API_KEY']
                st.session_state.openai_client = OpenAI(
                    api_key=env_vars['OPENAI_API_KEY'])
        else:
            st.session_state.config_settings = {}
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = None
    # Validation tab session state
    if 'validation_input_json' not in st.session_state:
        st.session_state.validation_input_json = None
    if 'validation_expected_json' not in st.session_state:
        st.session_state.validation_expected_json = None
    if 'validation_actual_json' not in st.session_state:
        st.session_state.validation_actual_json = None
