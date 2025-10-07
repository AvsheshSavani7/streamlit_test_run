# Deployment Guide for Render

## Files Created for Deployment

### 1. Dockerfile
- Uses Python 3.12 slim image
- Sets up proper environment variables for Streamlit
- Installs dependencies from requirements.txt
- Exposes port 8501
- Includes health check

### 2. .dockerignore
- Excludes unnecessary files from Docker build
- Reduces image size and build time
- Protects sensitive files (.env, etc.)

### 3. render.yaml
- Render deployment configuration
- Uses free plan
- Sets up proper environment variables

## Deployment Steps on Render

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub
2. Connect your GitHub repo to Render
3. Render will automatically detect the render.yaml file
4. Deploy with default settings

### Option 2: Manual Configuration
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: streamlit-company-analysis
   - **Environment**: Docker
   - **Dockerfile Path**: ./Dockerfile
   - **Docker Context**: .
   - **Plan**: Free
   - **Region**: Oregon (or your preferred region)

### Environment Variables to Set in Render Dashboard

#### Required for Production:
```
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=1000
TEMPERATURE=0.7
```

#### Streamlit Configuration (Optional - already set in Dockerfile):
```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## Important Notes

### Security
- ✅ Never commit .env files to Git
- ✅ Use Render's environment variables for secrets
- ✅ The app uses Streamlit secrets for cloud deployment

### Free Plan Limitations
- ⚠️ Service sleeps after 15 minutes of inactivity
- ⚠️ Limited to 512MB RAM
- ⚠️ Build time limited to 90 minutes

### Testing Locally (if Docker is installed)
```bash
# Build the image
docker build -t streamlit-app .

# Run the container
docker run -p 8501:8501 streamlit-app
```

## Troubleshooting

### Common Issues:
1. **Build Fails**: Check requirements.txt syntax
2. **App Won't Start**: Verify environment variables are set
3. **API Errors**: Ensure OpenAI API key is configured
4. **Port Issues**: Make sure port 8501 is exposed

### Logs:
- Check Render dashboard logs for errors
- Use Render's built-in logging system

## Post-Deployment

1. Test all functionality:
   - Company Analysis tab
   - Validation tab
   - Settings tab
2. Verify API key configuration
3. Test batch processing
4. Check file uploads/downloads
