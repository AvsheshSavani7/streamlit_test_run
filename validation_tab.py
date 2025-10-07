import streamlit as st
import json
from datetime import datetime
from utils import display_analysis_result


def render_validation_tab():
    """Render the Result Validation tab"""

    # Create three columns
    col1, col2, col3 = st.columns([1, 2, 1])

    # Left Panel - JSON File Inputs
    with col1:
        st.markdown("### JSON File Inputs")

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
            "Actual Output Source:",
            ["Use Current Batch Results", "Upload Custom JSON"],
            key="actual_source_radio"
        )

        if actual_source == "Use Current Batch Results":
            # First check if we have current batch results from Company Analysis tab
            if st.session_state.batch_results:
                actual_data = {
                    "generated_at": datetime.now().isoformat(),
                    "total_companies": len(st.session_state.batch_results),
                    "results": st.session_state.batch_results
                }
                st.session_state.validation_actual_json = actual_data
                st.success(
                    f"✅ Loaded {len(st.session_state.batch_results)} actual results from current Company Analysis batch run")
            else:
                # Fallback to static file if no batch results available
                try:
                    with open('twitter/company_analysis_20251006_163239.json', 'r') as f:
                        st.session_state.validation_actual_json = json.load(f)
                    st.success(
                        "✅ Loaded actual results from twitter/company_analysis_20251006_163239.json (fallback file)")
                except FileNotFoundError:
                    st.warning(
                        "⚠️ No batch results from Company Analysis and no fallback file found")
                    st.info(
                        "💡 Please run a batch analysis in the Company Analysis tab first, or upload a custom JSON file")
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

        default_validation_prompt = """You are a data validation expert. Validate the correctness of the system-generated output.  

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
