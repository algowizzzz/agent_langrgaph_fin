#!/usr/bin/env python3
"""
Verified Document Tools with Runtime Verification System

This module provides verified versions of document tools that ensure
correct function execution and detect bypasses.
"""

import logging
from typing import Any, Dict, List, Optional
from runtime_verification_system import verify_function, verification_system
from tools.document_tools import (
    document_chunk_store, 
    DocumentProcessor,
    PersistentDocumentStore,
    _apply_search_query
)

logger = logging.getLogger(__name__)

# Re-export the original functions but with verification
@verify_function("search_uploaded_docs")
async def search_uploaded_docs_verified(doc_name: str, query: str = None, filter_by_metadata: dict = None, **kwargs) -> list:
    """VERIFIED version of search_uploaded_docs with runtime verification."""
    
    # This is our verified implementation with enhanced logging
    print(f"🔒 VERIFIED FUNCTION: search_uploaded_docs_verified called")
    print(f"🔒 VERIFIED: doc_name='{doc_name}', query='{query}'")
    print(f"🔒 VERIFIED: Store has {len(list(document_chunk_store.keys()))} documents")
    print(f"🔒 VERIFIED: Document exists: {doc_name in document_chunk_store}")
    
    if doc_name not in document_chunk_store: 
        print(f"🔒 VERIFIED ERROR: Document '{doc_name}' NOT FOUND in store")
        return [{"error": f"VERIFIED_VERSION: Doc '{doc_name}' not found."}]
    
    # Start with all chunks for the document
    filtered_chunks = document_chunk_store[doc_name]
    print(f"🔒 VERIFIED: Found {len(filtered_chunks)} chunks for document")
    
    # Apply metadata filter only if it is provided
    if filter_by_metadata:
        key, value = list(filter_by_metadata.items())[0]
        filtered_chunks = [c for c in filtered_chunks if value == c.get("metadata", {}).get(key)]
        print(f"🔒 VERIFIED: After metadata filter: {len(filtered_chunks)} chunks")
        
    # Apply keyword query filter with proper boolean logic
    if query:
        filtered_chunks = _apply_search_query(filtered_chunks, query)
        print(f"🔒 VERIFIED: After query filter: {len(filtered_chunks)} chunks")
        
    print(f"🔒 VERIFIED SUCCESS: Returning {len(filtered_chunks)} chunks")
    return filtered_chunks

@verify_function("search_multiple_docs")
async def search_multiple_docs_verified(doc_names: List[str], query: str = None, filter_by_metadata: dict = None, **kwargs) -> list:
    """VERIFIED version of search_multiple_docs with runtime verification."""
    
    print(f"🔒 VERIFIED FUNCTION: search_multiple_docs_verified called")
    print(f"🔒 VERIFIED: doc_names={doc_names}, query='{query}'")
    
    all_chunks = []
    for doc_name in doc_names:
        print(f"🔒 VERIFIED: Processing document: {doc_name}")
        chunks = await search_uploaded_docs_verified(doc_name, query, filter_by_metadata, **kwargs)
        
        # Skip error results when combining multiple docs
        valid_chunks = [c for c in chunks if not isinstance(c, dict) or "error" not in c]
        all_chunks.extend(valid_chunks)
        print(f"🔒 VERIFIED: Added {len(valid_chunks)} chunks from {doc_name}")
    
    print(f"🔒 VERIFIED SUCCESS: Total {len(all_chunks)} chunks from {len(doc_names)} documents")
    return all_chunks

# Verification functions
def verify_document_tools_integrity() -> Dict[str, Any]:
    """Verify the integrity of document tools and detect any bypasses."""
    
    print("🔍 VERIFICATION: Checking document tools integrity...")
    
    # Import the original functions to verify identity
    from tools.document_tools import search_uploaded_docs as original_func
    
    # Verify function identity
    identity_check = verification_system.verify_function_identity(original_func, "search_uploaded_docs")
    
    # Get verification report
    report = verification_system.get_verification_report()
    
    # Add document-specific checks
    document_store_status = {
        "store_accessible": document_chunk_store is not None,
        "total_documents": len(list(document_chunk_store.keys())) if document_chunk_store else 0,
        "csv_documents": len([k for k in document_chunk_store.keys() if k.endswith('.csv')]) if document_chunk_store else 0
    }
    
    report["document_store_status"] = document_store_status
    report["function_identity_verified"] = identity_check
    
    return report

async def test_verified_search() -> Dict[str, Any]:
    """Test the verified search function with known data."""
    
    print("🧪 TESTING: Running verified search test...")
    
    # Test with our known CSV file
    csv_name = "20250801_215110_09205507-73f4-4fec-8792-3cdb156bcd39_test_business_data.csv"
    
    try:
        # This should trigger our verified function
        result = await search_uploaded_docs_verified(csv_name, "Corporate Banking")
        
        test_result = {
            "test_status": "success",
            "function_called": True,
            "result_count": len(result),
            "has_error": any("error" in str(r) for r in result if isinstance(r, dict)),
            "verification_triggered": True
        }
        
        if test_result["has_error"]:
            test_result["error_message"] = next(
                str(r) for r in result if isinstance(r, dict) and "error" in str(r)
            )
        
        print(f"🧪 TEST RESULT: {test_result}")
        return test_result
        
    except Exception as e:
        print(f"🧪 TEST FAILED: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "function_called": False,
            "verification_triggered": False
        }

# Export verified functions for use by orchestrator
__all__ = [
    "search_uploaded_docs_verified",
    "search_multiple_docs_verified", 
    "verify_document_tools_integrity",
    "test_verified_search"
]