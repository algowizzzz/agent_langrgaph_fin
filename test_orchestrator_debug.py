#!/usr/bin/env python3
"""
Test orchestrator directly with verbose logging to find where the error occurs
"""

import asyncio
import logging
import json
import sys
import os

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator

async def test_orchestrator_with_csv():
    """Test orchestrator with CSV document"""
    logger.info("=== Testing Orchestrator with CSV Document ===")
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        logger.info("Orchestrator initialized")
        
        # Test with a CSV document that we know exists
        session_id = "test_orchestrator_debug"
        query = "Summarize this CSV data"
        active_document = "sample_data.csv"  # We know this exists from our previous test
        
        logger.info(f"Running orchestrator with:")
        logger.info(f"  Query: {query}")
        logger.info(f"  Session: {session_id}")  
        logger.info(f"  Document: {active_document}")
        
        # Run the orchestrator
        result = await orchestrator.run(query, session_id, active_document=active_document)
        
        logger.info(f"Orchestrator result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        logger.exception("Full traceback:")
        return None

async def main():
    """Main test function"""
    result = await test_orchestrator_with_csv()
    
    if result:
        print("\n🎉 SUCCESS: Orchestrator completed")
        print(f"Status: {result.get('status')}")
        print(f"Answer: {result.get('final_answer', '')[:200]}...")
    else:
        print("\n❌ FAILED: Orchestrator encountered an error")

if __name__ == "__main__":
    asyncio.run(main())