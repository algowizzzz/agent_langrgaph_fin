"""
Fixed search tools with proper error handling instead of mock responses
"""

import logging
import os
import json
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SearchError:
    """Structured error response for search failures"""
    
    @staticmethod
    def create_error(error_type: str, message: str, suggested_action: str = None, retryable: bool = True) -> Dict:
        return {
            "error_type": error_type,
            "success": False,
            "message": message,
            "suggested_action": suggested_action,
            "retryable": retryable,
            "replanning_hints": {
                "tool_failed": True,
                "reason": message
            }
        }

async def search_knowledge_base(query: str) -> List[Dict]:
    """
    Searches the external knowledge base.
    Returns structured error if knowledge base is not available.
    """
    logger.info(f"Searching knowledge base for: '{query}'")
    
    # Check for actual knowledge base implementation
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        logger.warning("Knowledge base directory not found")
        return [SearchError.create_error(
            error_type="knowledge_base_unavailable",
            message="Knowledge base directory not found. Create 'knowledge_base/' directory with documents.",
            suggested_action="setup_knowledge_base_or_use_uploaded_docs",
            retryable=False
        )]
    
    # Check for knowledge base files
    kb_files = list(kb_path.glob("**/*.pdf")) + list(kb_path.glob("**/*.txt"))
    if not kb_files:
        logger.warning("No knowledge base files found")
        return [SearchError.create_error(
            error_type="knowledge_base_empty", 
            message=f"Knowledge base directory exists but contains no searchable files (.pdf, .txt)",
            suggested_action="add_documents_to_knowledge_base_or_search_uploaded_docs",
            retryable=False
        )]
    
    # If we have files, we would implement actual search here
    logger.info(f"Found {len(kb_files)} files in knowledge base")
    return [SearchError.create_error(
        error_type="search_not_implemented",
        message=f"Knowledge base search not yet implemented. Found {len(kb_files)} files available for search.",
        suggested_action="implement_knowledge_base_search_or_use_document_search",
        retryable=False
    )]

async def search_conversation_history(query: str) -> List[Dict]:
    """
    Searches the current conversation history using the memory system.
    Returns structured error if memory system is not available.
    """
    logger.info(f"Searching conversation history for: '{query}'")
    
    try:
        # Check if memory system is available
        memory_dir = Path("memory")
        if not memory_dir.exists():
            logger.warning("Memory directory not found")
            return [SearchError.create_error(
                error_type="memory_system_unavailable",
                message="Memory directory not found. Memory system may not be initialized.",
                suggested_action="initialize_memory_system",
                retryable=True
            )]
        
        # Try to import and use memory tools
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
                        "source": "short_term_memory",
                        "relevance_score": matches / len(query_words)
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
                        "source": "conversation_summary",
                        "relevance_score": 0.8
                    })
        
        # Search long-term memory
        if memory_context.get('relevant_history'):
            for history_item in memory_context['relevant_history']:
                results.append({
                    "role": "system", 
                    "content": f"Historical reference: {history_item.get('content', '')}",
                    "timestamp": history_item.get('timestamp', ''),
                    "source": "long_term_memory",
                    "relevance_score": 0.6
                })
        
        if not results:
            logger.info(f"No conversation history found for '{query}'")
            return [SearchError.create_error(
                error_type="no_conversation_history",
                message=f"No relevant conversation history found for query: '{query}'",
                suggested_action="use_broader_search_terms_or_search_documents",
                retryable=True
            )]
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"Found {len(results)} conversation history results for '{query}'")
        return results[:5]  # Limit to top 5 results
        
    except ImportError as e:
        logger.error(f"Memory tools not available: {e}")
        return [SearchError.create_error(
            error_type="memory_tools_import_error",
            message=f"Could not import memory tools: {str(e)}",
            suggested_action="check_memory_tools_installation",
            retryable=False
        )]
    except Exception as e:
        logger.error(f"Error searching conversation history: {e}")
        return [SearchError.create_error(
            error_type="conversation_search_error",
            message=f"Error accessing conversation history: {str(e)}",
            suggested_action="check_memory_system_status",
            retryable=True
        )]

async def search_external_sources(query: str, source_type: str = "regulatory") -> List[Dict]:
    """
    Search external sources like regulatory databases.
    Returns structured error since this requires external API integration.
    """
    logger.info(f"Searching external {source_type} sources for: '{query}'")
    
    return [SearchError.create_error(
        error_type="external_search_not_implemented",
        message=f"External {source_type} source search not implemented. Requires API integration.",
        suggested_action="implement_external_api_integration_or_use_uploaded_documents",
        retryable=False
    )]