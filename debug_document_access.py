#!/usr/bin/env python3
"""
Debug script to check document access and storage
"""

import asyncio
import json
from tools.document_tools import search_uploaded_docs, get_all_documents, document_chunk_store

async def debug_document_access():
    """Check what documents are available and test access."""
    
    print("🔍 DEBUGGING DOCUMENT ACCESS")
    print("=" * 40)
    
    # Check what's in the document store
    print("\n📋 Documents in store:")
    try:
        all_docs = await get_all_documents()
        for i, doc in enumerate(all_docs, 1):
            print(f"{i}. {doc.get('name', 'Unknown')} (internal: {doc.get('internal_name', 'N/A')})")
            print(f"   Type: {doc.get('file_type', 'Unknown')}, Size: {doc.get('file_size_display', 'Unknown')}")
            print(f"   Session: {doc.get('uploaded_by_session', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
    
    # Check document store keys directly
    print(f"\n📦 Direct store keys: {list(document_chunk_store.keys())}")
    
    # Test searching for risk document
    print("\n🔍 Testing document search:")
    
    test_names = [
        "riskandfinace.pdf",
        "20250801_215126_40e96e22-a0e5-41e0-a232-5f2478768aad_riskandfinace.pdf", 
        "riskandfinance.pdf"
    ]
    
    for doc_name in test_names:
        print(f"\n📄 Testing: {doc_name}")
        try:
            result = await search_uploaded_docs(doc_name=doc_name, query="risk")
            if isinstance(result, list) and len(result) > 0:
                first_result = result[0]
                if 'error' in first_result:
                    print(f"   ❌ Error: {first_result.get('error', 'Unknown error')}")
                else:
                    print(f"   ✅ Found {len(result)} results")
                    print(f"   📄 Sample: {str(first_result)[:200]}...")
            else:
                print(f"   ⚠️  No results returned")
        except Exception as e:
            print(f"   💥 Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_document_access())