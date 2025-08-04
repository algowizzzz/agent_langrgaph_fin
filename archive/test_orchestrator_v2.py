#!/usr/bin/env python3
"""
Simple test to demonstrate orchestrator v2 functionality
"""

import asyncio
import json
from orchestrator_v2.orchestrator_v2 import OrchestratorV2

async def test_orchestrator_v2():
    """Test basic orchestrator v2 functionality"""
    
    print("🧪 Testing Orchestrator V2 System")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = OrchestratorV2()
    print("✅ Orchestrator V2 initialized")
    
    # Test simple query
    test_query = "What is the current system status?"
    print(f"\n📝 Testing query: '{test_query}'")
    
    try:
        # Process the query
        result = await orchestrator.execute_query(
            user_query=test_query,
            session_id="test_session_001"
        )
        
        print("\n📊 Results:")
        print(f"Status: {result.get('status', 'Unknown')}")
        print(f"Final Answer: {result.get('final_answer', 'No response')[:200]}...")
        print(f"Confidence Score: {result.get('confidence_score', 'N/A')}")
        
        if result.get('execution_summary'):
            summary = result['execution_summary']
            print(f"Execution Time: {summary.get('total_execution_time', 'N/A')}s")
            print(f"Steps Executed: {summary.get('total_steps', 'N/A')}")
        
        if result.get('traceability_log'):
            trace = result['traceability_log']
            print(f"Trace Steps: {len(trace.get('steps', []))}")
            for i, step in enumerate(trace.get('steps', [])[:3], 1):  # Show first 3 steps
                step_name = step.get('step_name', 'Unknown')
                step_status = step.get('status', 'Unknown')
                print(f"  {i}. {step_name} - {step_status}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_v2())