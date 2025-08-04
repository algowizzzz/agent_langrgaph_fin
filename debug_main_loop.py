#!/usr/bin/env python3
"""Debug script to trace the main execution loop."""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, Set

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath('.'))

from orchestrator_integration import OrchestratorIntegration
from orchestrator_v2.planning_engine_enhanced import PlanningContext, PlanningStrategy

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_main_loop():
    """Debug the main execution loop behavior."""
    print("🔍 Debugging Main Execution Loop")
    print("=" * 60)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    orchestrator = integration.orchestrator_v2
    
    # Create planning context
    context = PlanningContext(
        user_query="What is risk?",
        session_id="debug_session",
        active_documents=["riskandfinace.pdf"],
        available_tools=list(orchestrator.tool_registry._tools.keys())
    )
    
    # Create execution plan
    print("🧠 Creating execution plan...")
    plan = await orchestrator.planning_engine.create_execution_plan(context, PlanningStrategy.ADAPTIVE)
    
    if not plan:
        print("❌ No plan created!")
        return
        
    print(f"✅ Plan created: {plan.plan_id}")
    print(f"📊 Total steps: {len(plan.steps)}")
    print()
    
    # Initialize execution state (mimicking the main loop)
    completed_steps = set()
    failed_steps = set()
    running_steps = set()
    
    print("🚀 Starting Main Execution Loop Simulation...")
    print("-" * 50)
    
    iteration = 0
    max_iterations = 10  # Safety limit
    
    while len(completed_steps) + len(failed_steps) < len(plan.steps) and iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 Loop Iteration {iteration}")
        
        # Get executable steps
        executable_steps = plan.get_executable_steps(completed_steps, failed_steps)
        print(f"📈 Executable steps: {executable_steps}")
        
        # Filter out already running steps
        executable_steps = [s for s in executable_steps if s not in running_steps]
        print(f"📋 After filtering running: {executable_steps}")
        
        if not executable_steps:
            if running_steps:
                print(f"⏳ Waiting for running steps: {running_steps}")
                await asyncio.sleep(0.1)
                continue
            else:
                print("❌ No executable or running steps - execution stuck!")
                break
        
        # Execute the first step
        step_id = executable_steps[0]
        print(f"🚀 Executing step: {step_id}")
        
        running_steps.add(step_id)
        step = plan.steps[step_id]
        
        try:
            # Execute the step
            result = await orchestrator.execution_engine._execute_step(step)
            print(f"📊 Step result: Status={result.status}, Time={result.execution_time:.3f}s")
            
            if result.output:
                print(f"📄 Output preview: {str(result.output)[:200]}...")
            
            if result.error:
                print(f"❌ Error: {result.error}")
            
            # Process result (mimicking main loop logic)
            orchestrator.execution_engine.execution_results[step_id] = result
            
            if result.status.value == 'completed':  # ExecutionStatus.COMPLETED
                completed_steps.add(step_id)
                orchestrator.execution_engine.step_outputs[step_id] = result.output
                print(f"✅ Step '{step_id}' marked as COMPLETED")
                print(f"🗃️  Added to step_outputs with key: {step_id}")
            else:
                failed_steps.add(step_id)
                print(f"❌ Step '{step_id}' marked as FAILED")
                
            running_steps.remove(step_id)
            
        except Exception as e:
            print(f"💥 Exception executing step '{step_id}': {e}")
            failed_steps.add(step_id)
            running_steps.remove(step_id)
    
    print(f"\n🎯 Final Results:")
    print(f"   Completed: {completed_steps}")
    print(f"   Failed: {failed_steps}")
    print(f"   Running: {running_steps}")
    print(f"   Total iterations: {iteration}")
    
    # Test if second step can now execute
    if len(completed_steps) > 0:
        print(f"\n🔍 Testing if dependent steps can now execute...")
        final_executable = plan.get_executable_steps(completed_steps, failed_steps)
        print(f"📈 Now executable: {final_executable}")

if __name__ == "__main__":
    asyncio.run(debug_main_loop())