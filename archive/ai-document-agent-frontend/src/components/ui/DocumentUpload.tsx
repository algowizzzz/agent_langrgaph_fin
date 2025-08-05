'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { DocumentTextIcon, CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

interface DocumentUploadProps {
  onFileUpload: (file: File) => void;
  isUploading?: boolean;
  maxSize?: number; // in MB
  acceptedTypes?: string[];
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onFileUpload,
  isUploading = false,
  maxSize = 200,
  acceptedTypes = ['.pdf', '.docx', '.csv', '.txt'],
}) => {
  const [uploadError, setUploadError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    setUploadError(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setUploadError(`File is too large. Maximum size is ${maxSize}MB.`);
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setUploadError(`Invalid file type. Supported formats: ${acceptedTypes.join(', ')}`);
      } else {
        setUploadError('Failed to upload file. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload, maxSize, acceptedTypes]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
    },
    maxSize: maxSize * 1024 * 1024, // Convert MB to bytes
    multiple: false,
  });

  const getFileTypeIcon = (type: string) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('docx')) return '📝';
    if (type.includes('csv')) return '📊';
    if (type.includes('text')) return '📋';
    return '📄';
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
          'hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-primary-accent focus:ring-offset-2',
          {
            'border-primary-accent bg-primary-accent/5': isDragActive && !isDragReject,
            'border-primary-error bg-primary-error/5': isDragReject,
            'border-neutral-300': !isDragActive && !isDragReject,
            'cursor-not-allowed opacity-50': isUploading,
          }
        )}
      >
        <input {...getInputProps()} disabled={isUploading} data-testid="document-upload-input" />

        {isUploading ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 border-4 border-primary-accent border-t-transparent rounded-full animate-spin" />
            <div>
              <p className="text-lg font-medium text-neutral-700">Uploading document...</p>
              <p className="text-sm text-neutral-500">Please wait while we process your file</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className={clsx(
              'w-16 h-16 rounded-full flex items-center justify-center',
              isDragActive && !isDragReject ? 'bg-primary-accent text-white' : 'bg-neutral-100 text-neutral-600'
            )}>
              {isDragActive ? (
                <CloudArrowUpIcon className="w-8 h-8" />
              ) : (
                <DocumentTextIcon className="w-8 h-8" />
              )}
            </div>

            <div>
              {isDragActive ? (
                isDragReject ? (
                  <p className="text-lg font-medium text-primary-error">
                    File type not supported
                  </p>
                ) : (
                  <p className="text-lg font-medium text-primary-accent">
                    Drop your document here
                  </p>
                )
              ) : (
                <div>
                  <p className="text-lg font-medium text-neutral-700">
                    Drag & drop your document here
                  </p>
                  <p className="text-sm text-neutral-500 mt-1">
                    or <span className="text-primary-accent font-medium">click to browse</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        )}


      </div>

      {/* Error Message */}
      {uploadError && (
        <div className="mt-4 p-4 bg-primary-error/10 border border-primary-error/20 rounded-lg flex items-start space-x-3">
          <XMarkIcon className="w-5 h-5 text-primary-error flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-primary-error">Upload Error</p>
            <p className="text-sm text-primary-error/80">{uploadError}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;