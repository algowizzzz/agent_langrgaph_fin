#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Suite for BMO Documentation Analysis Tool
Based on TRD specifications and HLRD requirements
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
import requests
import shutil

class BackendAPITester:
    """Complete backend API testing suite with TRD-compliant prompts."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        self.session_id = f"api_test_{uuid.uuid4().hex[:8]}"
        
    def log_test(self, test_name: str, endpoint: str, payload: dict, response: dict, 
                 status_code: int, execution_time: float, success: bool):
        """Log test results for documentation."""
        self.test_results.append({
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "endpoint": endpoint,
            "payload": payload,
            "response": response,
            "status_code": status_code,
            "execution_time_ms": round(execution_time * 1000, 2),
            "success": success
        })
    
    def test_health_endpoint(self):
        """Test system health endpoint."""
        print("🏥 Testing Health Endpoint")
        
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            execution_time = time.time() - start_time
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else {"error": response.text}
            
            self.log_test(
                "Health Check",
                "/health",
                {},
                response_data,
                response.status_code,
                execution_time,
                success
            )
            
            print(f"  ✅ Health: {response_data.get('status', 'Unknown')}")
            return success
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Health Check", "/health", {}, {"error": str(e)}, 0, execution_time, False)
            print(f"  ❌ Health check failed: {str(e)}")
            return False
    
    def test_file_upload(self):
        """Test file upload endpoint with various file types."""
        print("\n📁 Testing File Upload Endpoint")
        
        test_files = [
            ("sample_employees.csv", "text/csv"),
            ("quarterly_report.csv", "text/csv"),
            ("bmo_quarterly_review.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("bmo_business_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("bmo_tech_strategy.pdf", "application/pdf")
        ]
        
        uploaded_files = {}
        
        for filename, mime_type in test_files:
            file_path = Path(f"test_files/{filename}")
            if not file_path.exists():
                print(f"  ⚠️  File not found: {filename}")
                continue
                
            print(f"  📄 Testing upload: {filename}")
            
            start_time = time.time()
            try:
                with open(file_path, 'rb') as f:
                    files = {"file": (filename, f, mime_type)}
                    params = {"session_id": self.session_id}
                    
                    response = requests.post(
                        f"{self.base_url}/upload",
                        files=files,
                        params=params,
                        timeout=30
                    )
                
                execution_time = time.time() - start_time
                success = response.status_code == 200
                
                if success:
                    response_data = response.json()
                    file_id = response_data.get("file_id")
                    uploaded_files[filename] = {"id": file_id, "role": "Content"}
                    print(f"    ✅ Uploaded successfully: {file_id}")
                else:
                    response_data = {"error": response.text}
                    print(f"    ❌ Upload failed: {response.status_code}")
                
                self.log_test(
                    f"File Upload - {filename}",
                    "/upload",
                    {"filename": filename, "session_id": self.session_id},
                    response_data,
                    response.status_code,
                    execution_time,
                    success
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.log_test(
                    f"File Upload - {filename}",
                    "/upload",
                    {"filename": filename, "session_id": self.session_id},
                    {"error": str(e)},
                    0,
                    execution_time,
                    False
                )
                print(f"    💥 Exception: {str(e)}")
        
        return uploaded_files
    
    def test_qna_scenarios(self):
        """Test Q&A scenarios with TRD-compliant prompts."""
        print("\n💬 Testing Q&A Pod Scenarios")
        
        # TRD-specified Q&A test prompts
        qna_scenarios = [
            {
                "name": "BMO Business Hours Inquiry",
                "prompt": "What are BMO's business hours and how can I contact customer service?",
                "expected_source": "BMO Mock Data"
            },
            {
                "name": "Account Opening Process",
                "prompt": "I need to open a new business account with BMO. What documents do I need and what's the process?",
                "expected_source": "BMO Mock Data"
            },
            {
                "name": "Investment Services Inquiry",
                "prompt": "What investment and wealth management services does BMO offer for high-net-worth clients?",
                "expected_source": "BMO Mock Data"
            },
            {
                "name": "Digital Banking Features",
                "prompt": "Tell me about BMO's mobile app features and online banking capabilities.",
                "expected_source": "BMO Mock Data"
            },
            {
                "name": "Credit and Lending Products",
                "prompt": "What are BMO's current mortgage rates and business loan options?",
                "expected_source": "BMO Mock Data"
            },
            {
                "name": "General Banking Question",
                "prompt": "How does compound interest work in savings accounts?",
                "expected_source": "General LLM Knowledge"
            }
        ]
        
        for scenario in qna_scenarios:
            print(f"  🤔 Testing: {scenario['name']}")
            
            payload = {
                "session_id": self.session_id,
                "messages": [{"role": "user", "content": scenario["prompt"]}],
                "uploaded_files": {}
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=60
                )
                
                execution_time = time.time() - start_time
                success = response.status_code == 200
                
                if success:
                    response_data = response.json()
                    content = response_data.get("content", "")
                    source = response_data.get("source", "")
                    
                    print(f"    ✅ Response received ({len(content)} chars)")
                    print(f"    📍 Source: {source}")
                    print(f"    💭 Preview: {content[:100]}...")
                else:
                    response_data = {"error": response.text}
                    print(f"    ❌ Failed: {response.status_code}")
                
                self.log_test(
                    scenario["name"],
                    "/chat",
                    payload,
                    response_data,
                    response.status_code,
                    execution_time,
                    success
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.log_test(
                    scenario["name"],
                    "/chat",
                    payload,
                    {"error": str(e)},
                    0,
                    execution_time,
                    False
                )
                print(f"    💥 Exception: {str(e)}")
    
    def test_document_analysis_scenarios(self, uploaded_files: dict):
        """Test document analysis scenarios with TRD-compliant prompts."""
        print("\n📊 Testing Document Analysis Pod Scenarios")
        
        if not uploaded_files:
            print("  ⚠️  No uploaded files available for testing")
            return
        
        # TRD-specified document analysis prompts
        analysis_scenarios = [
            {
                "name": "Executive Summary Generation",
                "files": ["bmo_quarterly_review.docx"],
                "prompt": "Generate an executive summary of this quarterly business review, highlighting key performance indicators, strategic achievements, and future outlook."
            },
            {
                "name": "Financial Data Analysis", 
                "files": ["quarterly_report.csv"],
                "prompt": "Analyze the financial data trends in this report. Identify growth patterns, performance metrics, and provide insights on revenue and profitability trends."
            },
            {
                "name": "Employee Analytics",
                "files": ["sample_employees.csv"],
                "prompt": "Provide a comprehensive analysis of the employee data including department distribution, salary analysis, performance ratings, and geographical spread."
            },
            {
                "name": "Technology Strategy Review",
                "files": ["bmo_tech_strategy.pdf"],
                "prompt": "Summarize the key technology initiatives, budget allocations, timelines, and expected ROI from this strategic document."
            },
            {
                "name": "Multi-Document Cross-Analysis",
                "files": ["bmo_quarterly_review.docx", "quarterly_report.csv"],
                "prompt": "Compare and contrast the information in these documents. How do the narrative findings align with the quantitative data? Identify any discrepancies or supporting evidence."
            },
            {
                "name": "Business Intelligence Extraction",
                "files": ["bmo_business_data.xlsx"],
                "prompt": "Extract key business intelligence from this workbook. Provide insights on operational metrics, departmental performance, and strategic recommendations."
            }
        ]
        
        for scenario in analysis_scenarios:
            print(f"  📈 Testing: {scenario['name']}")
            
            # Select available files for this scenario
            scenario_files = {}
            for filename in scenario["files"]:
                if filename in uploaded_files:
                    scenario_files[filename] = uploaded_files[filename]
            
            if not scenario_files:
                print(f"    ⚠️  Required files not available: {scenario['files']}")
                continue
            
            payload = {
                "session_id": self.session_id,
                "messages": [{"role": "user", "content": scenario["prompt"]}],
                "uploaded_files": scenario_files
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=120  # Longer timeout for document analysis
                )
                
                execution_time = time.time() - start_time
                success = response.status_code == 200
                
                if success:
                    response_data = response.json()
                    content = response_data.get("content", "")
                    source = response_data.get("source", "")
                    
                    print(f"    ✅ Analysis completed ({len(content)} chars)")
                    print(f"    📍 Source: {source}")
                    print(f"    📄 Files processed: {len(scenario_files)}")
                    print(f"    💭 Preview: {content[:150]}...")
                else:
                    response_data = {"error": response.text}
                    print(f"    ❌ Failed: {response.status_code}")
                
                self.log_test(
                    scenario["name"],
                    "/chat",
                    payload,
                    response_data,
                    response.status_code,
                    execution_time,
                    success
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.log_test(
                    scenario["name"],
                    "/chat",
                    payload,
                    {"error": str(e)},
                    0,
                    execution_time,
                    False
                )
                print(f"    💥 Exception: {str(e)}")
    
    def test_error_scenarios(self):
        """Test error handling scenarios."""
        print("\n⚠️  Testing Error Handling Scenarios")
        
        error_scenarios = [
            {
                "name": "Empty Request",
                "payload": {},
                "expected_status": 422
            },
            {
                "name": "Invalid Session ID",
                "payload": {
                    "session_id": "",
                    "messages": [{"role": "user", "content": "test"}],
                    "uploaded_files": {}
                },
                "expected_status": 422
            },
            {
                "name": "Malformed Message",
                "payload": {
                    "session_id": "test123",
                    "messages": [{"role": "invalid", "content": "test"}],
                    "uploaded_files": {}
                },
                "expected_status": 422
            },
            {
                "name": "Missing Content",
                "payload": {
                    "session_id": "test123", 
                    "messages": [{"role": "user"}],
                    "uploaded_files": {}
                },
                "expected_status": 422
            }
        ]
        
        for scenario in error_scenarios:
            print(f"  🚫 Testing: {scenario['name']}")
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=scenario["payload"],
                    timeout=10
                )
                
                execution_time = time.time() - start_time
                success = response.status_code == scenario["expected_status"]
                
                response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"response": response.text}
                
                if success:
                    print(f"    ✅ Correctly returned {response.status_code}")
                else:
                    print(f"    ❌ Expected {scenario['expected_status']}, got {response.status_code}")
                
                self.log_test(
                    scenario["name"],
                    "/chat",
                    scenario["payload"],
                    response_data,
                    response.status_code,
                    execution_time,
                    success
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.log_test(
                    scenario["name"],
                    "/chat",
                    scenario["payload"],
                    {"error": str(e)},
                    0,
                    execution_time,
                    False
                )
                print(f"    💥 Exception: {str(e)}")
    
    def test_session_cleanup(self):
        """Test session cleanup endpoint."""
        print("\n🧹 Testing Session Cleanup")
        
        start_time = time.time()
        try:
            response = requests.delete(f"{self.base_url}/session/{self.session_id}", timeout=10)
            execution_time = time.time() - start_time
            
            success = response.status_code == 200
            response_data = response.json() if success else {"error": response.text}
            
            self.log_test(
                "Session Cleanup",
                f"/session/{self.session_id}",
                {"session_id": self.session_id},
                response_data,
                response.status_code,
                execution_time,
                success
            )
            
            if success:
                print(f"  ✅ Session cleaned up successfully")
            else:
                print(f"  ❌ Cleanup failed: {response.status_code}")
                
            return success
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test(
                "Session Cleanup",
                f"/session/{self.session_id}",
                {"session_id": self.session_id},
                {"error": str(e)},
                0,
                execution_time,
                False
            )
            print(f"  💥 Exception: {str(e)}")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 Generating Test Report...")
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        avg_response_time = sum(r["execution_time_ms"] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": round((successful_tests / total_tests * 100), 2) if total_tests > 0 else 0,
                "average_response_time_ms": round(avg_response_time, 2)
            },
            "detailed_results": self.test_results
        }
        
        # Save to JSON file
        with open("backend_api_test_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"  ✅ Test report saved to: backend_api_test_results.json")
        print(f"  📊 Summary: {successful_tests}/{total_tests} tests passed ({report['test_summary']['success_rate']}%)")
        
        return report
    
    async def run_all_tests(self):
        """Execute complete test suite."""
        print("🚀 Starting Comprehensive Backend API Testing Suite")
        print("=" * 80)
        print(f"🔗 Base URL: {self.base_url}")
        print(f"🆔 Test Session ID: {self.session_id}")
        print("=" * 80)
        
        # Test sequence
        if not self.test_health_endpoint():
            print("❌ Health check failed. Aborting tests.")
            return
        
        uploaded_files = self.test_file_upload()
        self.test_qna_scenarios()
        self.test_document_analysis_scenarios(uploaded_files)
        self.test_error_scenarios()
        self.test_session_cleanup()
        
        # Generate final report
        report = self.generate_test_report()
        
        print("\n" + "=" * 80)
        print("🎉 Backend API Testing Complete!")
        print(f"📊 Results: {report['test_summary']['successful_tests']}/{report['test_summary']['total_tests']} tests passed")
        print(f"⚡ Average Response Time: {report['test_summary']['average_response_time_ms']}ms")
        print("=" * 80)
        
        return report

def main():
    """Main test execution function."""
    tester = BackendAPITester()
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        report = loop.run_until_complete(tester.run_all_tests())
        return report
    finally:
        loop.close()

if __name__ == "__main__":
    main()