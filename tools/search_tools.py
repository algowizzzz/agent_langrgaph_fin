import logging
from typing import List, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def search_knowledge_base(query: str) -> List[Dict]:
    """
    (Mock) Searches the external knowledge base.
    """
    logger.info(f"Searching knowledge base for: '{query}'")
    return [
        {
            "page_content": f"This is a mock knowledge base result for '{query}'. It would typically contain information from external regulatory documents like OSFI guidelines.",
            "metadata": {"source": "Knowledge Base", "doc_id": "KB-OSFI-123"}
        }
    ]

async def search_conversation_history(query: str) -> List[Dict]:
    """
    (Mock) Searches the current conversation history.
    """
    logger.info(f"Searching conversation history for: '{query}'")
    # In a real implementation, this would search the orchestrator's state.
    return [
        {
            "role": "assistant",
            "content": f"This is a mock history result. I previously mentioned something about '{query}' in a summary."
        }
    ]
