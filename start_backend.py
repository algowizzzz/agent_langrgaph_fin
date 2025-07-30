#!/usr/bin/env python3
"""Start just the FastAPI backend"""

import uvicorn
import os

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🚀 Starting BMO Documentation Analysis Backend")
    print(f"📊 API will be available at: http://localhost:8000")
    print(f"📋 API Documentation at: http://localhost:8000/docs")
    
    # Check if we have API keys
    if os.getenv('OPENAI_API_KEY'):
        print("🔑 OpenAI API key detected - Production mode")
    elif os.getenv('ANTHROPIC_API_KEY'):
        print("🔑 Anthropic API key detected - Production mode")
    else:
        print("🧪 No API keys - Mock mode")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )