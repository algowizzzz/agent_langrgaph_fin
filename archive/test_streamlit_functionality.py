#!/usr/bin/env python3
"""
Comprehensive Streamlit Application Test Suite
Tests document upload, chat functionality, and summarization
"""

import requests
import json
import time
import os
from pathlib import Path

class StreamlitAppTester:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.session_id = f"test_session_{int(time.time())}"
        self.test_results = []
    
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def test_backend_health(self):
        """Test backend health check"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Health Check", True, "Backend is responsive")
                return True
            else:
                self.log_test("Backend Health Check", False, f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Backend connection failed: {str(e)}")
            return False
    
    def test_document_upload_txt(self):
        """Test TXT document upload"""
        try:
            # Read test document
            test_file_path = Path("test_documents/test_document.txt")
            if not test_file_path.exists():
                self.log_test("TXT Upload", False, "Test document not found")
                return False
            
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                
                response = requests.post(
                    f"{self.api_base}/upload?session_id={self.session_id}",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    chunks = result.get('chunks_created', 0)
                    self.log_test("TXT Upload", True, f"Successfully uploaded with {chunks} chunks", result)
                    return True, result.get('filename')
                else:
                    self.log_test("TXT Upload", False, f"Upload failed: {result.get('error_message', 'Unknown error')}")
                    return False, None
            else:
                self.log_test("TXT Upload", False, f"HTTP error: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("TXT Upload", False, f"Exception: {str(e)}")
            return False, None
    
    def test_document_upload_csv(self):
        """Test CSV document upload"""
        try:
            # Read test document
            test_file_path = Path("test_documents/sample_data.csv")
            if not test_file_path.exists():
                self.log_test("CSV Upload", False, "Test CSV not found")
                return False
            
            with open(test_file_path, 'rb') as f:
                files = {'file': ('sample_data.csv', f, 'text/csv')}
                
                response = requests.post(
                    f"{self.api_base}/upload?session_id={self.session_id}",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    chunks = result.get('chunks_created', 0)
                    self.log_test("CSV Upload", True, f"Successfully uploaded with {chunks} chunks", result)
                    return True, result.get('filename')
                else:
                    self.log_test("CSV Upload", False, f"Upload failed: {result.get('error_message', 'Unknown error')}")
                    return False, None
            else:
                self.log_test("CSV Upload", False, f"HTTP error: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("CSV Upload", False, f"Exception: {str(e)}")
            return False, None
    
    def test_chat_summarization(self, active_document):
        """Test chat summarization functionality"""
        try:
            query = "Summarize this document"
            payload = {
                "query": query,
                "session_id": self.session_id,
                "active_document": active_document
            }
            
            response = requests.post(
                f"{self.api_base}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    answer = result.get('final_answer', '')
                    reasoning = result.get('reasoning_log', [])
                    processing_time = result.get('processing_time_ms', 0)
                    
                    if len(answer) > 50:  # Reasonable summary length
                        self.log_test("Chat Summarization", True, 
                                    f"Generated summary ({len(answer)} chars) in {processing_time}ms",
                                    {"answer_preview": answer[:200] + "...", "reasoning_steps": len(reasoning)})
                        return True, result
                    else:
                        self.log_test("Chat Summarization", False, "Summary too short")
                        return False, None
                else:
                    self.log_test("Chat Summarization", False, f"Chat failed: {result.get('error_message', 'Unknown error')}")
                    return False, None
            else:
                self.log_test("Chat Summarization", False, f"HTTP error: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Chat Summarization", False, f"Exception: {str(e)}")
            return False, None
    
    def test_word_count_query(self, active_document):
        """Test word counting functionality"""
        try:
            query = "Count how many times the word 'risk' appears in this document"
            payload = {
                "query": query,
                "session_id": self.session_id,
                "active_document": active_document
            }
            
            response = requests.post(
                f"{self.api_base}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    answer = result.get('final_answer', '')
                    reasoning = result.get('reasoning_log', [])
                    
                    # Check if answer contains a number (word count)
                    if any(char.isdigit() for char in answer):
                        self.log_test("Word Count Query", True, 
                                    f"Successfully counted words: {answer[:100]}...",
                                    {"full_answer": answer, "reasoning_steps": len(reasoning)})
                        return True, result
                    else:
                        self.log_test("Word Count Query", False, "No word count found in response")
                        return False, None
                else:
                    self.log_test("Word Count Query", False, f"Query failed: {result.get('error_message', 'Unknown error')}")
                    return False, None
            else:
                self.log_test("Word Count Query", False, f"HTTP error: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Word Count Query", False, f"Exception: {str(e)}")
            return False, None
    
    def test_key_topics_extraction(self, active_document):
        """Test key topics extraction"""
        try:
            query = "Extract the main topics from this document"
            payload = {
                "query": query,
                "session_id": self.session_id,
                "active_document": active_document
            }
            
            response = requests.post(
                f"{self.api_base}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    answer = result.get('final_answer', '')
                    reasoning = result.get('reasoning_log', [])
                    
                    if len(answer) > 30:  # Reasonable topics length
                        self.log_test("Key Topics Extraction", True, 
                                    f"Extracted topics ({len(answer)} chars)",
                                    {"topics_preview": answer[:200] + "...", "reasoning_steps": len(reasoning)})
                        return True, result
                    else:
                        self.log_test("Key Topics Extraction", False, "Topics extraction too short")
                        return False, None
                else:
                    self.log_test("Key Topics Extraction", False, f"Query failed: {result.get('error_message', 'Unknown error')}")
                    return False, None
            else:
                self.log_test("Key Topics Extraction", False, f"HTTP error: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Key Topics Extraction", False, f"Exception: {str(e)}")
            return False, None
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Streamlit Application Test")
        print("=" * 60)
        
        # Test 1: Backend Health
        if not self.test_backend_health():
            print("❌ Backend health check failed. Stopping tests.")
            return self.generate_report()
        
        # Test 2: Document Uploads
        print("\n📄 Testing Document Uploads...")
        txt_success, txt_filename = self.test_document_upload_txt()
        csv_success, csv_filename = self.test_document_upload_csv()
        
        if not (txt_success or csv_success):
            print("❌ All document uploads failed. Stopping tests.")
            return self.generate_report()
        
        # Test 3: Chat Functionality with TXT document
        if txt_success:
            print(f"\n💬 Testing Chat Functionality with {txt_filename}...")
            self.test_chat_summarization(txt_filename)
            self.test_word_count_query(txt_filename)
            self.test_key_topics_extraction(txt_filename)
        
        # Test 4: Chat Functionality with CSV document
        if csv_success:
            print(f"\n📊 Testing Chat Functionality with {csv_filename}...")
            self.test_chat_summarization(csv_filename)
            
            # CSV-specific query
            try:
                query = "How many employees are in the Finance department?"
                payload = {
                    "query": query,
                    "session_id": self.session_id,
                    "active_document": csv_filename
                }
                
                response = requests.post(
                    f"{self.api_base}/api/chat",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        answer = result.get('final_answer', '')
                        if any(char.isdigit() for char in answer):
                            self.log_test("CSV Data Query", True, f"Successfully answered CSV query: {answer[:100]}...")
                        else:
                            self.log_test("CSV Data Query", False, "No numeric answer found")
                    else:
                        self.log_test("CSV Data Query", False, f"Query failed: {result.get('error_message')}")
                else:
                    self.log_test("CSV Data Query", False, f"HTTP error: {response.status_code}")
            except Exception as e:
                self.log_test("CSV Data Query", False, f"Exception: {str(e)}")
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: ✅ {passed_tests}")
        print(f"Failed: ❌ {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}: {result['message']}")
        
        # Save results to file
        report_file = f"streamlit_test_results_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate
                },
                "test_results": self.test_results,
                "session_id": self.session_id
            }, f, indent=2)
        
        print(f"\n💾 Full results saved to: {report_file}")
        
        if success_rate >= 80:
            print("\n🎉 TEST SUITE PASSED! Application is production ready.")
        else:
            print("\n⚠️  TEST SUITE NEEDS ATTENTION. Some functionality may need fixes.")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    # Ensure test documents directory exists
    os.makedirs("test_documents", exist_ok=True)
    
    # Run tests
    tester = StreamlitAppTester()
    success = tester.run_comprehensive_test()
    
    return success

if __name__ == "__main__":
    main()