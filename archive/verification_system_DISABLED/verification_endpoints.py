#!/usr/bin/env python3
"""
Verification Endpoints for Runtime Verification System

This module provides API endpoints to monitor and test the runtime verification system.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from runtime_verification_system import verification_system, get_verification_status
from tools.document_tools_verified import verify_document_tools_integrity, test_verified_search
from orchestrator_v2_verified import get_verified_orchestrator, run_verification_test

logger = logging.getLogger(__name__)

# Create router for verification endpoints
verification_router = APIRouter(prefix="/verification", tags=["verification"])

@verification_router.get("/status")
async def get_verification_system_status() -> Dict[str, Any]:
    """Get comprehensive verification system status."""
    try:
        return get_verification_status()
    except Exception as e:
        logger.error(f"Error getting verification status: {e}")
        raise HTTPException(status_code=500, detail=f"Verification status error: {str(e)}")

@verification_router.get("/integrity")
async def check_document_tools_integrity() -> Dict[str, Any]:
    """Check the integrity of document tools and detect bypasses."""
    try:
        return verify_document_tools_integrity()
    except Exception as e:
        logger.error(f"Error checking integrity: {e}")
        raise HTTPException(status_code=500, detail=f"Integrity check error: {str(e)}")

@verification_router.post("/test/search")
async def test_verified_search_endpoint() -> Dict[str, Any]:
    """Test the verified search function directly."""
    try:
        result = await test_verified_search()
        return result
    except Exception as e:
        logger.error(f"Error testing verified search: {e}")
        raise HTTPException(status_code=500, detail=f"Search test error: {str(e)}")

@verification_router.post("/test/comprehensive")
async def run_comprehensive_verification_test() -> Dict[str, Any]:
    """Run comprehensive verification test including orchestrator."""
    try:
        result = await run_verification_test()
        return result
    except Exception as e:
        logger.error(f"Error running comprehensive test: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive test error: {str(e)}")

@verification_router.get("/call-history")
async def get_function_call_history() -> Dict[str, Any]:
    """Get detailed function call history."""
    try:
        report = verification_system.get_verification_report()
        
        # Add detailed call records
        recent_calls = verification_system.call_records[-20:]  # Last 20 calls
        call_details = []
        
        for record in recent_calls:
            call_details.append({
                "function_name": record.function_name,
                "call_id": record.call_id,
                "timestamp": record.timestamp,
                "execution_time": record.execution_time,
                "success": record.success,
                "parameters": record.parameters,
                "caller_info": record.caller_info,
                "error": record.error
            })
        
        return {
            "summary": report,
            "recent_calls": call_details,
            "total_records": len(verification_system.call_records)
        }
    except Exception as e:
        logger.error(f"Error getting call history: {e}")
        raise HTTPException(status_code=500, detail=f"Call history error: {str(e)}")

@verification_router.post("/test/csv-analysis")
async def test_csv_analysis_with_verification() -> Dict[str, Any]:
    """Test CSV analysis with full verification."""
    try:
        orchestrator = get_verified_orchestrator()
        csv_name = "20250801_215110_09205507-73f4-4fec-8792-3cdb156bcd39_test_business_data.csv"
        
        # Execute with verification
        result = await orchestrator.execute_query_with_verification(
            user_query="Summarize the business data for executive review",
            session_id="verification_test_csv",
            active_documents=[csv_name]
        )
        
        # Get verification status after execution
        post_execution_status = verification_system.get_verification_report()
        
        return {
            "orchestrator_result": {
                "success": result.get("status") != "error",
                "final_answer": result.get("final_answer", ""),
                "bypass_detected": result.get("bypass_detected", False),
                "verification_active": result.get("verification_system_active", False),
                "confidence_score": result.get("confidence_score", 0)
            },
            "verification_status": post_execution_status,
            "test_timestamp": post_execution_status.get("verification_timestamp"),
            "function_calls_during_test": len([
                r for r in verification_system.call_records 
                if r.function_name == "search_uploaded_docs" and 
                   abs(r.timestamp - verification_system.call_records[-1].timestamp) < 60
            ]) if verification_system.call_records else 0
        }
    except Exception as e:
        logger.error(f"Error testing CSV analysis: {e}")
        raise HTTPException(status_code=500, detail=f"CSV analysis test error: {str(e)}")

@verification_router.post("/force-verification-mode")
async def force_verification_mode() -> Dict[str, Any]:
    """Force the system to use verified functions."""
    try:
        # Get the verified orchestrator (this switches to verification mode)
        orchestrator = get_verified_orchestrator()
        
        # Run a quick integrity check
        integrity = verify_document_tools_integrity()
        
        return {
            "status": "verification_mode_activated",
            "verified_orchestrator_active": True,
            "integrity_check": integrity,
            "message": "System is now using verified functions with runtime verification"
        }
    except Exception as e:
        logger.error(f"Error forcing verification mode: {e}")
        raise HTTPException(status_code=500, detail=f"Verification mode error: {str(e)}")

# Function to include the router in the main app
def include_verification_endpoints(app):
    """Include verification endpoints in the FastAPI app."""
    app.include_router(verification_router)
    logger.info("🔒 Verification endpoints added to application")
 
 
 