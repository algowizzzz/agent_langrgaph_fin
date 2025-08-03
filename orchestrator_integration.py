"""
Integration layer for Orchestrator 2.0

This module provides a compatibility layer to integrate Orchestrator 2.0
with the existing system while maintaining backward compatibility.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, AsyncGenerator

from orchestrator_v2 import OrchestratorV2, OrchestratorConfig, PlanningStrategy

logger = logging.getLogger(__name__)


class OrchestratorIntegration:
    """
    Integration wrapper that provides backward compatibility with the original orchestrator
    while enabling the use of Orchestrator 2.0's enhanced capabilities.
    """
    
    def __init__(self, enable_v2: bool = True, fallback_to_v1: bool = True):
        self.enable_v2 = enable_v2
        self.fallback_to_v1 = fallback_to_v1
        
        # Initialize Orchestrator 2.0
        if enable_v2:
            try:
                config = OrchestratorConfig(
                    max_parallel_steps=3,
                    enable_streaming=True,
                    enable_persistence=True,
                    planning_strategy=PlanningStrategy.ADAPTIVE,
                    confidence_threshold=0.7
                )
                self.orchestrator_v2 = OrchestratorV2(config)
                logger.info("✅ Orchestrator 2.0 initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Orchestrator 2.0: {e}")
                self.orchestrator_v2 = None
        else:
            self.orchestrator_v2 = None
        
        # Initialize original orchestrator as fallback
        if fallback_to_v1:
            try:
                from orchestrator import Orchestrator
                self.orchestrator_v1 = Orchestrator()
                logger.info("✅ Orchestrator 1.0 fallback initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Orchestrator 1.0 fallback: {e}")
                self.orchestrator_v1 = None
        else:
            self.orchestrator_v1 = None
    
    async def run(self, 
                  user_query: str,
                  session_id: str,
                  active_document: str = None,
                  active_documents: List[str] = None,
                  memory_context: Dict = None) -> Dict[str, Any]:
        """
        Execute query with automatic orchestrator selection and fallback.
        
        This method maintains compatibility with the original orchestrator interface
        while leveraging Orchestrator 2.0's enhanced capabilities when available.
        """
        
        # Normalize active documents parameter
        if active_documents is None and active_document:
            active_documents = [active_document]
        elif active_documents is None:
            active_documents = []
        
        # Try Orchestrator 2.0 first
        if self.orchestrator_v2:
            try:
                logger.info("🚀 Using Orchestrator 2.0")
                
                result = await self.orchestrator_v2.execute_query(
                    user_query=user_query,
                    session_id=session_id,
                    active_documents=active_documents,
                    memory_context=memory_context,
                    planning_strategy=PlanningStrategy.ADAPTIVE
                )
                
                # Check if result meets quality threshold
                if result.get("confidence_score", 0) >= self.orchestrator_v2.config.confidence_threshold:
                    logger.info(f"✅ Orchestrator 2.0 succeeded with {result['confidence_score']:.2f} confidence")
                    
                    # Convert to v1 format for backward compatibility
                    return self._convert_v2_to_v1_format(result)
                else:
                    logger.warning(f"⚠️ Orchestrator 2.0 confidence too low ({result['confidence_score']:.2f}), trying fallback")
                    
                    if self.fallback_to_v1 and self.orchestrator_v1:
                        return await self._run_v1_fallback(user_query, session_id, active_document, active_documents, memory_context)
                    else:
                        return self._convert_v2_to_v1_format(result)
                        
            except Exception as e:
                logger.error(f"❌ Orchestrator 2.0 failed: {e}")
                
                if self.fallback_to_v1 and self.orchestrator_v1:
                    logger.info("🔄 Falling back to Orchestrator 1.0")
                    return await self._run_v1_fallback(user_query, session_id, active_document, active_documents, memory_context)
                else:
                    raise e
        
        # Use Orchestrator 1.0 directly
        elif self.orchestrator_v1:
            logger.info("📎 Using Orchestrator 1.0 (v2 disabled)")
            return await self._run_v1_fallback(user_query, session_id, active_document, active_documents, memory_context)
        
        else:
            raise RuntimeError("No orchestrator available - both v1 and v2 failed to initialize")
    
    async def run_streaming(self,
                           user_query: str,
                           session_id: str,
                           active_document: str = None,
                           active_documents: List[str] = None,
                           memory_context: Dict = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute query with streaming feedback using Orchestrator 2.0.
        
        Falls back to non-streaming execution if v2 is not available.
        """
        
        # Normalize active documents parameter
        if active_documents is None and active_document:
            active_documents = [active_document]
        elif active_documents is None:
            active_documents = []
        
        # Use Orchestrator 2.0 streaming if available
        if self.orchestrator_v2:
            try:
                logger.info("🚀 Using Orchestrator 2.0 streaming")
                
                async for update in self.orchestrator_v2.execute_query_streaming(
                    user_query=user_query,
                    session_id=session_id,
                    active_documents=active_documents,
                    memory_context=memory_context,
                    planning_strategy=PlanningStrategy.ADAPTIVE
                ):
                    # Convert streaming updates to v1-compatible format
                    yield self._convert_streaming_update(update)
                
            except Exception as e:
                logger.error(f"❌ Orchestrator 2.0 streaming failed: {e}")
                
                # Fall back to non-streaming execution
                if self.orchestrator_v1:
                    result = await self._run_v1_fallback(user_query, session_id, active_document, active_documents, memory_context)
                    yield {
                        'type': 'final_answer',
                        'content': result,
                        'timestamp': time.time()
                    }
                else:
                    yield {
                        'type': 'error',
                        'message': f"Streaming execution failed: {e}",
                        'timestamp': time.time()
                    }
        
        # Fall back to v1 non-streaming
        elif self.orchestrator_v1:
            logger.info("📎 Using Orchestrator 1.0 (no streaming support)")
            
            # Provide basic progress feedback
            yield {
                'type': 'reasoning_step',
                'step': 'setup',
                'message': '🤔 Analyzing your query with Orchestrator 1.0...',
                'timestamp': time.time()
            }
            
            result = await self._run_v1_fallback(user_query, session_id, active_document, active_documents, memory_context)
            
            yield {
                'type': 'final_answer',
                'content': result,
                'timestamp': time.time()
            }
        
        else:
            yield {
                'type': 'error',
                'message': "No orchestrator available",
                'timestamp': time.time()
            }
    
    async def _run_v1_fallback(self,
                              user_query: str,
                              session_id: str, 
                              active_document: str = None,
                              active_documents: List[str] = None,
                              memory_context: Dict = None) -> Dict[str, Any]:
        """Run the original orchestrator as fallback."""
        
        try:
            result = await self.orchestrator_v1.run(
                user_query=user_query,
                session_id=session_id,
                active_document=active_document,
                active_documents=active_documents,
                memory_context=memory_context
            )
            
            logger.info("✅ Orchestrator 1.0 fallback succeeded")
            return result
            
        except Exception as e:
            logger.error(f"❌ Orchestrator 1.0 fallback also failed: {e}")
            
            # Return error result in expected format
            return {
                "status": "error",
                "final_answer": f"Both orchestrators failed. Error: {str(e)}",
                "reasoning_log": [{"error": str(e)}]
            }
    
    def _convert_v2_to_v1_format(self, v2_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Orchestrator 2.0 result format to v1 format for compatibility."""
        
        return {
            "status": v2_result.get("status", "error"),
            "final_answer": v2_result.get("final_answer", ""),
            "reasoning_log": self._convert_traceability_to_reasoning_log(
                v2_result.get("traceability_log", [])
            ),
            "confidence_score": v2_result.get("confidence_score", 0.0),
            "execution_summary": v2_result.get("execution_summary", {}),
            "query_type": v2_result.get("query_type", "unknown"),
            "orchestrator_version": "2.0"
        }
    
    def _convert_traceability_to_reasoning_log(self, traceability_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert v2 traceability log to v1 reasoning log format."""
        
        reasoning_log = []
        
        for entry in traceability_log:
            reasoning_log.append({
                "tool_name": entry.get("metadata", {}).get("tool_name", "unknown"),
                "tool_params": {},  # v2 doesn't expose raw params for security
                "tool_output": f"Step completed with {entry.get('confidence', 0):.2f} confidence",
                "timestamp": entry.get("timestamp", time.time())
            })
        
        return reasoning_log
    
    def _convert_streaming_update(self, v2_update: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 streaming update to v1-compatible format."""
        
        update_type = v2_update.get("type", "unknown")
        
        if update_type == "final_answer":
            return {
                'type': 'final_answer',
                'content': self._convert_v2_to_v1_format(v2_update.get("content", {})),
                'timestamp': v2_update.get("timestamp", time.time())
            }
        
        elif update_type in ["reasoning_step", "tool_execution"]:
            return {
                'type': 'reasoning_step',
                'step': v2_update.get("step", "unknown"),
                'message': v2_update.get("message", ""),
                'timestamp': v2_update.get("timestamp", time.time()),
                'confidence': v2_update.get("confidence", 0.0)
            }
        
        elif update_type == "error":
            return {
                'type': 'error',
                'message': v2_update.get("message", "Unknown error"),
                'timestamp': v2_update.get("timestamp", time.time())
            }
        
        else:
            return v2_update
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of both orchestrators."""
        
        status = {
            "integration_version": "1.0",
            "v2_enabled": self.enable_v2,
            "v1_fallback_enabled": self.fallback_to_v1,
            "v2_status": None,
            "v1_status": None
        }
        
        if self.orchestrator_v2:
            try:
                status["v2_status"] = self.orchestrator_v2.get_system_status()
            except Exception as e:
                status["v2_status"] = {"error": str(e)}
        
        if self.orchestrator_v1:
            try:
                status["v1_status"] = {"status": "available", "version": "1.0"}
            except Exception as e:
                status["v1_status"] = {"error": str(e)}
        
        return status
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up session data in both orchestrators."""
        
        if self.orchestrator_v2:
            try:
                self.orchestrator_v2.cleanup_session(session_id)
            except Exception as e:
                logger.error(f"Failed to cleanup v2 session: {e}")
        
        # v1 doesn't have explicit session cleanup, but we could add it if needed


# Global integration instance
orchestrator_integration = OrchestratorIntegration(
    enable_v2=True,
    fallback_to_v1=True
)