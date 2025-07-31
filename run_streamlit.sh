#!/bin/bash

# Document Intelligence Agent - Streamlit UI Launcher
echo "🚀 Starting Document Intelligence Agent UI..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install Streamlit requirements if needed
echo "📋 Checking Streamlit requirements..."
pip install streamlit>=1.28.0 plotly>=5.0.0

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Launch Streamlit app
echo "🌐 Launching Streamlit UI on http://localhost:8501"
echo "✨ Features included:"
echo "   • Professional chat interface"
echo "   • Document upload and processing"
echo "   • Chat history management"
echo "   • Real-time reasoning display"
echo "   • Memory system integration"
echo ""
echo "💡 Tip: Upload a document first, then ask questions about it!"
echo ""

streamlit run streamlit_app.py