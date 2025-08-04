#!/bin/bash

# 🤖 AI Finance & Risk Agent - Streamlit Chat UI Launcher
# This script launches the Streamlit chat interface

echo "🚀 Starting AI Finance & Risk Agent Chat UI..."
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed or not in PATH"
    exit 1
fi

# Install required packages
echo "📦 Installing required packages..."
pip3 install -r streamlit_requirements.txt

# Check if backend is running
echo "🔍 Checking backend connection..."
curl -s http://localhost:8000/health > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Warning: Backend not detected on http://localhost:8000"
    echo "   Make sure to start your FastAPI backend first:"
    echo "   python main.py"
    echo ""
    echo "   The Streamlit UI will start anyway, but you may see connection errors."
    echo ""
fi

# Start Streamlit
echo "🎨 Launching Streamlit Chat UI..."
echo "📱 The chat interface will open in your web browser"
echo "🔗 URL: http://localhost:8501"
echo "=================================================="

streamlit run streamlit_chat_ui.py \
  --server.port 8501 \
  --server.address localhost \
  --server.headless false \
  --browser.gatherUsageStats false \
  --theme.base "light" \
  --theme.primaryColor "#007bff" \
  --theme.backgroundColor "#ffffff" \
  --theme.secondaryBackgroundColor "#f8f9fa"