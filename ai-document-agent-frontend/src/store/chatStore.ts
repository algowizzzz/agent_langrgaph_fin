// Zustand store for chat state management

import { create } from 'zustand';
import { Message, UploadedDocument, ChatSession } from '@/types/api';

interface ChatState {
  // Current session
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  
  // Documents
  documents: UploadedDocument[];
  activeDocument: string | null;
  
  // Chat actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
  
  // Document actions
  addDocument: (document: UploadedDocument) => void;
  setActiveDocument: (filename: string | null) => void;
  removeDocument: (filename: string) => void;
  
  // Session actions
  generateSessionId: () => string;
  loadSession: (session: ChatSession) => void;
  exportSession: () => ChatSession;
}

const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export const useChatStore = create<ChatState>()((set, get) => ({
  // Initial state
  sessionId: generateSessionId(),
  messages: [],
  isLoading: false,
  error: null,
  documents: [],
  activeDocument: null,

  // Chat actions
  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: generateId(),
      timestamp: new Date(),
    };
    
    set((state) => ({
      messages: [...state.messages, newMessage],
      error: null,
    }));
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },

  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
  
  clearMessages: () => set({ 
    messages: [], 
    error: null,
    sessionId: generateSessionId(),
  }),

  // Document actions
  addDocument: (document) => {
    set((state) => ({
      documents: [...state.documents.filter(d => d.filename !== document.filename), document],
      activeDocument: document.filename, // Auto-select newly uploaded document
    }));
  },

  setActiveDocument: (filename) => set({ activeDocument: filename }),

  removeDocument: (filename) => {
    set((state) => ({
      documents: state.documents.filter(d => d.filename !== filename),
      activeDocument: state.activeDocument === filename ? null : state.activeDocument,
    }));
  },

  // Session actions
  generateSessionId,

  loadSession: (session) => {
    set({
      sessionId: session.session_id,
      messages: session.messages,
      documents: session.documents,
      activeDocument: session.documents.find(d => d.active)?.filename || null,
    });
  },

  exportSession: () => {
    const state = get();
    return {
      session_id: state.sessionId,
      messages: state.messages,
      documents: state.documents.map(d => ({
        ...d,
        active: d.filename === state.activeDocument,
      })),
      created_at: new Date(state.messages[0]?.timestamp || Date.now()),
      updated_at: new Date(),
    };
  },
}));