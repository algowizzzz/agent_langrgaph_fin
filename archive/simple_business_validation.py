#!/usr/bin/env python3
"""
Simple Business Validation Test for Orchestrator 2.0
Tests with pre-uploaded riskandfinace.pdf document
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

# Import orchestrator integration
from orchestrator_integration import OrchestratorIntegration

async def main():
    """Run simple business validation"""
    print("🚀 Simple Business Validation Test for Orchestrator 2.0")
    print("=" * 60)
    
    # Initialize integration
    integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
    session_id = f"business_validation_{int(time.time())}"
    
    # Use pre-uploaded document (assuming it exists in document store)
    doc_name = "riskandfinace.pdf"
    
    # Define business validation questions
    questions = [
        "What is finance?",
        "What is risk?", 
        "What is the difference between finance and risk?",
    ]
    
    results = []
    
    print(f"🎯 Running {len(questions)} business validation questions...")
    print(f"📁 Using document: {doc_name}")
    
    # Ask each question
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/{len(questions)} ---")
        print(f"🤔 Question: {question}")
        print("⏳ Processing...")
        
        start_time = time.time()
        
        try:
            result = await integration.run(
                user_query=question,
                session_id=session_id,
                active_documents=[doc_name]
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Record result
            test_result = {
                "question": question,
                "response_time": response_time,
                "status": result.get("status", "unknown"),
                "answer": result.get("final_answer", "No answer provided"),
                "confidence_score": result.get("confidence_score", 0),
                "orchestrator_version": result.get("orchestrator_version", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(test_result)
            
            print(f"✅ Response received in {response_time:.2f}s")
            print(f"🎯 Confidence: {test_result['confidence_score']:.2f}")
            print(f"🔧 Version: {test_result['orchestrator_version']}")
            print(f"📝 Answer: {test_result['answer'][:200]}...")
            
        except Exception as e:
            error_result = {
                "question": question,
                "response_time": time.time() - start_time,
                "status": "error",
                "answer": f"Error: {str(e)}",
                "confidence_score": 0,
                "orchestrator_version": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            
            results.append(error_result)
            print(f"❌ Error: {str(e)}")
        
        # Small delay between questions
        await asyncio.sleep(2)
    
    # Generate markdown results
    print("\n" + "=" * 60)
    print("📊 BUSINESS VALIDATION RESULTS")
    print("=" * 60)
    
    # Calculate summary stats
    total_questions = len(results)
    successful = len([r for r in results if r["status"] == "success"])
    avg_response_time = sum(r["response_time"] for r in results) / total_questions if total_questions > 0 else 0
    avg_confidence = sum(r["confidence_score"] for r in results if r["confidence_score"] > 0) / max(1, len([r for r in results if r["confidence_score"] > 0]))
    
    v2_responses = len([r for r in results if r.get("orchestrator_version") == "2.0"])
    v1_responses = len([r for r in results if r.get("orchestrator_version") == "1.0"])
    
    print(f"📋 Total Questions: {total_questions}")
    print(f"✅ Successful Responses: {successful}/{total_questions} ({successful/total_questions*100:.1f}%)")
    print(f"⏱️  Average Response Time: {avg_response_time:.2f} seconds")
    print(f"🎯 Average Confidence Score: {avg_confidence:.2f}")
    print(f"🆕 Orchestrator 2.0 Usage: {v2_responses}/{total_questions} ({v2_responses/total_questions*100:.1f}%)")
    print(f"🔄 Orchestrator 1.0 Fallback: {v1_responses}/{total_questions} ({v1_responses/total_questions*100:.1f}%)")
    
    # Create markdown content
    markdown_content = f"""# 📋 Business Validation Results - Orchestrator 2.0

**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Session ID:** {session_id}  
**Document:** riskandfinace.pdf  

## 📊 Summary Statistics

- **Total Questions:** {total_questions}
- **Successful Responses:** {successful}/{total_questions} ({successful/total_questions*100:.1f}%)
- **Average Response Time:** {avg_response_time:.2f} seconds
- **Average Confidence Score:** {avg_confidence:.2f}
- **Orchestrator 2.0 Usage:** {v2_responses}/{total_questions} ({v2_responses/total_questions*100:.1f}%)
- **Orchestrator 1.0 Fallback:** {v1_responses}/{total_questions} ({v1_responses/total_questions*100:.1f}%)

## 🎯 Test Results

"""

    for i, result in enumerate(results, 1):
        status_emoji = "✅" if result["status"] == "success" else "❌"
        version_info = f"v{result['orchestrator_version']}" if result['orchestrator_version'] != "unknown" else "unknown"
        
        markdown_content += f"""### {i}. {result['question']}

**Status:** {status_emoji} {result['status'].upper()}  
**Response Time:** {result['response_time']:.2f}s  
**Confidence Score:** {result['confidence_score']:.2f}  
**Orchestrator Version:** {version_info}  

**Answer:**
{result['answer']}

---

"""

    markdown_content += f"""
## 💡 Business Validation Assessment

### ✅ Key Findings
- **System Performance:** {'Excellent' if avg_response_time < 5 else 'Good' if avg_response_time < 10 else 'Needs Improvement'}
- **Response Quality:** {'High' if avg_confidence > 0.8 else 'Medium' if avg_confidence > 0.6 else 'Low'}
- **Reliability:** {'High' if successful/total_questions > 0.9 else 'Medium' if successful/total_questions > 0.7 else 'Low'}
- **V2 Adoption:** {'High' if v2_responses/total_questions > 0.8 else 'Medium' if v2_responses/total_questions > 0.5 else 'Low'}

### 🎯 Production Readiness Score
**Overall Score:** {(avg_confidence * 0.4 + (successful/total_questions) * 0.3 + (v2_responses/total_questions) * 0.2 + (1 if avg_response_time < 10 else 0.5) * 0.1) * 100:.1f}/100

---
*Generated by Simple Business Validation Test Suite*
"""

    # Save results
    output_file = "business_validation_results.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"🎉 Business Validation Complete!")

if __name__ == "__main__":
    asyncio.run(main())