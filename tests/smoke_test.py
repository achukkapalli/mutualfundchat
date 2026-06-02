import os
import sys
from dotenv import load_dotenv

def test_imports():
    print("Checking library imports...")
    try:
        import bs4
        print("  [OK] beautifulsoup4 imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import beautifulsoup4: {e}")
        return False

    try:
        import requests
        print("  [OK] requests imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import requests: {e}")
        return False

    try:
        import playwright
        print("  [OK] playwright imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import playwright: {e}")
        return False

    try:
        import chromadb
        print("  [OK] chromadb imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import chromadb: {e}")
        return False

    try:
        import groq
        print("  [OK] groq imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import groq: {e}")
        return False

    try:
        import streamlit
        print("  [OK] streamlit imported successfully")
    except ImportError as e:
        print(f"  [FAIL] Failed to import streamlit: {e}")
        return False

    return True

def test_groq_api():
    print("\nVerifying environment and Groq API connectivity...")
    # Load dotenv from workspace root
    load_dotenv()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("  [FAIL] GROQ_API_KEY environment variable not found in .env file.")
        return False
        
    print(f"  [OK] GROQ_API_KEY found (length: {len(api_key)})")
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # Test with a simple prompt
        print("  Sending test request to Groq API (llama-3.1-8b-instant)...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Groq API test passed successfully!' in one sentence.",
                }
            ],
            model="llama-3.1-8b-instant",
        )
        response = chat_completion.choices[0].message.content
        print(f"  Groq Response: {response.strip()}")
        print("  [OK] Groq API connection and generation successful!")
        return True
    except Exception as e:
        print(f"  [FAIL] Groq API call failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Mutual Funds Chatbot: Phase 0 Smoke Test ===")
    imports_ok = test_imports()
    if not imports_ok:
        print("\n[FAIL] Smoke test failed: Some imports are missing. Run pip install.")
        sys.exit(1)
        
    api_ok = test_groq_api()
    if not api_ok:
        print("\n[FAIL] Smoke test failed: API verification failed.")
        sys.exit(1)
        
    print("\n[OK] All Phase 0 checks passed successfully!")
    sys.exit(0)
