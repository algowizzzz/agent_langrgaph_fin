#!/usr/bin/env python3
"""
Test individual tools in isolation to debug CSV processing issues
"""

import asyncio
import logging
import json
import sys
import os
from pathlib import Path

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tool_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.document_tools import upload_document, search_uploaded_docs, document_chunk_store
from tools.code_execution_tools import process_table_data

async def test_csv_upload():
    """Test CSV document upload"""
    logger.info("=== Testing CSV Document Upload ===")
    
    test_file = "test_documents/sample_data.csv"
    if not os.path.exists(test_file):
        logger.error(f"Test file {test_file} not found")
        return None
    
    try:
        result = await upload_document(test_file)
        logger.info(f"Upload result: {result}")
        return result.get('doc_name') if result.get('status') == 'success' else None
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return None

async def test_document_search(doc_name):
    """Test document search functionality"""
    logger.info(f"=== Testing Document Search for {doc_name} ===")
    
    try:
        # Test basic search
        result = await search_uploaded_docs(doc_name, retrieve_full_doc=True)
        logger.info(f"Search result type: {type(result)}")
        logger.info(f"Search result length: {len(result) if isinstance(result, list) else 'N/A'}")
        
        if isinstance(result, list) and len(result) > 0:
            logger.info(f"First chunk keys: {result[0].keys() if isinstance(result[0], dict) else 'Not a dict'}")
            logger.info(f"First chunk content preview: {str(result[0])[:200]}...")
        
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return None

async def test_process_table_data(chunks):
    """Test process_table_data tool with document chunks"""
    logger.info("=== Testing process_table_data Tool ===")
    
    if not chunks:
        logger.error("No chunks provided to process_table_data")
        return None
    
    try:
        logger.info(f"Input chunks type: {type(chunks)}")
        logger.info(f"Input chunks length: {len(chunks)}")
        logger.info(f"First chunk structure: {chunks[0].keys() if isinstance(chunks[0], dict) else 'Not a dict'}")
        
        result = await process_table_data(chunks, operation='summary')
        logger.info(f"process_table_data result: {result}")
        return result
    except Exception as e:
        logger.error(f"process_table_data failed: {e}")
        logger.exception("Full traceback:")
        return None

def examine_document_store():
    """Examine what's in the document store"""
    logger.info("=== Examining Document Store ===")
    
    try:
        # Check document store keys
        docs = document_chunk_store.keys()
        logger.info(f"Documents in store: {list(docs)}")
        
        # Find CSV documents
        csv_docs = [doc for doc in docs if 'csv' in doc.lower()]
        logger.info(f"CSV documents found: {csv_docs}")
        
        if csv_docs:
            latest_csv = csv_docs[-1]  # Get the latest
            chunks = document_chunk_store[latest_csv]
            logger.info(f"Latest CSV ({latest_csv}) has {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Chunk {i}:")
                logger.info(f"  Type: {type(chunk)}")
                logger.info(f"  Keys: {chunk.keys() if isinstance(chunk, dict) else 'Not a dict'}")
                if isinstance(chunk, dict) and 'page_content' in chunk:
                    content = chunk['page_content']
                    logger.info(f"  Content preview: {content[:100]}...")
                    logger.info(f"  Content type: {type(content)}")
        
        return csv_docs
    except Exception as e:
        logger.error(f"Document store examination failed: {e}")
        return []

async def main():
    """Run all tests in sequence"""
    logger.info("Starting individual tool testing with verbose logging")
    
    # Step 1: Examine current document store
    csv_docs = examine_document_store()
    
    # Step 2: Upload a fresh CSV document
    doc_name = await test_csv_upload()
    if not doc_name:
        logger.error("CSV upload failed, cannot continue")
        return
    
    # Step 3: Re-examine document store after upload
    logger.info("\n=== Document Store After Upload ===")
    examine_document_store()
    
    # Step 4: Search for the uploaded document
    chunks = await test_document_search(doc_name)
    if not chunks:
        logger.error("Document search failed, cannot continue")
        return
    
    # Step 5: Test process_table_data with the chunks
    result = await test_process_table_data(chunks)
    
    # Step 6: Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"✅ CSV Upload: {'SUCCESS' if doc_name else 'FAILED'}")
    logger.info(f"✅ Document Search: {'SUCCESS' if chunks else 'FAILED'}")
    logger.info(f"✅ Table Processing: {'SUCCESS' if result and result.get('status') == 'success' else 'FAILED'}")
    
    if result:
        logger.info(f"Final result: {json.dumps(result, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())