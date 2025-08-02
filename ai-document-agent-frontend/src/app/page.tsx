'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { DocumentAgentAPI } from '@/lib/api';
import { useChatStore } from '@/store/chatStore';
import MessageBubble from '@/components/ui/MessageBubble';
import ChatInput from '@/components/ui/ChatInput';

import DocumentStatus from '@/components/ui/DocumentStatus';
import DocumentSidebar from '@/components/DocumentSidebar';
import { ChatBubbleLeftRightIcon, DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const {
    sessionId,
    messages,
    isLoading,
    error,
    documents,
    activeDocument,
    activeDocuments,
    addMessage,
    updateMessage,
    setLoading,
    setError,
    addDocument,
    removeDocument,
    toggleActiveDocument,
    setActiveDocuments,
    clearActiveDocuments,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Hide welcome screen when there are messages
  useEffect(() => {
    if (messages.length > 0) {
      setShowWelcome(false);
    }
  }, [messages]);

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: DocumentAgentAPI.sendChatMessage,
    onSuccess: (data) => {
      // Find the message we're updating (it has status 'sending')
      const messageToUpdate = messages.find(m => m.status === 'sending');
      if (messageToUpdate) {
        updateMessage(messageToUpdate.id, {
          content: data.final_answer,
          reasoning_steps: data.reasoning_log,
          processing_time: data.processing_time_ms,
          status: data.status === 'success' ? 'success' : 'error',
        });
      }
      setLoading(false);
      setError(null);
    },
    onError: (error: Error) => {
      // Update the sending message to show error
      const messageToUpdate = messages.find(m => m.status === 'sending');
      if (messageToUpdate) {
        updateMessage(messageToUpdate.id, {
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          status: 'error',
        });
      }
      setLoading(false);
      setError(error.message || 'Failed to send message');
    },
  });

  // Document upload mutation
  const uploadMutation = useMutation({
    mutationFn: ({ file, sessionId }: { file: File; sessionId: string }) =>
      DocumentAgentAPI.uploadDocument(file, sessionId),
    onSuccess: (data) => {
      addDocument({
        name: data.filename,
        file_type: data.file_type as 'PDF' | 'DOCX' | 'CSV' | 'TXT' | 'UNKNOWN',
        file_size: 0, // Will be populated by backend response
        file_size_display: data.file_size,
        chunks_count: data.chunks_created,
        upload_time: new Date().toISOString(),
        uploaded_by_session: sessionId,
        source: data.filename,
        active: true,
      });
      setError(null);
      setUploadSuccess(`Successfully uploaded ${data.filename} (${data.chunks_created} chunks created)`);
      setTimeout(() => setUploadSuccess(null), 4000); // Clear after 4 seconds
    },
    onError: (error: Error) => {
      setError(error.message || 'Failed to upload document');
    },
  });

  const handleSendMessage = (message: string) => {
    // Check if we have active documents for document-based queries
    if (activeDocuments.length === 0) {
      // Allow general Q&A even without documents
      const proceedWithoutDocs = true; // You can add a confirmation dialog here if needed
      if (!proceedWithoutDocs) {
        setError("Please select documents to analyze, or ask general questions.");
        return;
      }
    }

    // Add user message
    addMessage({
      role: 'user',
      content: message,
      status: 'success',
    });

    // Add placeholder assistant message with loading state
    addMessage({
      role: 'assistant',
      content: '',
      status: 'sending',
    });

    setLoading(true);

    // Send to API with multi-document support
    chatMutation.mutate({
      query: message,
      session_id: sessionId,
      active_document: activeDocument, // Backward compatibility
      active_documents: activeDocuments, // Multi-document support
    });
  };

  const handleFileUpload = (file: File) => {
    uploadMutation.mutate({ file, sessionId });
  };

  const activeDoc = documents.find(d => d.name === activeDocument);

  // Handlers for DocumentSidebar
  const handleDocumentToggle = (docName: string) => {
    toggleActiveDocument(docName);
  };

  const handleDocumentRemove = (docName: string) => {
    removeDocument(docName);
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-40">
        <div className="max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-accent rounded-lg flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-neutral-900">AI Document Agent</h1>
                <p className="text-xs text-neutral-500">Multi-document analysis powered by AI</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {activeDocuments.length > 0 && (
                <div className="flex items-center space-x-2 text-sm text-neutral-600">
                  <DocumentTextIcon className="w-4 h-4" />
                  <span>
                    {activeDocuments.length === 1 
                      ? `1 active document`
                      : `${activeDocuments.length} active documents`
                    }
                  </span>
                </div>
              )}
              

            </div>
          </div>
        </div>
      </header>

      {/* Main Layout with Sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Document Sidebar */}
        <DocumentSidebar
          activeDocuments={activeDocuments}
          onDocumentToggle={handleDocumentToggle}
          onDocumentRemove={handleDocumentRemove}
          className="flex-shrink-0"
        />

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Screen */}
        {showWelcome && messages.length === 0 && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-primary-accent/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <ChatBubbleLeftRightIcon className="w-10 h-10 text-primary-accent" />
            </div>
            <h2 className="text-2xl font-semibold text-neutral-900 mb-4">
              Welcome to AI Document Agent
            </h2>
            <p className="text-neutral-600 mb-8 max-w-2xl mx-auto">
              Upload your documents and start asking questions. I can help you analyze, summarize, 
              extract insights, and perform data analysis on PDF, DOCX, CSV, and TXT files.
            </p>
            
            <p className="text-lg text-neutral-600">
              👈 Use the sidebar to upload and select documents, then start asking questions!
            </p>
          </div>
        )}

        {/* Active Documents Summary */}
        {!showWelcome && activeDocuments.length > 0 && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-2">
              {activeDocuments.length === 1 
                ? 'Analyzing 1 document' 
                : `Analyzing ${activeDocuments.length} documents`
              }
            </h3>
            <div className="text-xs text-blue-700">
              {activeDocuments.map(internalName => {
                const doc = documents.find(d => d.internal_name === internalName);
                return doc?.name || internalName;
              }).join(', ')}
            </div>
          </div>
        )}

        {/* Chat Messages */}
        {messages.length > 0 && (
          <div className="space-y-4 mb-8">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Success Display */}
        {uploadSuccess && (
          <div className="mb-6 p-4 bg-primary-success/10 border border-primary-success/20 rounded-lg" data-testid="upload-success-message">
            <p className="text-sm text-primary-success">{uploadSuccess}</p>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-primary-error/10 border border-primary-error/20 rounded-lg" data-testid="error-message">
            <p className="text-sm text-primary-error">{error}</p>
          </div>
        )}

            {/* Chat Input */}
            <div className="sticky bottom-4">
              <ChatInput
                onSendMessage={handleSendMessage}
                onFileUpload={handleFileUpload}
                isLoading={isLoading}
                placeholder={
                  activeDocuments.length > 0
                    ? `Ask me anything about your ${activeDocuments.length === 1 ? 'document' : 'documents'}...`
                    : "Upload documents or ask general questions..."
                }
              />
            </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}