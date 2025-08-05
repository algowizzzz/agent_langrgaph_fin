#!/usr/bin/env python3
"""
Interactive Chat Session with AI Finance & Risk Agent
Run this script to start a terminal-based chat interface.
"""

import requests
import json
import sys
from datetime import datetime

# Server configuration
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/chat"
HEALTH_ENDPOINT = f"{BASE_URL}/health"

def check_server_status():
    """Check if the server is running and healthy."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print(f"   Make sure to start the server first: python main.py")
        return False

def send_message(message, document=None):
    """Send a message to the agent and return the response."""
    payload = {
        "query": message,
        "session_id": "interactive-session",
        "user_id": "terminal-user"
    }
    
    if document:
        payload["active_document"] = document
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=60  # Longer timeout for complex queries
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Server error {response.status_code}",
                "details": response.text
            }
    except requests.exceptions.RequestException as e:
        return {
            "error": "Connection error",
            "details": str(e)
        }

def print_response(response_data):
    """Print the agent's response in a formatted way."""
    if "error" in response_data:
        print(f"\n❌ Error: {response_data['error']}")
        if "details" in response_data:
            print(f"   Details: {response_data['details']}")
        return
    
    if "response" in response_data:
        print(f"\n🤖 Agent: {response_data['response']}")
        
        # Print additional info if available
        if "processing_time" in response_data:
            print(f"⏱️  Processing time: {response_data['processing_time']}ms")
        
        if "confidence" in response_data:
            print(f"🎯 Confidence: {response_data['confidence']}")
    else:
        print(f"\n📄 Response: {json.dumps(response_data, indent=2)}")

def show_help():
    """Show available commands."""
    help_text = """
📚 Available Commands:
  /help       - Show this help message
  /docs       - List available documents
  /tools      - List available tools and capabilities  
  /status     - Check system status
  /doc <name> - Set document for next query (use filename from /docs)
  /clear      - Clear document selection
  /exit       - Exit the interactive session

💡 Tips:
  - Ask questions about finance, risk management, regulations
  - Upload documents via the web interface or specify existing ones with /doc
  - Use natural language - the agent understands context
  - For document analysis, specify the full filename from /docs command

📝 Example queries:
  - "What tools do you have access to?"
  - "Analyze risk management practices"
  - "Summarize regulatory requirements for capital adequacy"
  - "What is wrong way risk?"
"""
    print(help_text)

def main():
    """Main interactive chat loop."""
    print("🚀 AI Finance & Risk Agent - Interactive Chat Session")
    print("=" * 60)
    
    # Check server status
    if not check_server_status():
        print("\n💡 To start the server, run: python main.py")
        sys.exit(1)
    
    print("\nType your message and press Enter. Type '/help' for commands or '/exit' to quit.")
    print("-" * 60)
    
    current_document = None
    
    while True:
        try:
            # Show prompt with current document context
            if current_document:
                prompt = f"\n📄 [{current_document}] 💬 You: "
            else:
                prompt = "\n💬 You: "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Smart document scoping is now handled automatically by the planner
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command == '/exit':
                    print("\n👋 Goodbye!")
                    break
                elif command == '/help':
                    show_help()
                elif command == '/docs':
                    print("\n🔍 Fetching available documents...")
                    response = send_message("what documents do you have access to?")
                    print_response(response)
                elif command == '/tools':
                    print("\n🔍 Fetching available tools...")
                    response = send_message("what tools do you have access to?")
                    print_response(response)
                elif command == '/status':
                    print("\n🔍 Checking system status...")
                    response = send_message("what is your current system status?")
                    print_response(response)
                elif command.startswith('/doc '):
                    current_document = command[5:].strip()
                    print(f"\n📄 Document set to: {current_document}")
                    print("   Next queries will analyze this document.")
                elif command == '/clear':
                    current_document = None
                    print("\n🗑️  Document selection cleared.")
                else:
                    print(f"\n❓ Unknown command: {user_input}")
                    print("   Type '/help' to see available commands.")
                continue
            
            # Send regular message (auto-discovery handles document scoping)
            print(f"\n🔄 Processing your request...")
            start_time = datetime.now()
            
            response = send_message(user_input)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            print_response(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("   Continuing chat session...")

if __name__ == "__main__":
    main()