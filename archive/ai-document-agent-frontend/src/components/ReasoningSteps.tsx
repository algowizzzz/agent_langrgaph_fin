'use client';

import React from 'react';

export interface ReasoningStep {
  type: 'reasoning_step' | 'status' | 'final_answer' | 'error' | 'complete';
  step?: string;
  tool_name?: string;
  message: string;
  result_preview?: string;
  timestamp: number;
}

interface ReasoningStepsProps {
  steps: ReasoningStep[];
  isActive: boolean;
}

const ReasoningSteps: React.FC<ReasoningStepsProps> = ({ steps, isActive }) => {
  const getStepIcon = (step: ReasoningStep) => {
    if (step.type === 'error') return '❌';
    if (step.step === 'setup') return '🤔';
    if (step.step === 'context') return '📄';
    if (step.step === 'memory') return '🧠';
    if (step.step === 'planning') return '🎯';
    if (step.step === 'plan_ready') return '📋';
    if (step.step === 'tool_execution') return '⚡';
    if (step.step === 'tool_complete') return '✅';
    if (step.step === 'tool_error') return '❌';
    if (step.step === 'synthesis') return '🧠';
    return '🔄';
  };

  const getStepColor = (step: ReasoningStep) => {
    if (step.type === 'error' || step.step === 'tool_error') return 'text-red-600 bg-red-50';
    if (step.step === 'tool_complete') return 'text-green-600 bg-green-50';
    if (step.step === 'synthesis') return 'text-purple-600 bg-purple-50';
    if (step.step === 'planning' || step.step === 'plan_ready') return 'text-blue-600 bg-blue-50';
    return 'text-gray-600 bg-gray-50';
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  if (!isActive && steps.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          🧠 AI Reasoning Steps
          {isActive && (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-600 font-normal">Processing...</span>
            </div>
          )}
        </h3>
        <span className="text-sm text-gray-500">{steps.length} steps</span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg border-l-4 ${getStepColor(step)} transition-all duration-300 ease-in-out`}
            style={{
              borderLeftColor: step.type === 'error' ? '#ef4444' : step.step === 'tool_complete' ? '#10b981' : '#6b7280'
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3 flex-1">
                <span className="text-lg flex-shrink-0 mt-0.5">
                  {getStepIcon(step)}
                </span>
                <div className="flex-1">
                  <div className="font-medium text-sm">
                    {step.message}
                  </div>
                  {step.tool_name && (
                    <div className="text-xs text-gray-500 mt-1">
                      Tool: <span className="font-mono">{step.tool_name}</span>
                    </div>
                  )}
                  {step.result_preview && (
                    <div className="text-xs text-gray-600 mt-2 p-2 bg-gray-100 rounded font-mono">
                      {step.result_preview}
                    </div>
                  )}
                </div>
              </div>
              <span className="text-xs text-gray-400 flex-shrink-0">
                {formatTimestamp(step.timestamp)}
              </span>
            </div>
          </div>
        ))}
        
        {isActive && (
          <div className="p-3 rounded-lg bg-blue-50 border-l-4 border-blue-400 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-blue-700 font-medium text-sm">
                Analyzing and processing...
              </span>
            </div>
          </div>
        )}
      </div>
      
      {steps.length === 0 && isActive && (
        <div className="text-center py-8 text-gray-500">
          <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p>Starting AI analysis...</p>
        </div>
      )}
    </div>
  );
};

export default ReasoningSteps;