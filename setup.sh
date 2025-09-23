#!/bin/bash

# Setup script for AI Cover Letter Assistant
echo "🎯 Setting up AI Cover Letter Assistant..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama is not installed. Please install it manually:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   Or visit: https://ollama.ai"
else
    echo "✅ Ollama is installed"
    
    # Pull required models
    echo "🤖 Pulling required AI models..."
    ollama pull qwen3:8b
    ollama pull nomic-embed-text
    echo "✅ AI models ready"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p chroma_db_multiuser uploads user_preferences

# Set up configuration
echo "⚙️ Setting up configuration..."
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "📝 Please edit .streamlit/secrets.toml to add your invited users and secrets"
fi

if [ ! -f "invited_users.json" ]; then
    echo "📝 Please edit invited_users.json to configure your invited users"
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   streamlit run app.py"
echo ""
echo "👥 To start the admin dashboard:"
echo "   streamlit run admin_dashboard.py --server.port 8502"
echo ""
echo "📖 For deployment instructions, see DEPLOYMENT.md"