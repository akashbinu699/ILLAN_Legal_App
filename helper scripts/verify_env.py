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

