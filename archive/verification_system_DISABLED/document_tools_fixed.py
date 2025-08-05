"""
Fixed document tools with proper error handling instead of mock configuration
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from datetime import datetime

# Import core functionality
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

logger = logging.getLogger(__name__)

# Check for optional dependencies
HAS_PDF_SUPPORT = True
HAS_DOCX_SUPPORT = True

try:
    import PyPDF2
except ImportError:
    HAS_PDF_SUPPORT = False
    logging.warning("PyPDF2 not available. PDF processing disabled.")

try:
    import docx
except ImportError:
    HAS_DOCX_SUPPORT = False
    logging.warning("python-docx not available. DOCX processing disabled.")

class ConfigurationError:
    """Structured error response for configuration failures"""
    
    @staticmethod
    def create_error(error_type: str, message: str, suggested_action: str = None) -> Dict:
        return {
            "error_type": error_type,
            "success": False,
            "message": message,
            "suggested_action": suggested_action,
            "retryable": False,
            "replanning_hints": {
                "configuration_error": True,
                "reason": message
            }
        }

# Use real config with proper error handling
try:
    from config import config
    logger.info(f"Using real config: chunk_size={config.ai.chunk_size}, chunk_overlap={config.ai.chunk_overlap}")
except ImportError as e:
    logger.error(f"Could not import config: {e}")
    # Don't create a mock - return error when needed
    config = None

class DocumentProcessor:
    """Service for processing uploaded documents into text chunks with proper error handling."""
    
    def __init__(self):
        if config is None:
            raise ValueError("Configuration not available. Cannot initialize DocumentProcessor without config.")
        
        self.headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        self.markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on, strip_headers=False)
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.ai.chunk_size, 
            chunk_overlap=config.ai.chunk_overlap
        )

def _get_document_store_path() -> str:
    """Get the path to the document store with error handling."""
    try:
        store_path = "document_store.json"
        if not os.path.exists(store_path):
            # Initialize empty document store
            with open(store_path, 'w') as f:
                json.dump({}, f)
            logger.info(f"Initialized new document store at {store_path}")
        return store_path
    except Exception as e:
        logger.error(f"Error accessing document store: {e}")
        raise

def _load_document_store() -> Dict:
    """Load document store with proper error handling."""
    try:
        store_path = _get_document_store_path()
        with open(store_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading document store: {e}")
        return {}

def _save_document_store(store_data: Dict) -> bool:
    """Save document store with error handling."""
    try:
        store_path = _get_document_store_path()
        with open(store_path, 'w') as f:
            json.dump(store_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving document store: {e}")
        return False

async def upload_document(file_path: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Upload and process a document with proper error handling.
    """
    logger.info(f"Processing document upload: {file_path} for session {session_id}")
    
    # Configuration check
    if config is None:
        return ConfigurationError.create_error(
            error_type="configuration_missing",
            message="Configuration not available. Cannot process documents without config.",
            suggested_action="check_config_import_and_setup"
        )
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "error_type": "file_not_found",
                "success": False,
                "message": f"File not found: {file_path}",
                "suggested_action": "check_file_path",
                "retryable": False
            }
        
        # Check file type support
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf' and not HAS_PDF_SUPPORT:
            return {
                "error_type": "pdf_support_missing",
                "success": False,
                "message": "PDF support not available. Install PyPDF2: pip install PyPDF2",
                "suggested_action": "install_pdf_dependencies",
                "retryable": False
            }
        
        if file_ext == '.docx' and not HAS_DOCX_SUPPORT:
            return {
                "error_type": "docx_support_missing", 
                "success": False,
                "message": "DOCX support not available. Install python-docx: pip install python-docx",
                "suggested_action": "install_docx_dependencies",
                "retryable": False
            }
        
        # Process the document
        try:
            processor = DocumentProcessor()
        except ValueError as e:
            return ConfigurationError.create_error(
                error_type="processor_init_failed",
                message=str(e),
                suggested_action="fix_configuration_import"
            )
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text_content = _extract_pdf_text(file_path)
        elif file_ext == '.docx':
            text_content = _extract_docx_text(file_path)
        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        else:
            return {
                "error_type": "unsupported_file_type",
                "success": False,
                "message": f"Unsupported file type: {file_ext}. Supported: .pdf, .docx, .txt",
                "suggested_action": "convert_to_supported_format",
                "retryable": False
            }
        
        if not text_content:
            return {
                "error_type": "no_text_extracted",
                "success": False,
                "message": f"No text content could be extracted from {file_path}",
                "suggested_action": "check_file_content_and_format",
                "retryable": False
            }
        
        # Create chunks
        chunks = processor.recursive_splitter.split_text(text_content)
        
        # Generate document ID
        doc_id = hashlib.md5(f"{file_path}_{session_id}".encode()).hexdigest()
        
        # Prepare document metadata
        doc_info = {
            "doc_id": doc_id,
            "original_filename": os.path.basename(file_path),
            "file_path": file_path,
            "session_id": session_id,
            "upload_timestamp": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path),
            "text_length": len(text_content),
            "chunk_count": len(chunks),
            "chunk_size": config.ai.chunk_size,
            "chunk_overlap": config.ai.chunk_overlap
        }
        
        # Save to document store
        store_data = _load_document_store()
        if session_id not in store_data:
            store_data[session_id] = {}
        
        store_data[session_id][doc_id] = {
            "metadata": doc_info,
            "chunks": [{"text": chunk, "chunk_id": i} for i, chunk in enumerate(chunks)]
        }
        
        if not _save_document_store(store_data):
            return {
                "error_type": "document_store_save_failed",
                "success": False,
                "message": "Failed to save document to store",
                "suggested_action": "check_file_permissions_and_disk_space",
                "retryable": True
            }
        
        logger.info(f"Successfully processed document {doc_id}: {len(chunks)} chunks created")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "filename": doc_info["original_filename"],
            "chunks_created": len(chunks),
            "text_length": len(text_content),
            "processing_details": {
                "chunk_size": config.ai.chunk_size,
                "chunk_overlap": config.ai.chunk_overlap,
                "file_type": file_ext
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {e}")
        return {
            "error_type": "document_processing_error",
            "success": False,
            "message": f"Error processing document: {str(e)}",
            "suggested_action": "check_file_format_and_try_again",
            "retryable": True
        }

def _extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF with error handling."""
    if not HAS_PDF_SUPPORT:
        raise ValueError("PDF support not available")
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise

def _extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX with error handling."""
    if not HAS_DOCX_SUPPORT:
        raise ValueError("DOCX support not available")
    
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {e}")
        raise

async def search_uploaded_docs(doc_name: str, query: str, session_id: str = "default") -> List[Dict]:
    """
    Search through uploaded documents with proper error handling.
    """
    logger.info(f"Searching document '{doc_name}' for '{query}' in session {session_id}")
    
    try:
        store_data = _load_document_store()
        
        if session_id not in store_data:
            return [{
                "error_type": "session_not_found",
                "success": False,
                "message": f"No documents found for session: {session_id}",
                "suggested_action": "upload_documents_first",
                "retryable": False
            }]
        
        session_docs = store_data[session_id]
        
        # Find document by name
        matching_docs = []
        for doc_id, doc_data in session_docs.items():
            filename = doc_data["metadata"]["original_filename"]
            if doc_name.lower() in filename.lower() or doc_name == doc_id:
                matching_docs.append((doc_id, doc_data))
        
        if not matching_docs:
            available_docs = [doc_data["metadata"]["original_filename"] for doc_data in session_docs.values()]
            return [{
                "error_type": "document_not_found",
                "success": False,
                "message": f"Document '{doc_name}' not found in session {session_id}",
                "available_documents": available_docs,
                "suggested_action": "use_exact_document_name_or_upload_document",
                "retryable": False
            }]
        
        # Search in matching documents
        results = []
        for doc_id, doc_data in matching_docs:
            chunks = doc_data["chunks"]
            query_lower = query.lower()
            
            for chunk in chunks:
                chunk_text = chunk["text"]
                if query_lower in chunk_text.lower():
                    results.append({
                        "doc_id": doc_id,
                        "filename": doc_data["metadata"]["original_filename"],
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk_text,
                        "relevance_score": chunk_text.lower().count(query_lower) / len(chunk_text.split())
                    })
        
        if not results:
            return [{
                "error_type": "no_search_results",
                "success": False,
                "message": f"No results found for query '{query}' in document '{doc_name}'",
                "suggested_action": "try_broader_search_terms",
                "retryable": True
            }]
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info(f"Found {len(results)} search results for '{query}' in '{doc_name}'")
        return results[:10]  # Return top 10 results
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return [{
            "error_type": "search_error",
            "success": False,
            "message": f"Error during document search: {str(e)}",
            "suggested_action": "check_document_store_integrity",
            "retryable": True
        }]

async def discover_document_structure(doc_name: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Analyze document structure with proper error handling.
    """
    logger.info(f"Analyzing structure of document '{doc_name}' in session {session_id}")
    
    try:
        store_data = _load_document_store()
        
        if session_id not in store_data:
            return {
                "error_type": "session_not_found",
                "success": False,
                "message": f"No documents found for session: {session_id}",
                "suggested_action": "upload_documents_first"
            }
        
        session_docs = store_data[session_id]
        
        # Find document
        doc_data = None
        for doc_id, data in session_docs.items():
            if doc_name.lower() in data["metadata"]["original_filename"].lower() or doc_name == doc_id:
                doc_data = data
                break
        
        if not doc_data:
            available_docs = [data["metadata"]["original_filename"] for data in session_docs.values()]
            return {
                "error_type": "document_not_found",
                "success": False,
                "message": f"Document '{doc_name}' not found",
                "available_documents": available_docs,
                "suggested_action": "use_exact_document_name"
            }
        
        # Analyze structure
        metadata = doc_data["metadata"]
        chunks = doc_data["chunks"]
        
        structure = {
            "success": True,
            "document_info": {
                "filename": metadata["original_filename"],
                "file_size": metadata["file_size"],
                "text_length": metadata["text_length"],
                "chunk_count": metadata["chunk_count"],
                "upload_date": metadata["upload_timestamp"]
            },
            "chunk_analysis": {
                "total_chunks": len(chunks),
                "average_chunk_size": sum(len(chunk["text"]) for chunk in chunks) // len(chunks),
                "chunk_size_distribution": _analyze_chunk_sizes(chunks)
            }
        }
        
        logger.info(f"Successfully analyzed structure of '{doc_name}'")
        return structure
        
    except Exception as e:
        logger.error(f"Error analyzing document structure: {e}")
        return {
            "error_type": "structure_analysis_error",
            "success": False,
            "message": f"Error analyzing document structure: {str(e)}",
            "suggested_action": "check_document_integrity"
        }

def _analyze_chunk_sizes(chunks: List[Dict]) -> Dict:
    """Analyze chunk size distribution."""
    sizes = [len(chunk["text"]) for chunk in chunks]
    return {
        "min_size": min(sizes),
        "max_size": max(sizes),
        "avg_size": sum(sizes) // len(sizes),
        "total_chunks": len(chunks)
    }