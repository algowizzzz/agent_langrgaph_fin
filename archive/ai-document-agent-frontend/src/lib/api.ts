// API Client for AI Document Agent Backend

import axios, { AxiosResponse } from 'axios';
import { ChatRequest, ChatResponse, DocumentUploadResponse, DocumentListResponse, DocumentRemovalResponse } from '@/types/api';

// Base configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for complex document analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth (if needed)
apiClient.interceptors.request.use((config) => {
  const token = process.env.NEXT_PUBLIC_API_KEY;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class DocumentAgentAPI {
  /**
   * Send a chat message to the AI Document Agent
   */
  static async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await apiClient.post('/chat', request);
    return response.data;
  }

  /**
   * Send a chat message with real-time streaming of reasoning steps
   */
  static async sendChatMessageStreaming(
    request: ChatRequest,
    onReasoningStep: (step: any) => void,
    onFinalAnswer: (answer: string, reasoningLog: any[]) => void,
    onError: (error: string) => void,
    onComplete: () => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)); // Remove 'data: ' prefix
              
              if (data.type === 'reasoning_step' || data.type === 'status') {
                onReasoningStep(data);
              } else if (data.type === 'final_answer') {
                onFinalAnswer(data.content, data.reasoning_log || []);
              } else if (data.type === 'error') {
                onError(data.message);
                return;
              } else if (data.type === 'complete') {
                onComplete();
                return;
              }
            } catch (parseError) {
              console.warn('Failed to parse streaming data:', line, parseError);
            }
          }
        }
      }
      
      onComplete();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown streaming error');
    }
  }

  /**
   * Upload a document for analysis
   */
  static async uploadDocument(file: File, sessionId: string): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<DocumentUploadResponse> = await apiClient.post(
      `/upload?session_id=${sessionId}`, 
      formData, 
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Test backend connectivity
   */
  static async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response: AxiosResponse = await apiClient.get('/health');
    return response.data;
  }

  /**
   * Get all uploaded documents across sessions
   */
  static async getAllDocuments(): Promise<DocumentListResponse> {
    const response: AxiosResponse<DocumentListResponse> = await apiClient.get('/documents');
    return response.data;
  }

  /**
   * Remove a document from the system
   */
  static async removeDocument(documentName: string): Promise<DocumentRemovalResponse> {
    const response: AxiosResponse<DocumentRemovalResponse> = await apiClient.delete(`/documents/${encodeURIComponent(documentName)}`);
    return response.data;
  }
}

// Proven query patterns from validation testing
export const PROVEN_QUERY_PATTERNS = {
  WORD_COUNTING: [
    'count of word risk',
    'how many times does the word "analysis" appear?',
    'word frequency for "management"',
  ],
  DOCUMENT_SUMMARY: [
    'summarize this document',
    'provide a summary of the main points',
    'what are the key insights from this document?',
  ],
  KEY_CONCEPTS: [
    'what are the main topics?',
    'extract key concepts',
    'identify the main themes',
  ],
  DATA_ANALYSIS: [
    'analyze this CSV data',
    'what insights can you extract from this data?',
    'create a chart from this data',
  ],
  MEMORY_QUERIES: [
    'what do you remember about my previous documents?',
    'what did I ask about earlier?',
    'recall our conversation about X',
  ],
} as const;

export default DocumentAgentAPI;