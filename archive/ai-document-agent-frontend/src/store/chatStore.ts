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
  activeDocument: string | null;  // Backward compatibility
  activeDocuments: string[];  // Multi-document support
  
  // Chat actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => string;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
  
  // Document actions
  addDocument: (document: UploadedDocument) => void;
  setActiveDocument: (filename: string | null) => void;  // Backward compatibility
  removeDocument: (filename: string) => void;
  // Multi-document actions
  toggleActiveDocument: (filename: string) => void;
  setActiveDocuments: (filenames: string[]) => void;
  clearActiveDocuments: () => void;
  
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
  activeDocuments: [],

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
    
    return newMessage.id;
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
      documents: [...state.documents.filter(d => d.internal_name !== document.internal_name), document],
      activeDocument: document.internal_name, // Auto-select newly uploaded document (use internal_name for backend)
      activeDocuments: [document.internal_name], // Auto-select for multi-document (use internal_name for backend)
    }));
  },

  setActiveDocument: (filename) => set({ 
    activeDocument: filename,
    activeDocuments: filename ? [filename] : []
  }),

  removeDocument: (filename) => {
    set((state) => ({
      documents: state.documents.filter(d => d.internal_name !== filename),
      activeDocument: state.activeDocument === filename ? null : state.activeDocument,
      activeDocuments: state.activeDocuments.filter(name => name !== filename),
    }));
  },

  // Multi-document actions
  toggleActiveDocument: (filename) => {
    set((state) => {
      const isActive = state.activeDocuments.includes(filename);
      const newActiveDocuments = isActive 
        ? state.activeDocuments.filter(name => name !== filename)
        : [...state.activeDocuments, filename];
      
      return {
        activeDocuments: newActiveDocuments,
        activeDocument: newActiveDocuments.length === 1 ? newActiveDocuments[0] : null
      };
    });
  },

  setActiveDocuments: (filenames) => set({ 
    activeDocuments: filenames,
    activeDocument: filenames.length === 1 ? filenames[0] : null
  }),

  clearActiveDocuments: () => set({ 
    activeDocuments: [],
    activeDocument: null
  }),

  // Session actions
  generateSessionId,

  loadSession: (session) => {
    const activeDocuments = session.documents.filter(d => d.active).map(d => d.name);
    set({
      sessionId: session.session_id,
      messages: session.messages,
      documents: session.documents,
      activeDocument: activeDocuments.length === 1 ? activeDocuments[0] : null,
      activeDocuments: activeDocuments,
    });
  },

  exportSession: () => {
    const state = get();
    return {
      session_id: state.sessionId,
      messages: state.messages,
      documents: state.documents.map(d => ({
        ...d,
        active: state.activeDocuments.includes(d.name),
      })),
      created_at: new Date(state.messages[0]?.timestamp || Date.now()),
      updated_at: new Date(),
    };
  },
}));