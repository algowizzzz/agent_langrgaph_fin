// API Types based on FRONTEND_API_DOCUMENTATION.md

export interface ChatRequest {
  query: string;
  session_id: string;
  active_document?: string;  // Backward compatibility
  active_documents?: string[];  // Multi-document support
}

export interface ReasoningStep {
  tool_name: string;
  tool_params: Record<string, unknown>;
  tool_output: string;
  execution_time_ms?: number;
  status?: 'success' | 'error';
}

export interface ChatResponse {
  status: 'success' | 'error';
  final_answer: string;
  reasoning_log: ReasoningStep[];
  processing_time_ms: number;
  session_id: string;
  error_message?: string;
}

export interface DocumentUploadResponse {
  status: 'success' | 'error';
  filename: string;
  chunks_created: number;
  file_size: string;
  file_type: 'PDF' | 'DOCX' | 'CSV' | 'TXT';
  processing_time_ms: number;
  error_message?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  reasoning_steps?: ReasoningStep[];
  processing_time?: number;
  status?: 'sending' | 'success' | 'error';
}

export interface UploadedDocument {
  name: string;  // Changed from filename for consistency
  file_type: 'PDF' | 'DOCX' | 'CSV' | 'TXT' | 'UNKNOWN';
  file_size: number;
  file_size_display: string;
  chunks_count: number;  // Changed from chunks_created for consistency
  upload_time: string;
  uploaded_by_session: string;
  source: string;
  active?: boolean;  // For UI state
}

// Document list response from backend
export interface DocumentListResponse {
  status: 'success' | 'error';
  documents: UploadedDocument[];
  total_count: number;
  message?: string;
}

// Document removal response
export interface DocumentRemovalResponse {
  status: 'success' | 'error';
  message: string;
}

export interface ChatSession {
  session_id: string;
  messages: Message[];
  documents: UploadedDocument[];
  created_at: Date;
  updated_at: Date;
}