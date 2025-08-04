#!/usr/bin/env python3
"""
FIXED test script that uses actual available documents with correct names.
"""

import asyncio
import time
from datetime import datetime
from orchestrator_integration import OrchestratorIntegration

async def test_fixed_core_functionality():
    """Test with actual available documents."""
    
    print("🧪 FIXED CORE FUNCTIONALITY TEST")
    print("=" * 50)
    
    integration = OrchestratorIntegration()
    
    # Use actual document names from the store
    available_docs = {
        "risk_pdf": "riskandfinace.pdf",  # This exists and works!
        "car24_chpt1": "20250801_231927_e702b3a7-5cbd-4557-b46b-9d352384f3ac_car24_chpt1_0.pdf",
        "car24_chpt7": "20250801_231934_cb90fddd-c3b9-4a48-8bba-d55d28f0a3b0_car24_chpt7.pdf"
    }
    
    results = []
    
    # Test 1: Document Q&A with REAL document
    print("\n📄 Test 1: Document Q&A (REAL DOCUMENT)")
    print("-" * 40)
    
    query1 = "What are the main types of financial risk mentioned in this document?"
    doc1 = available_docs["risk_pdf"]
    
    print(f"📝 Query: {query1}")
    print(f"📁 Document: {doc1}")
    
    start_time = time.time()
    result1 = await integration.orchestrator_v2.execute_query(
        user_query=query1,
        session_id="fixed_test_session_1",
        active_documents=[doc1]
    )
    time1 = time.time() - start_time
    
    answer1 = result1.get('final_answer', 'No answer')
    confidence1 = result1.get('confidence_score', 0)
    steps1 = result1.get('execution_summary', {})
    
    print(f"⏱️  Time: {time1:.1f}s")
    print(f"🎯 Confidence: {confidence1:.3f}")
    print(f"⚡ Steps: {steps1.get('completed', 0)}/{steps1.get('total', 0)}")
    
    # Check if it's a good response
    has_finance_content = any(word in answer1.lower() for word in ['risk', 'financial', 'market', 'credit', 'liquidity'])
    is_synthesis = len(answer1) > 200 and not answer1.startswith('[{')
    
    test1_success = has_finance_content and is_synthesis and confidence1 > 0.7
    print(f"📄 Result: {'✅ GOOD SYNTHESIS' if test1_success else '❌ POOR/RAW'}")
    print(f"📊 Length: {len(answer1)} chars")
    print(f"📖 Preview: {answer1[:200]}...")
    
    results.append({
        "test": "Document Q&A",
        "success": test1_success,
        "confidence": confidence1,
        "time": time1,
        "answer_length": len(answer1),
        "preview": answer1[:300]
    })
    
    # Test 2: Knowledge Base Fallback 
    print("\n❓ Test 2: Knowledge Fallback (NO DOCUMENTS)")
    print("-" * 40)
    
    query2 = "What is portfolio diversification and why is it important in finance?"
    
    print(f"📝 Query: {query2}")
    print(f"📁 Documents: None (testing fallback)")
    
    start_time = time.time()
    result2 = await integration.orchestrator_v2.execute_query(
        user_query=query2,
        session_id="fixed_test_session_2",
        active_documents=None
    )
    time2 = time.time() - start_time
    
    answer2 = result2.get('final_answer', 'No answer')
    confidence2 = result2.get('confidence_score', 0)
    steps2 = result2.get('execution_summary', {})
    
    print(f"⏱️  Time: {time2:.1f}s")
    print(f"🎯 Confidence: {confidence2:.3f}")
    print(f"⚡ Steps: {steps2.get('completed', 0)}/{steps2.get('total', 0)}")
    
    # Check if it's a helpful knowledge response
    has_diversification_content = any(word in answer2.lower() for word in ['diversification', 'portfolio', 'risk', 'investment'])
    is_helpful = len(answer2) > 200 and 'sorry' not in answer2.lower()[:100]
    
    test2_success = has_diversification_content and is_helpful and confidence2 > 0.7
    print(f"📄 Result: {'✅ HELPFUL KNOWLEDGE' if test2_success else '❌ ERROR/APOLOGY'}")
    print(f"📊 Length: {len(answer2)} chars")
    print(f"📖 Preview: {answer2[:200]}...")
    
    results.append({
        "test": "Knowledge Fallback",
        "success": test2_success,
        "confidence": confidence2,
        "time": time2,
        "answer_length": len(answer2),
        "preview": answer2[:300]
    })
    
    # Test 3: Multi-Document Analysis with REAL documents
    print("\n🔍 Test 3: Multi-Document Analysis (REAL DOCUMENTS)")
    print("-" * 40)
    
    query3 = "Compare the content and focus of these two documents"
    docs3 = [available_docs["car24_chpt1"], available_docs["car24_chpt7"]]
    
    print(f"📝 Query: {query3}")
    print(f"📁 Documents: 2 car24 chapters")
    
    start_time = time.time()
    result3 = await integration.orchestrator_v2.execute_query(
        user_query=query3,
        session_id="fixed_test_session_3",
        active_documents=docs3
    )
    time3 = time.time() - start_time
    
    answer3 = result3.get('final_answer', 'No answer')
    confidence3 = result3.get('confidence_score', 0)
    steps3 = result3.get('execution_summary', {})
    
    print(f"⏱️  Time: {time3:.1f}s")
    print(f"🎯 Confidence: {confidence3:.3f}")
    print(f"⚡ Steps: {steps3.get('completed', 0)}/{steps3.get('total', 0)}")
    
    # Check if it's a comparison
    has_comparison = any(word in answer3.lower() for word in ['compare', 'both', 'difference', 'similar', 'contrast'])
    is_substantial = len(answer3) > 300
    
    test3_success = has_comparison and is_substantial and confidence3 > 0.7
    print(f"📄 Result: {'✅ GOOD COMPARISON' if test3_success else '❌ POOR/FAILED'}")
    print(f"📊 Length: {len(answer3)} chars")
    print(f"📖 Preview: {answer3[:200]}...")
    
    results.append({
        "test": "Multi-Document Analysis",
        "success": test3_success,
        "confidence": confidence3,
        "time": time3,
        "answer_length": len(answer3),
        "preview": answer3[:300]
    })
    
    # Final Assessment
    print(f"\n📊 FINAL ASSESSMENT")
    print("=" * 40)
    
    success_count = sum(1 for r in results if r["success"])
    total_tests = len(results)
    success_rate = (success_count / total_tests) * 100
    avg_confidence = sum(r["confidence"] for r in results) / total_tests
    avg_time = sum(r["time"] for r in results) / total_tests
    
    for i, result in enumerate(results, 1):
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"{i}. {result['test']}: {status} ({result['confidence']:.3f} confidence)")
    
    print(f"\n🎯 SUCCESS RATE: {success_count}/{total_tests} = {success_rate:.1f}%")
    print(f"⏱️  AVERAGE TIME: {avg_time:.1f}s")
    print(f"🎯 AVERAGE CONFIDENCE: {avg_confidence:.3f}")
    
    if success_rate >= 100:
        print("🎉 PERFECT! ALL CORE FUNCTIONALITY WORKING!")
    elif success_rate >= 80:
        print("✅ EXCELLENT! Core functionality is production-ready!")
    elif success_rate >= 60:
        print("⚠️  GOOD! Most functionality working, minor issues remain.")
    else:
        print("🚨 NEEDS WORK! Major functionality issues detected.")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fixed_core_test_results_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(f"# Fixed Core Functionality Test Results\n\n")
        f.write(f"**Test Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Success Rate:** {success_count}/{total_tests} = {success_rate:.1f}%\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"## Test {i}: {result['test']}\n\n")
            f.write(f"**Status:** {'✅ SUCCESS' if result['success'] else '❌ FAILED'}\n")
            f.write(f"**Confidence:** {result['confidence']:.3f}\n")
            f.write(f"**Time:** {result['time']:.1f}s\n")
            f.write(f"**Length:** {result['answer_length']} chars\n\n")
            f.write(f"**Response Preview:**\n```\n{result['preview']}\n```\n\n")
    
    print(f"\n📄 Detailed results saved to: {filename}")
    return filename

if __name__ == "__main__":
    filename = asyncio.run(test_fixed_core_functionality())