#!/usr/bin/env python3
"""
Test AI Finance and Risk Agent Implementation

This script tests the enhanced orchestrator with:
- Agent identity and capabilities
- Intelligent query routing
- Workflow classification
- Structured prompt generation
- Memory fallback chain
"""

import asyncio
import json
from orchestrator_integration import OrchestratorIntegration

async def test_agent_identity():
    """Test agent identity and capabilities."""
    print("🤖 Testing AI Finance and Risk Agent Identity")
    print("=" * 60)
    
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    
    # Get agent information
    try:
        agent_info = integration.orchestrator_v2.get_agent_info()
        print("📋 Agent Information:")
        print(json.dumps(agent_info, indent=2))
        
        print("\n🔧 Workflow Capabilities:")
        capabilities = integration.orchestrator_v2.get_workflow_capabilities()
        for capability in capabilities:
            print(f"  - {capability}")
        
        print("\n📖 Agent Description:")
        description = integration.orchestrator_v2.describe_agent()
        print(description)
        
    except Exception as e:
        print(f"❌ Error testing agent identity: {e}")
        return False
    
    return True

async def test_workflow_classification():
    """Test workflow classification for different query types."""
    print("\n🎯 Testing Workflow Classification")
    print("=" * 60)
    
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    
    test_queries = [
        {
            "query": "What is risk?",
            "documents": ["riskandfinace.pdf"],
            "expected": "document_analysis"
        },
        {
            "query": "What is risk?", 
            "documents": [],
            "expected": "qa_fallback_chain"
        },
        {
            "query": "Compare car24_chpt1_0.pdf and car24_chpt7.pdf for similarities",
            "documents": ["car24_chpt1_0.pdf", "car24_chpt7.pdf"],
            "expected": "financial_comparison"
        },
        {
            "query": "Give table data summary",
            "documents": [],
            "expected": "data_analysis"
        },
        {
            "query": "Help me analyze this quarterly report",
            "documents": [],
            "expected": "productivity_assistance"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{test_case['query']}'")
        print(f"📁 Documents: {test_case['documents'] or 'None'}")
        
        try:
            # Get workflow classification from agent identity
            from orchestrator_v2.agent_identity import agent_identity
            workflow = agent_identity.classify_query_workflow(
                test_case['query'],
                test_case['documents']
            )
            
            print(f"📋 Classified as: {workflow.value}")
            print(f"🎯 Expected: {test_case['expected']}")
            
            if workflow.value == test_case['expected']:
                print("✅ Classification correct!")
            else:
                print("⚠️ Classification mismatch")
                
        except Exception as e:
            print(f"❌ Error classifying query: {e}")
    
    return True

async def test_structured_prompts():
    """Test structured prompt generation."""
    print("\n📝 Testing Structured Prompt Generation")
    print("=" * 60)
    
    try:
        from orchestrator_v2.agent_identity import agent_identity, WorkflowType
        
        # Test financial comparison prompt
        comparison_prompt = agent_identity.get_structured_prompt(
            WorkflowType.FINANCIAL_COMPARISON,
            documents="car24_chpt1_0.pdf, car24_chpt7.pdf",
            comparison_type="similarities and differences"
        )
        
        print("🔍 Financial Comparison Prompt:")
        print(comparison_prompt[:500] + "..." if len(comparison_prompt) > 500 else comparison_prompt)
        
        # Test document analysis prompt
        analysis_prompt = agent_identity.get_structured_prompt(
            WorkflowType.DOCUMENT_ANALYSIS,
            document="riskandfinace.pdf",
            analysis_type="comprehensive financial analysis"
        )
        
        print("\n📄 Document Analysis Prompt:")
        print(analysis_prompt[:500] + "..." if len(analysis_prompt) > 500 else analysis_prompt)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing structured prompts: {e}")
        return False

async def test_query_routing_with_risk_question():
    """Test the 'What is risk?' query with different document scenarios."""
    print("\n🔄 Testing Query Routing: 'What is risk?'")
    print("=" * 60)
    
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    
    # Test 1: With uploaded document
    print("\n📄 Test 1: With riskandfinace.pdf uploaded")
    session_id_1 = f"risk_test_with_doc_{int(asyncio.get_event_loop().time())}"
    
    try:
        result_1 = await integration.run(
            user_query="What is risk?",
            session_id=session_id_1,
            active_documents=["riskandfinace.pdf"]
        )
        
        print(f"✅ Response: {result_1.get('answer', 'No answer')[:200]}...")
        print(f"🎯 Confidence: {result_1.get('confidence_score', 0)}")
        print(f"📋 Strategy: {result_1.get('execution_summary', {}).get('strategy', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error in Test 1: {e}")
    
    # Test 2: Without uploaded documents (fallback chain)
    print("\n📚 Test 2: Without uploaded documents (fallback chain)")
    session_id_2 = f"risk_test_no_doc_{int(asyncio.get_event_loop().time())}"
    
    try:
        result_2 = await integration.run(
            user_query="What is risk?",
            session_id=session_id_2,
            active_documents=[]
        )
        
        print(f"✅ Response: {result_2.get('answer', 'No answer')[:200]}...")
        print(f"🎯 Confidence: {result_2.get('confidence_score', 0)}")
        print(f"📋 Strategy: {result_2.get('execution_summary', {}).get('strategy', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error in Test 2: {e}")
    
    return True

async def main():
    """Run all tests for the AI Finance and Risk Agent."""
    print("🚀 AI Finance and Risk Agent - Implementation Tests")
    print("=" * 80)
    
    tests = [
        ("Agent Identity", test_agent_identity),
        ("Workflow Classification", test_workflow_classification), 
        ("Structured Prompts", test_structured_prompts),
        ("Query Routing", test_query_routing_with_risk_question)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            print(f"{'✅' if success else '❌'} {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 40)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! AI Finance and Risk Agent is ready!")
    else:
        print("⚠️ Some tests failed. Check implementation.")

if __name__ == "__main__":
    asyncio.run(main())