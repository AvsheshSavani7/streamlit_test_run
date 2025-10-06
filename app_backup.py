import streamlit as st
from openai import OpenAI
import json
import os
from datetime import datetime
from typing import Dict

# Configure page
st.set_page_config(
    page_title="Company Analysis Tool",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'generated_output' not in st.session_state:
    st.session_state.generated_output = ""
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'output_file' not in st.session_state:
    st.session_state.output_file = None
if 'config_settings' not in st.session_state:
    st.session_state.config_settings = {}
if 'env_file_content' not in st.session_state:
    st.session_state.env_file_content = ""
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = None

# Configuration functions


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
                env_vars = parse_env_content(content)
                save_config_to_session(env_vars)
                return content
        except Exception as e:
            st.error(f"Error reading .env file: {str(e)}")
    return ""


# Load existing .env file on startup
if not st.session_state.env_file_content:
    st.session_state.env_file_content = load_env_from_file()

# Header with tabs
tab1, validation_tab, settings_tab = st.tabs(
    ["Company Analysis", "Result Validation", "Settings"])

# Tab 1 - Main functionality
with tab1:
    st.subheader("Company Analysis Dashboard")

    # Create three columns
    col1, col2, col3 = st.columns([1, 2, 1])

    # Left Panel - Company Input
    with col1:
        company_name = st.text_input(
            "Company Name", placeholder="Enter company name", key="company_input")

        # Show current configuration status
        if st.session_state.config_settings:
            st.success("✅ Configuration loaded from Settings")
        else:
            st.info("💡 Go to Settings tab to configure environment variables")

    # Center Panel - Prompt and Single Run
    with col2:
        st.markdown("### Prompt box")
        default_prompt = """You are a social media research expert. I need you to find the official Twitter handles for {company_name}.

Company: {company_name}

Please provide:
1. The main company's official Twitter handle

Focus on:
- Official corporate accounts (usually verified with blue checkmark)

Format your response strictly as JSON with the following schema:
{{
  "company_name": "{company_name}",
  "main_twitter_handle": "@company_handle"
}}

Important:
- Only include verified or clearly official accounts
- Use @ symbol for all handles
- If no Twitter handle is found, use null for the handle field
- Be specific about account types and descriptions
- Only return JSON, no additional text"""

        prompt_text = st.text_area(
            "Prompt box",
            value=default_prompt,
            height=300,
            key="prompt_input"
        )

        # Single run button
        if st.button("Single run", key="single_run_btn"):
            if not company_name:
                st.error("Please enter a company name")
            elif not st.session_state.openai_api_key:
                st.error("Please enter your OpenAI API key")
            else:
                with st.spinner("Generating analysis..."):
                    try:
                        cleaned_prompt = clean_json_syntax(prompt_text)

                        if "{company_name}" in cleaned_prompt:
                            formatted_prompt = cleaned_prompt.format(
                                company_name=company_name)
                        else:
                            formatted_prompt = f"{cleaned_prompt}\n\nCompany to analyze: {company_name}"

                        model = st.session_state.config_settings.get(
                            'OPENAI_MODEL', 'gpt-3.5-turbo')
                        max_tokens = int(
                            st.session_state.config_settings.get('MAX_TOKENS', 1000))
                        temperature = float(
                            st.session_state.config_settings.get('TEMPERATURE', 0.7))

                        if st.session_state.openai_client:
                            client = st.session_state.openai_client
                        else:
                            client = OpenAI(
                                api_key=st.session_state.openai_api_key)

                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "You are a business analyst providing detailed company analysis."},
                                {"role": "user", "content": formatted_prompt}
                            ],
                            max_tokens=max_tokens,
                            temperature=temperature
                        )

                        analysis_content = response.choices[0].message.content
                        try:
                            parsed_analysis = json.loads(analysis_content)
                            st.session_state.generated_output = parsed_analysis
                        except json.JSONDecodeError:
                            st.session_state.generated_output = analysis_content
                        st.success("Analysis generated successfully!")

                    except Exception as e:
                        st.error(f"Error generating analysis: {str(e)}")

        # Output display area
        st.markdown("### Show Output Here")
        if st.session_state.generated_output:
            display_analysis_result(
                st.session_state.generated_output, company_name)
        else:
            st.info("Click 'Single run' to generate analysis output")

    # Right Panel - JSON Upload and Batch Processing
    with col3:
        st.markdown("### Company Data Source")

        # Choose between default or upload
        data_source = st.radio(
            "Choose data source:",
            ["Use Default Sample", "Upload Custom JSON"],
            key="data_source_radio"
        )

        json_data = None

        if data_source == "Use Default Sample":
            st.info("📋 Using default sample companies")
            try:
                with open('twitter/deafult_Input.json', 'r') as f:
                    json_data = json.load(f)
                st.success(f"✅ Loaded {len(json_data)} default companies")
                st.json(json_data)
            except FileNotFoundError:
                st.error(
                    "❌ Default sample file not found at twitter/deafult_Input.json")
                json_data = None
            except Exception as e:
                st.error(f"❌ Error loading default file: {str(e)}")
                json_data = None

        else:  # Upload Custom JSON
            uploaded_file = st.file_uploader("Upload JSON file", type=[
                                             'json'], key="json_upload")

            if uploaded_file:
                try:
                    json_data = json.load(uploaded_file)
                    st.success(
                        f"✅ Loaded {len(json_data)} companies from upload")
                    st.json(json_data)
                except Exception as e:
                    st.error(f"❌ Error reading uploaded file: {str(e)}")
                    json_data = None

        if json_data:
            try:
                if isinstance(json_data, list):
                    st.success(f"Loaded {len(json_data)} companies")

                    # Generated output display
                    st.markdown("### Generated output")
                    if st.session_state.batch_results:
                        st.write(
                            f"Processed {len(st.session_state.batch_results)} companies")

                        # Show complete results
                        with st.expander("📊 View Complete Results", expanded=False):
                            for i, result in enumerate(st.session_state.batch_results):
                                st.markdown(f"**{result['company']}:**")
                                display_analysis_result(
                                    result['analysis'], result['company'])
                                if i < len(st.session_state.batch_results) - 1:
                                    st.markdown("---")
                    else:
                        st.info("No batch results yet")

                    # Batch run button
                    if st.button("Run btn", key="batch_run_btn"):
                        if not st.session_state.openai_api_key:
                            st.error("Please enter your OpenAI API key")
                        else:
                            with st.spinner("Processing companies..."):
                                results = []
                                for i, company in enumerate(json_data):
                                    if isinstance(company, dict) and 'name' in company:
                                        company_name_batch = company['name']
                                    elif isinstance(company, str):
                                        company_name_batch = company
                                    else:
                                        continue

                                    try:
                                        cleaned_prompt = clean_json_syntax(
                                            prompt_text)

                                        if "{company_name}" in cleaned_prompt:
                                            formatted_prompt = cleaned_prompt.format(
                                                company_name=company_name_batch)
                                        else:
                                            formatted_prompt = f"{cleaned_prompt}\n\nCompany to analyze: {company_name_batch}"

                                        model = st.session_state.config_settings.get(
                                            'OPENAI_MODEL', 'gpt-3.5-turbo')
                                        max_tokens = int(
                                            st.session_state.config_settings.get('MAX_TOKENS', 1000))
                                        temperature = float(
                                            st.session_state.config_settings.get('TEMPERATURE', 0.7))

                                        if st.session_state.openai_client:
                                            client = st.session_state.openai_client
                                        else:
                                            client = OpenAI(
                                                api_key=st.session_state.openai_api_key)

                                        response = client.chat.completions.create(
                                            model=model,
                                            messages=[
                                                {"role": "system", "content": "You are a business analyst providing detailed company analysis."},
                                                {"role": "user",
                                                    "content": formatted_prompt}
                                            ],
                                            max_tokens=max_tokens,
                                            temperature=temperature
                                        )

                                        analysis_content = response.choices[0].message.content
                                        try:
                                            parsed_analysis = json.loads(
                                                analysis_content)
                                        except json.JSONDecodeError:
                                            parsed_analysis = analysis_content

                                        results.append({
                                            "company": company_name_batch,
                                            "analysis": parsed_analysis,
                                            "timestamp": datetime.now().isoformat()
                                        })

                                        st.progress((i + 1) / len(json_data))

                                    except Exception as e:
                                        results.append({
                                            "company": company_name_batch,
                                            "analysis": f"Error: {str(e)}",
                                            "timestamp": datetime.now().isoformat()
                                        })

                                st.session_state.batch_results = results
                                st.success(
                                    f"Processed {len(results)} companies successfully!")

                                output_data = {
                                    "generated_at": datetime.now().isoformat(),
                                    "total_companies": len(results),
                                    "results": results
                                }

                                json_output = json.dumps(output_data, indent=2)
                                st.session_state.output_file = json_output

                else:
                    st.error("JSON file must contain an array of companies")

            except Exception as e:
                st.error(f"Error reading JSON file: {str(e)}")

        # Download section
        if st.session_state.output_file:
            st.markdown("### Download Results")
            st.download_button(
                label="Download Analysis Results",
                data=st.session_state.output_file,
                file_name=f"company_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Result Validation Tab
with validation_tab:
    st.subheader("Result Validation Dashboard")

    # Create three columns
    col1, col2, col3 = st.columns([1, 2, 1])

    # Left Panel - JSON File Inputs
    with col1:
        st.markdown("### JSON File Inputs")

        # Initialize session state for validation files
        if 'validation_input_json' not in st.session_state:
            st.session_state.validation_input_json = None
        if 'validation_expected_json' not in st.session_state:
            st.session_state.validation_expected_json = None
        if 'validation_actual_json' not in st.session_state:
            st.session_state.validation_actual_json = None

        # 1. Previous Tab JSON Input File
        st.markdown("#### 1. Previous Tab JSON Input")
        input_source = st.radio(
            "Input source:",
            ["Use Default Sample", "Upload Custom"],
            key="input_source_radio"
        )

        if input_source == "Use Default Sample":
            try:
                with open('twitter/deafult_Input.json', 'r') as f:
                    st.session_state.validation_input_json = json.load(f)
                st.success(
                    f"✅ Loaded {len(st.session_state.validation_input_json)} companies")
            except FileNotFoundError:
                st.error(
                    "❌ Default input file not found at twitter/deafult_Input.json")
                st.session_state.validation_input_json = None
        else:
            uploaded_input = st.file_uploader("Upload Input JSON", type=[
                                              'json'], key="input_json_upload")
            if uploaded_input:
                try:
                    st.session_state.validation_input_json = json.load(
                        uploaded_input)
                    st.success(f"✅ Loaded input JSON")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.validation_input_json = None

        # 2. Expected Output File
        st.markdown("#### 2. Expected Output JSON")
        expected_source = st.radio(
            "Expected source:",
            ["Use Sample Expected", "Upload Custom"],
            key="expected_source_radio"
        )

        if expected_source == "Use Sample Expected":
            try:
                with open('twitter/expected_output.json', 'r') as f:
                    st.session_state.validation_expected_json = json.load(f)
                st.success(
                    "✅ Loaded expected output from twitter/expected_output.json")
            except FileNotFoundError:
                st.error(
                    "❌ Expected output file not found at twitter/expected_output.json")
                st.session_state.validation_expected_json = None
        else:
            uploaded_expected = st.file_uploader("Upload Expected JSON", type=[
                                                 'json'], key="expected_json_upload")
            if uploaded_expected:
                try:
                    st.session_state.validation_expected_json = json.load(
                        uploaded_expected)
                    st.success(f"✅ Loaded expected JSON")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.validation_expected_json = None

        # 3. Actual Output File
        st.markdown("#### 3. Actual Output JSON")
        actual_source = st.radio(
            "Actual source:",
            ["Use Previous Results", "Upload Custom"],
            key="actual_source_radio"
        )

        if actual_source == "Use Previous Results":
            try:
                with open('twitter/company_analysis_20251006_163239.json', 'r') as f:
                    st.session_state.validation_actual_json = json.load(f)
                st.success(
                    "✅ Loaded actual results from twitter/company_analysis_20251006_163239.json")
            except FileNotFoundError:
                st.warning(
                    "⚠️ Actual results file not found, trying previous results...")
                if st.session_state.batch_results:
                    actual_data = {
                        "generated_at": datetime.now().isoformat(),
                        "total_companies": len(st.session_state.batch_results),
                        "results": st.session_state.batch_results
                    }
                    st.session_state.validation_actual_json = actual_data
                    st.success(
                        f"✅ Loaded {len(st.session_state.batch_results)} actual results from previous analysis")
                else:
                    st.warning("⚠️ No previous results available")
                    st.session_state.validation_actual_json = None
        else:
            uploaded_actual = st.file_uploader("Upload Actual JSON", type=[
                                               'json'], key="actual_json_upload")
            if uploaded_actual:
                try:
                    st.session_state.validation_actual_json = json.load(
                        uploaded_actual)
                    st.success(f"✅ Loaded actual JSON")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.validation_actual_json = None

    # Center Panel - Validation Prompt
    with col2:
        st.markdown("### Validation Prompt")

        default_validation_prompt = """You are a data validation expert. I need you to analyze and compare the following three JSON files:

1. **INPUT DATA**: The original company list that was processed
2. **EXPECTED OUTPUT**: The expected results format and structure  
3. **ACTUAL OUTPUT**: The actual results generated

Please analyze these files and provide your assessment:

**INPUT DATA:**
{input_json}

**EXPECTED OUTPUT:**
{expected_json}

**ACTUAL OUTPUT:**
{actual_json}

Please provide your analysis covering:
1. **Data Completeness**: Are all input companies processed?
2. **Format Compliance**: Does the actual output match the expected format?
3. **Data Quality**: Are the results accurate and well-structured?
4. **Missing Elements**: What's missing or incorrect?
5. **Overall Assessment**: Is the result appropriate and usable?

Format your response as structured JSON:
{{
  "data_completeness": "score/assessment",
  "format_compliance": "score/assessment", 
  "data_quality": "score/assessment",
  "missing_elements": ["list", "of", "issues"],
  "overall_assessment": "final verdict",
  "recommendations": ["suggestion1", "suggestion2"]
}}"""

        validation_prompt = st.text_area(
            "Validation Prompt",
            value=default_validation_prompt,
            height=400,
            key="validation_prompt_input"
        )

        # Validation Run Button
        if st.button("🔍 Run Validation", key="validation_run_btn"):
            if not st.session_state.openai_api_key:
                st.error("Please configure your OpenAI API key in Settings tab")
            elif not all([st.session_state.validation_input_json,
                         st.session_state.validation_expected_json,
                         st.session_state.validation_actual_json]):
                st.error(
                    "Please load all three JSON files before running validation")
            else:
                with st.spinner("Running validation analysis..."):
                    try:
                        # Format the prompt with actual JSON data
                        formatted_prompt = validation_prompt.format(
                            input_json=json.dumps(
                                st.session_state.validation_input_json, indent=2),
                            expected_json=json.dumps(
                                st.session_state.validation_expected_json, indent=2),
                            actual_json=json.dumps(
                                st.session_state.validation_actual_json, indent=2)
                        )

                        # Get configuration settings
                        model = st.session_state.config_settings.get(
                            'OPENAI_MODEL', 'gpt-3.5-turbo')
                        max_tokens = int(
                            st.session_state.config_settings.get('MAX_TOKENS', 1000))
                        temperature = float(
                            st.session_state.config_settings.get('TEMPERATURE', 0.7))

                        # Use OpenAI client
                        if st.session_state.openai_client:
                            client = st.session_state.openai_client
                        else:
                            client = OpenAI(
                                api_key=st.session_state.openai_api_key)

                        # Call OpenAI API
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "You are a data validation expert specializing in JSON data analysis and comparison."},
                                {"role": "user", "content": formatted_prompt}
                            ],
                            max_tokens=max_tokens,
                            temperature=temperature
                        )

                        # Parse and store the validation result
                        validation_content = response.choices[0].message.content
                        try:
                            parsed_validation = json.loads(validation_content)
                            st.session_state.validation_result = parsed_validation
                        except json.JSONDecodeError:
                            st.session_state.validation_result = validation_content

                        st.success("✅ Validation analysis completed!")

                    except Exception as e:
                        st.error(f"Error running validation: {str(e)}")

    # Right Panel - Validation Results
    with col3:
        st.markdown("### Validation Results")

        if hasattr(st.session_state, 'validation_result') and st.session_state.validation_result:
            st.success("📊 Validation Analysis Available")

            # Display validation results
            display_analysis_result(
                st.session_state.validation_result, "Validation Analysis")

            # Show individual file summaries
            with st.expander("📋 File Summaries", expanded=False):
                if st.session_state.validation_input_json:
                    st.markdown("**Input Data:**")
                    st.json({
                        "type": "input_companies",
                        "count": len(st.session_state.validation_input_json) if isinstance(st.session_state.validation_input_json, list) else "N/A"
                    })

                if st.session_state.validation_expected_json:
                    st.markdown("**Expected Output:**")
                    if isinstance(st.session_state.validation_expected_json, dict) and 'total_companies' in st.session_state.validation_expected_json:
                        st.json({
                            "type": "expected_results",
                            "total_companies": st.session_state.validation_expected_json.get('total_companies', 0)
                        })

                if st.session_state.validation_actual_json:
                    st.markdown("**Actual Output:**")
                    if isinstance(st.session_state.validation_actual_json, dict) and 'total_companies' in st.session_state.validation_actual_json:
                        st.json({
                            "type": "actual_results",
                            "total_companies": st.session_state.validation_actual_json.get('total_companies', 0)
                        })

            # Download validation results
            if isinstance(st.session_state.validation_result, dict):
                validation_download = {
                    "validation_timestamp": datetime.now().isoformat(),
                    "input_summary": {
                        "type": "input_companies",
                        "count": len(st.session_state.validation_input_json) if isinstance(st.session_state.validation_input_json, list) else "N/A"
                    },
                    "expected_summary": {
                        "type": "expected_results",
                        "total_companies": st.session_state.validation_expected_json.get('total_companies', 0) if isinstance(st.session_state.validation_expected_json, dict) else "N/A"
                    },
                    "actual_summary": {
                        "type": "actual_results",
                        "total_companies": st.session_state.validation_actual_json.get('total_companies', 0) if isinstance(st.session_state.validation_actual_json, dict) else "N/A"
                    },
                    "validation_analysis": st.session_state.validation_result
                }

                st.download_button(
                    label="📥 Download Validation Report",
                    data=json.dumps(validation_download, indent=2),
                    file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        else:
            st.info("🔍 Run validation analysis to see results here")

            # Show status of loaded files
            st.markdown("#### File Status:")
            files_status = []

            if st.session_state.validation_input_json:
                files_status.append("✅ Input JSON loaded")
            else:
                files_status.append("❌ Input JSON missing")

            if st.session_state.validation_expected_json:
                files_status.append("✅ Expected JSON loaded")
            else:
                files_status.append("❌ Expected JSON missing")

            if st.session_state.validation_actual_json:
                files_status.append("✅ Actual JSON loaded")
            else:
                files_status.append("❌ Actual JSON missing")

            for status in files_status:
                st.text(status)

# Settings Tab - Configuration Management
with settings_tab:
    st.markdown("## ⚙️ Configuration Settings")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🔧 Environment Variables")
        st.markdown("Configure individual environment variables:")

        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.config_settings.get('OPENAI_API_KEY', ''),
            help="Your OpenAI API key for generating company analysis"
        )

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
                'OPENAI_API_KEY': openai_key,
                'OPENAI_MODEL': model_name,
                'MAX_TOKENS': str(max_tokens),
                'TEMPERATURE': str(temperature)
            }
            save_config_to_session(config)
            st.success("✅ Individual settings saved!")

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
                            if 'KEY' in key.upper() or 'SECRET' in key.upper():
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

            if st.button("🗑️ Clear Configuration", key="clear_config"):
                st.session_state.config_settings = {}
                st.session_state.env_file_content = ""
                st.session_state.openai_api_key = ""
                st.session_state.openai_client = None
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

# Footer
st.markdown("---")
st.markdown(
    "Built with Streamlit | OpenAI Integration | Configuration Management")
