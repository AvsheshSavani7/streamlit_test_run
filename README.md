# Company Analysis Tool

A Streamlit application for analyzing companies using OpenAI's API. The app allows you to analyze individual companies or process multiple companies in batch from a JSON file.

## Features

- **Tab-based Navigation**: Clean interface with multiple tabs (Tab 1 is the main functionality)
- **Single Company Analysis**: Input a company name and generate AI-powered analysis
- **Batch Processing**: Upload a JSON file with multiple companies for bulk analysis
- **Customizable Prompts**: Edit the analysis prompt to suit your needs
- **Download Results**: Export analysis results as JSON files

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. **For Single Company Analysis**:
   - Enter your OpenAI API key in the left panel
   - Enter a company name in the "input filed"
   - Optionally modify the prompt in the center panel
   - Click "Single run" to generate analysis
   - View results in the output area below

3. **For Batch Processing**:
   - Upload a JSON file containing an array of companies in the right panel
   - JSON format should be:
     ```json
     [
       {"name": "Company 1"},
       {"name": "Company 2"},
       "Company 3"
     ]
     ```
   - Click "Run btn" to process all companies
   - Download the results when processing is complete

## API Key Setup

You can configure your API keys and settings in multiple ways:

### Option 1: Settings Tab (Recommended)
1. Go to the "Settings" tab
2. Use the "Environment Variables" section to configure individual settings
3. Or paste your entire `.env` file content in the ".env File Configuration" section
4. Click "Load from .env Content" to apply the settings

### Option 2: Direct Input
Enter your OpenAI API key directly in the "OpenAI Configuration" section in the left panel of Tab 1.

### Option 3: .env File
Create a `.env` file in the project directory with your configuration:
```env
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=1000
TEMPERATURE=0.7
```

## JSON File Format

For batch processing, your JSON file should contain an array of companies. Each company can be:
- An object with a "name" property: `{"name": "Apple Inc."}`
- A simple string: `"Apple Inc."`

## Output

The application generates structured analysis including:
- Business model insights
- Market position analysis
- Key strengths identification
- Potential risks assessment
- Growth opportunities

Results are displayed in the app and can be downloaded as JSON files with timestamps.
