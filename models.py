from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class UploadedFileInfo(BaseModel):
    id: str
    role: Literal["Content", "Template"]

class ChatRequest(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    uploaded_files: Dict[str, UploadedFileInfo] = {}

class ChatResponse(BaseModel):
    role: Literal["assistant"]
    content: str
    status: str = "success"
    source: Optional[str] = None
    reasoning_steps: List[Dict] = []
    thoughts: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None
    timestamp: datetime = datetime.now()

class UploadResponse(BaseModel):
    file_id: str
    status: str = "success"

class SessionCleanupResponse(BaseModel):
    status: str = "success"
    message: str = "Session cleaned up"