import gradio as gr
from openai import OpenAI
import json
from datetime import datetime

# Initialize OpenAI client dynamically


def get_client(api_key: str):
    return OpenAI(api_key=api_key)

# --- Helper functions ---


def run_single(company_name, api_key, prompt, model, max_tokens, temperature):
    if not company_name:
        return {"error": "Please enter a company name"}
    if not api_key:
        return {"error": "Please enter API key"}

    client = get_client(api_key)
    formatted_prompt = prompt.replace("{company_name}", company_name)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a business analyst providing detailed company analysis."},
            {"role": "user", "content": formatted_prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
        return parsed
    except:
        return {"raw_output": content}


def run_batch(file, api_key, prompt, model, max_tokens, temperature):
    if file is None:
        return {"error": "Please upload a JSON file of companies"}, None
    if not api_key:
        return {"error": "Please enter API key"}, None

    with open(file.name, "r") as f:
        data = json.load(f)

    client = get_client(api_key)
    results = []
    for company in data:
        name = company.get("name") if isinstance(
            company, dict) else str(company)
        formatted_prompt = prompt.replace("{company_name}", name)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a business analyst providing detailed company analysis."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            try:
                parsed = json.loads(content)
            except:
                parsed = {"raw_output": content}
            results.append({"company": name, "analysis": parsed})
        except Exception as e:
            results.append({"company": name, "analysis": f"Error: {str(e)}"})

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_companies": len(results),
        "results": results
    }

    # Save to file for download
    out_file = f"company_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(output_data, f, indent=2)

    return results, out_file


# --- Gradio UI ---
with gr.Blocks(theme="default") as demo:
    with gr.Tab("Company Analysis"):
        with gr.Row():
            with gr.Column(scale=1):
                company_name = gr.Textbox(
                    label="Company Name", placeholder="Enter company name")
                api_key = gr.Textbox(label="OpenAI API Key", type="password")
            with gr.Column(scale=2):
                prompt = gr.Textbox(
                    label="Prompt",
                    lines=12,
                    value="""You are a social media research expert. I need you to find the official Twitter handles for {company_name}.
Format strictly as JSON:
{
  "company_name": "{company_name}",
  "main_twitter_handle": "@company_handle"
}"""
                )
                run_btn = gr.Button("Single Run")
                single_output = gr.JSON(label="Single Run Output")
            with gr.Column(scale=1):
                file_upload = gr.File(
                    label="Upload JSON File", file_types=[".json"])
                batch_btn = gr.Button("Run Batch")
                batch_output = gr.JSON(label="Batch Results")
                download_file = gr.File(label="Download Results")

    with gr.Tab("Settings"):
        model = gr.Textbox(label="Model", value="gpt-3.5-turbo")
        max_tokens = gr.Slider(
            label="Max Tokens", minimum=100, maximum=4000, value=1000, step=100)
        temperature = gr.Slider(label="Temperature",
                                minimum=0, maximum=2, value=0.7, step=0.1)

    # Link buttons with functions
    run_btn.click(
        fn=run_single,
        inputs=[company_name, api_key, prompt, model, max_tokens, temperature],
        outputs=single_output
    )

    batch_btn.click(
        fn=run_batch,
        inputs=[file_upload, api_key, prompt, model, max_tokens, temperature],
        outputs=[batch_output, download_file]
    )

demo.launch(share=True)
