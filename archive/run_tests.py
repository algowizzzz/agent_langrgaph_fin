#!/usr/bin/env python3
"""
Simplified test runner for BMO Documentation Analysis Tool
Tests core functionality with proper method signatures
"""

import asyncio
import sys
import uuid
import shutil
from pathlib import Path

# Import application components
from document_analysis_pod import document_analysis_pod
from qna_pod import qna_pod

async def test_qna_pod():
    """Test Q&A Pod functionality."""
    print("🔍 Testing Q&A Pod")
    print("-" * 40)
    
    test_questions = [
        "What are BMO's hours of operation?",
        "How do I open a new account?", 
        "What are the fees for international transfers?",
        "Tell me about BMO's mobile banking app features"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n  Test {i}: {question}")
        try:
            result = await qna_pod.process_question(question)
            
            if result.get('error'):
                print(f"    ❌ FAILED - Error: {result['error']}")
            else:
                print(f"    ✅ SUCCESS")
                print(f"    💬 Answer: {result['answer'][:100]}...")
                print(f"    📚 Context used: {result.get('context_used', False)}")
                
        except Exception as e:
            print(f"    💥 EXCEPTION - {str(e)}")

async def test_document_analysis():
    """Test Document Analysis Pod with available files."""
    print("\n📊 Testing Document Analysis Pod")
    print("-" * 40)
    
    # Test session ID
    test_session_id = f"test_{uuid.uuid4().hex[:8]}"
    
    # Create uploads directory
    uploads_dir = Path(f"./uploads/{test_session_id}")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Test files to analyze
    test_files = [
        "sample_employees.csv",
        "quarterly_report.csv",
        "bmo_quarterly_review.docx",
        "bmo_business_data.xlsx",
        "bmo_tech_strategy.pdf"
    ]
    
    for i, filename in enumerate(test_files, 1):
        print(f"\n  Test {i}: {filename}")
        
        # Copy test file to uploads directory
        source_file = Path(f"./test_files/{filename}")
        if not source_file.exists():
            print(f"    ⚠️  Source file not found: {source_file}")
            continue
            
        file_id = str(uuid.uuid4())
        target_file = uploads_dir / f"{file_id}_{filename}"
        
        try:
            shutil.copy2(source_file, target_file)
            
            # Create file info for analysis
            uploaded_files = {
                filename: {
                    "id": file_id,
                    "role": "Content"
                }
            }
            
            # Run document analysis
            result = await document_analysis_pod.analyze_documents(
                user_query=f"Please analyze this {filename} file and provide key insights.",
                uploaded_files=uploaded_files,
                template_instructions="",
                session_id=test_session_id
            )
            
            if result.get('error'):
                print(f"    ❌ FAILED - Error: {result['error']}")
            else:
                print(f"    ✅ SUCCESS")
                print(f"    📄 Status: {result.get('status', 'unknown')}")
                print(f"    📊 Chunks processed: {result.get('chunks_processed', 0)}")
                print(f"    📝 Result: {result['result'][:150]}...")
                
        except Exception as e:
            print(f"    💥 EXCEPTION - {str(e)}")

async def test_error_handling():
    """Test error scenarios."""
    print("\n⚠️  Testing Error Handling")
    print("-" * 40)
    
    # Test 1: Empty files
    print("\n  Test 1: Empty file list")
    try:
        result = await document_analysis_pod.analyze_documents(
            user_query="Analyze these documents",
            uploaded_files={},
            session_id="test_empty"
        )
        
        if result.get('error'):
            print(f"    ✅ Correctly handled empty files: {result['error']}")
        else:
            print(f"    ⚠️  No error for empty files")
            
    except Exception as e:
        print(f"    💥 EXCEPTION - {str(e)}")
    
    # Test 2: Empty question
    print("\n  Test 2: Empty question")
    try:
        result = await qna_pod.process_question("")
        
        if result.get('error'):
            print(f"    ✅ Correctly handled empty question: {result['error']}")
        else:
            print(f"    ⚠️  Handled empty question: {result['answer'][:50]}...")
            
    except Exception as e:
        print(f"    💥 EXCEPTION - {str(e)}")

async def test_combined_workflow():
    """Test Q&A followed by document analysis."""
    print("\n🔄 Testing Combined Workflow")
    print("-" * 40)
    
    # Step 1: Q&A
    print("\n  Step 1: Q&A Query")
    qna_result = await qna_pod.process_question("What services does BMO offer?")
    
    if qna_result.get('error'):
        print(f"    ❌ Q&A Failed - {qna_result['error']}")
    else:
        print(f"    ✅ Q&A Success - {qna_result['answer'][:100]}...")
    
    # Step 2: Document Analysis
    print("\n  Step 2: Document Analysis")
    
    # Setup test file
    test_session_id = f"workflow_{uuid.uuid4().hex[:8]}"
    uploads_dir = Path(f"./uploads/{test_session_id}")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    source_file = Path(f"./test_files/quarterly_report.csv")
    if source_file.exists():
        file_id = str(uuid.uuid4())
        target_file = uploads_dir / f"{file_id}_quarterly_report.csv"
        shutil.copy2(source_file, target_file)
        
        uploaded_files = {
            "quarterly_report.csv": {
                "id": file_id,
                "role": "Content"
            }
        }
        
        doc_result = await document_analysis_pod.analyze_documents(
            user_query="Analyze this quarterly report and relate it to BMO's services.",
            uploaded_files=uploaded_files,
            session_id=test_session_id
        )
        
        if doc_result.get('error'):
            print(f"    ❌ Document Analysis Failed - {doc_result['error']}")
        else:
            print(f"    ✅ Document Analysis Success")
            print(f"    📊 Combined workflow completed successfully!")
    else:
        print(f"    ⚠️  Test file not found for workflow test")

async def main():
    """Run all tests."""
    print("🚀 BMO Documentation Analysis Tool - Test Suite")
    print("=" * 60)
    
    try:
        # Run individual test suites
        await test_qna_pod()
        await test_document_analysis()
        await test_error_handling()
        await test_combined_workflow()
        
        print("\n" + "=" * 60)
        print("🎉 Test Suite Completed!")
        print("Check the output above for individual test results.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n💥 Test Suite Failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())