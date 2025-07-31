"""
Test script to verify document context awareness fix
"""

import asyncio
from orchestrator import Orchestrator
from tools.document_tools import upload_document

async def test_context_awareness():
    """Test that orchestrator correctly identifies active document."""
    
    print("🧪 Testing Document Context Awareness Fix")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Test 1: Upload a specific document
    print("\n📄 Test 1: Uploading test document...")
    
    # Create a simple test file
    test_content = """
This is a test document about financial regulations.
It contains information about capital adequacy requirements.
The document discusses risk management frameworks.
Basel III compliance is mentioned several times.
    """
    
    with open("test_context_doc.txt", "w") as f:
        f.write(test_content)
    
    # Upload the document
    upload_result = await upload_document("test_context_doc.txt")
    print(f"Upload result: {upload_result}")
    
    if upload_result.get('status') == 'success':
        active_doc = upload_result.get('doc_name')
        print(f"✅ Document uploaded: {active_doc}")
        
        # Test 2: Query with context awareness
        print(f"\n🎯 Test 2: Query with active document context...")
        
        user_query = "summarise the attached document"
        
        # Test with active document context
        result_with_context = await orchestrator.run(
            user_query, 
            session_id="test_session", 
            active_document=active_doc
        )
        
        print(f"\n📊 Result with context:")
        print(f"Status: {result_with_context.get('status')}")
        print(f"Answer: {result_with_context.get('final_answer', 'No answer')[:200]}...")
        
        # Check if the reasoning log shows the correct document
        reasoning = result_with_context.get('reasoning_log', [])
        print(f"\n🧠 Reasoning steps: {len(reasoning)}")
        for i, step in enumerate(reasoning):
            if isinstance(step, dict) and 'tool_params' in step:
                params = step['tool_params']
                if 'doc_name' in params:
                    print(f"  Step {i+1}: Used doc_name = '{params['doc_name']}'")
        
        # Test 3: Query without context (old behavior)
        print(f"\n🔄 Test 3: Query without active document context...")
        
        result_without_context = await orchestrator.run(
            user_query, 
            session_id="test_session"
            # No active_document parameter
        )
        
        print(f"\n📊 Result without context:")
        print(f"Status: {result_without_context.get('status')}")
        
        # Compare behavior
        print(f"\n📈 Comparison:")
        print(f"With context - targeted specific document: {active_doc in str(result_with_context)}")
        print(f"Without context - may use random documents from memory")
        
        print(f"\n✅ Test completed! The fix should ensure 'attached document' queries target: {active_doc}")
        
    else:
        print(f"❌ Upload failed: {upload_result}")
    
    # Cleanup
    import os
    if os.path.exists("test_context_doc.txt"):
        os.remove("test_context_doc.txt")

if __name__ == "__main__":
    asyncio.run(test_context_awareness())