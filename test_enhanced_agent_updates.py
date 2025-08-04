#!/usr/bin/env python3
"""Test script for Enhanced AI Finance and Risk Agent with updated features."""

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

async def test_enhanced_agent_updates():
    """Test the enhanced agent with updated chunking strategy and memory search."""
    print("🧪 Testing Enhanced AI Finance and Risk Agent - Updated Features")
    print("=" * 75)
    
    # Initialize integration
    integration = OrchestratorIntegration()
    
    # Test cases covering all updated workflows
    test_cases = [
        {
            "name": "📄 Single Document Analysis",
            "query": "What is risk?",
            "documents": ["riskandfinace.pdf"],
            "expected_workflow": "document_analysis",
            "description": "Test single document workflow with direct synthesis"
        },
        {
            "name": "📊 Multi-Document Financial Comparison (10k Chunking)",
            "query": "Compare car24_chpt1_0.pdf and car24_chpt7.pdf for similarities and differences as a financial analyst",
            "documents": ["car24_chpt1_0.pdf", "car24_chpt7.pdf"],
            "expected_workflow": "financial_comparison",
            "description": "Test updated 10k word chunking strategy for multi-document analysis"
        },
        {
            "name": "🧠 Memory Search Workflow",
            "query": "Remember what we discussed about risk analysis?",
            "documents": None,
            "expected_workflow": "memory_search",
            "description": "Test new memory search workflow with conversation history"
        },
        {
            "name": "❓ Q&A Fallback Chain",
            "query": "What is financial liquidity?",
            "documents": None,
            "expected_workflow": "qa_fallback_chain",
            "description": "Test knowledge base fallback chain without documents"
        },
        {
            "name": "📈 Data Analysis Workflow",
            "query": "Give table data summary",
            "documents": ["test_business_data.csv"],
            "expected_workflow": "data_analysis",
            "description": "Test progressive data analysis workflow"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🔍 Test {i}/5: {test_case['name']}")
        print(f"📝 Query: '{test_case['query']}'")
        print(f"📁 Documents: {test_case['documents'] or 'None'}")
        print(f"🎯 Expected Workflow: {test_case['expected_workflow']}")
        print(f"📋 Description: {test_case['description']}")
        print("=" * 60)
        
        session_id = f"enhanced_test_{i}_{int(asyncio.get_event_loop().time())}"
        
        try:
            result = await integration.run(
                user_query=test_case['query'],
                session_id=session_id,
                active_documents=test_case['documents']
            )
            
            # Extract key information
            success = result.get('status') == 'success'
            answer = result.get('final_answer', result.get('answer', 'No answer provided'))
            confidence = result.get('confidence_score', 0)
            execution_summary = result.get('execution_summary', {})
            
            # Extract workflow information from metadata
            query_type = result.get('query_type', 'unknown')
            workflow_info = f"Type: {query_type}"
            
            print(f"📊 Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"🎯 Confidence: {confidence:.3f}")
            print(f"📋 Workflow: {workflow_info}")
            print(f"⚡ Steps: {execution_summary.get('total_steps', 0)} total, {execution_summary.get('completed', 0)} completed")
            
            if answer and answer != "No answer provided" and len(answer) > 50:
                print(f"✅ Response Generated:")
                print(f"📄 Preview: {answer[:150]}...")
                print(f"📏 Length: {len(answer)} characters")
                
                # Check for specific features based on test case
                if test_case['expected_workflow'] == 'financial_comparison':
                    if '10k' in str(execution_summary) or 'chunk' in answer.lower():
                        print("🔧 Chunking Strategy: ✅ 10k word chunking detected")
                    else:
                        print("🔧 Chunking Strategy: ⚠️  10k word chunking not clearly detected")
                
                elif test_case['expected_workflow'] == 'memory_search':
                    if 'memory' in answer.lower() or 'conversation' in answer.lower():
                        print("🧠 Memory Search: ✅ Memory-related response detected")
                    else:
                        print("🧠 Memory Search: ⚠️  Memory search features not clearly detected")
                
                results.append({
                    'test': test_case['name'],
                    'success': True,
                    'confidence': confidence,
                    'answer_length': len(answer),
                    'workflow': workflow_info
                })
            else:
                print(f"❌ No meaningful response generated")
                print(f"📄 Got: '{answer}'")
                results.append({
                    'test': test_case['name'],
                    'success': False,
                    'confidence': confidence,
                    'answer_length': len(answer) if answer else 0,
                    'workflow': workflow_info
                })
                
            # Log execution details
            if execution_summary:
                print(f"📈 Execution Details:")
                print(f"   Success Rate: {execution_summary.get('success_rate', 0)*100:.1f}%")
                print(f"   Execution Time: {execution_summary.get('total_execution_time', 0):.2f}s")
                if execution_summary.get('step_details'):
                    print(f"   Step Details: {len(execution_summary['step_details'])} steps logged")
                
        except Exception as e:
            print(f"💥 Test failed with exception: {e}")
            logger.exception("Test execution error:")
            results.append({
                'test': test_case['name'],
                'success': False,
                'confidence': 0,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'='*75}")
    print("📊 ENHANCED AGENT TEST SUMMARY")
    print("=" * 75)
    
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed Tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        avg_confidence = sum(r['confidence'] for r in successful_tests) / len(successful_tests)
        print(f"📈 Average Confidence: {avg_confidence:.3f}")
    
    print(f"\n🎯 Key Features Tested:")
    print(f"   📄 Document Analysis: {'✅' if any('Document Analysis' in r['test'] for r in successful_tests) else '❌'}")
    print(f"   📊 10k Word Chunking: {'✅' if any('Multi-Document' in r['test'] for r in successful_tests) else '❌'}")
    print(f"   🧠 Memory Search: {'✅' if any('Memory Search' in r['test'] for r in successful_tests) else '❌'}")
    print(f"   ❓ Q&A Fallback: {'✅' if any('Q&A Fallback' in r['test'] for r in successful_tests) else '❌'}")
    print(f"   📈 Data Analysis: {'✅' if any('Data Analysis' in r['test'] for r in successful_tests) else '❌'}")
    
    if failed_tests:
        print(f"\n⚠️  Failed Tests Details:")
        for failed in failed_tests:
            print(f"   ❌ {failed['test']}: {failed.get('error', 'No response generated')}")
    
    success_rate = len(successful_tests) / len(results) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 EXCELLENT: Enhanced agent is working well with updated features!")
    elif success_rate >= 60:
        print("✅ GOOD: Enhanced agent is functional with minor issues")
    else:
        print("⚠️  NEEDS WORK: Enhanced agent requires debugging")

if __name__ == "__main__":
    asyncio.run(test_enhanced_agent_updates())