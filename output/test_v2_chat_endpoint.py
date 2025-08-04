#!/usr/bin/env python3
"""
Test V2 Chat Endpoint with Risk and Finance Document

This script tests the V2 orchestrator chat endpoint using a real risk and finance document
to validate the end-to-end improvements from Phase 1 and Phase 2 fixes.
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from pathlib import Path

class V2ChatEndpointTester:
    """Test the V2 chat endpoint with real documents."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"v2_test_{int(time.time())}"
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: dict):
        """Log a test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if details.get("response_time"):
            print(f"      Response time: {details['response_time']:.2f}s")
        if details.get("error"):
            print(f"      Error: {details['error']}")
    
    def test_server_health(self):
        """Test if the server is running."""
        print("🏥 Testing Server Health...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            success = response.status_code == 200
            
            self.log_test_result(
                "Server Health Check",
                success,
                {
                    "status_code": response.status_code,
                    "response": response.text if not success else "OK"
                }
            )
            return success
            
        except requests.RequestException as e:
            self.log_test_result(
                "Server Health Check",
                False,
                {"error": str(e)}
            )
            return False
    
    def upload_risk_finance_document(self):
        """Upload a risk and finance document for testing."""
        print("📄 Uploading Risk and Finance Document...")
        
        # Use one of the available risk and finance PDFs
        doc_path = "global_uploads/20250801_231832_2f86b731-2374-4f61-97fa-096a21bd2362_riskandfinace.pdf"
        
        if not Path(doc_path).exists():
            self.log_test_result(
                "Document Upload",
                False,
                {"error": f"Document not found: {doc_path}"}
            )
            return False
        
        try:
            start_time = time.time()
            
            with open(doc_path, 'rb') as f:
                files = {'file': ('riskandfinace.pdf', f, 'application/pdf')}
                data = {'session_id': self.session_id}
                
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            response_time = time.time() - start_time
            success = response.status_code == 200
            
            details = {
                "response_time": response_time,
                "status_code": response.status_code,
                "document_path": doc_path
            }
            
            if success:
                try:
                    upload_result = response.json()
                    details["upload_result"] = upload_result
                    details["doc_id"] = upload_result.get("doc_id")
                except:
                    details["response_text"] = response.text
            else:
                details["error"] = response.text
            
            self.log_test_result("Document Upload", success, details)
            return success
            
        except Exception as e:
            self.log_test_result(
                "Document Upload",
                False,
                {"error": str(e)}
            )
            return False
    
    def test_v2_chat_query(self, query: str, expected_keywords: list = None):
        """Test a chat query using V2 orchestrator."""
        print(f"💬 Testing V2 Chat Query: '{query[:50]}...'")
        
        try:
            start_time = time.time()
            
            payload = {
                "query": query,
                "session_id": self.session_id,
                # V2 is automatically used by orchestrator_integration
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=60
            )
            
            response_time = time.time() - start_time
            success = response.status_code == 200
            
            details = {
                "query": query,
                "response_time": response_time,
                "status_code": response.status_code
            }
            
            if success:
                try:
                    chat_result = response.json()
                    details["chat_result"] = chat_result
                    
                    # Extract response content
                    response_text = ""
                    if isinstance(chat_result, dict):
                        response_text = chat_result.get("response", str(chat_result))
                    else:
                        response_text = str(chat_result)
                    
                    details["response_text"] = response_text
                    details["response_length"] = len(response_text)
                    
                    # Check for V2 improvements
                    improvements_detected = []
                    
                    # Check if response is not mock data
                    if "mock knowledge base result" not in response_text.lower():
                        improvements_detected.append("No mock responses")
                    
                    # Check for structured content
                    if len(response_text) > 100:  # Substantial response
                        improvements_detected.append("Substantial response")
                    
                    # Check for expected keywords if provided
                    if expected_keywords:
                        found_keywords = [kw for kw in expected_keywords if kw.lower() in response_text.lower()]
                        if found_keywords:
                            improvements_detected.append(f"Found keywords: {found_keywords}")
                    
                    # Check for error information (should be structured if present)
                    if "error" in response_text.lower() and "error_type" in response_text:
                        improvements_detected.append("Structured error handling")
                    
                    details["v2_improvements"] = improvements_detected
                    
                    # Consider success if we got a substantial response without mock data
                    if len(response_text) > 50 and "mock knowledge base result" not in response_text.lower():
                        success = True
                    
                except Exception as e:
                    details["json_error"] = str(e)
                    details["response_text"] = response.text
            else:
                details["error"] = response.text
            
            self.log_test_result(f"V2 Chat Query", success, details)
            return success, details
            
        except Exception as e:
            details = {
                "query": query,
                "error": str(e)
            }
            self.log_test_result(f"V2 Chat Query", False, details)
            return False, details
    
    def run_comprehensive_v2_test(self):
        """Run comprehensive V2 chat endpoint test."""
        print("🚀 V2 CHAT ENDPOINT COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Session ID: {self.session_id}")
        print(f"Base URL: {self.base_url}")
        print()
        
        # Test queries focused on risk and finance
        test_queries = [
            {
                "query": "What are the main risk factors mentioned in the document?",
                "keywords": ["risk", "factor", "financial", "market", "credit"]
            },
            {
                "query": "Summarize the key financial metrics and ratios from the risk assessment",
                "keywords": ["ratio", "metric", "financial", "assessment", "performance"]
            },
            {
                "query": "What recommendations are provided for risk management?",
                "keywords": ["recommendation", "management", "strategy", "mitigation"]
            },
            {
                "query": "Analyze the operational risk factors discussed in the document",
                "keywords": ["operational", "risk", "analysis", "factors"]
            }
        ]
        
        # Run tests in sequence
        tests_passed = 0
        total_tests = 0
        
        # 1. Server health check
        total_tests += 1
        if self.test_server_health():
            tests_passed += 1
        else:
            print("\n❌ Server not available. Cannot proceed with chat testing.")
            return False
        
        print()
        
        # 2. Document upload
        total_tests += 1
        if self.upload_risk_finance_document():
            tests_passed += 1
        else:
            print("\n⚠️ Document upload failed. Proceeding with existing documents.")
        
        print()
        
        # 3. Chat queries
        for i, test_case in enumerate(test_queries, 1):
            total_tests += 1
            print(f"📋 Query {i}/{len(test_queries)}")
            
            success, details = self.test_v2_chat_query(
                test_case["query"],
                test_case["keywords"]
            )
            
            if success:
                tests_passed += 1
                
                # Show response preview
                response_text = details.get("response_text", "")
                if len(response_text) > 200:
                    print(f"      Response: {response_text[:200]}...")
                else:
                    print(f"      Response: {response_text}")
                
                # Show V2 improvements
                improvements = details.get("v2_improvements", [])
                if improvements:
                    print(f"      V2 Improvements: {', '.join(improvements)}")
            
            print()
        
        # Generate summary
        success_rate = (tests_passed / total_tests) * 100
        
        print("=" * 60)
        print("📊 V2 CHAT ENDPOINT TEST SUMMARY")
        print("=" * 60)
        
        print(f"Tests Passed: {tests_passed}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Categorize results
        if success_rate >= 80:
            print("🏆 EXCELLENT! V2 chat endpoint is working well.")
            print("   ✅ V2 orchestrator improvements are functioning")
            print("   ✅ End-to-end workflow successful")
        elif success_rate >= 60:
            print("🟡 GOOD PROGRESS! Most V2 features working.")
            print("   ✅ Core functionality operational")
            print("   ⚠️ Some areas may need attention")
        else:
            print("🔴 NEEDS WORK! Significant issues remain.")
            print("   ❌ V2 chat endpoint may need debugging")
            print("   ❌ End-to-end workflow has problems")
        
        print()
        print("📈 V2 IMPROVEMENT INDICATORS:")
        
        # Analyze improvements across all tests
        all_improvements = []
        for result in self.test_results:
            if "v2_improvements" in result.get("details", {}):
                all_improvements.extend(result["details"]["v2_improvements"])
        
        unique_improvements = list(set(all_improvements))
        
        if unique_improvements:
            for improvement in unique_improvements:
                print(f"   ✅ {improvement}")
        else:
            print("   ⚠️ No specific V2 improvements detected")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path("output") / f"v2_chat_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "test_session": self.session_id,
                "timestamp": timestamp,
                "success_rate": success_rate,
                "tests_passed": tests_passed,
                "total_tests": total_tests,
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return success_rate >= 60

def main():
    """Run the V2 chat endpoint test."""
    print("Starting V2 Chat Endpoint Test with Risk and Finance Document...")
    print()
    
    tester = V2ChatEndpointTester()
    success = tester.run_comprehensive_v2_test()
    
    if success:
        print("\n🎉 V2 Chat Endpoint Test Completed Successfully!")
    else:
        print("\n💥 V2 Chat Endpoint Test Failed. Check server and configuration.")

if __name__ == "__main__":
    main()