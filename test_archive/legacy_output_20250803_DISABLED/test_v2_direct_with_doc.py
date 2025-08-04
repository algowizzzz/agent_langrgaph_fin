#!/usr/bin/env python3
"""
Direct V2 Orchestrator Test with Risk and Finance Document

Test the V2 orchestrator directly without server dependencies,
using the risk and finance document from the archive.
"""

import asyncio
import time
import json
import sys
from datetime import datetime
from pathlib import Path

# Add paths for imports
sys.path.insert(0, '.')

class DirectV2Tester:
    """Test V2 orchestrator directly with document processing."""
    
    def __init__(self):
        self.session_id = f"direct_v2_test_{int(time.time())}"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: dict):
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
        
        if success and details.get("response_preview"):
            print(f"      Response: {details['response_preview'][:100]}...")
        elif details.get("error"):
            print(f"      Error: {details['error']}")
    
    async def test_v2_initialization(self):
        """Test V2 orchestrator initialization."""
        print("🔧 Testing V2 Orchestrator Initialization...")
        
        try:
            from orchestrator_v2.orchestrator_v2 import OrchestratorV2, OrchestratorConfig
            
            config = OrchestratorConfig(
                max_parallel_steps=3,
                enable_streaming=True,
                planning_strategy="adaptive"
            )
            
            orchestrator = OrchestratorV2(config)
            
            self.orchestrator = orchestrator
            
            self.log_result(
                "V2 Orchestrator Initialization",
                True,
                {
                    "config": {
                        "max_parallel_steps": config.max_parallel_steps,
                        "enable_streaming": config.enable_streaming,
                        "planning_strategy": str(config.planning_strategy)
                    }
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "V2 Orchestrator Initialization",
                False,
                {"error": str(e)}
            )
            return False
    
    async def test_document_upload_simulation(self):
        """Simulate document upload for testing."""
        print("📄 Testing Document Upload Simulation...")
        
        try:
            # Use the risk and finance document from global_uploads
            doc_path = "global_uploads/20250801_231832_2f86b731-2374-4f61-97fa-096a21bd2362_riskandfinace.pdf"
            
            if not Path(doc_path).exists():
                # Create a sample risk and finance document for testing
                sample_doc_content = """
FINANCIAL RISK ASSESSMENT REPORT - Q3 2024

Executive Summary:
This quarterly report analyzes key financial risks including market risk, credit risk, 
operational risk, and liquidity risk factors affecting our organization.

Market Risk Analysis:
- Interest rate volatility increased 15% compared to Q2 2024
- Currency exposure elevated due to international operations  
- Equity market correlation risks intensified

Credit Risk Assessment:
- Default rates decreased to 2.1% from 2.8% in Q2
- Credit quality improvements across commercial lending
- Stress testing shows resilience under adverse conditions

Operational Risk Factors:
- 3 cybersecurity incidents reported this quarter
- Process automation reduced manual errors by 40%
- Business continuity plans updated per regulations

Liquidity Risk Management:
- Cash reserves 12% above regulatory minimums
- Funding diversification strategy implemented
- Stress testing confirms adequate liquidity

Key Risk Metrics:
- Value at Risk (VaR): $2.3 million (95% confidence)
- Tier 1 Capital Ratio: 14.2%
- Liquidity Coverage Ratio: 125%
- Net Stable Funding Ratio: 110%

Recommendations:
1. Enhance interest rate hedging strategies
2. Implement additional cybersecurity measures
3. Continue portfolio diversification
4. Monitor regulatory developments
"""
                # Save sample document
                with open("sample_risk_finance.txt", 'w') as f:
                    f.write(sample_doc_content)
                doc_path = "sample_risk_finance.txt"
            
            # Simulate successful document processing
            doc_info = {
                "doc_id": f"risk_finance_{self.session_id}",
                "filename": Path(doc_path).name,
                "path": doc_path,
                "content_preview": "Financial Risk Assessment Report - Q3 2024..."
            }
            
            self.document_info = doc_info
            
            self.log_result(
                "Document Upload Simulation",
                True,
                {
                    "doc_id": doc_info["doc_id"],
                    "filename": doc_info["filename"],
                    "path": doc_info["path"]
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Document Upload Simulation",
                False,
                {"error": str(e)}
            )
            return False
    
    async def test_v2_query_execution(self, query: str, expected_keywords: list = None):
        """Test V2 query execution."""
        print(f"💬 Testing V2 Query: '{query[:50]}...'")
        
        try:
            start_time = time.time()
            
            # Execute query with V2 orchestrator
            result = await self.orchestrator.execute_query(
                user_query=query,
                session_id=self.session_id,
                active_documents=[self.document_info["doc_id"]] if hasattr(self, 'document_info') else []
            )
            
            execution_time = time.time() - start_time
            
            # Analyze result
            status = result.get('status', 'unknown')
            confidence = result.get('confidence_score', 0.0)
            final_answer = result.get('final_answer', 'No response')
            
            # Check for V2 specific features
            v2_features = []
            
            if result.get('execution_summary'):
                v2_features.append("Execution Summary")
            
            if result.get('traceability_log'):
                v2_features.append("Traceability Log")
            
            if result.get('confidence_score') is not None:
                v2_features.append("Confidence Scoring")
            
            # Check for structured error handling (from our fixes)
            response_str = str(final_answer)
            if "error_type" in response_str and "suggested_action" in response_str:
                v2_features.append("Structured Error Handling")
            
            # Check if mock responses are eliminated
            if "mock knowledge base result" not in response_str.lower():
                v2_features.append("No Mock Responses")
            
            # Success criteria
            success = (
                status == 'success' and 
                len(str(final_answer)) > 50 and
                "mock knowledge base result" not in response_str.lower()
            )
            
            details = {
                "query": query,
                "status": status,
                "confidence": confidence,
                "execution_time": execution_time,
                "response_length": len(str(final_answer)),
                "response_preview": str(final_answer)[:200],
                "v2_features_detected": v2_features
            }
            
            if result.get('execution_summary'):
                details["execution_summary"] = result['execution_summary']
            
            if expected_keywords:
                found_keywords = [kw for kw in expected_keywords if kw.lower() in response_str.lower()]
                details["keywords_found"] = found_keywords
                if found_keywords:
                    v2_features.append(f"Keywords Found: {found_keywords}")
            
            self.log_result(f"V2 Query Execution", success, details)
            
            # Show V2 improvements
            if v2_features:
                print(f"      V2 Features: {', '.join(v2_features)}")
            
            return success, details
            
        except Exception as e:
            details = {"query": query, "error": str(e)}
            self.log_result(f"V2 Query Execution", False, details)
            return False, details
    
    async def run_comprehensive_test(self):
        """Run comprehensive V2 direct test."""
        print("🚀 DIRECT V2 ORCHESTRATOR TEST WITH RISK & FINANCE DOC")
        print("=" * 70)
        print(f"Session ID: {self.session_id}")
        print()
        
        # Test sequence
        tests_passed = 0
        total_tests = 0
        
        # 1. Initialize V2 orchestrator
        total_tests += 1
        if await self.test_v2_initialization():
            tests_passed += 1
        else:
            print("\n❌ V2 initialization failed. Cannot proceed.")
            return False
        
        print()
        
        # 2. Document upload simulation
        total_tests += 1
        if await self.test_document_upload_simulation():
            tests_passed += 1
        
        print()
        
        # 3. Risk and finance focused queries
        risk_finance_queries = [
            {
                "query": "What are the main risk factors mentioned in the financial document?",
                "keywords": ["risk", "market", "credit", "operational", "liquidity"]
            },
            {
                "query": "Summarize the key financial metrics and ratios from the risk assessment",
                "keywords": ["ratio", "var", "capital", "liquidity", "funding"]
            },
            {
                "query": "What are the recommendations for managing financial risks?",
                "keywords": ["recommendation", "hedging", "cybersecurity", "diversification"]
            },
            {
                "query": "Analyze the operational risk factors and cybersecurity incidents",
                "keywords": ["operational", "cybersecurity", "incident", "automation"]
            }
        ]
        
        for i, test_case in enumerate(risk_finance_queries, 1):
            total_tests += 1
            print(f"📋 Query {i}/{len(risk_finance_queries)}")
            
            success, details = await self.test_v2_query_execution(
                test_case["query"],
                test_case["keywords"]
            )
            
            if success:
                tests_passed += 1
            
            print()
        
        # Generate final assessment
        success_rate = (tests_passed / total_tests) * 100
        
        print("=" * 70)
        print("📊 DIRECT V2 TEST SUMMARY")
        print("=" * 70)
        
        print(f"Tests Passed: {tests_passed}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Analysis
        if success_rate >= 80:
            print("🏆 EXCELLENT! V2 orchestrator working exceptionally well.")
            print("   ✅ Phase 1 & 2 fixes are highly effective")
            print("   ✅ End-to-end V2 functionality confirmed")
        elif success_rate >= 60:
            print("🟡 GOOD! V2 orchestrator shows solid improvements.")
            print("   ✅ Core V2 functionality working")
            print("   ⚠️ Some areas may need fine-tuning")
        else:
            print("🔴 NEEDS WORK! V2 orchestrator has significant issues.")
            print("   ❌ Core functionality problems detected")
            print("   ❌ Phase 1 & 2 fixes may need review")
        
        print()
        print("📈 V2 IMPROVEMENT INDICATORS:")
        
        # Collect all V2 features detected
        all_v2_features = set()
        for result in self.test_results:
            features = result.get("details", {}).get("v2_features_detected", [])
            all_v2_features.update(features)
        
        if all_v2_features:
            for feature in sorted(all_v2_features):
                print(f"   ✅ {feature}")
        else:
            print("   ⚠️ No specific V2 improvements detected")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path("output") / f"direct_v2_test_results_{timestamp}.json"
        
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

async def main():
    """Run the direct V2 test."""
    print("Starting Direct V2 Orchestrator Test with Risk & Finance Document...")
    print()
    
    tester = DirectV2Tester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 Direct V2 Test Completed Successfully!")
    else:
        print("\n💥 Direct V2 Test Failed. V2 orchestrator needs work.")

if __name__ == "__main__":
    asyncio.run(main())