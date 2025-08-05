"""
Orchestrator 2.0 Integration Layer

This module provides the integration layer for Orchestrator 2.0.
All queries are handled exclusively by Orchestrator 2.0.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, AsyncGenerator

from orchestrator_v2 import OrchestratorV2, OrchestratorConfig, PlanningStrategy

logger = logging.getLogger(__name__)


class OrchestratorIntegration:
    """
    Integration wrapper for Orchestrator 2.0.
    All queries are handled exclusively by Orchestrator 2.0.
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        
        # Initialize Orchestrator 2.0
        try:
            config = OrchestratorConfig(
                max_parallel_steps=3,
                enable_streaming=True,
                enable_persistence=True,
                planning_strategy=PlanningStrategy.ADAPTIVE,
                confidence_threshold=confidence_threshold
            )
            self.orchestrator_v2 = OrchestratorV2(config)
            logger.info("✅ Orchestrator 2.0 initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Orchestrator 2.0: {e}")
            raise RuntimeError(f"Orchestrator 2.0 initialization failed: {e}") from e
    
    async def run(self, 
                  user_query: str,
                  session_id: str,
                  active_document: str = None,
                  active_documents: List[str] = None,
                  memory_context: Dict = None) -> Dict[str, Any]:
        """
        Execute query using Orchestrator 2.0.
        
        This method handles all queries exclusively through Orchestrator 2.0.
        """
        
        # Normalize active documents parameter with smart auto-discovery
        if active_documents is None and active_document:
            active_documents = [active_document]
        elif active_documents is None:
            # 🧠 SMART DOCUMENT SCOPING: Auto-discover relevant documents
            from orchestrator_v2.agent_identity import FinanceRiskAgentIdentity
            agent_identity = FinanceRiskAgentIdentity()
            active_documents = agent_identity._auto_discover_documents_from_query(user_query)
            
            if active_documents:
                logger.info(f"🎯 Auto-discovered {len(active_documents)} documents: {[doc.split('_')[-1] for doc in active_documents]}")
            else:
                logger.info("🎯 No documents auto-discovered, using general knowledge")
                active_documents = []
        
        try:
            logger.info("🚀 Using Orchestrator 2.0")
            
            result = await self.orchestrator_v2.execute_query(
                user_query=user_query,
                session_id=session_id,
                active_documents=active_documents,
                memory_context=memory_context,
                planning_strategy=PlanningStrategy.ADAPTIVE
            )
            
            logger.info(f"✅ Orchestrator 2.0 completed with {result.get('confidence_score', 0):.2f} confidence")
            
            # Convert to v1 format for backward compatibility
            return self._convert_v2_to_v1_format(result)
                    
        except Exception as e:
            logger.error(f"❌ Orchestrator 2.0 failed: {e}")
            
            # Return error result in expected format
            return {
                "status": "error",
                "final_answer": f"Query execution failed: {str(e)}",
                "reasoning_log": [{"error": str(e)}],
                "confidence_score": 0.0,
                "orchestrator_version": "2.0"
            }
    
    async def run_streaming(self,
                           user_query: str,
                           session_id: str,
                           active_document: str = None,
                           active_documents: List[str] = None,
                           memory_context: Dict = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute query with streaming feedback using Orchestrator 2.0.
        """
        
        # Normalize active documents parameter
        if active_documents is None and active_document:
            active_documents = [active_document]
        elif active_documents is None:
            active_documents = []
        
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
            
            yield {
                'type': 'error',
                'message': f"Streaming execution failed: {e}",
                'timestamp': time.time()
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
        """Get status of Orchestrator 2.0."""
        
        status = {
            "integration_version": "2.0",
            "orchestrator_version": "2.0",
            "v2_enabled": True,  # ✅ NEW: Properly report V2 as enabled
            "v2_status": None
        }
        
        try:
            v2_status = self.orchestrator_v2.get_system_status()
            status["v2_status"] = v2_status
            # V2 is fully enabled if orchestrator is working and has no errors
            status["v2_enabled"] = v2_status is not None and v2_status.get("status") == "active"
        except Exception as e:
            status["v2_status"] = {"error": str(e)}
            status["v2_enabled"] = False  # Disable if V2 has errors
        
        return status
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up session data in Orchestrator 2.0."""
        
        try:
            self.orchestrator_v2.cleanup_session(session_id)
        except Exception as e:
            logger.error(f"Failed to cleanup v2 session: {e}")


# Global integration instance
orchestrator_integration = OrchestratorIntegration(
    confidence_threshold=0.5
)