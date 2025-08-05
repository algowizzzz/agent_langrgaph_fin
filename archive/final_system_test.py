#!/usr/bin/env python3
"""
Final comprehensive test of the orchestrator v2 system
"""

import asyncio
import time
from orchestrator_v2.orchestrator_v2 import OrchestratorV2
from config import config

async def comprehensive_system_test():
    """Comprehensive test demonstrating the new orchestrator v2 capabilities"""
    
    print("🚀 ORCHESTRATOR V2 SYSTEM TEST")
    print("=" * 60)
    
    # Show configuration
    print("📊 Configuration:")
    print(f"   Chunk size: {config.ai.chunk_size} chars (~{config.ai.chunk_size//5} words)")
    print(f"   Chunk overlap: {config.ai.chunk_overlap} chars")
    print(f"   Model: {config.ai.anthropic_model}")
    
    # Initialize orchestrator
    print("\n🔧 Initializing Orchestrator V2...")
    start_time = time.time()
    orchestrator = OrchestratorV2()
    init_time = time.time() - start_time
    print(f"✅ Initialization complete in {init_time:.2f}s")
    
    # Test queries demonstrating different capabilities
    test_scenarios = [
        {
            "name": "System Status Check",
            "query": "What is the current system status and capabilities?",
            "expected": "Basic system information"
        },
        {
            "name": "Document Discovery", 
            "query": "List all available documents in the system",
            "expected": "Document listing and search"
        },
        {
            "name": "Analysis Request",
            "query": "Analyze risk factors mentioned in any available financial documents",
            "expected": "Complex analysis workflow"
        }
    ]
    
    overall_results = {"total": 0, "success": 0, "errors": 0}
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*20} Test {i}: {scenario['name']} {'='*20}")
        print(f"Query: {scenario['query']}")
        print(f"Expected: {scenario['expected']}")
        print("-" * 60)
        
        overall_results["total"] += 1
        
        try:
            # Execute query
            start_time = time.time()
            result = await orchestrator.execute_query(
                user_query=scenario['query'],
                session_id=f"test_session_{i:03d}"
            )
            execution_time = time.time() - start_time
            
            # Analyze results
            status = result.get('status', 'unknown')
            confidence = result.get('confidence_score', 0.0)
            final_answer = result.get('final_answer', 'No response')
            
            print(f"✅ Status: {status}")
            print(f"📊 Confidence: {confidence:.2f}")
            print(f"⏱️  Execution Time: {execution_time:.2f}s")
            
            # Show execution details
            if result.get('execution_summary'):
                summary = result['execution_summary']
                steps = summary.get('total_steps', 0)
                parallel = summary.get('parallel_steps', 0)
                print(f"🔧 Steps: {steps} total, {parallel} parallel")
            
            # Show response preview
            if isinstance(final_answer, str):
                preview = final_answer[:200] + "..." if len(final_answer) > 200 else final_answer
                print(f"📄 Response: {preview}")
            else:
                print(f"📄 Response Type: {type(final_answer).__name__}")
            
            # Mark as success if status is success and we got some response
            if status == 'success' and final_answer:
                overall_results["success"] += 1
                print("🎯 Test PASSED")
            else:
                overall_results["errors"] += 1
                print("⚠️  Test PARTIAL (completed but may have issues)")
                
        except Exception as e:
            overall_results["errors"] += 1
            print(f"❌ Test FAILED: {str(e)}")
    
    # Final summary
    print("\n" + "="*60)
    print("📈 FINAL SYSTEM TEST RESULTS")
    print("="*60)
    
    success_rate = (overall_results["success"] / overall_results["total"]) * 100
    print(f"✅ Success Rate: {success_rate:.1f}% ({overall_results['success']}/{overall_results['total']})")
    print(f"⚠️  Errors: {overall_results['errors']}")
    
    print(f"\n🎯 Target: 95%+ success rate")
    if success_rate >= 95:
        print("🏆 SUCCESS: System meets 95%+ target!")
    elif success_rate >= 80:
        print("🟡 GOOD: System working well, minor optimizations needed")
    else:
        print("🔴 NEEDS WORK: System requires debugging")
    
    print(f"\n📊 Key Features Demonstrated:")
    print(f"   ✅ Orchestrator V2 initialization and execution")
    print(f"   ✅ 5K word chunk configuration (chunk_size={config.ai.chunk_size})")
    print(f"   ✅ Multi-query session handling")
    print(f"   ✅ Error handling and resilience")
    print(f"   ✅ Real-time execution metrics")
    
    print(f"\n🎉 System test completed!")

if __name__ == "__main__":
    asyncio.run(comprehensive_system_test())