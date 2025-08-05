#!/usr/bin/env python3
"""
Simple script to test backend queries from terminal
"""

import requests
import json
import sys

def test_simple_query(query="Hello, who are you?"):
    """Test a simple non-streaming query."""
    
    print(f"🔍 Testing query: '{query}'")
    print("=" * 60)
    
    # Parse --doc flag if present
    active_documents = []
    actual_query = query
    
    if "--doc " in query:
        doc_flag_idx = query.find("--doc ")
        actual_query = query[:doc_flag_idx].strip()
        doc_names_str = query[doc_flag_idx + 6:].strip()
        # Split multiple document names by spaces
        active_documents = doc_names_str.split() if doc_names_str else []
        print(f"📄 Using document(s): {active_documents}")
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "query": actual_query,
                "session_id": "terminal-test-session",
                "active_documents": active_documents
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📝 Answer: {result.get('final_answer', 'No answer')}")
            print(f"⏱️  Time: {result.get('processing_time_ms', 0)}ms")
            print(f"🎯 Confidence: {result.get('confidence_score', 0)}")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure the backend is running: python main.py")
        return False

def test_streaming_query(query="What is finance?"):
    """Test the streaming endpoint."""
    
    print(f"🌊 Testing streaming query: '{query}'")
    print("=" * 60)
    
    try:
        response = requests.post(
            "http://localhost:8000/chat/stream",
            json={
                "query": query,
                "session_id": "terminal-stream-test",
                "active_documents": []
            },
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ STREAMING SUCCESS!")
            print("📡 Receiving events:")
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        event_type = data.get("type", "unknown")
                        message = data.get("message", "")
                        print(f"   📨 {event_type}: {message}")
                        
                        if event_type == "final_answer":
                            content = data.get("content", {})
                            final_answer = content.get("final_answer", "No answer")
                            print(f"   📝 Final Answer: {final_answer[:100]}...")
                            break
                    except json.JSONDecodeError:
                        continue
            return True
        else:
            print(f"❌ Streaming HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming Error: {e}")
        return False

def test_system_status():
    """Test system status endpoint."""
    
    print("🔍 Testing system status...")
    
    try:
        response = requests.get("http://localhost:8000/system/status", timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            print("✅ System Status:")
            print(f"   📊 Status: {status.get('status', 'unknown')}")
            features = status.get('features', {})
            print(f"   🤖 Orchestrator V2: {'✅' if features.get('orchestrator_v2') else '❌'}")
            print(f"   💾 Memory: {'✅' if features.get('memory_integration') else '❌'}")
            print(f"   📄 Multi-docs: {'✅' if features.get('multi_document_analysis') else '❌'}")
            print(f"   🌊 Streaming: {'✅' if features.get('streaming_support') else '❌'}")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Status Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stream":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What is finance?"
            if test_system_status():
                print()
                test_streaming_query(query)
        else:
            query = " ".join(sys.argv[1:])
            if test_system_status():
                print()
                test_simple_query(query)
    else:
        # Default: test both
        print("🧪 COMPLETE BACKEND TEST")
        print("=" * 60)
        
        if test_system_status():
            print()
            if test_simple_query("Hello, who are you?"):
                print()
                test_streaming_query("What is finance?")
        else:
            print("💡 Start backend: python main.py")
            print("💡 Usage: python test_query.py [--stream] [your question]")
