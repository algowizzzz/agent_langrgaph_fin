'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  TrashIcon, 
  DocumentIcon, 
  CalendarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { DocumentAgentAPI } from '@/lib/api';
import { UploadedDocument } from '@/types/api';

interface DocumentSidebarProps {
  activeDocuments: string[];
  onDocumentToggle: (docName: string) => void;
  onDocumentRemove: (docName: string) => void;
  className?: string;
}

export default function DocumentSidebar({ 
  activeDocuments, 
  onDocumentToggle, 
  onDocumentRemove,
  className = '' 
}: DocumentSidebarProps) {
  const queryClient = useQueryClient();

  // Fetch all documents
  const { data: documentsResponse, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: DocumentAgentAPI.getAllDocuments,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Remove document mutation
  const removeDocumentMutation = useMutation({
    mutationFn: DocumentAgentAPI.removeDocument,
    onSuccess: (data, documentName) => {
      if (data.status === 'success') {
        // Update the cache
        queryClient.invalidateQueries({ queryKey: ['documents'] });
        // Notify parent component
        onDocumentRemove(documentName);
      }
    },
    onError: (error) => {
      console.error('Error removing document:', error);
    },
  });

  const handleDocumentRemove = async (docName: string) => {
    const confirmMessage = `Are you sure you want to remove "${docName}"?\n\nThis action cannot be undone and will affect all sessions.`;
    if (confirm(confirmMessage)) {
      removeDocumentMutation.mutate(docName);
    }
  };

  const formatUploadTime = (timeString: string) => {
    if (!timeString) return 'Unknown';
    try {
      const date = new Date(timeString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return 'Invalid date';
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    const iconClass = "w-4 h-4";
    switch (fileType?.toLowerCase()) {
      case 'pdf': return <DocumentIcon className={`${iconClass} text-red-500`} />;
      case 'csv': return <DocumentIcon className={`${iconClass} text-green-500`} />;
      case 'docx': return <DocumentIcon className={`${iconClass} text-blue-500`} />;
      case 'txt': return <DocumentIcon className={`${iconClass} text-gray-500`} />;
      default: return <DocumentIcon className={`${iconClass} text-gray-400`} />;
    }
  };

  const documents = documentsResponse?.documents || [];

  if (isLoading) {
    return (
      <div className={`w-80 bg-white border-r border-gray-200 p-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`w-80 bg-white border-r border-gray-200 p-4 ${className}`}>
        <div className="text-center py-8">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-300 mx-auto mb-3" />
          <p className="text-red-600 text-sm">Error loading documents</p>
          <p className="text-gray-500 text-xs mt-1">Please refresh the page</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-80 bg-white border-r border-gray-200 flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">📚 Documents</h2>
        <p className="text-sm text-gray-500 mt-1">
          {documents.length} document{documents.length !== 1 ? 's' : ''} available
        </p>
        {activeDocuments.length > 0 && (
          <p className="text-xs text-blue-600 mt-1">
            {activeDocuments.length} selected for analysis
          </p>
        )}
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {documents.length === 0 ? (
          <div className="text-center py-8">
            <DocumentIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No documents uploaded yet</p>
            <p className="text-sm text-gray-400 mt-1">Upload documents to get started</p>
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.internal_name}
              className={`border rounded-lg p-3 cursor-pointer transition-all ${
                activeDocuments.includes(doc.internal_name)
                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              {/* Document Header */}
              <div className="flex items-start justify-between mb-2">
                <div 
                  className="flex-1 min-w-0"
                  onClick={() => onDocumentToggle(doc.internal_name)}
                >
                  <div className="flex items-center space-x-2">
                    {getFileTypeIcon(doc.file_type)}
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {doc.name}
                    </h3>
                    {activeDocuments.includes(doc.internal_name) && (
                      <CheckCircleIcon className="w-4 h-4 text-blue-500 flex-shrink-0" />
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                    <span className="flex items-center space-x-1">
                      <CalendarIcon className="w-3 h-3" />
                      <span>{formatUploadTime(doc.upload_time)}</span>
                    </span>
                    <span>{doc.chunks_count} chunks</span>
                    <span>{doc.file_size_display}</span>
                  </div>
                  
                  {doc.uploaded_by_session && (
                    <div className="text-xs text-gray-400 mt-1">
                      Session: {doc.uploaded_by_session.slice(-8)}
                    </div>
                  )}
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDocumentRemove(doc.internal_name);
                  }}
                  disabled={removeDocumentMutation.isPending}
                  className="text-gray-400 hover:text-red-500 transition-colors p-1 disabled:opacity-50"
                  title="Remove document"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>

              {/* Selection Indicator */}
              {activeDocuments.includes(doc.internal_name) && (
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    ✓ Selected
                  </span>
                  <span className="text-xs text-blue-600 font-medium">
                    {doc.file_type.toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Selection Summary */}
      {activeDocuments.length > 0 && (
        <div className="border-t border-gray-200 p-4 bg-blue-50">
          <h3 className="text-sm font-medium text-blue-900 mb-2">
            Active Documents ({activeDocuments.length})
          </h3>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {activeDocuments.map((internalName) => {
              const doc = documents.find(d => d.internal_name === internalName);
              return (
                <div key={internalName} className="text-xs text-blue-700 truncate">
                  • {doc?.name || internalName}
                </div>
              );
            })}
          </div>
          {activeDocuments.length > 1 && (
            <div className="text-xs text-blue-600 mt-2 font-medium">
              Multi-document analysis enabled
            </div>
          )}
        </div>
      )}
    </div>
  );
}