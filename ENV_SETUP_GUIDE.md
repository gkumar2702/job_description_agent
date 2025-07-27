# Environment Setup Guide for JD Agent

This guide will help you set up your `.env` file with all the necessary API keys and configuration settings.

## 📋 Required API Keys

### 1. OpenAI API Key (REQUIRED)

**Purpose**: Generate interview questions using GPT-4o

**Steps to get OpenAI API Key**:
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Give it a name (e.g., "JD Agent")
5. Copy the generated key (starts with `sk-`)
6. **Important**: You get $5 free credit when you sign up

**Cost**: ~$0.01-0.05 per job description processed

---

### 2. SerpAPI Key (OPTIONAL)

**Purpose**: Limited web search for finding interview questions (free tier available)

**Steps to get SerpAPI Key**:
1. Go to [SerpAPI](https://serpapi.com/dashboard)
2. Sign up for a free account
3. You get 100 free searches per month
4. Copy your API key from the dashboard

**Cost**: Free tier includes 100 searches/month

---

### 3. Gmail API (OPTIONAL)

**Purpose**: Automatically collect job description emails from Gmail

**Steps to set up Gmail API**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file
5. Save the downloaded file as `credentials.json` in the project root directory
6. Run the authentication setup script:
   ```bash
   python setup_gmail_auth.py
   ```

**Alternative Manual Setup**:
If you prefer to set up manually, extract the credentials from the JSON file and add them to your `.env` file.

**Cost**: Free for personal use

---

## 🔧 Setting Up Your .env File

1. **Copy the template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** with your API keys:
   ```bash
   nano .env
   # or use any text editor
   ```

3. **Fill in your API keys**:
   ```env
   # Required
   OPENAI_API_KEY=sk-your-openai-key-here
   
   # Optional - for limited web search
   SERPAPI_KEY=your-serpapi-key-here
   
   # Optional - for Gmail integration
   GMAIL_CLIENT_ID=your-gmail-client-id
   GMAIL_CLIENT_SECRET=your-gmail-client-secret
   GMAIL_REFRESH_TOKEN=your-gmail-refresh-token
   ```

## 🚀 Quick Start (Minimal Setup)

For the **minimum setup** to test the system, you only need:

```env
# Required for question generation
OPENAI_API_KEY=sk-your-openai-key-here

# Optional - for web search (free tier available)
SERPAPI_KEY=your-serpapi-key-here
```

## 💰 Cost Estimation

**Per job description processed**:
- **OpenAI API**: $0.01-0.05 (depending on content length)
- **SerpAPI**: Free (within 100 searches/month limit)
- **Gmail API**: Free for personal use

**Total cost**: ~$0.01-0.05 per job description

## 🔒 Security Notes

1. **Never commit your .env file** to version control
2. **Keep your API keys secure** and don't share them
3. **Use environment variables** in production
4. **Monitor your API usage** to avoid unexpected charges

## 🧪 Testing Your Setup

After setting up your `.env` file, test it:

```bash
python example.py
```

This will validate your configuration and run a test job description.

## 🆘 Troubleshooting

### Common Issues:

1. **"OpenAI API key not configured"**
   - Make sure your OpenAI API key is correct
   - Check that you have sufficient credits

2. **"SerpAPI key not configured"**
   - This is optional - the system will use free scraping methods
   - If you want to use SerpAPI, get a free key from their website

3. **"Gmail API not configured"**
   - This is optional - you can manually input job descriptions
   - Follow the Gmail API setup guide above if needed

### Getting Help:

- Check the logs for detailed error messages
- Ensure all API keys are correctly formatted
- Verify you have sufficient credits/quotas

## 📞 Support

If you encounter issues:
1. Check the error logs
2. Verify your API keys are correct
3. Ensure you have sufficient credits
4. Try running with just the OpenAI API key first 