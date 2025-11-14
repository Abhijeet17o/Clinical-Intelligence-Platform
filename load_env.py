"""
Load environment variables from .env file
"""
import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print(f"❌ .env file not found at: {env_file}")
        print("\n📝 To create it:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your GEMINI_API_KEY")
        print("3. Get your API key from: https://aistudio.google.com/app/apikey")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
                    print(f"✓ Loaded: {key}")
    
    return True


if __name__ == "__main__":
    load_env()
    
    # Test if GEMINI_API_KEY is loaded
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print(f"\n✅ GEMINI_API_KEY is set (length: {len(api_key)} characters)")
    else:
        print("\n❌ GEMINI_API_KEY is not set")
