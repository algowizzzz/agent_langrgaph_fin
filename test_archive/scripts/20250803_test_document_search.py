#!/usr/bin/env python3
"""
Simple test to verify document search is working
"""

import asyncio
from orchestrator_integration import OrchestratorIntegration

async def test_document_search():
    """Test document search functionality"""
    print("🚀 Testing Document Search with V2-Only Orchestrator")
    print("=" * 60)
    
    # Initialize V2-only integration
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    session_id = f"doc_test_{int(asyncio.get_event_loop().time())}"
    
    # Test with explicit document search instruction
    query = "I need you to search specifically within the uploaded document riskandfinace.pdf (not the knowledge base) to find information about finance. Please use the document search tools to analyze the PDF content and tell me what this specific document says about finance. Focus on extracting information directly from the uploaded document."
    print(f"🔍 Query: {query}")
    print("📁 Testing with explicit document search instruction...")
    
    try:
        result = await integration.run(
            user_query=query,
            session_id=session_id,
            active_documents=["riskandfinace.pdf"]
        )
        
        print(f"✅ Status: {result.get('status', 'unknown')}")
        print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
        print(f"🔧 Version: {result.get('orchestrator_version', 'unknown')}")
        print(f"📝 Answer: {result.get('final_answer', 'No answer')[:200]}...")
        
        if result.get('execution_summary'):
            summary = result['execution_summary']
            print(f"📊 Execution: {summary.get('completed', 0)}/{summary.get('total_steps', 0)} steps completed")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_document_search())