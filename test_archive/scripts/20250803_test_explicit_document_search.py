#!/usr/bin/env python3
"""
Test with extremely explicit document search queries
"""

import asyncio
from orchestrator_integration import OrchestratorIntegration

async def test_explicit_document_queries():
    """Test with very explicit document search instructions"""
    print("🚀 Testing Explicit Document Search Instructions")
    print("=" * 70)
    
    # Initialize V2-only integration
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    session_id = f"explicit_test_{int(asyncio.get_event_loop().time())}"
    
    # Test queries with explicit tool instructions
    queries = [
        "Use the search_uploaded_docs tool to search riskandfinace.pdf for the word 'finance'. Do not use knowledge base search. Extract information about finance from the uploaded PDF document.",
        
        "I have uploaded riskandfinace.pdf. Please use document tools (search_uploaded_docs, discover_document_structure) to analyze this specific PDF file and find content about finance. Avoid knowledge base search.",
        
        "Execute these steps: 1) Use search_uploaded_docs with doc_name='riskandfinace.pdf' and query='finance' 2) Use synthesize_content to summarize the results. Do not use search_knowledge_base tool."
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Test {i}/3 ---")
        print(f"🔍 Query: {query[:100]}...")
        
        try:
            result = await integration.run(
                user_query=query,
                session_id=session_id,
                active_documents=["riskandfinace.pdf"]
            )
            
            print(f"✅ Status: {result.get('status', 'unknown')}")
            print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"📝 Answer: {result.get('final_answer', 'No answer')[:150]}...")
            
            if result.get('execution_summary'):
                summary = result['execution_summary']
                print(f"📊 Tools: {summary.get('completed', 0)}/{summary.get('total_steps', 0)} completed")
                
                # Show tool details if available
                if 'step_details' in summary:
                    for step_id, details in summary['step_details'].items():
                        print(f"   - {step_id}: {details.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_explicit_document_queries())