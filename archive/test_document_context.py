"""
Test script to verify document context awareness fix
"""

import asyncio
from orchestrator import Orchestrator
from tools.document_tools import upload_document

async def test_context_awareness():
    """Test that orchestrator correctly identifies active document."""
    
    print("🧪 Testing Document Context Awareness Fix")
    print("🎯 Using REAL USER DOCUMENT: riskandfinace.pdf")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Test 1: Upload the user's actual document
    print("\n📄 Test 1: Uploading user's document...")
    
    # Check if the file exists
    import os
    pdf_file = "riskandfinace.pdf"
    if not os.path.exists(pdf_file):
        print(f"❌ File not found: {pdf_file}")
        print("📂 Available files:")
        for f in os.listdir("."):
            if f.endswith('.pdf'):
                print(f"  - {f}")
        return
    
    print(f"✅ Found document: {pdf_file}")
    
    # Upload the actual PDF document
    upload_result = await upload_document(pdf_file)
    print(f"Upload result: {upload_result}")
    
    if upload_result.get('status') == 'success':
        active_doc = upload_result.get('doc_name')
        print(f"✅ Document uploaded: {active_doc}")
        
        # Test 2: Query with context awareness (REAL USER SCENARIO)
        print(f"\n🎯 Test 2: Testing REAL USER SCENARIO...")
        print(f"🔍 Query: 'comprehensive summary of the document'")
        print(f"📄 Should target: {active_doc} (the PDF you uploaded)")
        print(f"💡 This will show the full agent capabilities with your PDF!")
        
        user_query = "comprehensive summary of the document"
        
        # Test with active document context
        result_with_context = await orchestrator.run(
            user_query, 
            session_id="test_session", 
            active_document=active_doc
        )
        
        print(f"\n📊 RESULT WITH CONTEXT AWARENESS:")
        print(f"Status: {result_with_context.get('status')}")
        
        # Show the full answer
        answer = result_with_context.get('final_answer', 'No answer')
        if answer and isinstance(answer, str):
            print(f"\n📝 COMPREHENSIVE SUMMARY:")
            print(f"\n{answer}")
        elif answer:
            print(f"\n📝 COMPREHENSIVE SUMMARY:")
            print(f"\n{str(answer)}")
        
        # Check if the reasoning log shows the correct document
        reasoning = result_with_context.get('reasoning_log', [])
        print(f"\n🧠 Reasoning Analysis ({len(reasoning)} steps):")
        
        correct_target_count = 0
        for i, step in enumerate(reasoning):
            if isinstance(step, dict) and 'tool_params' in step:
                params = step['tool_params']
                if 'doc_name' in params:
                    doc_used = params['doc_name']
                    if doc_used == active_doc:
                        print(f"  ✅ Step {i+1}: Correctly used '{doc_used}'")
                        correct_target_count += 1
                    else:
                        print(f"  ❌ Step {i+1}: Used wrong doc '{doc_used}' (should be '{active_doc}')")
                    
        # Test 3: Verify the fix worked
        print(f"\n🎯 CONTEXT AWARENESS VERIFICATION:")
        if correct_target_count > 0:
            print(f"✅ SUCCESS: Agent correctly targeted '{active_doc}' in {correct_target_count} steps")
            print(f"✅ FIX CONFIRMED: 'Attached document' now refers to your uploaded PDF!")
        else:
            print(f"❌ ISSUE: Agent didn't target the correct document")
            
        print(f"\n🎊 REAL-WORLD TEST COMPLETED!")
        print(f"📄 Your document: {active_doc}")
        print(f"🎯 Context awareness: {'WORKING' if correct_target_count > 0 else 'NEEDS DEBUGGING'}")
        print(f"💬 User experience: {'FIXED' if correct_target_count > 0 else 'STILL BROKEN'}")
        
    else:
        print(f"❌ Upload failed: {upload_result}")
    
    # No cleanup needed - we used the user's actual PDF file
    print(f"\n✨ Test complete! Your {pdf_file} remains untouched.")

if __name__ == "__main__":
    asyncio.run(test_context_awareness())