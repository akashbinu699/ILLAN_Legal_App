import os
import google.generativeai as genai
from backend.config import settings

def test_gemini_simple():
    api_key = settings.gemini_api_key
    print(f"Key length: {len(api_key)}")
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, can you hear me?")
        print("Success!")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_simple()
