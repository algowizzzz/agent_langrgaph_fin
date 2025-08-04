#!/usr/bin/env python3
"""Debug script to trace individual step execution."""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath('.'))

from orchestrator_integration import OrchestratorIntegration
from orchestrator_v2.execution_engine import ExecutionStep, ConditionType

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_step_execution():
    """Debug individual step execution."""
    print("🔍 Debugging Step Execution")
    print("=" * 50)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    orchestrator = integration.orchestrator_v2
    
    # Test the search_uploaded_docs tool directly
    print("🧪 Testing search_uploaded_docs tool directly...")
    
    try:
        # Get the tool
        tool = orchestrator.tool_registry._tools.get('search_uploaded_docs')
        if not tool:
            print("❌ Tool 'search_uploaded_docs' not found!")
            return
        
        print(f"✅ Tool found: {tool}")
        
        # Test tool parameters
        test_params = {
            'doc_name': 'riskandfinace.pdf',
            'query': 'What is risk?'
        }
        
        print(f"🔢 Test parameters: {test_params}")
        
        # Validate parameters
        validation = orchestrator.tool_registry.validate_parameters('search_uploaded_docs', test_params)
        print(f"✅ Parameter validation: {validation.is_valid}")
        if not validation.is_valid:
            print(f"❌ Validation errors: {validation.errors}")
            return
        
        # Test tool execution
        print("🚀 Executing tool...")
        result = await tool.ainvoke(test_params)
        print(f"🎯 Tool result: {result}")
        print(f"📊 Result type: {type(result)}")
        
        if hasattr(result, '__len__'):
            print(f"📏 Result length: {len(result)}")
        
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
        logger.exception("Full error details:")
    
    print()
    print("🔍 Testing step execution through ExecutionEngine...")
    
    # Create a test step
    test_step = ExecutionStep(
        step_id="test_search",
        tool_name="search_uploaded_docs",
        parameters={
            'doc_name': 'riskandfinace.pdf',
            'query': 'What is risk?'
        },
        dependencies=[],
        condition=ConditionType.ALWAYS,
        description="Test search step"
    )
    
    # Test step execution
    try:
        result = await orchestrator.execution_engine._execute_step(test_step)
        print(f"🎯 Step execution result: {result}")
        print(f"📊 Status: {result.status}")
        print(f"📄 Output: {result.output}")
        if result.error:
            print(f"❌ Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Step execution failed: {e}")
        logger.exception("Full step execution error:")

if __name__ == "__main__":
    asyncio.run(debug_step_execution())