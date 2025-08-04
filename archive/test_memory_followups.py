#!/usr/bin/env python3
"""
Test Memory-Enabled Follow-up Questions
Tests conversation references and document-specific follow-ups
"""

import requests
import json
import time
from pathlib import Path

class MemoryFollowupTester:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.session_id = f"memory_test_{int(time.time())}"
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
        if details and details.get('answer_preview'):
            print(f"    Preview: {details['answer_preview'][:100]}...")
    
    def upload_document(self, file_path, expected_type):
        """Upload a document and return the stored filename"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f)}
                response = requests.post(
                    f"{self.api_base}/upload?session_id={self.session_id}",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.log_test(f"{expected_type} Upload", True, 
                                f"Uploaded {result['filename']} ({result.get('chunks_created', 0)} chunks)")
                    return result['filename']
            
            self.log_test(f"{expected_type} Upload", False, f"Failed: {response.status_code}")
            return None
            
        except Exception as e:
            self.log_test(f"{expected_type} Upload", False, f"Exception: {str(e)}")
            return None
    
    def send_chat(self, query, active_document=None, expect_success=True):
        """Send a chat message and return the response"""
        try:
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
                    return result
            
            print(f"    Chat failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            print(f"    Chat exception: {str(e)}")
            return None
    
    def test_csv_memory_sequence(self, csv_file):
        """Test CSV follow-up questions with memory"""
        print(f"\n📊 Testing CSV Memory Sequence with {csv_file}")
        
        # Step 1: Initial analysis
        result1 = self.send_chat("Summarize the employee data", csv_file)
        if result1:
            self.log_test("CSV Initial Summary", True, "Generated initial summary",
                         {"answer_preview": result1.get('final_answer', '')[:200]})
        else:
            self.log_test("CSV Initial Summary", False, "Failed to get initial summary")
            return
        
        # Step 2: Follow-up with conversation reference
        result2 = self.send_chat("Based on your analysis, how many employees are in Finance?", csv_file)
        if result2:
            answer = result2.get('final_answer', '')
            success = any(word in answer.lower() for word in ['finance', 'employees', 'based on'])
            self.log_test("CSV Conversation Reference", success, 
                         "Referenced previous analysis" if success else "No conversation reference found",
                         {"answer_preview": answer[:200]})
        else:
            self.log_test("CSV Conversation Reference", False, "Failed to get response")
        
        # Step 3: Another follow-up 
        result3 = self.send_chat("What was the average salary you calculated earlier?", csv_file)
        if result3:
            answer = result3.get('final_answer', '')
            success = any(word in answer.lower() for word in ['salary', 'average', 'calculated', 'earlier'])
            self.log_test("CSV Memory Reference", success,
                         "Referenced previous calculation" if success else "No memory reference found",
                         {"answer_preview": answer[:200]})
        else:
            self.log_test("CSV Memory Reference", False, "Failed to get response")
        
        # Step 4: Test conversation history search
        result4 = self.send_chat("Earlier you mentioned employees - remind me what you said about Finance department", csv_file)
        if result4:
            answer = result4.get('final_answer', '')
            success = any(word in answer.lower() for word in ['earlier', 'mentioned', 'finance'])
            self.log_test("CSV History Search", success,
                         "Found conversation history" if success else "No history reference found",
                         {"answer_preview": answer[:200]})
        else:
            self.log_test("CSV History Search", False, "Failed to get response")
    
    def test_txt_memory_sequence(self, txt_file):
        """Test TXT follow-up questions with memory"""
        print(f"\n📄 Testing TXT Memory Sequence with {txt_file}")
        
        # Step 1: Initial analysis
        result1 = self.send_chat("What are the main risk factors in this document?", txt_file)
        if result1:
            self.log_test("TXT Risk Analysis", True, "Generated risk analysis",
                         {"answer_preview": result1.get('final_answer', '')[:200]})
        else:
            self.log_test("TXT Risk Analysis", False, "Failed to get risk analysis")
            return
        
        # Step 2: Follow-up with memory reference
        result2 = self.send_chat("You mentioned several risks - which one is most critical?", txt_file)
        if result2:
            answer = result2.get('final_answer', '')
            success = any(word in answer.lower() for word in ['mentioned', 'risks', 'critical'])
            self.log_test("TXT Memory Follow-up", success,
                         "Referenced previous risks" if success else "No memory reference found",
                         {"answer_preview": answer[:200]})
        else:
            self.log_test("TXT Memory Follow-up", False, "Failed to get response")
        
        # Step 3: Conversation context test
        result3 = self.send_chat("In our conversation about risks, did you find any financial numbers?", txt_file)
        if result3:
            answer = result3.get('final_answer', '')
            success = any(word in answer.lower() for word in ['conversation', 'financial', 'numbers'])
            self.log_test("TXT Conversation Context", success,
                         "Used conversation context" if success else "No context awareness found",
                         {"answer_preview": answer[:200]})
        else:
            self.log_test("TXT Conversation Context", False, "Failed to get response")
    
    def test_memory_persistence(self):
        """Test if memory persists across different document contexts"""
        print(f"\n🧠 Testing Cross-Document Memory Persistence")
        
        # Test conversation reference without active document
        result = self.send_chat("What did we discuss about employee data earlier in our conversation?")
        if result:
            answer = result.get('final_answer', '')
            success = any(word in answer.lower() for word in ['employee', 'data', 'earlier', 'discussed'])
            self.log_test("Cross-Document Memory", success,
                         "Remembered cross-document conversation" if success else "No cross-document memory found",
                         {"answer_preview": answer[:200]})
        else:
            self.log_test("Cross-Document Memory", False, "Failed to get response")
    
    def run_comprehensive_memory_test(self):
        """Run complete memory follow-up test suite"""
        print("🧠 Starting Memory-Enabled Follow-up Question Tests")
        print("=" * 60)
        
        # Upload test documents
        csv_file = self.upload_document("test_documents/sample_data.csv", "CSV")
        txt_file = self.upload_document("test_documents/test_document.txt", "TXT")
        
        if not csv_file or not txt_file:
            print("❌ Document uploads failed, cannot continue")
            return self.generate_report()
        
        # Test CSV memory sequence
        self.test_csv_memory_sequence(csv_file)
        
        # Test TXT memory sequence  
        self.test_txt_memory_sequence(txt_file)
        
        # Test cross-document memory
        self.test_memory_persistence()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("🧠 MEMORY FOLLOW-UP TEST RESULTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: ✅ {passed_tests}")
        print(f"Failed: ❌ {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📊 CATEGORY BREAKDOWN:")
        categories = {}
        for result in self.test_results:
            category = result['test_name'].split()[0]
            if category not in categories:
                categories[category] = {"passed": 0, "total": 0}
            categories[category]["total"] += 1
            if result['success']:
                categories[category]["passed"] += 1
        
        for category, stats in categories.items():
            rate = (stats["passed"] / stats["total"]) * 100
            print(f"  {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # Save results
        report_file = f"memory_test_results_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "categories": categories
                },
                "test_results": self.test_results,
                "session_id": self.session_id
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {report_file}")
        
        if success_rate >= 70:
            print("\n🎉 MEMORY SYSTEM WORKING! Conversation references and follow-ups functional.")
        else:
            print("\n⚠️  MEMORY SYSTEM NEEDS WORK. Limited conversation awareness.")
        
        return success_rate >= 70

def main():
    """Main test execution"""
    tester = MemoryFollowupTester()
    success = tester.run_comprehensive_memory_test()
    return success

if __name__ == "__main__":
    main()