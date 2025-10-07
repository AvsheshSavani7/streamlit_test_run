import streamlit as st
import json
from datetime import datetime
from utils import clean_json_syntax, display_analysis_result

# Validation prompt template - defined once to avoid duplication
VALIDATION_PROMPT_TEMPLATE = """You are a data validation expert. Validate the correctness of the system-generated output.  

**INPUT DATA (original companies):**  
{input_json}  

**EXPECTED OUTPUT (reference example):**  
{expected_json}  

**ACTUAL OUTPUT (to validate):**  
{actual_json}  

Ignore:
- Data completeness (not all inputs need to appear in actual)  
- Format compliance (don't check structure/schema)  
- Missing elements  

Focus only on validating the **data values** in `analysis`.  

Check the following:  
1. **Company Name Match**: Does `company` exactly equal `analysis.company_name`?  
2. **Twitter Handle Validity**: Is `main_twitter_handle` in the correct format (must start with `@`)?  
3. **Twitter Handle Accuracy**: Compare with the style/pattern in EXPECTED (e.g., `Apple Inc.` → `@Apple`, `Tesla Inc.` → `@Tesla`). Assess if the mapping is reasonable for the company in ACTUAL.  
4. **Inconsistencies**: List mismatches between `company` and `analysis.company_name`, invalid handles, or unlikely mappings.  
5. **Final Verdict**: Is the ACTUAL output data correct and usable?  

Return only structured JSON:  

{{
  "company_name_match": "score/assessment",
  "twitter_handle_validity": "score/assessment",
  "twitter_handle_accuracy": "score/assessment",
  "inconsistencies": ["list of issues"],
  "overall_assessment": "final verdict",
  "recommendations": ["suggestion1", "suggestion2"]
}}"""


def render_company_analysis_tab():
    """Render the Company Analysis tab"""
    st.subheader("Company Twitter Handle Analysis")

    # Create three columns
    col1, col2, col3 = st.columns([0.8, 2, 1.3])

    # Left Panel - Company Input
    with col1:
        company_name = st.text_input(
            "Company Name", placeholder="Enter company name", key="company_input")

        # Model Selection Dropdown
        available_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1",
            "gpt-4.1-mini",

        ]

        selected_model = st.selectbox(
            "Select Model:",
            available_models,
            index=available_models.index(st.session_state.config_settings.get(
                'OPENAI_MODEL', 'gpt-4o')) if st.session_state.config_settings.get('OPENAI_MODEL', 'gpt-4o') in available_models else 0,
            key="model_selection"
        )

        # Update the config settings when model changes
        if selected_model != st.session_state.config_settings.get('OPENAI_MODEL'):
            st.session_state.config_settings['OPENAI_MODEL'] = selected_model

    # Center Panel - Prompt and Single Run
    with col2:
        # Create tabs for different prompts
        tab1, tab2 = st.tabs(["Main Prompt", "Validation Prompt"])

        # Tab 1: Main Prompt (current functionality)
        with tab1:
            st.markdown("### Main Prompt")
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
                                from openai import OpenAI
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

                        except Exception as e:
                            st.error(f"Error generating analysis: {str(e)}")

            # Output display area
            st.markdown("### Show Output Here")
            if st.session_state.generated_output:
                display_analysis_result(
                    st.session_state.generated_output, company_name)
            else:
                st.info("Click 'Single run' to generate analysis output")

        # Tab 2: Validation Prompt (non-editable)
        with tab2:
            st.markdown("### Validation Prompt")

            validation_prompt = VALIDATION_PROMPT_TEMPLATE

            st.text_area(
                "Validation Prompt (Read-only)",
                value=validation_prompt,
                height=400,
                key="validation_prompt_display",
                disabled=True
            )

            st.markdown("---")
            st.markdown(
                "**Note:** This prompt is used in the Validation for analyzing the quality of generated results.")

    # Right Panel - JSON Upload and Batch Processing
    with col3:
        st.markdown("### Data Source")

        # Choose between default or upload
        data_source = st.radio(
            "Choose data source:",
            ["Use Default", "Upload Custom JSON"],
            key="data_source_radio",
            horizontal=True
        )

        # Initialize previous data source if not exists
        if 'data_source_radio_prev' not in st.session_state:
            st.session_state.data_source_radio_prev = data_source

        # Reset session state variables when data source changes
        if st.session_state.data_source_radio_prev != data_source:
            st.session_state.generated_output = None
            st.session_state.batch_results = None
            st.session_state.col3_validation_result = None
            st.session_state.data_source_radio_prev = data_source
            st.rerun()

        json_data = None

        st.subheader("Input Json")

        if data_source == "Use Default":

            try:
                with open('twitter/deafult_Input.json', 'r') as f:
                    json_data = json.load(f)

                # st.json(json_data)
                with st.expander("View Input Json", expanded=False):
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

            # Track file upload changes to reset session state
            current_file_name = uploaded_file.name if uploaded_file else None
            if 'input_file_prev' not in st.session_state:
                st.session_state.input_file_prev = current_file_name

            # Reset session state if file changes
            if st.session_state.input_file_prev != current_file_name:
                st.session_state.generated_output = None
                st.session_state.batch_results = None
                st.session_state.col3_validation_result = None
                st.session_state.input_file_prev = current_file_name
                st.rerun()

            if uploaded_file:
                try:
                    json_data = json.load(uploaded_file)

                    # st.json(json_data)
                    with st.expander("View Input Json", expanded=False):
                        st.json(json_data)
                except Exception as e:
                    st.error(f"❌ Error reading uploaded file: {str(e)}")
                    json_data = None

        st.subheader("Expected Json")

        expected_json_data = None

        if data_source == "Use Default":

            try:
                with open('twitter/expected_output.json', 'r') as f:
                    expected_json_data = json.load(f)

                # st.json(expected_json_data)
                with st.expander("View Expected Json", expanded=False):
                    st.json(expected_json_data)
            except FileNotFoundError:
                st.error(
                    "❌ Default sample file not found at twitter/expected_output.json")
                expected_json_data = None
            except Exception as e:
                st.error(f"❌ Error loading default file: {str(e)}")
                expected_json_data = None

        else:  # Upload Custom JSON
            uploaded_file = st.file_uploader("Upload JSON file", type=[
                                             'json'], key="expected_json_upload")

            # Track expected file upload changes to reset session state
            current_expected_file_name = uploaded_file.name if uploaded_file else None
            if 'expected_file_prev' not in st.session_state:
                st.session_state.expected_file_prev = current_expected_file_name

            # Reset session state if expected file changes
            if st.session_state.expected_file_prev != current_expected_file_name:
                st.session_state.generated_output = None
                st.session_state.batch_results = None
                st.session_state.col3_validation_result = None
                st.session_state.expected_file_prev = current_expected_file_name
                st.rerun()

            if uploaded_file:
                try:
                    expected_json_data = json.load(uploaded_file)

                    # st.json(expected_json_data)
                    with st.expander("View Expected Json", expanded=False):
                        st.json(expected_json_data)
                except Exception as e:
                    st.error(f"❌ Error reading uploaded file: {str(e)}")
                    expected_json_data = None

        if json_data and expected_json_data:
            try:
                if isinstance(json_data, list):

                    # Batch run button and download button
                    col_run, col_download = st.columns([1, 1])

                    with col_run:
                        if st.button("Bulk Run", key="batch_run_btn"):
                            if not st.session_state.openai_api_key:
                                st.error("Please enter your OpenAI API key")
                            else:
                                # Create progress bar and status text
                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                results = []
                                total_companies = len(json_data)

                                for i, company in enumerate(json_data):
                                    if isinstance(company, dict) and 'name' in company:
                                        company_name_batch = company['name']
                                    elif isinstance(company, str):
                                        company_name_batch = company
                                    else:
                                        continue

                                    # Update status text
                                    status_text.text(
                                        f"Processing {company_name_batch} ({i+1}/{total_companies})")

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
                                            from openai import OpenAI
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

                                        # Update progress bar
                                        progress_bar.progress(
                                            (i + 1) / total_companies)

                                    except Exception as e:
                                        results.append({
                                            "company": company_name_batch,
                                            "analysis": f"Error: {str(e)}",
                                            "timestamp": datetime.now().isoformat()
                                        })

                                        # Update progress bar even for errors
                                        progress_bar.progress(
                                            (i + 1) / total_companies)

                                # Clear status text when done
                                status_text.empty()
                                progress_bar.empty()

                                st.session_state.batch_results = results

                                # Format output to match expected output structure
                                # Expected format: [{"company": "...", "analysis": {...}}, ...]
                                formatted_results = []
                                for result in results:
                                    if isinstance(result.get('analysis'), dict):
                                        # Valid analysis result
                                        formatted_results.append({
                                            "company": result['company'],
                                            "analysis": result['analysis']
                                        })
                                    else:
                                        # Error case - still include but with error info
                                        formatted_results.append({
                                            "company": result['company'],
                                            "analysis": {
                                                "company_name": result['company'],
                                                "main_twitter_handle": None,
                                                "error": result['analysis']
                                            }
                                        })

                                json_output = json.dumps(
                                    formatted_results, indent=2)
                                st.session_state.output_file = json_output

                    # Download button in the second column
                    with col_download:
                        if st.session_state.output_file:
                            st.download_button(
                                label="Download Results",
                                data=st.session_state.output_file,
                                file_name=f"company_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )

                    # Generated output display - moved here so it updates after processing
                    st.markdown("### Generated output")
                    if st.session_state.batch_results:

                        # Show complete results
                        with st.expander("📊 View Complete Results", expanded=True):
                            for i, result in enumerate(st.session_state.batch_results):
                                st.markdown(f"**{result['company']}:**")
                                display_analysis_result(
                                    result['analysis'], result['company'])
                                if i < len(st.session_state.batch_results) - 1:
                                    st.markdown("---")
                    else:
                        st.info(
                            "No batch results yet - click 'Bulk Run'")

                else:
                    st.error("JSON file must contain an array of companies")

            except Exception as e:
                st.error(f"Error reading JSON file: {str(e)}")

        # Validation section - only show if there's generated output
        if st.session_state.batch_results:
            st.markdown("### Validation")

            # Run Validation button
            if st.button("🔍 Run Validation", key="col3_validation_run_btn"):
                if not st.session_state.openai_api_key:
                    st.error(
                        "Please configure your OpenAI API key in Settings tab")
                else:
                    with st.spinner("Running validation analysis..."):
                        try:
                            # Prepare validation data
                            # Input data: single company from the single run
                            input_data = {"company": company_name}

                            # Expected data: load from default expected output file
                            try:
                                with open('twitter/expected_output.json', 'r') as f:
                                    expected_data = json.load(f)
                            except FileNotFoundError:
                                st.error(
                                    "❌ Expected output file not found. Please ensure twitter/expected_output.json exists.")
                                return

                            # Actual data: current generated output
                            actual_data = {
                                "generated_at": datetime.now().isoformat(),
                                "total_companies": 1,
                                "results": [{
                                    "company": company_name,
                                    "analysis": st.session_state.generated_output,
                                    "timestamp": datetime.now().isoformat()
                                }]
                            }

                            # Validation prompt - using the template constant
                            validation_prompt = VALIDATION_PROMPT_TEMPLATE

                            # Format the prompt with actual JSON data
                            formatted_prompt = validation_prompt.format(
                                input_json=json.dumps(input_data, indent=2),
                                expected_json=json.dumps(
                                    expected_data, indent=2),
                                actual_json=json.dumps(actual_data, indent=2)
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
                                from openai import OpenAI
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
                                parsed_validation = json.loads(
                                    validation_content)
                                st.session_state.col3_validation_result = parsed_validation
                            except json.JSONDecodeError:
                                st.session_state.col3_validation_result = validation_content

                        except Exception as e:
                            st.error(f"Error running validation: {str(e)}")

            # Show validation results if available
            if hasattr(st.session_state, 'col3_validation_result') and st.session_state.col3_validation_result:
                with st.expander("📊 Validation Results", expanded=True):
                    display_analysis_result(
                        st.session_state.col3_validation_result, "Validation Analysis")

                    # Download validation results
                    if isinstance(st.session_state.col3_validation_result, dict):
                        validation_download = {
                            "validation_timestamp": datetime.now().isoformat(),
                            "company_analyzed": company_name,
                            "validation_analysis": st.session_state.col3_validation_result
                        }

                        st.download_button(
                            label="📥 Download Validation Report",
                            data=json.dumps(validation_download, indent=2),
                            file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key="col3_validation_download"
                        )
