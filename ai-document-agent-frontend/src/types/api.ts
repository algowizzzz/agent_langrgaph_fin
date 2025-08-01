// API Types based on FRONTEND_API_DOCUMENTATION.md

export interface ChatRequest {
  query: string;
  session_id: string;
  active_document?: string;
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
  filename: string;
  file_type: 'PDF' | 'DOCX' | 'CSV' | 'TXT';
  file_size: string;
  chunks_created: number;
  upload_date: Date;
  active: boolean;
}

export interface ChatSession {
  session_id: string;
  messages: Message[];
  documents: UploadedDocument[];
  created_at: Date;
  updated_at: Date;
}