#!/usr/bin/env python3
"""
Test script to verify OpenAI integration for Cover Letter Assistant
Run this script to check if your OpenAI setup is working correctly.
"""

import os
import sys
from pathlib import Path

def test_openai_imports():
    """Test if OpenAI-related packages can be imported."""
    print("🧪 Testing OpenAI imports...")
    try:
        import openai
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        print("✅ OpenAI packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run: pip install langchain-openai openai")
        return False

def test_api_key_setup():
    """Test if OpenAI API key is configured."""
    print("\n🔑 Testing API key configuration...")
    
    api_key = None
    
    # Check environment variable
    if 'OPENAI_API_KEY' in os.environ:
        api_key = os.environ['OPENAI_API_KEY']
        print("✅ Found API key in environment variable")
    
    # Check secrets.toml file
    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.exists():
        try:
            with open(secrets_file, 'r') as f:
                content = f.read()
                if 'api_key' in content and 'openai' in content:
                    print("✅ Found API key configuration in secrets.toml")
                    if not api_key:
                        print("💡 API key found in secrets.toml (will be used in Streamlit)")
        except Exception as e:
            print(f"⚠️ Could not read secrets.toml: {e}")
    
    if not api_key and not secrets_file.exists():
        print("❌ No API key found")
        print("💡 Set OPENAI_API_KEY environment variable or configure secrets.toml")
        return False
    
    return True

def test_openai_connection():
    """Test actual connection to OpenAI API."""
    print("\n🌐 Testing OpenAI API connection...")
    
    if 'OPENAI_API_KEY' not in os.environ:
        print("⚠️ Skipping API test - no environment variable set")
        print("💡 For full testing, set OPENAI_API_KEY environment variable")
        return True
    
    try:
        import openai
        from langchain_openai import ChatOpenAI
        
        # Initialize client
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=50)
        
        # Test with a simple prompt
        response = llm.invoke("Say 'Hello from OpenAI!' in exactly those words.")
        print(f"✅ API connection successful!")
        print(f"📝 Test response: {response.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        if "authentication" in str(e).lower():
            print("💡 Check your API key is valid")
        elif "rate limit" in str(e).lower():
            print("💡 Rate limit reached - try again later")
        elif "quota" in str(e).lower():
            print("💡 Usage quota exceeded - check billing")
        return False

def test_embedding_model():
    """Test OpenAI embedding model."""
    print("\n🔗 Testing embedding model...")
    
    if 'OPENAI_API_KEY' not in os.environ:
        print("⚠️ Skipping embedding test - no environment variable set")
        return True
    
    try:
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        test_text = "This is a test document for embedding."
        
        result = embeddings.embed_query(test_text)
        print(f"✅ Embeddings working! Vector dimension: {len(result)}")
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 OpenAI Integration Test for Cover Letter Assistant")
    print("=" * 55)
    
    tests = [
        test_openai_imports,
        test_api_key_setup,
        test_openai_connection,
        test_embedding_model
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 55)
    print("📊 Test Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed! Your OpenAI setup is ready.")
        print("\n🚀 Next steps:")
        print("1. Deploy to Streamlit Community Cloud")
        print("2. Add your API key to Streamlit secrets")
        print("3. Configure invited users")
        print("4. Test the full application")
    else:
        print(f"⚠️ {passed}/{total} tests passed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()