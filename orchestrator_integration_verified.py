#!/usr/bin/env python3
"""
Orchestrator Integration with Verification Support

This module extends the orchestrator integration to support runtime verification mode.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from orchestrator_integration import OrchestratorIntegration
from orchestrator_v2_verified import get_verified_orchestrator

logger = logging.getLogger(__name__)

class OrchestratorIntegrationVerified(OrchestratorIntegration):
    """
    Enhanced orchestrator integration with verification support.
    """
    
    def __init__(self, confidence_threshold: float = 0.5, enable_verification: bool = False):
        self.verification_enabled = enable_verification or os.getenv("ENABLE_VERIFICATION", "false").lower() == "true"
        
        if self.verification_enabled:
            logger.info("🔒 Initializing orchestrator with verification system")
            # Use verified orchestrator instead of normal one
            self.verified_orchestrator = get_verified_orchestrator()
            # Still initialize the base class for fallback
            super().__init__(confidence_threshold)
        else:
            logger.info("📋 Initializing standard orchestrator")
            super().__init__(confidence_threshold)
    
    async def run(self, 
                  user_query: str,
                  session_id: str,
                  active_document: str = None,
                  active_documents: List[str] = None,
                  memory_context: Dict = None) -> Dict[str, Any]:
        """
        Execute query with optional verification.
        """
        
        # Normalize active documents parameter
        if active_documents is None and active_document:
            active_documents = [active_document]
        elif active_documents is None:
            active_documents = []
        
        # Check if this is a CSV analysis that could benefit from verification
        needs_verification = (
            self.verification_enabled or 
            (active_documents and any(doc.endswith('.csv') for doc in active_documents))
        )
        
        if needs_verification and hasattr(self, 'verified_orchestrator'):
            logger.info("🔒 Using verified orchestrator for enhanced reliability")
            
            try:
                result = await self.verified_orchestrator.execute_query_with_verification(
                    user_query=user_query,
                    session_id=session_id,
                    active_documents=active_documents,
                    memory_context=memory_context
                )
                
                # Convert to v1 format for backward compatibility
                return self._convert_v2_to_v1_format(result)
                
            except Exception as e:
                logger.warning(f"⚠️ Verified orchestrator failed, falling back to standard: {e}")
                # Fall back to standard orchestrator
                pass
        
        # Use standard orchestrator
        logger.info("📋 Using standard orchestrator")
        return await super().run(user_query, session_id, active_document, active_documents, memory_context)
    
    def enable_verification_mode(self):
        """Enable verification mode at runtime."""
        if not hasattr(self, 'verified_orchestrator'):
            self.verified_orchestrator = get_verified_orchestrator()
        self.verification_enabled = True
        logger.info("🔒 Verification mode enabled")
    
    def disable_verification_mode(self):
        """Disable verification mode at runtime."""
        self.verification_enabled = False
        logger.info("📋 Verification mode disabled")
    
    def get_verification_status(self) -> Dict[str, Any]:
        """Get verification system status."""
        if hasattr(self, 'verified_orchestrator'):
            return self.verified_orchestrator.get_verification_status()
        else:
            return {
                "verification_enabled": False,
                "message": "Verification system not initialized"
            }

# Global instance
orchestrator_integration_verified = None

def get_orchestrator_integration(enable_verification: bool = False) -> OrchestratorIntegrationVerified:
    """Get or create orchestrator integration with optional verification."""
    global orchestrator_integration_verified
    
    if orchestrator_integration_verified is None:
        orchestrator_integration_verified = OrchestratorIntegrationVerified(
            confidence_threshold=0.5,
            enable_verification=enable_verification
        )
    
    return orchestrator_integration_verified

# Patch function to enable verification in existing integration
def enable_verification_globally():
    """Enable verification mode globally."""
    integration = get_orchestrator_integration()
    integration.enable_verification_mode()
    return integration