#!/usr/bin/env python3
"""
Test Basic Tools Available in Orchestrator

Quick test to see what tools are actually registered and working
"""

import asyncio
from orchestrator_integration import OrchestratorIntegration

async def test_basic_tools():
    """Test basic tool availability and execution."""
    print("🔧 Testing Basic Tool Availability")
    print("=" * 50)
    
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    
    # Check what tools are registered
    try:
        available_tools = list(integration.orchestrator_v2.tool_registry._tools.keys())
        print(f"📋 Available Tools ({len(available_tools)}):")
        for tool in sorted(available_tools):
            print(f"  - {tool}")
        
        # Test simple knowledge base search (should work)
        print(f"\n🧪 Testing simple knowledge base search...")
        
        session_id = f"tool_test_{int(asyncio.get_event_loop().time())}"
        
        result = await integration.run(
            user_query="What is artificial intelligence?",
            session_id=session_id,
            active_documents=[]  # No documents - should use knowledge base
        )
        
        answer = result.get('answer', 'No answer')
        confidence = result.get('confidence_score', 0)
        
        print(f"🎯 Result: {answer[:100]}..." if len(answer) > 100 else f"🎯 Result: {answer}")
        print(f"📊 Confidence: {confidence}")
        
        if answer and answer != "No answer" and len(answer) > 30:
            print("✅ Basic tool execution working!")
        else:
            print("❌ Basic tool execution failing")
            
    except Exception as e:
        print(f"❌ Error testing tools: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_tools())