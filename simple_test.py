#!/usr/bin/env python3
"""
Simple test to debug document analysis issues
"""

import asyncio
import uuid
import shutil
from pathlib import Path
from document_analysis_pod import document_analysis_pod

async def simple_document_test():
    """Test a single document analysis."""
    print("🔍 Simple Document Analysis Test")
    print("-" * 40)
    
    # Test session ID
    test_session_id = f"simple_test_{uuid.uuid4().hex[:8]}"
    print(f"Using session ID: {test_session_id}")
    
    # Create uploads directory
    uploads_dir = Path(f"./uploads/{test_session_id}")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created uploads directory: {uploads_dir}")
    
    # Test with CSV file (simplest format)
    filename = "sample_employees.csv"
    source_file = Path(f"./test_files/{filename}")
    
    if not source_file.exists():
        print(f"❌ Source file not found: {source_file}")
        return
    
    # Copy file to uploads directory
    file_id = str(uuid.uuid4())
    target_file = uploads_dir / f"{file_id}_{filename}"
    shutil.copy2(source_file, target_file)
    print(f"Copied file to: {target_file}")
    
    # Verify file exists
    if target_file.exists():
        print(f"✅ Target file exists: {target_file}")
        print(f"File size: {target_file.stat().st_size} bytes")
    else:
        print(f"❌ Target file missing: {target_file}")
        return
    
    # Create file info
    uploaded_files = {
        filename: {
            "id": file_id,
            "role": "Content"
        }
    }
    
    print(f"File info: {uploaded_files}")
    
    # Run document analysis
    print("\nStarting document analysis...")
    try:
        result = await document_analysis_pod.analyze_documents(
            user_query="Please analyze this employee data and provide insights.",
            uploaded_files=uploaded_files,
            template_instructions="Focus on key employee statistics and department distribution.",
            session_id=test_session_id
        )
        
        print("\n📊 Analysis Results:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Error: {result.get('error', 'None')}")
        print(f"Files processed: {result.get('files_processed', 0)}")
        print(f"Chunks processed: {result.get('chunks_processed', 0)}")
        
        if result.get('result'):
            print(f"\n📝 Analysis Result:")
            print(result['result'])
        else:
            print("❌ No analysis result returned")
            
    except Exception as e:
        print(f"💥 Exception during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_document_test())