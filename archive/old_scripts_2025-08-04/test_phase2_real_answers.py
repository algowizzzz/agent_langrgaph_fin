#!/usr/bin/env python3
"""
Test Phase 2: Real Document Answers

Quick test to verify our AI Finance and Risk Agent can produce real answers
from actual documents, not just "No answer..."
"""

import asyncio
from orchestrator_integration import OrchestratorIntegration

async def test_real_document_answers():
    """Test if the agent produces real answers from documents."""
    print("🧪 Testing AI Finance and Risk Agent - Real Document Answers")
    print("=" * 70)
    
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    
    # Test with a document that should exist
    test_cases = [
        {
            "query": "What is risk?",
            "documents": ["riskandfinace.pdf"],
            "description": "Document analysis with uploaded document"
        },
        {
            "query": "What is risk?", 
            "documents": [],
            "description": "Knowledge base fallback (no documents)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"📝 Query: '{test_case['query']}'")
        print(f"📁 Documents: {test_case['documents'] or 'None'}")
        
        session_id = f"phase2_test_{i}_{int(asyncio.get_event_loop().time())}"
        
        try:
            result = await integration.run(
                user_query=test_case['query'],
                session_id=session_id,
                active_documents=test_case['documents']
            )
            
            answer = result.get('final_answer', result.get('answer', 'No answer provided'))
            confidence = result.get('confidence_score', 0)
            execution_summary = result.get('execution_summary', {})
            
            print(f"🎯 Confidence: {confidence:.3f}")
            print(f"📋 Strategy: {execution_summary.get('strategy', 'Unknown')}")
            print(f"⚡ Steps: {execution_summary.get('total_steps', 0)} total, {execution_summary.get('completed', 0)} completed")
            
            if answer and answer != "No answer..." and len(answer) > 50:
                print(f"✅ Real Answer Generated:")
                print(f"📄 Preview: {answer[:200]}...")
                print(f"📊 Length: {len(answer)} characters")
            else:
                print(f"❌ No Real Answer:")
                print(f"📄 Got: '{answer}'")
                
                # Show execution results for debugging
                if 'execution_results' in result:
                    print(f"🔍 Execution Results:")
                    for step_id, step_result in result['execution_results'].items():
                        status = step_result.get('status', 'unknown')
                        error = step_result.get('error', '')
                        print(f"  - {step_id}: {status} {f'(Error: {error})' if error else ''}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_real_document_answers())