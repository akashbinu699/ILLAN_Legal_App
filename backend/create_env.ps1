$envContent = @"
# Google Gemini AI (Required for frontend)
GEMINI_API_KEY=AIzaSyYourKeyHere

# Gmail API (Optional - for email collection)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Database Paths (Defaults - usually no changes needed)
DATABASE_PATH=./data/database.db
CHROMA_DB_PATH=./data/chroma_db

# LLM (Required for backend RAG pipeline)
GROQ_API_KEY=gsk_your_groq_key_here
# OR use OpenAI as fallback:
# OPENAI_API_KEY=sk-your_openai_key_here

# Embedding Model (Default - usually no changes needed)
EMBEDDING_MODEL=nomic-embed-text-v1.5

# Re-ranker (Optional - improves search quality)
RERANKER_API_KEY=your_cohere_key_here
"@

Set-Content -Path "c:\Users\Nannie AI\Desktop\Ilan_Legal_App\.env" -Value $envContent
Write-Host "✅ Created .env file successfully in project root."
Write-Host "⚠️  IMPORTANT: Open the .env file and paste your GEMINI_API_KEY and GROQ_API_KEY!"
