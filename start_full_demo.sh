#!/bin/bash

# 🚀 AI Finance & Risk Agent - Full Demo Launcher
# Starts both backend and Streamlit frontend

echo "🤖 AI Finance & Risk Agent - Full Demo"
echo "======================================"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start backend
start_backend() {
    echo "🔧 Starting FastAPI Backend..."
    
    if check_port 8000; then
        echo "   ⚠️  Port 8000 already in use (backend may already be running)"
        echo "   🔗 Testing connection..."
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "   ✅ Backend is running and accessible"
            return 0
        else
            echo "   ❌ Port 8000 occupied but backend not responding"
            echo "   💡 Kill the process and restart, or use a different port"
            return 1
        fi
    else
        echo "   🚀 Starting backend on port 8000..."
        python main.py &
        BACKEND_PID=$!
        
        # Wait for backend to start
        echo "   ⏳ Waiting for backend to initialize..."
        for i in {1..30}; do
            sleep 1
            if curl -s http://localhost:8000/health > /dev/null; then
                echo "   ✅ Backend started successfully (PID: $BACKEND_PID)"
                return 0
            fi
        done
        
        echo "   ❌ Backend failed to start within 30 seconds"
        return 1
    fi
}

# Function to start Streamlit frontend
start_frontend() {
    echo ""
    echo "🎨 Starting Streamlit Chat UI..."
    
    if check_port 8501; then
        echo "   ⚠️  Port 8501 already in use"
        echo "   💡 Streamlit may already be running at http://localhost:8501"
        echo "   🔄 You can stop it and restart, or use a different port"
        return 1
    else
        echo "   📦 Installing requirements..."
        pip install -q -r streamlit_requirements.txt
        
        echo "   🚀 Starting Streamlit on port 8501..."
        echo "   🌐 Opening in browser: http://localhost:8501"
        echo ""
        echo "   📋 Quick Usage Guide:"
        echo "   1. Upload documents using the sidebar"
        echo "   2. Select documents for analysis"
        echo "   3. Ask questions in the chat interface"
        echo "   4. Watch real-time AI reasoning steps"
        echo ""
        echo "   🛑 Press Ctrl+C to stop both services"
        echo ""
        
        streamlit run streamlit_chat_ui.py \
            --server.port 8501 \
            --server.address localhost \
            --server.headless false \
            --browser.gatherUsageStats false \
            --theme.base "light" \
            --theme.primaryColor "#007bff"
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Kill backend if we started it
    if [ ! -z "$BACKEND_PID" ]; then
        echo "   🔧 Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    
    # Kill any remaining Streamlit processes
    echo "   🎨 Stopping Streamlit..."
    pkill -f "streamlit run" 2>/dev/null
    
    echo "   ✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
echo "🔍 Checking Python environment..."
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+ and try again."
    exit 1
fi

echo "📂 Working directory: $(pwd)"
echo ""

# Start backend
if start_backend; then
    # Start frontend
    start_frontend
else
    echo "❌ Failed to start backend. Please check the error messages above."
    exit 1
fi