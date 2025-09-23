"""
Quick test script to verify the AI Cover Letter Assistant setup.
Run this to check if everything is configured correctly.
"""

import sys
import os
import json
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists and print status."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_python_package(package_name):
    """Check if a Python package is installed."""
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"✅ Python package: {package_name}")
        return True
    else:
        print(f"❌ Python package: {package_name} - NOT INSTALLED")
        return False

def check_json_valid(filepath):
    """Check if JSON file is valid."""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print(f"✅ Valid JSON: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Invalid JSON: {filepath} - {e}")
        return False

def main():
    print("🎯 AI Cover Letter Assistant - Setup Verification")
    print("=" * 50)
    
    all_good = True
    
    # Check essential files
    print("\n📁 Checking essential files:")
    essential_files = [
        ("app.py", "Main application"),
        ("security_utils.py", "Security utilities"),
        ("requirements.txt", "Dependencies file"),
        (".streamlit/config.toml", "Streamlit configuration"),
        ("invited_users.json", "User configuration"),
        (".gitignore", "Git ignore file"),
        ("README.md", "Documentation")
    ]
    
    for filepath, description in essential_files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    # Check JSON configuration files
    print("\n📝 Checking JSON configuration:")
    json_files = ["invited_users.json"]
    for filepath in json_files:
        if os.path.exists(filepath):
            if not check_json_valid(filepath):
                all_good = False
    
    # Check Python dependencies
    print("\n📦 Checking Python dependencies:")
    required_packages = [
        "streamlit",
        "langchain",
        "langchain_community", 
        "langchain_ollama",
        "chromadb",
        "reportlab",
        "llm_guard"
    ]
    
    missing_packages = []
    for package in required_packages:
        if not check_python_package(package):
            missing_packages.append(package)
            all_good = False
    
    # Check Ollama (optional for local development)
    print("\n🤖 Checking Ollama:")
    if os.system("ollama --version > /dev/null 2>&1") == 0:
        print("✅ Ollama is installed")
        
        # Check if models are available
        if os.system("ollama list | grep qwen3 > /dev/null 2>&1") == 0:
            print("✅ qwen3:8b model is available")
        else:
            print("⚠️ qwen3:8b model not found. Run: ollama pull qwen3:8b")
            
        if os.system("ollama list | grep nomic-embed-text > /dev/null 2>&1") == 0:
            print("✅ nomic-embed-text model is available")
        else:
            print("⚠️ nomic-embed-text model not found. Run: ollama pull nomic-embed-text")
    else:
        print("⚠️ Ollama not found. Install from: https://ollama.ai")
    
    # Check directories
    print("\n📂 Checking data directories:")
    data_dirs = ["chroma_db_multiuser", "uploads", "user_preferences"]
    for dir_name in data_dirs:
        if os.path.exists(dir_name):
            print(f"✅ Directory exists: {dir_name}")
        else:
            print(f"ℹ️ Directory will be created: {dir_name}")
    
    # Configuration check
    print("\n⚙️ Configuration check:")
    
    # Check invited users configuration
    if os.path.exists("invited_users.json"):
        try:
            with open("invited_users.json", 'r') as f:
                config = json.load(f)
                invited_users = config.get("invited_users", {})
                if invited_users:
                    print(f"✅ {len(invited_users)} invited users configured")
                    for email in list(invited_users.keys())[:3]:  # Show first 3
                        print(f"   - {email}")
                    if len(invited_users) > 3:
                        print(f"   - ... and {len(invited_users) - 3} more")
                else:
                    print("⚠️ No invited users configured in invited_users.json")
        except Exception as e:
            print(f"❌ Error reading invited_users.json: {e}")
            all_good = False
    
    # Check secrets file
    if os.path.exists(".streamlit/secrets.toml"):
        print("✅ Secrets file exists (.streamlit/secrets.toml)")
        print("ℹ️ Make sure to configure your secrets for production")
    else:
        print("⚠️ Secrets file not found. Copy from template for local development.")
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All checks passed! Your setup looks good.")
        print("\n🚀 Ready to start:")
        print("   streamlit run app.py")
    else:
        print("❌ Some issues found. Please fix them before running the app.")
        
        if missing_packages:
            print(f"\n📦 Install missing packages:")
            print(f"   pip install {' '.join(missing_packages)}")
    
    print("\n📖 For deployment instructions, see DEPLOYMENT.md")

if __name__ == "__main__":
    main()