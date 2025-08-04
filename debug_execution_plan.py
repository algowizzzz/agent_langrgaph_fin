#!/usr/bin/env python3
"""Debug script to inspect execution plan creation and step execution."""

import asyncio
import sys
import os
from typing import Dict, Any, List

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath('.'))

from orchestrator_integration import OrchestratorIntegration

async def debug_execution_plan():
    """Debug the execution plan creation and step analysis."""
    print("🔍 Debugging Execution Plan Creation")
    print("=" * 60)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    
    # Test simple query
    query = "What is risk?"
    active_documents = ["riskandfinace.pdf"]
    
    print(f"📝 Query: '{query}'")
    print(f"📁 Documents: {active_documents}")
    print()
    
    # Get the orchestrator 
    orchestrator = integration.orchestrator_v2
    
    # Create planning context
    from orchestrator_v2.planning_engine_enhanced import PlanningContext
    context = PlanningContext(
        user_query=query,
        session_id="debug_session",
        active_documents=active_documents,
        available_tools=list(orchestrator.tool_registry._tools.keys())
    )
    
    # Create execution plan
    print("🧠 Creating execution plan...")
    from orchestrator_v2.planning_engine_enhanced import PlanningStrategy
    plan = await orchestrator.planning_engine.create_execution_plan(context, PlanningStrategy.ADAPTIVE)
    
    if not plan:
        print("❌ No plan created!")
        return
        
    print(f"✅ Plan created: {plan.plan_id}")
    print(f"📊 Total steps: {len(plan.steps)}")
    print()
    
    # Analyze each step
    print("🔍 Step Analysis:")
    print("-" * 40)
    
    for step_id, step in plan.steps.items():
        print(f"📋 Step: {step_id}")
        print(f"   🔧 Tool: {step.tool_name}")
        print(f"   📝 Description: {step.description}")
        print(f"   🔗 Dependencies: {step.dependencies}")
        print(f"   ⚡ Condition: {step.condition}")
        print(f"   📄 Condition Expression: {step.condition_expression}")
        print(f"   🔢 Parameters: {step.parameters}")
        
        # Test if step can execute initially
        can_execute = step.can_execute(set(), set())
        print(f"   ✅ Can Execute Initially: {can_execute}")
        
        if not can_execute and step.dependencies:
            print(f"   ⚠️  Blocked by dependencies: {step.dependencies}")
        elif not can_execute:
            print(f"   ⚠️  Blocked by condition: {step.condition} / {step.condition_expression}")
        print()
    
    # Test executable steps
    print("🚀 Executable Steps Analysis:")
    print("-" * 40)
    
    executable_steps = plan.get_executable_steps(set(), set())
    print(f"📈 Initially executable steps: {executable_steps}")
    
    if not executable_steps:
        print("❌ No steps can execute initially!")
        print("🔍 Checking why each step is blocked:")
        
        for step_id, step in plan.steps.items():
            print(f"   {step_id}: Dependencies={step.dependencies}, Condition={step.condition}")
            
            # Test dependency blocking
            if step.dependencies:
                for dep in step.dependencies:
                    if dep not in set() and dep not in set():
                        print(f"      ❌ Blocked by dependency: {dep}")
            else:
                print(f"      ✅ No dependency issues")
                
            # Test condition blocking  
            if step.condition != "always" and hasattr(step, 'condition_expression'):
                print(f"      🔍 Condition check: {step.condition} / {step.condition_expression}")
    
    print()
    print("🎯 Summary:")
    print(f"   Total Steps: {len(plan.steps)}")
    print(f"   Executable: {len(executable_steps)}")
    print(f"   Plan Valid: {plan.validate()[0]}")

if __name__ == "__main__":
    asyncio.run(debug_execution_plan())