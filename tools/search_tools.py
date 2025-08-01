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
    Searches the current conversation history using the memory system.
    """
    logger.info(f"Searching conversation history for: '{query}'")
    
    try:
        from tools.memory_tools import get_conversation_memory
        conversation_memory = get_conversation_memory()
        
        # Get memory context
        memory_context = await conversation_memory.get_context(query=query)
        
        results = []
        
        # Search short-term memory with flexible matching
        if memory_context.get('short_term'):
            query_words = query.lower().split()
            for message in memory_context['short_term']:
                content = message.get('content', '').lower()
                # Check if any query words match or if there's substantial overlap
                matches = sum(1 for word in query_words if word in content)
                if matches >= 1 or any(word in content for word in ['department', 'summary', 'csv', 'employee']):
                    results.append({
                        "role": message.get('role', 'unknown'),
                        "content": message.get('content', ''),
                        "timestamp": message.get('timestamp', ''),
                        "source": "short_term_memory"
                    })
        
        # Search recent summaries
        if memory_context.get('recent_summaries'):
            for summary in memory_context['recent_summaries']:
                summary_content = summary.get('summary', '').lower()
                if query.lower() in summary_content:
                    results.append({
                        "role": "system",
                        "content": f"Summary: {summary.get('summary', '')}",
                        "timestamp": summary.get('timestamp', ''),
                        "source": "conversation_summary"
                    })
        
        # Search long-term memory
        if memory_context.get('relevant_history'):
            for history_item in memory_context['relevant_history']:
                results.append({
                    "role": "system", 
                    "content": f"Historical reference: {history_item.get('content', '')}",
                    "timestamp": history_item.get('timestamp', ''),
                    "source": "long_term_memory"
                })
        
        logger.info(f"Found {len(results)} conversation history results for '{query}'")
        return results[:5]  # Limit to top 5 results
        
    except Exception as e:
        logger.error(f"Error searching conversation history: {e}")
        return [{
            "role": "system",
            "content": f"Error accessing conversation history: {str(e)}",
            "source": "error"
        }]
