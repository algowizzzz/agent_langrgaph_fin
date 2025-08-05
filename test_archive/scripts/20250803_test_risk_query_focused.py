#!/usr/bin/env python3
"""
Focused test for 'What is risk?' query to debug the step reference error
"""

import asyncio
from orchestrator_integration import OrchestratorIntegration

async def test_risk_query_focused():
    """Test specifically the 'What is risk?' query that had issues"""
    print("🚀 Focused Test: 'What is risk?' Query")
    print("=" * 60)
    
    # Initialize V2-only integration
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    session_id = f"risk_test_{int(asyncio.get_event_loop().time())}"
    
    # Test the problematic query
    query = "What is risk?"
    print(f"🔍 Query: {query}")
    print("📁 Testing with the exact query that had step reference errors...")
    
    try:
        result = await integration.run(
            user_query=query,
            session_id=session_id,
            active_documents=["riskandfinace.pdf"]
        )
        
        print(f"✅ Status: {result.get('status', 'unknown')}")
        print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
        print(f"🔧 Version: {result.get('orchestrator_version', 'unknown')}")
        print(f"📝 Answer: {result.get('final_answer', 'No answer received')[:200]}...")
        
        # Check execution details
        if 'execution_summary' in result:
            print(f"📊 Execution: {result['execution_summary']}")
            
        # Check for step reference errors
        if 'traceability_log' in result:
            print("\n🔍 Execution Details:")
            for log_entry in result['traceability_log']:
                if 'error' in str(log_entry).lower() or 'failed' in str(log_entry).lower():
                    print(f"   ⚠️ Error: {log_entry}")
                    
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_risk_query_focused())