#!/usr/bin/env python3

import asyncio
import sys
from document_analysis_pod import document_analysis_pod

async def test_document_analysis():
    print("Testing Document Analysis Pod...")
    
    # Test data
    uploaded_files = {
        "test_document.csv": {
            "id": "73f31d03-a371-4398-a0b4-dbaa0f15327f",
            "role": "Content"
        }
    }
    
    # Test with correct parameters  
    result = await document_analysis_pod.analyze_documents(
        user_query="Please analyze this employee data",
        uploaded_files=uploaded_files,
        template_instructions="",
        session_id="doc_test_123"
    )
    
    print("Result:")
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    print(f"Files processed: {result['files_processed']}")
    print(f"Chunks processed: {result['chunks_processed']}")
    print("\nContent preview:")
    print(result['result'][:500] + "..." if len(result['result']) > 500 else result['result'])

if __name__ == "__main__":
    asyncio.run(test_document_analysis())