# Complete API Keys Setup Guide

This comprehensive guide will walk you through setting up **every single** API key and configuration value required for your `.env` file.

## Table of Contents

1. [GEMINI_API_KEY](#1-gemini_api_key-google-gemini-ai)
2. [Gmail API Keys](#2-gmail-api-keys)
3. [GROQ_API_KEY](#3-groq_api_key-groq-llm)
4. [RERANKER_API_KEY](#4-reranker_api_key-cohere)
5. [Configuration Paths](#5-configuration-paths-not-api-keys)
6. [Complete .env Template](#complete-env-template)
7. [Verification Script](#verification-script)

---

## 1. GEMINI_API_KEY (Google Gemini AI)

The Gemini API key is used for AI-powered case analysis, stage detection, and document generation in the frontend.

### Step 1: Get Your API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"** or **"Create API Key"**
4. If prompted, create a new Google Cloud project or select an existing one
5. Your API key will be displayed (starts with `AIza...`)

### Step 2: Copy the Key

- Click the **copy icon** next to your API key
- **Important**: Copy it immediately - you won't be able to see it again!

### Step 3: Add to .env

```env
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```

### Step 4: Verify

The key should:
- Start with `AIza`
- Be about 39 characters long
- Have no spaces or line breaks

### Troubleshooting

- **"API key not found"**: Make sure you copied the entire key without spaces
- **"Quota exceeded"**: Check your usage limits in [Google Cloud Console](https://console.cloud.google.com/)
- **"Invalid API key"**: Regenerate a new key if needed

---

## 2. Gmail API Keys

The Gmail API requires OAuth 2.0 credentials (Client ID, Client Secret) and a Refresh Token to collect form submissions from emails.

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter a project name (e.g., "Ilan Legal App")
5. Click **"Create"**
6. Wait for the project to be created, then select it

### Step 2: Enable Gmail API

1. In your Google Cloud project, go to **"APIs & Services"** > **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"**
4. Click **"Enable"**
5. Wait for the API to be enabled

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace account)
3. Click **"Create"**
4. Fill in the required fields:
   - **App name**: "Ilan Legal App" (or your preferred name)
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **"Save and Continue"**
6. **Scopes** (Step 2):
   - Click **"Add or Remove Scopes"**
   - Search for and add:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
   - Click **"Update"** then **"Save and Continue"**
7. **Test users** (Step 3):
   - Click **"Add Users"**
   - Add your Gmail address (the one you want to use for collecting emails)
   - Click **"Add"**
   - Click **"Save and Continue"**
8. **Summary** (Step 4):
   - Review your settings
   - Click **"Back to Dashboard"**

### Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**
3. Select **"Desktop app"** as the application type
   - **Name**: "Ilan Legal App Client" (or your preferred name)
4. Click **"Create"**
5. **IMPORTANT**: A popup will appear with your credentials
   - **Copy the Client ID** immediately
   - **Copy the Client Secret** immediately
   - Click **"OK"**

### Step 5: Download Credentials File

1. In the Credentials page, find your newly created OAuth client
2. Click the **download icon** (⬇️) on the right
3. Save the file as `credentials.json` in your `backend/` directory
   - Full path: `/Users/artemprokhorov/Desktop/Jobs : Work/Nanny AI/Ilan_Legal_App/backend/credentials.json`

### Step 6: Get the Refresh Token

You need to run an authentication flow to get the refresh token. Use the provided script:

1. Save this script as `get_gmail_token.py` in your project root:

```python
"""Script to get Gmail API refresh token."""
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

def main():
    credentials_path = 'backend/credentials.json'
    
    if not os.path.exists(credentials_path):
        print("ERROR: credentials.json not found!")
        print(f"Please download it from Google Cloud Console and save it to {credentials_path}")
        return
    
    print("Starting OAuth flow...")
    print("A browser window will open. Please sign in and authorize the app.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Extract values
    refresh_token = creds.refresh_token
    
    # Read credentials.json to get client ID and secret
    with open(credentials_path, 'r') as f:
        creds_data = json.load(f)
        client_data = creds_data.get('installed') or creds_data.get('web')
        client_id = client_data['client_id']
        client_secret = client_data['client_secret']
    
    print("\n" + "="*60)
    print("✅ SUCCESS! Add these to your .env file:")
    print("="*60)
    print(f"GMAIL_CLIENT_ID={client_id}")
    print(f"GMAIL_CLIENT_SECRET={client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={refresh_token}")
    print("="*60)
    print("\n⚠️  Keep these credentials secure and never commit them to git!")

if __name__ == '__main__':
    main()
```

2. Install required package (if not already installed):
   ```bash
   pip install google-auth-oauthlib
   ```

3. Run the script:
   ```bash
   python get_gmail_token.py
   ```

4. A browser window will open:
   - Sign in with the Gmail account you want to use
   - Click **"Allow"** to grant permissions
   - The script will display your credentials

### Step 7: Add to .env

Copy the three values from the script output:

```env
GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REFRESH_TOKEN=your_refresh_token_here
```

### Troubleshooting

- **"Access blocked: This app's request is invalid"**: 
  - Make sure you added your email as a test user in the OAuth consent screen
  - Wait a few minutes after adding test users
- **"Invalid credentials"**: 
  - Double-check that you copied the Client ID and Secret correctly (no extra spaces)
  - Make sure `credentials.json` is in the `backend/` directory
- **"Refresh token expired"**: 
  - Re-run the `get_gmail_token.py` script to get a new refresh token
- **"ModuleNotFoundError: No module named 'google_auth_oauthlib'"**:
  - Run: `pip install google-auth-oauthlib`

---

## 3. GROQ_API_KEY (Groq LLM)

Groq provides fast LLM inference. This is used as an alternative to local LLM or OpenAI.

### Step 1: Create a Groq Account

1. Go to [Groq Console](https://console.groq.com/)
2. Click **"Sign Up"** or **"Log In"**
3. Sign up with your email or use Google/GitHub OAuth
4. Verify your email if required

### Step 2: Get Your API Key

1. Once logged in, you'll be taken to the dashboard
2. Click on **"API Keys"** in the left sidebar (or go to https://console.groq.com/keys)
3. Click **"Create API Key"**
4. Give it a name (e.g., "Ilan Legal App")
5. Click **"Submit"**
6. **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!
   - The key starts with `gsk_`

### Step 3: Add to .env

```env
GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 4: Verify

The key should:
- Start with `gsk_`
- Be about 50+ characters long
- Have no spaces

### Step 5: Test the Key (Optional)

You can test if your key works:

```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY"
```

If successful, you'll see a JSON response with available models.

### Troubleshooting

- **"Invalid API key"**: Make sure you copied the entire key starting with `gsk_`
- **"Rate limit exceeded"**: Check your usage limits in the Groq dashboard
- **"Authentication failed"**: Verify the key is correct and hasn't been revoked

---

## 4. RERANKER_API_KEY (Cohere)

Cohere provides reranking services to improve search result relevance. This is used in the RAG pipeline.

### Step 1: Create a Cohere Account

1. Go to [Cohere Dashboard](https://dashboard.cohere.com/)
2. Click **"Sign Up"** or **"Log In"**
3. Sign up with your email or use Google/GitHub OAuth
4. Verify your email if required

### Step 2: Get Your API Key

1. Once logged in, you'll see the dashboard
2. Click on **"API Keys"** in the left sidebar (or go to https://dashboard.cohere.com/api-keys)
3. You'll see your default API key, or click **"Create API Key"**
4. If creating new:
   - Give it a name (e.g., "Ilan Legal App Reranker")
   - Click **"Create"**
5. **Copy the API key** - it starts with a long string of characters

### Step 3: Add to .env

```env
RERANKER_API_KEY=your_cohere_api_key_here
```

**Note**: The code uses `RERANKER_API_KEY` from the config. Make sure your `backend/services/retrieval_service.py` uses `settings.reranker_api_key` (which it should).

### Step 4: Verify

The key should:
- Be a long string (typically 40+ characters)
- Have no spaces
- Be visible in your Cohere dashboard

### Step 5: Test the Key (Optional)

You can test if your key works:

```bash
curl -X POST https://api.cohere.ai/v1/rerank \
  -H "Authorization: Bearer YOUR_RERANKER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rerank-english-v3.0",
    "query": "test",
    "documents": ["test document"]
  }'
```

If successful, you'll see a JSON response with reranked results.

### Troubleshooting

- **"Invalid API key"**: Make sure you copied the entire key correctly
- **"Insufficient credits"**: Check your Cohere account balance
- **Reranking fails silently**: The code will automatically fall back to distance-based ranking if Cohere fails

---

## 5. Configuration Paths (Not API Keys)

These are file paths, not API keys. They're already set correctly, but here's what they mean:

### DATABASE_PATH

```env
DATABASE_PATH=./data/database.db
```

- **What it is**: Path to the SQLite database file
- **Default**: `./data/database.db` (relative to project root)
- **Action needed**: None - this is correct
- **Note**: The `data/` directory will be created automatically

### CHROMA_DB_PATH

```env
CHROMA_DB_PATH=./data/chroma_db
```

- **What it is**: Path to the ChromaDB vector database directory
- **Default**: `./data/chroma_db` (relative to project root)
- **Action needed**: None - this is correct
- **Note**: The directory will be created automatically when ChromaDB is first used

### EMBEDDING_MODEL

```env
EMBEDDING_MODEL=nomic-embed-text-v1.5
```

- **What it is**: Name of the embedding model to use
- **Default**: `nomic-embed-text-v1.5`
- **Action needed**: None - this is correct
- **Note**: This is a model identifier, not an API key. The model will be downloaded automatically on first use.

---

## Complete .env Template

Here's a complete `.env` file template with all required values:

```env
# Google Gemini AI (for frontend AI features)
GEMINI_API_KEY=AIzaSyYourGeminiKeyHere

# Gmail API (for email collection)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Database (file path - no changes needed)
DATABASE_PATH=./data/database.db

# ChromaDB (directory path - no changes needed)
CHROMA_DB_PATH=./data/chroma_db

# Groq LLM (for backend LLM inference)
GROQ_API_KEY=gsk_your_groq_key_here

# Embedding Model (model name - no changes needed)
EMBEDDING_MODEL=nomic-embed-text-v1.5

# Cohere Reranker (for RAG pipeline)
RERANKER_API_KEY=your_cohere_key_here
```

---

## Verification Script

Save this as `verify_env.py` in your project root to check if all keys are set:

```python
"""Verify that all required environment variables are set."""
import os
from dotenv import load_dotenv

load_dotenv()

required_keys = {
    'GEMINI_API_KEY': 'Google Gemini AI',
    'GMAIL_CLIENT_ID': 'Gmail API Client ID',
    'GMAIL_CLIENT_SECRET': 'Gmail API Client Secret',
    'GMAIL_REFRESH_TOKEN': 'Gmail API Refresh Token',
    'GROQ_API_KEY': 'Groq LLM',
    'RERANKER_API_KEY': 'Cohere Reranker',
}

optional_keys = {
    'DATABASE_PATH': 'Database path (has default)',
    'CHROMA_DB_PATH': 'ChromaDB path (has default)',
    'EMBEDDING_MODEL': 'Embedding model name (has default)',
}

print("="*60)
print("Environment Variables Verification")
print("="*60)

all_good = True

print("\n📋 Required Keys:")
for key, description in required_keys.items():
    value = os.getenv(key)
    if value:
        # Show first/last few chars for security
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        print(f"  ✅ {key:25} {description:30} ({masked})")
    else:
        print(f"  ❌ {key:25} {description:30} (MISSING)")
        all_good = False

print("\n📋 Optional Keys (with defaults):")
for key, description in optional_keys.items():
    value = os.getenv(key)
    if value:
        print(f"  ✅ {key:25} {description:30} ({value})")
    else:
        print(f"  ⚠️  {key:25} {description:30} (using default)")

print("\n" + "="*60)
if all_good:
    print("✅ All required API keys are set!")
else:
    print("❌ Some required keys are missing. Please set them in your .env file.")
print("="*60)
```

Run it with:
```bash
pip install python-dotenv
python verify_env.py
```

---

## Setup Checklist

Use this checklist to track your progress:

### Required API Keys
- [ ] **GEMINI_API_KEY** - Obtained from Google AI Studio
- [ ] **GMAIL_CLIENT_ID** - Obtained from Google Cloud Console
- [ ] **GMAIL_CLIENT_SECRET** - Obtained from Google Cloud Console
- [ ] **GMAIL_REFRESH_TOKEN** - Obtained via authentication flow
- [ ] **GROQ_API_KEY** - Obtained from Groq Console
- [ ] **RERANKER_API_KEY** - Obtained from Cohere Dashboard

### Configuration (Already Set)
- [x] **DATABASE_PATH** - Default value is correct
- [x] **CHROMA_DB_PATH** - Default value is correct
- [x] **EMBEDDING_MODEL** - Default value is correct

### Verification
- [ ] Ran `verify_env.py` script
- [ ] All required keys show as ✅
- [ ] Tested backend server startup
- [ ] Tested frontend connection to backend

---

## Quick Reference: Where to Get Each Key

| Key | Where to Get It | Link |
|-----|----------------|------|
| GEMINI_API_KEY | Google AI Studio | https://aistudio.google.com/app/apikey |
| GMAIL_CLIENT_ID | Google Cloud Console | https://console.cloud.google.com/ |
| GMAIL_CLIENT_SECRET | Google Cloud Console | https://console.cloud.google.com/ |
| GMAIL_REFRESH_TOKEN | Via auth flow script | (see Step 6 above) |
| GROQ_API_KEY | Groq Console | https://console.groq.com/keys |
| RERANKER_API_KEY | Cohere Dashboard | https://dashboard.cohere.com/api-keys |

---

## Security Best Practices

1. **Never commit your `.env` file to git** - It's already in `.gitignore`
2. **Don't share API keys** - Each key is tied to your account and usage
3. **Rotate keys periodically** - Especially if you suspect they've been compromised
4. **Use different keys for development and production** - Create separate projects/accounts
5. **Monitor usage** - Check your API dashboards regularly for unexpected usage

---

## Troubleshooting Common Issues

### "ModuleNotFoundError" when running scripts
- Install missing packages: `pip install google-auth-oauthlib python-dotenv`

### "Invalid API key" errors
- Double-check you copied the entire key (no spaces, no line breaks)
- Verify the key is active in the respective dashboard
- Check if the key has expired or been revoked

### Gmail API authentication fails
- Make sure you're using the Gmail account you added as a test user
- Wait a few minutes after adding test users before trying to authenticate
- Re-run the authentication script if the refresh token expires

### Backend can't connect to APIs
- Verify all keys are in the `.env` file (not `.env.local` or other names)
- Make sure the `.env` file is in the project root directory
- Restart the backend server after adding new keys

---

## Need Help?

If you encounter issues not covered here:

1. Check the respective service's documentation:
   - [Google Gemini API Docs](https://ai.google.dev/docs)
   - [Gmail API Docs](https://developers.google.com/gmail/api)
   - [Groq API Docs](https://console.groq.com/docs)
   - [Cohere API Docs](https://docs.cohere.com/)

2. Check your backend logs for specific error messages

3. Verify your `.env` file syntax (no quotes needed, no spaces around `=`)

Good luck with your setup! 🚀
