#!/usr/bin/env python3
"""
Business Validation Test with Detailed Document Search Queries
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

# Import orchestrator integration
from orchestrator_integration import OrchestratorIntegration

async def main():
    """Run V2-only business validation with detailed document queries"""
    print("🚀 V2-Only Business Validation Test - Detailed Document Queries")
    print("=" * 70)
    
    # Initialize integration - V2 ONLY
    integration = OrchestratorIntegration(confidence_threshold=0.3)
    session_id = f"detailed_validation_{int(time.time())}"
    
    # Use pre-uploaded document
    doc_name = "riskandfinace.pdf"
    
    # Define detailed business validation questions with explicit tool instructions
    questions = [
        "Please search within the uploaded document riskandfinace.pdf using the search_uploaded_docs tool to find information about finance. Extract the document's definition and explanation of finance from the PDF content.",
        
        "Use document search tools to analyze the riskandfinace.pdf file and find information about risk. Search the uploaded document content (not knowledge base) and provide what this specific document says about risk.",
        
        "Search the riskandfinace.pdf document using search_uploaded_docs tool to compare finance and risk. Use the document content to explain the differences between finance and risk as described in this uploaded PDF file."
    ]
    
    results = []
    
    print(f"🎯 Running {len(questions)} detailed document search questions...")
    print(f"📁 Using document: {doc_name}")
    
    # Ask each detailed question
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/{len(questions)} ---")
        print(f"🤔 Question: {question[:100]}...")
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
            print(f"📝 Answer: {str(test_result['answer'])[:200]}...")
            
            # Show execution details
            if result.get('execution_summary'):
                summary = result['execution_summary']
                print(f"📊 Execution: {summary.get('completed', 0)}/{summary.get('total_steps', 0)} steps")
                if 'step_details' in summary:
                    for step_id, details in summary['step_details'].items():
                        print(f"   - {step_id}: {details.get('status', 'unknown')}")
            
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
    
    # Generate summary
    print("\n" + "=" * 70)
    print("📊 DETAILED QUERY VALIDATION RESULTS")
    print("=" * 70)
    
    # Calculate summary stats
    total_questions = len(results)
    successful = len([r for r in results if r["status"] == "success"])
    avg_response_time = sum(r["response_time"] for r in results) / total_questions if total_questions > 0 else 0
    avg_confidence = sum(r["confidence_score"] for r in results if r["confidence_score"] > 0) / max(1, len([r for r in results if r["confidence_score"] > 0]))
    
    v2_responses = len([r for r in results if r.get("orchestrator_version") == "2.0"])
    
    print(f"📋 Total Questions: {total_questions}")
    print(f"✅ Successful Responses: {successful}/{total_questions} ({successful/total_questions*100:.1f}%)")
    print(f"⏱️  Average Response Time: {avg_response_time:.2f} seconds")
    print(f"🎯 Average Confidence Score: {avg_confidence:.2f}")
    print(f"🆕 Orchestrator 2.0 Usage: {v2_responses}/{total_questions} ({v2_responses/total_questions*100:.1f}%)")
    
    print(f"\n💾 Results summary complete!")
    print(f"🎉 Detailed Query Validation Complete!")

if __name__ == "__main__":
    asyncio.run(main())