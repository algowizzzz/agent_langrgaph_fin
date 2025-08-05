#!/usr/bin/env python3
"""
Simple memory test - just tests the conversation history functionality
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/chat"
SESSION_ID = "memory_test_simple"

def test_memory():
    print("🧠 Testing Memory Functionality\n")
    
    # First message - establish context
    print("=" * 50)
    print("Step 1: Establishing context")
    print("=" * 50)
    
    response1 = requests.post(CHAT_ENDPOINT, json={
        "query": "Remember that there are 4 departments: Finance, IT, Marketing, and HR.",
        "session_id": SESSION_ID,
        "active_document": None
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"✅ Response 1: {result1.get('final_answer', '')[:100]}...")
    else:
        print(f"❌ Error: {response1.status_code}")
        return False
    
    time.sleep(2)  # Brief pause
    
    # Second message - test memory
    print("\n" + "=" * 50)
    print("Step 2: Testing memory recall")
    print("=" * 50)
    
    response2 = requests.post(CHAT_ENDPOINT, json={
        "query": "Based on what I told you earlier, how many departments are there?",
        "session_id": SESSION_ID,
        "active_document": None
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        answer = result2.get('final_answer', '')
        print(f"✅ Response 2: {answer}")
        
        # Check if the answer mentions "4" or "four"
        if "4" in answer or "four" in answer.lower():
            print("\n🎉 SUCCESS: Memory system is working! Agent remembered the number of departments.")
            return True
        else:
            print("\n❌ FAILURE: Agent did not recall the department count correctly.")
            return False
    else:
        print(f"❌ Error: {response2.status_code}")
        return False

if __name__ == "__main__":
    success = test_memory()
    print("\n" + "=" * 60)
    if success:
        print("🎉 MEMORY TEST PASSED!")
    else:
        print("❌ MEMORY TEST FAILED!")
    print("=" * 60)