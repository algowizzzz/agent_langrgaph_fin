#!/usr/bin/env python3
"""
Orchestrator V2 with Runtime Verification System

This module provides a verified version of Orchestrator V2 that ensures
correct function execution and detects bypasses.
"""

import logging
from typing import Any, Dict, List, Optional
from orchestrator_v2.orchestrator_v2 import OrchestratorV2, OrchestratorConfig
from orchestrator_v2.tool_registry import ToolReliability
from tools.document_tools_verified import (
    search_uploaded_docs_verified,
    search_multiple_docs_verified,
    verify_document_tools_integrity,
    test_verified_search
)
from runtime_verification_system import verification_system, check_for_bypasses

logger = logging.getLogger(__name__)

class OrchestratorV2Verified(OrchestratorV2):
    """
    Verified version of Orchestrator V2 with runtime verification system.
    """
    
    def __init__(self, config: OrchestratorConfig = None):
        super().__init__(config)
        
        # Override document tools with verified versions
        self._register_verified_tools()
        
        logger.info("🔒 Orchestrator V2 initialized with runtime verification")
    
    def _register_verified_tools(self):
        """Register verified versions of document tools."""
        
        print("🔒 REGISTERING VERIFIED TOOLS...")
        
        # Re-register search_uploaded_docs with verified version
        self.tool_registry.register_function(
            name="search_uploaded_docs",
            func=search_uploaded_docs_verified,
            description="VERIFIED: Search within uploaded documents with runtime verification",
            category="search",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.5,
            retrieve_full_doc_description="Set to True to retrieve the entire document content."
        )
        
        # Re-register search_multiple_docs with verified version
        self.tool_registry.register_function(
            name="search_multiple_docs",
            func=search_multiple_docs_verified,
            description="VERIFIED: Search across multiple documents with runtime verification",
            category="search",
            reliability=ToolReliability.HIGH,
            estimated_duration=2.0
        )
        
        print("✅ VERIFIED TOOLS REGISTERED")
        logger.info("🔒 Verified document tools registered successfully")
    
    async def execute_query_with_verification(self, 
                                            user_query: str,
                                            session_id: str,
                                            active_documents: List[str] = None,
                                            memory_context: Dict = None,
                                            planning_strategy = None) -> Dict[str, Any]:
        """Execute query with additional verification checks."""
        
        print(f"🔒 VERIFIED ORCHESTRATOR: Executing query with verification")
        print(f"🔒 VERIFIED: Query: {user_query}")
        print(f"🔒 VERIFIED: Active documents: {active_documents}")
        
        # Run normal execution
        result = await self.execute_query(
            user_query=user_query,
            session_id=session_id, 
            active_documents=active_documents,
            memory_context=memory_context,
            planning_strategy=planning_strategy
        )
        
        # Check for bypasses if document-related query
        if active_documents and any(doc.endswith('.csv') for doc in active_documents):
            bypass_detected = check_for_bypasses("search_uploaded_docs", result)
            
            if bypass_detected:
                print("🚨 BYPASS DETECTED: Adding verification metadata to result")
                result["verification_warning"] = "Function call bypass detected - result may be from cached/mocked execution"
                result["bypass_detected"] = True
        
        # Add verification metadata
        result["verification_system_active"] = True
        result["verification_timestamp"] = verification_system.get_verification_report()["verification_timestamp"]
        
        return result
    
    def get_verification_status(self) -> Dict[str, Any]:
        """Get comprehensive verification status."""
        return verify_document_tools_integrity()

# Global verified orchestrator instance
verified_orchestrator = None

def get_verified_orchestrator() -> OrchestratorV2Verified:
    """Get or create the verified orchestrator instance."""
    global verified_orchestrator
    
    if verified_orchestrator is None:
        config = OrchestratorConfig(
            max_parallel_steps=3,
            enable_streaming=True,
            enable_persistence=True,
            confidence_threshold=0.5
        )
        verified_orchestrator = OrchestratorV2Verified(config)
        print("🔒 VERIFIED ORCHESTRATOR: Created new verified instance")
    
    return verified_orchestrator

async def run_verification_test() -> Dict[str, Any]:
    """Run comprehensive verification test."""
    
    print("🧪 RUNNING COMPREHENSIVE VERIFICATION TEST...")
    
    # Test 1: Verify function integrity
    integrity_report = verify_document_tools_integrity()
    
    # Test 2: Test verified search directly
    search_test = await test_verified_search()
    
    # Test 3: Test through orchestrator
    orchestrator = get_verified_orchestrator()
    csv_name = "20250801_215110_09205507-73f4-4fec-8792-3cdb156bcd39_test_business_data.csv"
    
    try:
        orchestrator_test = await orchestrator.execute_query_with_verification(
            user_query="Explain the data and extract key insights",
            session_id="verification_test",
            active_documents=[csv_name]
        )
        
        orchestrator_result = {
            "status": "success",
            "bypass_detected": orchestrator_test.get("bypass_detected", False),
            "verification_active": orchestrator_test.get("verification_system_active", False),
            "response_length": len(str(orchestrator_test.get("final_answer", "")))
        }
    except Exception as e:
        orchestrator_result = {
            "status": "failed",
            "error": str(e)
        }
    
    # Compile comprehensive report
    verification_report = {
        "verification_test_timestamp": verification_system.get_verification_report()["verification_timestamp"],
        "integrity_check": integrity_report,
        "direct_search_test": search_test,
        "orchestrator_test": orchestrator_result,
        "overall_status": "verified" if search_test["test_status"] == "success" else "issues_detected"
    }
    
    print(f"🧪 VERIFICATION TEST COMPLETE: {verification_report['overall_status']}")
    return verification_report