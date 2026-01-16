
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env manually to be sure
# Go up two levels to find .env
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

def test_key():
    api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"Checking API Key from: {env_path}")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment!")
        return

    print(f"Key found. Length: {len(api_key)}")
    print(f"Key prefix: {api_key[:4]}...")
    
    # Configure GenAI
    genai.configure(api_key=api_key)
    
    try:
        print("\nAttempting to list models...")
        models = list(genai.list_models())
        print("✅ SUCCESS! API Key is valid.")
        print(f"Found {len(models)} models available.")
        # Print first model name as proof
        if models:
            print(f"First model: {models[0].name}")
            
    except Exception as e:
        print("\n❌ FAILURE: API Key invalid or request failed.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    test_key()
