# 🚀 Frontend Implementation Guide

**Quick Start Guide for Building the AI Document Agent Frontend**

---

## 📦 **Technology Stack Recommendation**

### **Framework & Core**
- **React 18+** with TypeScript for type safety
- **Next.js 14** for SSR and routing (recommended)
- **Tailwind CSS** for rapid styling (matches design system)
- **Framer Motion** for smooth animations

### **State Management**
- **Zustand** for global state (lightweight, modern)
- **React Query/TanStack Query** for API state management
- **React Hook Form** for form handling

### **File Upload & Utilities**
- **React Dropzone** for drag-and-drop file upload
- **Axios** for HTTP requests with interceptors
- **date-fns** for timestamp formatting

---

## 🏃‍♂️ **Quick Start Implementation**

### **1. Project Setup**
```bash
# Create Next.js project with TypeScript
npx create-next-app@latest ai-document-agent --typescript --tailwind --app

# Install dependencies
npm install zustand @tanstack/react-query axios react-dropzone framer-motion
npm install @types/node @types/react @types/react-dom
```

### **2. API Client Setup**
```typescript
// lib/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = process.env.NEXT_PUBLIC_API_KEY;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ChatRequest {
  query: string;
  session_id: string;
  active_document?: string;
}

export interface ChatResponse {
  status: 'success' | 'error';
  final_answer: string;
  reasoning_log: ReasoningStep[];
  processing_time_ms: number;
  session_id: string;
  error_message?: string;
}

export const chatApi = {
  sendMessage: (data: ChatRequest): Promise<ChatResponse> =>
    apiClient.post('/api/chat', data).then(res => res.data),
    
  uploadDocument: (file: File, sessionId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    return apiClient.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data);
  },
};
```

### **3. Global State Setup**
```typescript
// store/chatStore.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'reasoning';
  content: string;
  timestamp: string;
  reasoning_log?: ReasoningStep[];
}

interface ChatStore {
  messages: Message[];
  currentSession: string;
  activeDocument: string | null;
  isLoading: boolean;
  
  // Actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setLoading: (loading: boolean) => void;
  setActiveDocument: (filename: string | null) => void;
  clearChat: () => void;
  generateSessionId: () => string;
}

export const useChatStore = create<ChatStore>()(
  devtools((set, get) => ({
    messages: [],
    currentSession: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    activeDocument: null,
    isLoading: false,
    
    addMessage: (message) => set((state) => ({
      messages: [...state.messages, {
        ...message,
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        timestamp: new Date().toISOString(),
      }]
    })),
    
    setLoading: (loading) => set({ isLoading: loading }),
    
    setActiveDocument: (filename) => set({ activeDocument: filename }),
    
    clearChat: () => set({
      messages: [],
      currentSession: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    }),
    
    generateSessionId: () => {
      const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      set({ currentSession: sessionId });
      return sessionId;
    },
  }))
);
```

### **4. Core Chat Component**
```tsx
// components/ChatInterface.tsx
'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { chatApi } from '@/lib/api';
import { useChatStore } from '@/store/chatStore';
import MessageBubble from './MessageBubble';
import ReasoningSteps from './ReasoningSteps';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const { 
    messages, 
    currentSession, 
    activeDocument, 
    isLoading,
    addMessage, 
    setLoading 
  } = useChatStore();

  const chatMutation = useMutation({
    mutationFn: chatApi.sendMessage,
    onMutate: () => setLoading(true),
    onSuccess: (data) => {
      // Add reasoning if available
      if (data.reasoning_log?.length > 0) {
        addMessage({
          role: 'reasoning',
          content: 'Reasoning steps',
          reasoning_log: data.reasoning_log,
        });
      }
      
      // Add assistant response
      addMessage({
        role: 'assistant',
        content: data.final_answer,
      });
      
      setLoading(false);
    },
    onError: (error) => {
      addMessage({
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}`,
      });
      setLoading(false);
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    
    // Add user message
    addMessage({
      role: 'user',
      content: input,
    });
    
    // Send to API
    chatMutation.mutate({
      query: input,
      session_id: currentSession,
      active_document: activeDocument || undefined,
    });
    
    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {message.role === 'reasoning' ? (
                <ReasoningSteps steps={message.reasoning_log || []} />
              ) : (
                <MessageBubble message={message} />
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        
        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center space-x-2 text-gray-500"
          >
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
            </div>
            <span>🤔 Agent is thinking...</span>
          </motion.div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}
```

### **5. Message Bubble Component**
```tsx
// components/MessageBubble.tsx
import { Message } from '@/store/chatStore';
import { motion } from 'framer-motion';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <motion.div
        className={`
          max-w-[80%] rounded-lg px-4 py-2 shadow-sm
          ${isUser 
            ? 'bg-blue-500 text-white ml-auto' 
            : 'bg-gray-100 text-gray-800'
          }
        `}
        whileHover={{ scale: 1.02 }}
        transition={{ type: "spring", stiffness: 300 }}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
        
        <div className="mt-2 text-xs opacity-70">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </motion.div>
    </div>
  );
}
```

### **6. Document Upload Component**
```tsx
// components/DocumentUpload.tsx
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';
import { useChatStore } from '@/store/chatStore';

export default function DocumentUpload() {
  const { currentSession, setActiveDocument } = useChatStore();
  
  const uploadMutation = useMutation({
    mutationFn: ({ file, sessionId }: { file: File; sessionId: string }) =>
      chatApi.uploadDocument(file, sessionId),
    onSuccess: (data) => {
      setActiveDocument(data.filename);
      // Show success message
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      uploadMutation.mutate({ file, sessionId: currentSession });
    }
  }, [currentSession, uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
    },
    maxSize: 200 * 1024 * 1024, // 200MB
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
        ${isDragActive 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-300 hover:border-gray-400'
        }
        ${uploadMutation.isPending ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      <input {...getInputProps()} />
      
      <div className="space-y-4">
        <div className="text-4xl">📄</div>
        
        <div>
          <h3 className="text-lg font-medium">
            {isDragActive ? 'Drop your file here' : 'Upload a document to analyze'}
          </h3>
          <p className="text-gray-500 mt-1">
            Drop files here or click to browse
          </p>
        </div>
        
        <div className="flex justify-center space-x-2">
          {['PDF', 'DOCX', 'CSV', 'TXT'].map(format => (
            <span key={format} className="bg-gray-100 px-2 py-1 rounded text-sm">
              {format}
            </span>
          ))}
        </div>
        
        <p className="text-xs text-gray-400">Maximum file size: 200MB</p>
        
        {uploadMutation.isPending && (
          <div className="mt-4">
            <div className="text-sm text-blue-600">Uploading...</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse w-1/3"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

### **7. Main Layout**
```tsx
// app/page.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ChatInterface from '@/components/ChatInterface';
import DocumentUpload from '@/components/DocumentUpload';
import { useChatStore } from '@/store/chatStore';

const queryClient = new QueryClient();

export default function Home() {
  return (
    <QueryClientProvider client={queryClient}>
      <main className="h-screen flex">
        {/* Sidebar */}
        <div className="w-80 bg-gray-50 border-r p-4">
          <h1 className="text-xl font-bold mb-6">🤖 AI Document Agent</h1>
          <DocumentUpload />
        </div>
        
        {/* Main Chat Area */}
        <div className="flex-1">
          <ChatInterface />
        </div>
      </main>
    </QueryClientProvider>
  );
}
```

---

## 🎯 **Key Implementation Tips**

### **Performance Optimization**
1. **Use React.memo** for message components to prevent unnecessary re-renders
2. **Implement virtual scrolling** for long chat histories (react-window)
3. **Debounce typing indicators** to reduce API calls
4. **Cache uploaded documents** in localStorage/sessionStorage

### **Error Handling**
1. **Implement retry logic** for failed API calls
2. **Show meaningful error messages** to users
3. **Handle network timeouts** gracefully
4. **Validate file uploads** before sending

### **Accessibility**
1. **Add proper ARIA labels** to all interactive elements
2. **Implement keyboard navigation** for chat interface
3. **Provide screen reader announcements** for new messages
4. **Ensure proper color contrast** ratios

### **Testing Strategy**
1. **Unit tests** for components using Jest + React Testing Library
2. **Integration tests** for API interactions
3. **E2E tests** for critical user flows using Playwright
4. **Visual regression tests** using Chromatic

---

## 📱 **Mobile Considerations**

### **Touch Interactions**
- **Swipe gestures** for message actions
- **Pull-to-refresh** for chat history
- **Touch-friendly button sizes** (min 44px)

### **Performance**
- **Lazy load images** and file previews
- **Reduce bundle size** with code splitting
- **Optimize animations** for 60fps on mobile

---

## 🚀 **Deployment Checklist**

### **Environment Variables**
```bash
# .env.local
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_API_KEY=your_secret_api_key
NEXT_PUBLIC_UPLOAD_MAX_SIZE=200
```

### **Production Optimizations**
- ✅ Enable Next.js optimization features
- ✅ Configure CDN for static assets
- ✅ Set up error monitoring (Sentry)
- ✅ Implement analytics tracking
- ✅ Configure proper caching headers

---

**🎉 This implementation guide provides everything needed to build a production-ready frontend that leverages the proven 80% success rate AI Document Agent API!**