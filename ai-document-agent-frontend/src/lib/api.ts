// API Client for AI Document Agent Backend

import axios, { AxiosResponse } from 'axios';
import { ChatRequest, ChatResponse, DocumentUploadResponse } from '@/types/api';

// Base configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for complex queries
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