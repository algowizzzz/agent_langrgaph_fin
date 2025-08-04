#!/usr/bin/env python3
"""
Test multi-document comparison capabilities
"""

import requests
import json
import time
from datetime import datetime

def test_multi_document_comparison():
    """Test comparative analysis between car24_chpt1_0.pdf and car24_chpt7.pdf"""
    
    BACKEND_URL = "http://localhost:8000"
    session_id = f"comparison_test_{int(time.time())}"
    
    # Get document internal names
    try:
        docs_response = requests.get(f"{BACKEND_URL}/documents")
        docs_data = docs_response.json()
        
        # Find the car24 documents
        chap1_internal = None
        chap7_internal = None
        
        for doc in docs_data['documents']:
            if 'car24_chpt1_0.pdf' in doc['name']:
                chap1_internal = doc['internal_name']
            elif 'car24_chpt7.pdf' in doc['name']:
                chap7_internal = doc['internal_name']
        
        if not chap1_internal or not chap7_internal:
            print("❌ Could not find both car24 documents")
            return
            
        print(f"✅ Found documents:")
        print(f"   Chapter 1: {chap1_internal}")
        print(f"   Chapter 7: {chap7_internal}")
        
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
        return
    
    # Test questions
    questions = [
        {
            "query": "compare and contrast the policy, requirements and procedures mentioned in the two chapters?",
            "description": "Multi-document comparative analysis"
        },
        {
            "query": "list them all down in concise bullet from above response",
            "description": "Follow-up bullet list extraction"
        }
    ]
    
    print(f"\n🔍 MULTI-DOCUMENT COMPARISON TEST")
    print(f"Session: {session_id}")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question['query']}")
        print(f"Description: {question['description']}")
        print("-" * 50)
        
        # Prepare request
        request_data = {
            "query": question["query"],
            "session_id": session_id,
            "active_documents": [chap1_internal, chap7_internal]
        }
        
        try:
            # Send request
            response = requests.post(
                f"{BACKEND_URL}/chat",
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=300  # 5 minutes
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('final_answer', 'No response')
                
                print(f"✅ Response received ({len(answer)} chars):")
                print(f"\n{answer}\n")
                
                # Save to file for detailed analysis
                filename = f"comparison_test_q{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Question: {question['query']}\n")
                    f.write(f"Description: {question['description']}\n")
                    f.write(f"Session: {session_id}\n")
                    f.write(f"Time: {datetime.now()}\n")
                    f.write("="*60 + "\n\n")
                    f.write(answer)
                
                print(f"💾 Full response saved to: {filename}")
                
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Small delay between questions
        if i < len(questions):
            print("\n⏱️  Waiting 3 seconds before next question...")
            time.sleep(3)
    
    print(f"\n🎯 ANALYSIS COMPLETE")
    print(f"Check the saved files for detailed comparison analysis")

if __name__ == "__main__":
    test_multi_document_comparison()