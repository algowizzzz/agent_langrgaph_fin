#!/usr/bin/env python3
"""
Test script to validate core functionality fixes:
1. Document Q&A synthesis (no more raw dumps)  
2. Knowledge base fallback (helpful answers, not errors)
3. User value assessment
"""

import asyncio
import time
from orchestrator_integration import OrchestratorIntegration

async def test_core_fixes():
    """Test the core fixes for user-beneficial responses."""
    
    print("🧪 TESTING CORE FUNCTIONALITY FIXES")
    print("=" * 50)
    
    integration = OrchestratorIntegration()
    
    # Test 1: Document Q&A (should synthesize, not return raw chunks)
    print("\n📄 Test 1: Document Q&A Synthesis")
    print("-" * 30)
    
    start_time = time.time()
    result1 = await integration.orchestrator_v2.execute_query(
        user_query="What types of financial risk are mentioned in the document?",
        session_id="test_doc_qa",
        active_documents=["riskandfinace.pdf"]
    )
    time1 = time.time() - start_time
    
    answer1 = result1.get('final_answer', 'No answer')
    confidence1 = result1.get('confidence_score', 0)
    
    print(f"📝 Query: Document risk analysis")
    print(f"⏱️  Time: {time1:.1f}s")
    print(f"🎯 Confidence: {confidence1:.3f}")
    print(f"📄 Answer Type: {'✅ Synthesized' if len(answer1) > 100 and not answer1.startswith('[{') else '❌ Raw Dump'}")
    print(f"📊 Length: {len(answer1)} chars")
    print(f"📖 Preview: {answer1[:150]}...")
    
    # Test 2: Knowledge Fallback (should return helpful knowledge, not errors)
    print("\n❓ Test 2: Knowledge Base Fallback")
    print("-" * 30)
    
    start_time = time.time()
    result2 = await integration.orchestrator_v2.execute_query(
        user_query="What is financial liquidity and why is it important?",
        session_id="test_kb_fallback",
        active_documents=None  # No documents - should use LLM knowledge
    )
    time2 = time.time() - start_time
    
    answer2 = result2.get('final_answer', 'No answer')
    confidence2 = result2.get('confidence_score', 0)
    
    print(f"📝 Query: Financial concept (no documents)")
    print(f"⏱️  Time: {time2:.1f}s") 
    print(f"🎯 Confidence: {confidence2:.3f}")
    print(f"📄 Answer Type: {'✅ Helpful Knowledge' if 'liquidity' in answer2.lower() and len(answer2) > 100 else '❌ Error/Apology'}")
    print(f"📊 Length: {len(answer2)} chars")
    print(f"📖 Preview: {answer2[:150]}...")
    
    # Test 3: Multi-Document Analysis (existing working feature)
    print("\n🔍 Test 3: Multi-Document Analysis")
    print("-" * 30)
    
    start_time = time.time()
    result3 = await integration.orchestrator_v2.execute_query(
        user_query="Compare the risk topics discussed in these documents",
        session_id="test_multi_doc",
        active_documents=["riskandfinace.pdf", "car24_chpt1_0.pdf"]
    )
    time3 = time.time() - start_time
    
    answer3 = result3.get('final_answer', 'No answer')
    confidence3 = result3.get('confidence_score', 0)
    
    print(f"📝 Query: Multi-document comparison")
    print(f"⏱️  Time: {time3:.1f}s")
    print(f"🎯 Confidence: {confidence3:.3f}")
    print(f"📄 Answer Type: {'✅ Comparison Analysis' if 'compar' in answer3.lower() and len(answer3) > 100 else '❌ Failed'}")
    print(f"📊 Length: {len(answer3)} chars")
    print(f"📖 Preview: {answer3[:150]}...")
    
    # Assessment
    print("\n📊 CORE FUNCTIONALITY ASSESSMENT")
    print("=" * 50)
    
    working_features = 0
    total_features = 3
    
    # Check Document Q&A Fix
    if len(answer1) > 100 and not answer1.startswith('[{') and confidence1 > 0.5:
        print("✅ Document Q&A: FIXED - Returns synthesized answers")
        working_features += 1
    else:
        print("❌ Document Q&A: BROKEN - Still returning raw data")
    
    # Check Knowledge Fallback Fix  
    if 'liquidity' in answer2.lower() and len(answer2) > 100 and confidence2 > 0.5:
        print("✅ Knowledge Fallback: FIXED - Returns helpful knowledge")
        working_features += 1
    else:
        print("❌ Knowledge Fallback: BROKEN - Still returning errors")
    
    # Check Multi-Document (existing feature)
    if 'compar' in answer3.lower() and len(answer3) > 100 and confidence3 > 0.5:
        print("✅ Multi-Document: WORKING - Analysis functioning")
        working_features += 1
    else:
        print("⚠️  Multi-Document: DEGRADED - May have issues")
    
    # Overall Score
    success_rate = (working_features / total_features) * 100
    print(f"\n🎯 SUCCESS RATE: {working_features}/{total_features} = {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 CORE FUNCTIONALITY: PRODUCTION READY")
    elif success_rate >= 60:
        print("⚠️  CORE FUNCTIONALITY: MOSTLY WORKING") 
    else:
        print("🚨 CORE FUNCTIONALITY: NEEDS MORE FIXES")
    
    print(f"\n⏱️  Average Response Time: {(time1 + time2 + time3) / 3:.1f}s")
    print(f"🎯 Average Confidence: {(confidence1 + confidence2 + confidence3) / 3:.3f}")

if __name__ == "__main__":
    asyncio.run(test_core_fixes())