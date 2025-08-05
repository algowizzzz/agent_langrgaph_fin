'use client';

import React, { useState, useRef, KeyboardEvent } from 'react';
import { PaperAirplaneIcon, PaperClipIcon } from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { PROVEN_QUERY_PATTERNS } from '@/lib/api';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onFileUpload: (file: File) => void;
  isLoading?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onFileUpload,
  isLoading = false,
  placeholder = "Ask me anything about your documents...",
}) => {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
      setShowSuggestions(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  // Flatten all proven query patterns for suggestions
  const allSuggestions = Object.values(PROVEN_QUERY_PATTERNS).flat();

  return (
    <div className="relative">
      {/* Quick Suggestions */}
      {showSuggestions && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-neutral-200 rounded-lg shadow-lg max-h-48 overflow-y-auto z-10">
          <div className="p-3">
            <h4 className="text-sm font-medium text-neutral-800 mb-2">Suggested queries:</h4>
            <div className="space-y-1">
              {allSuggestions.slice(0, 8).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="block w-full text-left px-3 py-2 text-sm text-neutral-800 hover:bg-neutral-50 rounded transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Input Area */}
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm focus-within:border-primary-accent focus-within:ring-2 focus-within:ring-primary-accent/20 transition-all">
        <div className="flex items-end p-3 space-x-3">
          {/* File Upload Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className={clsx(
              'flex-shrink-0 p-2 rounded-lg transition-colors',
              isLoading
                ? 'text-neutral-400 cursor-not-allowed'
                : 'text-neutral-600 hover:text-primary-accent hover:bg-primary-accent/10'
            )}
            title="Upload document"
          >
            <PaperClipIcon className="w-5 h-5" />
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.csv,.txt"
            onChange={handleFileUpload}
            className="hidden"
            data-testid="chat-upload-input"
          />

          {/* Message Input */}
          <div className="flex-grow">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              onFocus={() => setShowSuggestions(true)}
              placeholder={placeholder}
              disabled={isLoading}
              className={clsx(
                'w-full resize-none border-0 bg-transparent text-neutral-800 placeholder-neutral-500',
                'focus:outline-none focus:ring-0 text-sm leading-5',
                'min-h-[20px] max-h-[120px] overflow-y-auto',
                isLoading && 'cursor-not-allowed opacity-50'
              )}
              rows={1}
              data-testid="chat-message-input"
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSubmit}
            disabled={!message.trim() || isLoading}
            className={clsx(
              'flex-shrink-0 p-2 rounded-lg transition-all',
              message.trim() && !isLoading
                ? 'text-white bg-primary-accent hover:bg-primary-accent/90 shadow-sm'
                : 'text-neutral-400 cursor-not-allowed'
            )}
            title="Send message"
            data-testid="send-message-button"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <PaperAirplaneIcon className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Helpful Tips */}
        {!message && (
          <div className="px-3 pb-3">
            <div className="flex flex-wrap gap-2">
              {['Summarize document', 'Count word "risk"', 'Extract key topics'].map((tip) => (
                <button
                  key={tip}
                  onClick={() => handleSuggestionClick(tip)}
                  className="px-3 py-1 text-xs text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-full transition-colors"
                >
                  {tip}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Click outside to hide suggestions */}
      {showSuggestions && (
        <div
          className="fixed inset-0 -z-10"
          onClick={() => setShowSuggestions(false)}
        />
      )}
    </div>
  );
};

export default ChatInput;