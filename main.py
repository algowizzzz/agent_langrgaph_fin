import json
from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uuid
import os
import shutil
from pathlib import Path
import logging
from datetime import datetime

from config import config
from models import (
    ChatRequest, ChatResponse, ErrorResponse, 
    UploadResponse, SessionCleanupResponse,
    FrontendChatRequest, FrontendChatResponse, FrontendUploadResponse
)
from tools.document_tools import get_all_documents, remove_document

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format
)
logger = logging.getLogger(__name__)

app = FastAPI(title="BMO Documentation Analysis Tool")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_error_response(error_type: str, message: str, details: dict = None, status_code: int = 400) -> JSONResponse:
    """Create standardized error response."""
    error_content = {
        "error": error_type,
        "message": message,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    return JSONResponse(
        status_code=status_code,
        content=error_content
    )

def validate_file_upload(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file size and type."""
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.upload.allowed_extensions:
        return False, f"File type {file_ext} not allowed. Allowed types: {', '.join(config.upload.allowed_extensions)}"
    
    # More lenient MIME type checking - allow common variations
    allowed_mime_types = config.upload.allowed_mime_types + [
        'application/octet-stream',  # Generic binary
        'text/plain',  # Plain text
        'text/csv',    # CSV alternative
        'application/csv'  # CSV alternative
    ]
    
    if file.content_type and file.content_type not in allowed_mime_types:
        return False, f"MIME type {file.content_type} not allowed for {file_ext}"
    
    # Check file size using file.size if available
    if hasattr(file, 'size') and file.size:
        max_size = config.upload.max_file_size_mb * 1024 * 1024  # Convert to bytes
        if file.size > max_size:
            return False, f"File size {file.size / (1024*1024):.1f}MB exceeds {config.upload.max_file_size_mb}MB limit"
    
    return True, "Valid file"

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/document-processing/stats")
async def get_document_processing_stats():
    """Get statistics about document processing capabilities."""
    try:
        from tools.document_tools import document_chunk_store
        
        # Get basic stats from the document store
        all_docs = document_chunk_store.keys()
        total_docs = len(all_docs)
        
        # Calculate total chunks
        total_chunks = 0
        for doc_name in all_docs:
            chunks = document_chunk_store[doc_name]
            total_chunks += len(chunks)
        
        stats = {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "supported_formats": ["PDF", "DOCX", "CSV", "TXT"],
            "cross_session_storage": True,
            "multi_document_support": True
        }
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting document processing stats: {str(e)}")
        return create_error_response(
            error_type="stats_failed",
            message="Failed to retrieve document processing statistics",
            details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.post("/upload", response_model=FrontendUploadResponse)
async def upload_file(session_id: str, file: UploadFile = File(...)):
    """Upload, process, and validate file for document analysis."""
    from tools.document_tools import upload_document
    
    start_time = datetime.now()
    correlation_id = str(uuid.uuid4())
    logger.info(f"File upload request - session: {session_id}, file: {file.filename}, correlation_id: {correlation_id}")
    
    try:
        # Validate file
        is_valid, validation_message = validate_file_upload(file)
        if not is_valid:
            logger.warning(f"File validation failed - session: {session_id}, reason: {validation_message}, correlation_id: {correlation_id}")
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return FrontendUploadResponse(
                status="error",
                filename=file.filename or "unknown",
                chunks_created=0,
                file_size="0 KB",
                file_type="UNKNOWN",
                processing_time_ms=processing_time_ms,
                error_message=validation_message
            )
        
        # Generate file ID and create global directory (cross-session storage)
        file_id = str(uuid.uuid4())
        upload_dir = Path(f"./global_uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save file with enhanced naming for cross-session access
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file_path = upload_dir / f"{timestamp}_{file_id}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size_bytes = temp_file_path.stat().st_size
        file_size_str = f"{file_size_bytes / 1024:.1f} KB" if file_size_bytes < 1024*1024 else f"{file_size_bytes / (1024*1024):.1f} MB"
        
        # Determine file type
        file_ext = Path(file.filename).suffix.lower()
        file_type_map = {'.pdf': 'PDF', '.docx': 'DOCX', '.csv': 'CSV', '.txt': 'TXT'}
        file_type = file_type_map.get(file_ext, 'UNKNOWN')
        
        # Process document through orchestrator's document tools
        try:
            result = await upload_document(str(temp_file_path), session_id=session_id)
            chunks_created = result.get('chunks_created', 0) if isinstance(result, dict) else 0
            stored_doc_name = result.get('doc_name', file.filename) if isinstance(result, dict) else file.filename
            logger.info(f"Document processing result - session: {session_id}, result: {result}, correlation_id: {correlation_id}")
        except Exception as doc_error:
            logger.error(f"Document processing error - session: {session_id}, error: {str(doc_error)}, correlation_id: {correlation_id}")
            chunks_created = 0
            stored_doc_name = file.filename
        
        # Calculate processing time
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        logger.info(f"File uploaded and processed - session: {session_id}, chunks: {chunks_created}, stored_as: {stored_doc_name}, correlation_id: {correlation_id}")
        return FrontendUploadResponse(
            status="success",
            filename=stored_doc_name,  # Return the actual stored document name
            chunks_created=chunks_created,
            file_size=file_size_str,
            file_type=file_type,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.error(f"File upload error - session: {session_id}, error: {str(e)}, correlation_id: {correlation_id}")
        return FrontendUploadResponse(
            status="error",
            filename=file.filename or "unknown",
            chunks_created=0,
            file_size="0 KB",
            file_type="UNKNOWN",
            processing_time_ms=processing_time_ms,
            error_message=str(e)
        )

@app.get("/test-documents")
async def test_documents():
    """Test endpoint for debugging."""
    return {"message": "Test endpoint works", "timestamp": "2025-08-01"}

@app.get("/documents")
async def get_all_documents_endpoint():
    """Get list of all uploaded documents across sessions."""
    try:
        documents = await get_all_documents()
        return {
            "status": "success", 
            "documents": documents,
            "total_count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "documents": [],
            "total_count": 0
        }

@app.delete("/documents/{doc_name}")
async def delete_document_endpoint(doc_name: str):
    """Delete a document from the system."""
    try:
        result = await remove_document(doc_name)
        return result
    except Exception as e:
        logger.error(f"Error deleting document {doc_name}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/chat", response_model=FrontendChatResponse)
async def chat(request: FrontendChatRequest):
    """Handle chat requests using the Orchestrator with memory integration."""
    from orchestrator import Orchestrator
    from tools.memory_tools import get_conversation_memory
    
    start_time = datetime.now()
    correlation_id = str(uuid.uuid4())
    logger.info(f"Frontend Chat request - session: {request.session_id}, query: {request.query}, correlation_id: {correlation_id}")
    
    try:
        # Get conversation memory
        conversation_memory = get_conversation_memory()
        
        # Load conversation context
        memory_context = await conversation_memory.get_context(query=request.query)
        logger.info(f"Loaded memory context - short_term: {len(memory_context.get('short_term', []))}, summaries: {len(memory_context.get('recent_summaries', []))}")
        
        # Add user message to memory
        await conversation_memory.add_message(
            role="user",
            content=request.query,
            session_id=request.session_id
        )
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Determine active documents (support both single and multiple)
        active_docs = []
        if request.active_documents:
            active_docs = request.active_documents
        elif request.active_document:
            active_docs = [request.active_document]
        
        # Run orchestrator with the user query and memory context
        result = await orchestrator.run(
            user_query=request.query,
            session_id=request.session_id,
            active_document=request.active_document,  # Backward compatibility
            active_documents=active_docs,  # Multi-document support
            memory_context=memory_context
        )
        
        # Calculate processing time
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Add assistant response to memory
        if result.get("status") == "success":
            await conversation_memory.add_message(
                role="assistant",
                content=result.get("final_answer", ""),
                session_id=request.session_id
            )
            final_answer_for_log = result.get('final_answer', '') or ''
            logger.info(f"Added assistant response to memory - length: {len(final_answer_for_log)}")
        
        # Convert reasoning log to frontend format
        reasoning_log = []
        for step in result.get("reasoning_log", []):
            reasoning_log.append({
                "tool_name": step.get("tool_name", "unknown"),
                "tool_params": step.get("tool_params", {}),
                "tool_output": step.get("tool_output", "")
            })
        
        final_answer_str = result.get("final_answer", "")
        if isinstance(final_answer_str, dict):
            final_answer_str = json.dumps(final_answer_str)
        elif not isinstance(final_answer_str, str):
            final_answer_str = str(final_answer_str)

        response = FrontendChatResponse(
            status=result.get("status", "success"),
            final_answer=final_answer_str,
            reasoning_log=reasoning_log,
            processing_time_ms=processing_time_ms,
            session_id=request.session_id,
            error_message=result.get("error_message") if result.get("status") == "error" else None
        )
        
        logger.info(f"Chat response generated - session: {request.session_id}, processing_time: {processing_time_ms}ms, correlation_id: {correlation_id}")
        return response
        
    except Exception as e:
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.exception(f"Critical chat error - session: {request.session_id}, error: {str(e)}, correlation_id: {correlation_id}")
        
        return FrontendChatResponse(
            status="error",
            final_answer="An unexpected error occurred while processing your request. Please try again.",
            reasoning_log=[],
            processing_time_ms=processing_time_ms,
            session_id=request.session_id,
            error_message=str(e)
        )

@app.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """Download generated file."""
    correlation_id = str(uuid.uuid4())
    logger.info(f"Download request - session: {session_id}, file: {filename}, correlation_id: {correlation_id}")
    
    try:
        file_path = Path(f"./generated/{session_id}/{filename}")
        
        if not file_path.exists():
            logger.warning(f"Download file not found - session: {session_id}, file: {filename}, correlation_id: {correlation_id}")
            return create_error_response(
                error_type="file_not_found",
                message=f"File {filename} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"File download successful - session: {session_id}, file: {filename}, correlation_id: {correlation_id}")
        return FileResponse(file_path, filename=filename)
        
    except Exception as e:
        logger.error(f"Download error - session: {session_id}, error: {str(e)}, correlation_id: {correlation_id}")
        return create_error_response(
            error_type="download_failed",
            message="Failed to download file",
            details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.delete("/session/{session_id}", response_model=SessionCleanupResponse)
async def cleanup_session(session_id: str):
    """Clean up session files."""
    correlation_id = str(uuid.uuid4())
    logger.info(f"Session cleanup request - session: {session_id}, correlation_id: {correlation_id}")
    
    try:
        # Clean upload and generated directories
        for dir_path in [f"./uploads/{session_id}", f"./generated/{session_id}"]:
            path = Path(dir_path)
            if path.exists():
                shutil.rmtree(path)
                logger.info(f"Cleaned directory: {dir_path}")
        
        logger.info(f"Session cleanup successful - session: {session_id}, correlation_id: {correlation_id}")
        return SessionCleanupResponse(status="success", message="Session cleaned up")
        
    except Exception as e:
        logger.error(f"Session cleanup error - session: {session_id}, error: {str(e)}, correlation_id: {correlation_id}")
        return create_error_response(
            error_type="cleanup_failed",
            message="Failed to clean up session",
            details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api.host, port=config.api.port)