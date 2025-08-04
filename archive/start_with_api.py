#!/usr/bin/env python3
"""
Start the BMO Documentation Analysis Tool with real API integration
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required keys."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("\n📋 To use real APIs, please:")
        print("1. Copy .env.template to .env")
        print("2. Add your API keys to .env")
        print("3. Run this script again")
        print("\n💡 For testing with mock data, you can still proceed.")
        
        response = input("\nContinue with mock mode? (y/n): ").lower().strip()
        if response != 'y':
            print("Exiting...")
            sys.exit(1)
        return False
    
    # Check for required keys
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_keys = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
    has_api_key = any(key in content and not content.split(key + '=')[1].split('\n')[0].strip().endswith('_here') 
                     for key in required_keys if key in content)
    
    if not has_api_key:
        print("⚠️  No API keys found in .env file")
        print("Running in MOCK MODE for testing")
        return False
    
    return True

def update_config_for_production(has_real_api):
    """Update config.yaml to enable/disable mock mode."""
    config_file = Path("config.yaml")
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Update mock mode setting
        if has_real_api:
            content = content.replace('enable_mock_mode: true', 'enable_mock_mode: false')
            print("✅ Configured for PRODUCTION mode with real APIs")
        else:
            content = content.replace('enable_mock_mode: false', 'enable_mock_mode: true')
            print("✅ Configured for MOCK mode for testing")
        
        with open(config_file, 'w') as f:
            f.write(content)

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting FastAPI backend...")
    
    # Start backend in background
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])
    
    # Give backend time to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    return backend_process

def start_frontend():
    """Start the Streamlit frontend."""
    print("🎨 Starting Streamlit frontend...")
    
    # Start frontend
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])
    
    return frontend_process

def main():
    print("🏦 BMO Documentation Analysis Tool - Production Starter")
    print("=" * 60)
    
    # Check environment setup
    has_real_api = check_env_file()
    
    # Update configuration
    update_config_for_production(has_real_api)
    
    # Start services
    try:
        backend_process = start_backend()
        frontend_process = start_frontend()
        
        print("\n🎉 Application started successfully!")
        print("=" * 60)
        print(f"📊 Backend API: http://localhost:8000")
        print(f"🎨 Frontend UI: http://localhost:8501")
        print(f"📋 API Docs: http://localhost:8000/docs")
        print("=" * 60)
        
        if has_real_api:
            print("🔑 Running with REAL API integration")
            print("💡 Upload documents and ask questions using actual AI!")
        else:
            print("🧪 Running in MOCK mode for testing")
            print("💡 Perfect for testing without API costs")
        
        print("\n⚡ Ready to analyze documents and answer questions!")
        print("Press Ctrl+C to stop both services...")
        
        # Wait for processes
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            backend_process.terminate()
            frontend_process.terminate()
            
            # Wait for graceful shutdown
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
            
            print("✅ Services stopped successfully")
    
    except Exception as e:
        print(f"❌ Error starting services: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()