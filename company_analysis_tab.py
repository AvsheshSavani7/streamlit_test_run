import streamlit as st
import json
from datetime import datetime
from utils import clean_json_syntax, display_analysis_result


def render_company_analysis_tab():
    """Render the Company Analysis tab"""
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

                                # Rerun to immediately show the "View Complete Results" section
                                st.rerun()

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
