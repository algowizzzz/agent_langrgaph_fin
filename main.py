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
    UploadResponse, SessionCleanupResponse
)

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
        from document_processor import document_processor
        stats = document_processor.get_processing_stats()
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

@app.post("/upload", response_model=UploadResponse)
async def upload_file(session_id: str, file: UploadFile = File(...)):
    """Upload and validate file."""
    correlation_id = str(uuid.uuid4())
    logger.info(f"File upload request - session: {session_id}, file: {file.filename}, correlation_id: {correlation_id}")
    
    try:
        # Validate file
        is_valid, validation_message = validate_file_upload(file)
        if not is_valid:
            logger.warning(f"File validation failed - session: {session_id}, reason: {validation_message}, correlation_id: {correlation_id}")
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "size" in validation_message.lower() else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            error_type = "file_too_large" if status_code == 413 else "unsupported_file_type"
            return create_error_response(
                error_type=error_type,
                message=validation_message,
                status_code=status_code
            )
        
        # Generate file ID and create directory
        file_id = str(uuid.uuid4())
        upload_dir = Path(f"./uploads/{session_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / f"{file_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded successfully - session: {session_id}, file_id: {file_id}, correlation_id: {correlation_id}")
        return UploadResponse(file_id=file_id, status="success")
        
    except Exception as e:
        logger.error(f"File upload error - session: {session_id}, error: {str(e)}, correlation_id: {correlation_id}")
        return create_error_response(
            error_type="upload_failed",
            message="Failed to upload file",
            details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests with dynamic pod integration."""
    from qna_pod import qna_pod
    from document_analysis_pod import document_analysis_pod
    
    correlation_id = str(uuid.uuid4())
    logger.info(f"Chat request - session: {request.session_id}, correlation_id: {correlation_id}")
    
    try:
        # Route to appropriate pod based on uploaded files
        if request.uploaded_files:
            user_message = request.messages[-1].content if request.messages else ""
            
            template_instructions = ""
            template_files = {name: info for name, info in request.uploaded_files.items() if info.role == "Template"}
            if template_files:
                template_instructions = f"Analysis guided by {len(template_files)} template file(s)"
            
            analysis_result = await document_analysis_pod.analyze_documents(
                user_query=user_message,
                uploaded_files=request.uploaded_files,
                template_instructions=template_instructions,
                session_id=request.session_id
            )
            
            response = ChatResponse(
                role="assistant",
                content=analysis_result["result"],
                status="success" if not analysis_result.get("error") else "error",
                source="Document Analysis Pod",
                reasoning_steps=analysis_result.get("reasoning_steps", []),
                thoughts=analysis_result.get("thoughts", "")
            )
            
            logger.info(f"Document Analysis result - files: {analysis_result.get('files_processed', 0)}, "
                        f"chunks: {analysis_result.get('chunks_processed', 0)}, "
                        f"status: {analysis_result.get('status', 'unknown')}, correlation_id: {correlation_id}")
        else:
            user_message = request.messages[-1].content if request.messages else ""
            qna_result = await qna_pod.process_question(user_message)
            
            response = ChatResponse(
                role="assistant",
                content=qna_result["answer"],
                status="success" if not qna_result.get("error") else "error",
                source=qna_result["source"]
            )
            
            logger.info(f"Q&A Pod result - context_used: {qna_result.get('context_used', False)}, "
                        f"num_pairs: {qna_result.get('num_context_pairs', 0)}, correlation_id: {correlation_id}")
        
        logger.info(f"Chat response generated - session: {request.session_id}, correlation_id: {correlation_id}")
        return response
        
    except Exception as e:
        logger.exception(f"Critical chat error - session: {request.session_id}, error: {str(e)}, correlation_id: {correlation_id}")
        return create_error_response(
            error_type="chat_failed",
            message="An unexpected error occurred while processing your request.",
            details={"error": str(e), "correlation_id": correlation_id},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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