#!/usr/bin/env python3
"""Debug script to test the exact real execution flow."""

import asyncio
import sys
import os
import logging

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath('.'))

from orchestrator_integration import OrchestratorIntegration

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_real_execution():
    """Test the exact execution flow used by the orchestrator."""
    print("🔍 Testing Real Execution Flow")
    print("=" * 50)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    
    # Test the exact same call as the real system
    print("🚀 Testing real orchestrator execution...")
    
    try:
        result = await integration.run(
            user_query="What is risk?",
            session_id="debug_session",
            active_documents=["riskandfinace.pdf"],
            memory_context={}
        )
        
        print(f"🎯 Result: {result}")
        print(f"📊 Success: {result.get('success', False)}")
        print(f"📄 Answer: {result.get('answer', 'No answer')}")
        print(f"📈 Confidence: {result.get('confidence', 0.0)}")
        print(f"⚡ Steps Completed: {result.get('steps_completed', 0)}")
        print(f"📋 Steps Total: {result.get('steps_total', 0)}")
        
        if result.get('execution_summary'):
            print(f"📝 Execution Summary: {result['execution_summary']}")
            
    except Exception as e:
        print(f"❌ Real execution failed: {e}")
        logger.exception("Full error details:")
    
    print()
    print("🔍 Testing execute_plan directly with context...")
    
    # Test execute_plan with the exact context
    orchestrator = integration.orchestrator_v2
    
    # Create planning context 
    from orchestrator_v2.planning_engine_enhanced import PlanningContext, PlanningStrategy
    context = PlanningContext(
        user_query="What is risk?",
        session_id="debug_session",
        active_documents=["riskandfinace.pdf"],
        available_tools=list(orchestrator.tool_registry._tools.keys())
    )
    
    # Create execution plan
    plan = await orchestrator.planning_engine.create_execution_plan(context, PlanningStrategy.ADAPTIVE)
    
    if plan:
        print(f"✅ Plan created: {plan.plan_id}")
        
        # Test execute_plan with exact context used by orchestrator
        execution_context = {
            "session_id": "debug_session", 
            "active_documents": ["riskandfinace.pdf"],
            "user_query": "What is risk?"
        }
        
        try:
            results = await orchestrator.execution_engine.execute_plan(
                plan=plan,
                context=execution_context
            )
            
            print(f"📊 Execution results: {len(results)} steps")
            for step_id, result in results.items():
                print(f"   {step_id}: {result.status} (confidence: {result.confidence_score})")
                if result.error:
                    print(f"      Error: {result.error}")
                    
        except Exception as e:
            print(f"❌ execute_plan failed: {e}")
            logger.exception("execute_plan error:")
    else:
        print("❌ No plan created!")

if __name__ == "__main__":
    asyncio.run(debug_real_execution())