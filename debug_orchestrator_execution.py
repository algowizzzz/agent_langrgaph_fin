#!/usr/bin/env python3
"""
Debug script to trace what happens during orchestrator execution
"""

import asyncio
import json
from orchestrator_integration import OrchestratorIntegration
from tools.document_tools import search_uploaded_docs

async def debug_orchestrator_step_by_step():
    """Debug the orchestrator execution step by step."""
    
    print("🔍 DEBUGGING ORCHESTRATOR EXECUTION")
    print("=" * 50)
    
    integration = OrchestratorIntegration()
    
    # Test 1: Direct tool call (what we know works)
    print("\n📄 Test 1: Direct Tool Call")
    print("-" * 30)
    
    try:
        direct_result = await search_uploaded_docs("riskandfinace.pdf", "financial risk")
        print(f"✅ Direct call works: {len(direct_result)} results")
        if direct_result and len(direct_result) > 0:
            first_result = direct_result[0]
            if 'page_content' in first_result:
                print(f"📄 Content preview: {first_result['page_content'][:200]}...")
            else:
                print(f"⚠️  No page_content, got: {list(first_result.keys())}")
    except Exception as e:
        print(f"❌ Direct call failed: {e}")
    
    # Test 2: Orchestrator execution with debug
    print("\n🎯 Test 2: Orchestrator Execution")
    print("-" * 30)
    
    query = "What types of financial risk are mentioned?"
    documents = ["riskandfinace.pdf"]
    session_id = "debug_session_trace"
    
    print(f"📝 Query: {query}")
    print(f"📁 Documents: {documents}")
    print(f"🆔 Session: {session_id}")
    
    try:
        # Execute with orchestrator
        result = await integration.orchestrator_v2.execute_query(
            user_query=query,
            session_id=session_id,
            active_documents=documents
        )
        
        print(f"🎯 Orchestrator result keys: {list(result.keys())}")
        print(f"📊 Confidence: {result.get('confidence_score', 'N/A')}")
        
        # Check execution summary
        exec_summary = result.get('execution_summary', {})
        print(f"⚡ Steps: {exec_summary.get('completed', 0)}/{exec_summary.get('total', 0)}")
        
        # Check step details
        step_details = exec_summary.get('step_details', {})
        print(f"🔧 Step details: {list(step_details.keys())}")
        
        for step_name, details in step_details.items():
            print(f"   📋 {step_name}: {details.get('status', 'unknown')} ({details.get('confidence', 'N/A')} confidence)")
        
        # Check final answer
        final_answer = result.get('final_answer', 'No answer')
        print(f"📄 Final answer length: {len(final_answer)} chars")
        print(f"📖 Final answer preview: {final_answer[:300]}...")
        
        # Check traceability
        traceability = result.get('traceability_log', [])
        print(f"🔍 Traceability entries: {len(traceability)}")
        
    except Exception as e:
        print(f"❌ Orchestrator execution failed: {e}")
        import traceback
        print(f"🚨 Full traceback: {traceback.format_exc()}")

    # Test 3: Check what documents are available to this session
    print("\n📋 Test 3: Session Document Check")
    print("-" * 30)
    
    try:
        from tools.document_tools import get_all_documents
        all_docs = await get_all_documents()
        
        print(f"📚 Total documents in system: {len(all_docs)}")
        
        # Find riskandfinace.pdf documents
        risk_docs = [doc for doc in all_docs if 'risk' in doc.get('name', '').lower()]
        print(f"🎯 Risk-related documents: {len(risk_docs)}")
        
        for doc in risk_docs[:3]:  # Show first 3
            print(f"   📄 {doc.get('name', 'Unknown')} (session: {doc.get('uploaded_by_session', 'Unknown')})")
            
    except Exception as e:
        print(f"❌ Document check failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_orchestrator_step_by_step())