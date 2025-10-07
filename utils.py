import streamlit as st
from openai import OpenAI
import json
import os
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
    """Save configuration to session state"""
    st.session_state.config_settings = config
    if 'OPENAI_API_KEY' in config:
        st.session_state.openai_api_key = config['OPENAI_API_KEY']
        st.session_state.openai_client = OpenAI(
            api_key=config['OPENAI_API_KEY'])


def load_config_from_secrets():
    """Load configuration from Streamlit secrets (for cloud deployment)"""
    try:
        # Check if we're running on Streamlit Cloud with secrets
        if hasattr(st, 'secrets'):
            # Try to access secrets - this will fail gracefully if no secrets.toml exists
            try:
                # Check if secrets is accessible and has content
                secrets_dict = dict(st.secrets)
                if not secrets_dict:
                    return None

                config = {}
                # Map common secret keys
                secret_mapping = {
                    'OPENAI_API_KEY': 'OPENAI_API_KEY',
                    'openai_api_key': 'OPENAI_API_KEY',
                    'OPENAI_MODEL': 'OPENAI_MODEL',
                    'openai_model': 'OPENAI_MODEL',
                    'MAX_TOKENS': 'MAX_TOKENS',
                    'max_tokens': 'MAX_TOKENS',
                    'TEMPERATURE': 'TEMPERATURE',
                    'temperature': 'TEMPERATURE'
                }

                # Try to get secrets
                for secret_key, config_key in secret_mapping.items():
                    try:
                        if secret_key in secrets_dict:
                            config[config_key] = secrets_dict[secret_key]
                    except:
                        pass

                return config if config else None
            except Exception as secrets_error:
                # No secrets.toml file or other secrets access error
                # This is normal for local development
                return None
    except Exception as e:
        # General error accessing st.secrets
        return None
    return None


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
        # First try to load from Streamlit secrets (for cloud deployment)
        secrets_config = load_config_from_secrets()
        if secrets_config:
            st.session_state.config_settings = secrets_config
            st.session_state.is_cloud_deployment = True
            if secrets_config.get('OPENAI_API_KEY'):
                st.session_state.openai_api_key = secrets_config['OPENAI_API_KEY']
                st.session_state.openai_client = OpenAI(
                    api_key=secrets_config['OPENAI_API_KEY'])
        else:
            # Fallback to .env file (for local development)
            env_content = load_env_from_file()
            if env_content:
                env_vars = parse_env_content(env_content)
                st.session_state.config_settings = env_vars
                st.session_state.is_cloud_deployment = False
                if env_vars.get('OPENAI_API_KEY'):
                    st.session_state.openai_api_key = env_vars['OPENAI_API_KEY']
                    st.session_state.openai_client = OpenAI(
                        api_key=env_vars['OPENAI_API_KEY'])
            else:
                st.session_state.config_settings = {}
                st.session_state.is_cloud_deployment = False
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = None
    if 'is_cloud_deployment' not in st.session_state:
        st.session_state.is_cloud_deployment = False
    # Validation tab session state
    if 'validation_input_json' not in st.session_state:
        st.session_state.validation_input_json = None
    if 'validation_expected_json' not in st.session_state:
        st.session_state.validation_expected_json = None
    if 'validation_actual_json' not in st.session_state:
        st.session_state.validation_actual_json = None
