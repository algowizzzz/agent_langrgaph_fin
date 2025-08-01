'use client';

import React from 'react';
import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { UploadedDocument } from '@/types/api';
import { clsx } from 'clsx';

interface DocumentStatusProps {
  document: UploadedDocument | null;
  onRemove?: () => void;
  className?: string;
}

const DocumentStatus: React.FC<DocumentStatusProps> = ({ 
  document, 
  onRemove,
  className 
}) => {
  if (!document) return null;

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'PDF': return '📄';
      case 'DOCX': return '📝';
      case 'CSV': return '📊';
      case 'TXT': return '📋';
      default: return '📄';
    }
  };

  const formatFileSize = (sizeStr: string) => {
    // If it's already formatted (e.g., "1.2 MB"), return as is
    if (sizeStr.includes(' ')) return sizeStr;
    
    // If it's just a number, format it
    const size = parseInt(sizeStr);
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className={clsx(
      'bg-primary-success/10 border border-primary-success/20 rounded-lg p-4',
      className
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {/* File Icon */}
          <div className="flex-shrink-0">
            <span className="text-2xl">{getFileIcon(document.file_type)}</span>
          </div>

          {/* Document Info */}
          <div className="flex-grow min-w-0">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="w-4 h-4 text-primary-success flex-shrink-0" />
              <span className="text-sm font-medium text-primary-success">Document Ready</span>
            </div>
            
            <p className="text-sm font-medium text-neutral-800 truncate mt-1">
              {document.filename}
            </p>
            
            <div className="flex items-center space-x-4 mt-1">
              <span className="text-xs text-neutral-600">
                {document.file_type} • {formatFileSize(document.file_size)}
              </span>
              <span className="text-xs text-neutral-600">
                {document.chunks_created} chunks processed
              </span>
            </div>
          </div>

          {/* Remove Button */}
          {onRemove && (
            <button
              onClick={onRemove}
              className="flex-shrink-0 p-1 text-neutral-400 hover:text-primary-error transition-colors"
              title="Remove document"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-3 pt-3 border-t border-primary-success/20">
        <p className="text-xs text-neutral-600 mb-2">Try asking:</p>
        <div className="flex flex-wrap gap-2">
          {[
            'Summarize this document',
            'What are the main topics?',
            'Count word "risk"',
          ].map((suggestion) => (
            <span
              key={suggestion}
              className="px-2 py-1 text-xs bg-white border border-neutral-200 rounded-full text-neutral-600"
            >
&quot;{suggestion}&quot;
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DocumentStatus;