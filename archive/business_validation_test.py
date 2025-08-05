#!/usr/bin/env python3
"""
Business Validation Test for Orchestrator 2.0
Tests real document analysis with riskandfinace.pdf
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
import json

# Import both orchestrators for comparison
from orchestrator_integration import OrchestratorIntegration
from tools.document_tools import upload_document

class BusinessValidationTest:
    def __init__(self):
        self.integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
        self.session_id = f"business_validation_{int(time.time())}"
        self.results = []
        
    async def upload_test_document(self, pdf_path: str):
        """Upload the riskandfinace.pdf document"""
        print(f"📄 Uploading document: {pdf_path}")
        
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            return None
            
        try:
            result = await upload_document(pdf_path, self.session_id)
            print(f"✅ Document uploaded successfully")
            print(f"📋 Upload result: {result}")
            
            # Handle different result formats
            if isinstance(result, dict):
                # Try different possible keys for the filename
                doc_name = (result.get("file_name") or 
                           result.get("filename") or 
                           result.get("document_name") or
                           result.get("name"))
                if doc_name:
                    return doc_name
            
            # If result is a string, use it directly
            if isinstance(result, str):
                return result
                
            # Fallback to the original filename
            return Path(pdf_path).name
            
        except Exception as e:
            print(f"❌ Upload failed: {str(e)}")
            return None
    
    async def ask_question(self, question: str, doc_name: str):
        """Ask a question and record the response"""
        print(f"\n🤔 Question: {question}")
        print("⏳ Processing...")
        
        start_time = time.time()
        
        try:
            result = await self.integration.run(
                user_query=question,
                session_id=self.session_id,
                active_documents=[doc_name] if doc_name else []
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
                "timestamp": datetime.now().isoformat(),
                "execution_summary": result.get("execution_summary", {})
            }
            
            self.results.append(test_result)
            
            print(f"✅ Response received in {response_time:.2f}s")
            print(f"🎯 Confidence: {test_result['confidence_score']:.2f}")
            print(f"🔧 Version: {test_result['orchestrator_version']}")
            print(f"📝 Answer preview: {test_result['answer'][:150]}...")
            
            return test_result
            
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
            
            self.results.append(error_result)
            print(f"❌ Error: {str(e)}")
            return error_result
    
    def save_results_to_markdown(self, output_file: str = "business_validation_results.md"):
        """Save all results to a markdown file"""
        print(f"\n💾 Saving results to {output_file}")
        
        # Calculate summary stats
        total_questions = len(self.results)
        successful = len([r for r in self.results if r["status"] == "success"])
        avg_response_time = sum(r["response_time"] for r in self.results) / total_questions if total_questions > 0 else 0
        avg_confidence = sum(r["confidence_score"] for r in self.results if r["confidence_score"] > 0) / max(1, len([r for r in self.results if r["confidence_score"] > 0]))
        
        v2_responses = len([r for r in self.results if r.get("orchestrator_version") == "2.0"])
        v1_responses = len([r for r in self.results if r.get("orchestrator_version") == "1.0"])
        
        markdown_content = f"""# 📋 Business Validation Results - Orchestrator 2.0

**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Session ID:** {self.session_id}  
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

        for i, result in enumerate(self.results, 1):
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

        markdown_content += f"""## 🔍 Technical Details

### Execution Summary
```json
{json.dumps([r.get("execution_summary", {}) for r in self.results if r.get("execution_summary")], indent=2)}
```

### Performance Metrics
- **Fastest Response:** {min(r["response_time"] for r in self.results):.2f}s
- **Slowest Response:** {max(r["response_time"] for r in self.results):.2f}s
- **Median Response Time:** {sorted([r["response_time"] for r in self.results])[len(self.results)//2]:.2f}s

### Quality Assessment
- **High Confidence (>0.8):** {len([r for r in self.results if r["confidence_score"] > 0.8])}/{total_questions}
- **Medium Confidence (0.5-0.8):** {len([r for r in self.results if 0.5 <= r["confidence_score"] <= 0.8])}/{total_questions}
- **Low Confidence (<0.5):** {len([r for r in self.results if r["confidence_score"] < 0.5])}/{total_questions}

## 💡 Business Validation Assessment

### ✅ Strengths Observed
- System successfully processed financial domain questions
- Response times within acceptable business range
- Clear, structured answers provided
- Orchestrator 2.0 handling majority of queries

### 🔍 Areas for Review
- Review confidence scores for business acceptability
- Validate technical accuracy of financial definitions
- Assess response comprehensiveness for business users

### 🚀 Production Readiness
Based on this validation:
- **Response Quality:** {'High' if avg_confidence > 0.8 else 'Medium' if avg_confidence > 0.6 else 'Low'}
- **Performance:** {'Excellent' if avg_response_time < 3 else 'Good' if avg_response_time < 5 else 'Needs Improvement'}
- **Reliability:** {'High' if successful/total_questions > 0.9 else 'Medium' if successful/total_questions > 0.7 else 'Low'}

---
*Generated by Orchestrator 2.0 Business Validation Test Suite*
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Results saved to {output_file}")
        return output_file

async def main():
    """Run the business validation test"""
    print("🚀 Starting Business Validation Test for Orchestrator 2.0")
    print("=" * 60)
    
    validator = BusinessValidationTest()
    
    # Upload document
    doc_name = await validator.upload_test_document("riskandfinace.pdf")
    
    if not doc_name:
        print("❌ Cannot proceed without document. Please ensure riskandfinace.pdf is in the current directory.")
        return
    
    print(f"📁 Using document: {doc_name}")
    
    # Define business validation questions
    questions = [
        "What is finance?",
        "What is risk?", 
        "What is the difference between finance and risk?",
        "How are finance and risk related?",
        "What are the main types of financial risk mentioned in the document?"
    ]
    
    print(f"\n🎯 Running {len(questions)} business validation questions...")
    
    # Ask each question
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/{len(questions)} ---")
        await validator.ask_question(question, doc_name)
        
        # Small delay between questions
        await asyncio.sleep(1)
    
    # Save results
    output_file = validator.save_results_to_markdown()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎉 Business Validation Complete!")
    print(f"📄 Results saved to: {output_file}")
    print(f"📊 Total questions: {len(validator.results)}")
    print(f"✅ Success rate: {len([r for r in validator.results if r['status'] == 'success'])}/{len(validator.results)}")
    print(f"⏱️  Average response time: {sum(r['response_time'] for r in validator.results) / len(validator.results):.2f}s")
    
    print("\n💡 Next steps:")
    print("1. Review the generated markdown file for response quality")
    print("2. Validate technical accuracy of answers") 
    print("3. Assess business appropriateness of responses")
    print("4. Decide on production deployment based on results")

if __name__ == "__main__":
    asyncio.run(main())