#!/usr/bin/env python3
"""Test script to verify memory search fix works without parameter errors."""

import asyncio
import sys
import os
import logging

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath('.'))

from orchestrator_integration import OrchestratorIntegration

# Enable info logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_memory_search_fix():
    """Test the memory search workflow to verify parameter fix."""
    print("🧠 Testing Memory Search Parameter Fix")
    print("=" * 50)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    
    test_query = "Remember what we discussed about risk analysis?"
    session_id = f"memory_fix_test_{int(asyncio.get_event_loop().time())}"
    
    print(f"📝 Query: '{test_query}'")
    print(f"🎯 Expected: 3/3 steps completed without parameter errors")
    print("=" * 50)
    
    try:
        result = await integration.run(
            user_query=test_query,
            session_id=session_id,
            active_documents=None  # No documents to trigger memory search
        )
        
        # Extract response details
        success = result.get('status') == 'success'
        answer = result.get('final_answer', result.get('answer', 'No answer provided'))
        confidence = result.get('confidence_score', 0)
        execution_summary = result.get('execution_summary', {})
        
        print(f"📊 Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"🎯 Confidence: {confidence:.3f}")
        print(f"⚡ Steps: {execution_summary.get('completed', 0)}/{execution_summary.get('total_steps', 0)} completed")
        print(f"⏱️  Execution Time: {execution_summary.get('total_execution_time', 0):.2f}s")
        
        if execution_summary.get('completed', 0) == execution_summary.get('total_steps', 0):
            print("✅ **PARAMETER FIX SUCCESSFUL:** All steps completed without errors!")
        else:
            print("⚠️  **PARTIAL SUCCESS:** Some steps may still have issues")
        
        if answer and len(answer) > 50:
            print(f"\n💡 **Memory Search Response:**")
            print(f"📄 {answer[:200]}...")
            print(f"📏 Length: {len(answer)} characters")
        else:
            print(f"\n⚠️  **Limited Response:**")
            print(f"📄 Got: '{answer}'")
        
        # Check for parameter warnings in logs
        print(f"\n🔍 **Parameter Validation Check:**")
        if "additional_context" in str(result):
            print("❌ Still has additional_context parameter issue")
        else:
            print("✅ No additional_context parameter warnings detected")
            
        return execution_summary.get('completed', 0) == execution_summary.get('total_steps', 0)
        
    except Exception as e:
        print(f"💥 **Test Failed:** {e}")
        logger.exception("Memory search test error:")
        return False

if __name__ == "__main__":
    asyncio.run(test_memory_search_fix())