#!/usr/bin/env python3
"""
Document Tools Testing Script
Tests the 6 core document tools systematically with detailed logging.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator
from tools.document_tools import upload_document, discover_document_structure, search_uploaded_docs
from tools.synthesis_tools import synthesize_content

class DocumentToolsTester:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.test_results = []
        self.test_files = {
            'riskfinance': 'testing_31jul/test_files/riskandfinace.pdf',
            'quarterly': 'testing_31jul/test_files/quarterly_report.csv',
            'car24': 'testing_31jul/test_files/car24_chpt1_0.pdf'
        }
        
    def log_test(self, test_name, status, details, error=None):
        """Log test result with timestamp."""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'status': status,
            'details': details,
            'error': str(error) if error else None
        }
        self.test_results.append(result)
        
        # Print to console
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
        print(f"\n{status_emoji} {test_name}")
        print(f"   Status: {status}")
        print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
    
    async def test_1_upload_documents(self):
        """Test 1: Upload all three test documents"""
        print("\n" + "="*60)
        print("TEST 1: UPLOAD DOCUMENTS")
        print("="*60)
        
        for doc_name, file_path in self.test_files.items():
            try:
                print(f"\n📄 Uploading {doc_name}: {file_path}")
                
                # Check if file exists
                if not Path(file_path).exists():
                    self.log_test(f"Upload {doc_name}", "FAIL", f"File not found: {file_path}")
                    continue
                
                # Upload document
                result = await upload_document(file_path)
                
                if result.get('status') == 'success':
                    chunks_count = result.get('chunks_processed', 0)
                    self.log_test(f"Upload {doc_name}", "PASS", f"Successfully uploaded, {chunks_count} chunks created")
                else:
                    self.log_test(f"Upload {doc_name}", "FAIL", f"Upload failed: {result}")
                    
            except Exception as e:
                self.log_test(f"Upload {doc_name}", "FAIL", "Exception during upload", e)
    
    async def test_2_discover_structure(self):
        """Test 2: Discover document structure"""
        print("\n" + "="*60)
        print("TEST 2: DISCOVER DOCUMENT STRUCTURE")
        print("="*60)
        
        # Test with the risk and finance document (should have clear structure)
        doc_name = "riskandfinace.pdf"
        
        try:
            print(f"\n🔍 Analyzing structure of {doc_name}")
            
            result = await discover_document_structure(doc_name)
            
            if result.get('status') == 'success':
                headers = result.get('headers', [])
                sections = result.get('sections', [])
                self.log_test("Discover Structure", "PASS", 
                            f"Found {len(headers)} headers, {len(sections)} sections")
                
                # Print some structure details
                if headers:
                    print(f"   📋 Headers found: {headers[:3]}..." if len(headers) > 3 else f"   📋 Headers: {headers}")
                    
            else:
                self.log_test("Discover Structure", "FAIL", f"Structure discovery failed: {result}")
                
        except Exception as e:
            self.log_test("Discover Structure", "FAIL", "Exception during structure discovery", e)
    
    async def test_3_search_documents(self):
        """Test 3: Search uploaded documents"""
        print("\n" + "="*60)
        print("TEST 3: SEARCH DOCUMENTS") 
        print("="*60)
        
        search_tests = [
            ("riskandfinace.pdf", "risk", "Should find risk management content"),
            ("riskandfinace.pdf", "finance", "Should find financial content"),
            ("quarterly_report.csv", "revenue", "Should find financial data")
        ]
        
        for doc_name, query, expected in search_tests:
            try:
                print(f"\n🔍 Searching '{query}' in {doc_name}")
                print(f"   Expected: {expected}")
                
                result = await search_uploaded_docs(doc_name=doc_name, query=query)
                
                if isinstance(result, list) and len(result) > 0:
                    chunk_count = len(result)
                    preview = result[0].get('page_content', '')[:100]
                    self.log_test(f"Search {doc_name}", "PASS", 
                                f"Found {chunk_count} chunks. Preview: {preview}...")
                else:
                    self.log_test(f"Search {doc_name}", "FAIL", f"No results found for '{query}'")
                    
            except Exception as e:
                self.log_test(f"Search {doc_name}", "FAIL", f"Exception during search", e)
    
    async def test_4_synthesize_summary(self):
        """Test 4: Synthesize content - Document Summary"""
        print("\n" + "="*60)
        print("TEST 4: SYNTHESIZE CONTENT - SUMMARY")
        print("="*60)
        
        doc_name = "riskandfinace.pdf"
        
        try:
            print(f"\n📝 Creating summary of {doc_name}")
            
            # First get all chunks from the document
            chunks = await search_uploaded_docs(doc_name=doc_name, retrieve_full_doc=True)
            
            if not chunks:
                self.log_test("Synthesize Summary", "FAIL", "No chunks found for synthesis")
                return
                
            # Synthesize using refine method
            result = await synthesize_content(
                chunks=chunks,
                method="refine", 
                length="two paragraphs",
                tone="professional",
                user_query="Summarize the entire document"
            )
            
            if result and len(result) > 50:  # Reasonable summary length
                summary_preview = result[:200] + "..." if len(result) > 200 else result
                self.log_test("Synthesize Summary", "PASS", 
                            f"Generated {len(result)} char summary: {summary_preview}")
            else:
                self.log_test("Synthesize Summary", "FAIL", f"Poor quality summary: {result}")
                
        except Exception as e:
            self.log_test("Synthesize Summary", "FAIL", "Exception during synthesis", e)
    
    async def test_5_synthesize_section(self):
        """Test 5: Synthesize content - Section Extract"""
        print("\n" + "="*60)
        print("TEST 5: SYNTHESIZE CONTENT - SECTION EXTRACT")
        print("="*60)
        
        doc_name = "riskandfinace.pdf"
        section_query = "risk"
        
        try:
            print(f"\n📝 Extracting section about '{section_query}' from {doc_name}")
            
            # Search for specific section
            chunks = await search_uploaded_docs(doc_name=doc_name, query=section_query)
            
            if not chunks:
                self.log_test("Synthesize Section", "FAIL", f"No chunks found for '{section_query}'")
                return
                
            # Synthesize using map_reduce method
            result = await synthesize_content(
                chunks=chunks,
                method="map_reduce",
                length="one paragraph", 
                tone="professional",
                user_query=f"Explain the {section_query} section"
            )
            
            if result and len(result) > 30:
                section_preview = result[:200] + "..." if len(result) > 200 else result
                self.log_test("Synthesize Section", "PASS",
                            f"Generated {len(result)} char section: {section_preview}")
            else:
                self.log_test("Synthesize Section", "FAIL", f"Poor quality section: {result}")
                
        except Exception as e:
            self.log_test("Synthesize Section", "FAIL", "Exception during section synthesis", e)
    
    async def test_6_synthesize_simple(self):
        """Test 6: Synthesize content - Simplification"""
        print("\n" + "="*60)
        print("TEST 6: SYNTHESIZE CONTENT - SIMPLIFICATION")
        print("="*60)
        
        doc_name = "riskandfinace.pdf"
        
        try:
            print(f"\n📝 Simplifying risk and finance content from {doc_name} for 5th grader")
            
            # Get document chunks
            chunks = await search_uploaded_docs(doc_name=doc_name, retrieve_full_doc=True)
            
            if not chunks:
                self.log_test("Synthesize Simple", "FAIL", "No chunks found for simplification")
                return
                
            # Synthesize with simple tone
            result = await synthesize_content(
                chunks=chunks,
                method="refine",
                length="one paragraph",
                tone="simple and educational", 
                user_query="Explain this to a 5th grader"
            )
            
            if result and len(result) > 30:
                simple_preview = result[:200] + "..." if len(result) > 200 else result
                self.log_test("Synthesize Simple", "PASS",
                            f"Generated {len(result)} char simple explanation: {simple_preview}")
            else:
                self.log_test("Synthesize Simple", "FAIL", f"Poor quality simplification: {result}")
                
        except Exception as e:
            self.log_test("Synthesize Simple", "FAIL", "Exception during simplification", e)
    
    async def test_follow_up_questions(self):
        """Follow-up questions to test tool integration"""
        print("\n" + "="*60)
        print("FOLLOW-UP QUESTIONS TEST")
        print("="*60)
        
        follow_ups = [
            ("What is the definition of risk in this document?", "riskandfinace.pdf"),
            ("How many times is 'risk' mentioned in the document?", "riskandfinace.pdf"),
            ("What financial concepts are explained in this document?", "riskandfinace.pdf")
        ]
        
        for question, target_doc in follow_ups:
            try:
                print(f"\n❓ {question}")
                print(f"   Target: {target_doc}")
                
                # Use orchestrator for integrated testing
                result = await self.orchestrator.run(
                    user_query=question,
                    session_id="test_session",
                    active_document=target_doc
                )
                
                if result.get('status') == 'success':
                    answer = result.get('final_answer', '')
                    answer_preview = answer[:150] + "..." if len(answer) > 150 else answer
                    self.log_test(f"Follow-up: {question[:30]}...", "PASS", 
                                f"Got answer: {answer_preview}")
                else:
                    self.log_test(f"Follow-up: {question[:30]}...", "FAIL", 
                                f"No answer received: {result}")
                    
            except Exception as e:
                self.log_test(f"Follow-up: {question[:30]}...", "FAIL", "Exception during follow-up", e)
    
    def save_results(self):
        """Save test results to JSON file"""
        results_file = "testing_31jul/document_tools_test_results.json"
        
        summary = {
            'test_run_date': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed': len([r for r in self.test_results if r['status'] == 'PASS']),
            'failed': len([r for r in self.test_results if r['status'] == 'FAIL']),
            'test_results': self.test_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n💾 Results saved to: {results_file}")
        return summary
    
    def print_summary(self):
        """Print test execution summary"""
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        total = len(self.test_results)
        
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)
        print(f"📊 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test_name']}: {result['details']}")

async def main():
    """Main test execution function"""
    print("🧪 DOCUMENT TOOLS TESTING SCRIPT")
    print("=" * 60)
    print("Testing 6 core document tools with 3 test files")
    print("Files: Risk&Finance PDF, Quarterly CSV, CAR24 PDF")
    
    tester = DocumentToolsTester()
    
    try:
        # Run all tests in sequence
        await tester.test_1_upload_documents()
        await tester.test_2_discover_structure()
        await tester.test_3_search_documents()
        await tester.test_4_synthesize_summary()
        await tester.test_5_synthesize_section()
        await tester.test_6_synthesize_simple()
        await tester.test_follow_up_questions()
        
        # Generate summary and save results
        tester.print_summary()
        summary = tester.save_results()
        
        print(f"\n🎯 Testing Complete!")
        print(f"Check testing_31jul/document_tools_test_results.json for detailed results")
        
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Testing failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())