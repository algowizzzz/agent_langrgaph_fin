'use client';

import React, { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon, ClockIcon } from '@heroicons/react/24/outline';
import { Message, ReasoningStep } from '@/types/api';
import { clsx } from 'clsx';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [showReasoning, setShowReasoning] = useState(false);
  const isUser = message.role === 'user';
  const isLoading = message.status === 'sending';
  const hasError = message.status === 'error';
  const hasReasoning = message.reasoning_steps && message.reasoning_steps.length > 0;

  return (
    <div
      data-testid="chat-message"
      className={clsx(
        'flex w-full mb-4 animate-slide-up',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div className={clsx(
        'max-w-[80%] rounded-2xl px-4 py-3 shadow-sm',
        isUser 
          ? 'bg-blue-200 text-gray-800 ml-4' 
          : 'bg-white text-neutral-800 mr-4 border border-neutral-200'
      )}>
        {/* Message Content */}
        <div className="whitespace-pre-wrap break-words">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-current rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-sm text-neutral-600">AI is thinking...</span>
            </div>
          ) : (
            message.content
          )}
        </div>

        {/* Error State */}
        {hasError && (
          <div className="mt-2 px-3 py-2 bg-primary-error/10 border border-primary-error/20 rounded-lg">
            <p className="text-sm text-primary-error">
              Failed to process message. Please try again.
            </p>
          </div>
        )}

        {/* Reasoning Section */}
        {hasReasoning && !isUser && !isLoading && (
          <div className="mt-3 border-t border-neutral-200 pt-3">
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="flex items-center space-x-2 text-sm text-neutral-700 hover:text-neutral-900 transition-colors font-medium"
            >
              {showReasoning ? (
                <ChevronDownIcon className="w-4 h-4" />
              ) : (
                <ChevronRightIcon className="w-4 h-4" />
              )}
              <span>Show AI reasoning ({message.reasoning_steps?.length} steps)</span>
              {message.processing_time && (
                <span className="flex items-center space-x-1 text-neutral-400">
                  <ClockIcon className="w-3 h-3" />
                  <span>{(message.processing_time / 1000).toFixed(1)}s</span>
                </span>
              )}
            </button>

            {showReasoning && (
              <div className="mt-3 space-y-2">
                {message.reasoning_steps?.map((step, index) => (
                  <ReasoningStepCard key={index} step={step} index={index} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className={clsx(
          'mt-2 text-xs opacity-70',
          isUser ? 'text-right' : 'text-left'
        )}>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
};

interface ReasoningStepCardProps {
  step: ReasoningStep;
  index: number;
}

const ReasoningStepCard: React.FC<ReasoningStepCardProps> = ({ step, index }) => {
  const [expanded, setExpanded] = useState(false);
  
  const getToolIcon = (toolName: string) => {
    if (toolName.includes('search') || toolName.includes('document')) return '📄';
    if (toolName.includes('memory') || toolName.includes('conversation')) return '🧠';
    if (toolName.includes('python') || toolName.includes('execute')) return '🐍';
    if (toolName.includes('chart') || toolName.includes('visual')) return '📊';
    if (toolName.includes('analyze') || toolName.includes('extract')) return '🔍';
    return '🔧';
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'success': return 'text-primary-success';
      case 'error': return 'text-primary-error';
      default: return 'text-neutral-600';
    }
  };

  return (
    <div className="bg-reasoning-bg border border-reasoning-border rounded-lg p-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getToolIcon(step.tool_name)}</span>
          <span className="font-medium text-sm text-neutral-800">
            Step {index + 1}: {step.tool_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
          {step.execution_time_ms && (
            <span className="text-xs text-neutral-400">
              {step.execution_time_ms}ms
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {step.status && (
            <div className={clsx('w-2 h-2 rounded-full', {
              'bg-primary-success': step.status === 'success',
              'bg-primary-error': step.status === 'error',
              'bg-neutral-400': !step.status,
            })} />
          )}
          {expanded ? (
            <ChevronDownIcon className="w-4 h-4 text-neutral-400" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 text-neutral-400" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="mt-3 space-y-2 text-sm">
          {step.tool_params && Object.keys(step.tool_params).length > 0 && (
            <div>
              <p className="font-medium text-neutral-800 mb-1">Parameters:</p>
              <pre className="bg-neutral-100 p-2 rounded text-xs overflow-x-auto text-neutral-800">
                {JSON.stringify(step.tool_params, null, 2)}
              </pre>
            </div>
          )}
          
          <div>
            <p className="font-medium text-neutral-800 mb-1">Output:</p>
            <div className="bg-white p-2 rounded border text-xs max-h-32 overflow-y-auto text-neutral-800">
              {step.tool_output.length > 200 && !expanded ? 
                `${step.tool_output.substring(0, 200)}...` : 
                step.tool_output
              }
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageBubble;