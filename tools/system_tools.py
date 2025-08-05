"""
System self-awareness tools for AI Finance and Risk Agent
Provides accurate information about agent capabilities, documents, and workflows.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Import register_tool only when needed to avoid circular imports
def _register_tools():
    """Register tools after all imports are complete."""
    try:
        from orchestrator_v2.tool_registry import register_tool, ToolReliability
        
        # Register the tools programmatically
        global_registry = None
        try:
            from orchestrator_v2.tool_registry import global_tool_registry
            global_registry = global_tool_registry
        except ImportError:
            pass
            
        if global_registry:
            global_registry.register_function("get_agent_capabilities", get_agent_capabilities, "system", ToolReliability.HIGH)
            global_registry.register_function("get_available_documents", get_available_documents, "system", ToolReliability.HIGH)
            global_registry.register_function("get_workflow_information", get_workflow_information, "system", ToolReliability.HIGH)
            
    except Exception as e:
        logger.warning(f"Could not register system tools: {e}")

async def get_agent_capabilities() -> Dict[str, Any]:
    """
    Get comprehensive information about the agent's capabilities, tools, and workflows.
    
    Returns:
        Dict containing agent capabilities, available tools, workflows, and document access
    """
    logger.info("Retrieving agent capabilities for self-awareness query")
    
    try:
        # Import here to avoid circular imports
        from orchestrator_v2.agent_identity import agent_identity
        from tools.document_tools import document_chunk_store
        
        # Get agent info from the identity system
        agent_info = agent_identity.get_agent_info()
        
        # Get available documents using the dedicated function
        doc_info = await get_available_documents()
        doc_count = doc_info.get("total_documents", 0)
        available_docs = [doc.get("display_name", doc.get("internal_name", "")) for doc in doc_info.get("documents", [])]
        
        # Get tool information from centralized registry
        tools_info = await _get_live_tool_registry_data()
        
        return {
            "agent_identity": {
                "name": agent_info.get("name", "AI Finance and Risk Agent"),
                "version": agent_info.get("version", "2.0.0"),
                "specialization": agent_info.get("specialization", "Financial Analysis, Risk Assessment, and Data Processing")
            },
            "core_capabilities": agent_info.get("core_capabilities", []),
            "workflow_types": agent_info.get("workflow_types", []),
            "memory_sources": agent_info.get("memory_sources", []),
            "document_access": {
                "has_document_store": True,
                "total_documents": doc_count,
                "supported_formats": ["PDF", "DOCX", "TXT", "CSV", "Excel (multi-sheet)"],
                "sample_documents": available_docs[:3] if available_docs else []
            },
            "available_tools": {
                "total_tools": tools_info.get("total_tools", 0),
                "registry_status": tools_info.get("status", "unknown"),
                "tools_by_category": tools_info.get("tools_by_category", {}),
                "all_tools": tools_info.get("all_tools", [])
            },
            "system_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving agent capabilities: {e}")
        return {
            "error": f"Unable to retrieve full capabilities: {e}",
            "agent_identity": {
                "name": "AI Finance and Risk Agent",
                "version": "2.0.0",
                "specialization": "Financial Analysis and Risk Assessment"
            },
            "system_status": "limited_info"
        }

async def get_available_documents() -> Dict[str, Any]:
    """
    Get information about currently available documents in the system.
    
    Returns:
        Dict containing document inventory and metadata
    """
    logger.info("Retrieving available documents for self-awareness query")
    
    try:
        from tools.document_tools import document_chunk_store
        
        if not document_chunk_store:
            return {
                "total_documents": 0,
                "documents": [],
                "message": "No documents currently uploaded. You can upload PDF, DOCX, TXT, CSV, or Excel files for analysis."
            }
        
        documents = []
        for doc_name, chunks in document_chunk_store.items():
            # Extract clean display name
            display_name = doc_name
            if chunks and len(chunks) > 0:
                metadata = chunks[0].get('metadata', {})
                display_name = metadata.get('display_name', doc_name)
                
            doc_info = {
                "display_name": display_name,
                "internal_name": doc_name,
                "chunk_count": len(chunks),
                "file_type": _get_file_type(doc_name),
                "available_for_analysis": True
            }
            documents.append(doc_info)
        
        return {
            "total_documents": len(documents),
            "documents": documents,
            "capabilities": [
                "Financial analysis and ratio calculations",
                "Multi-document comparison and synthesis", 
                "Data visualization and statistical analysis",
                "Risk assessment and trend identification",
                "Comprehensive document summarization"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving available documents: {e}")
        return {
            "error": f"Unable to retrieve document information: {e}",
            "total_documents": 0,
            "documents": []
        }

async def get_workflow_information() -> Dict[str, Any]:
    """
    Get detailed information about available workflows and their capabilities.
    
    Returns:
        Dict containing workflow descriptions and use cases
    """
    logger.info("Retrieving workflow information for self-awareness query")
    
    try:
        from orchestrator_v2.agent_identity import agent_identity, WorkflowType
        
        workflows = {
            WorkflowType.DOCUMENT_ANALYSIS.value: {
                "name": "Document Analysis",
                "description": "Comprehensive analysis of single documents (PDF, DOCX, TXT)",
                "use_cases": [
                    "Analyze financial reports and statements",
                    "Extract key insights from risk assessments", 
                    "Summarize regulatory documents",
                    "Answer questions about document content"
                ],
                "example_queries": [
                    "What is the company's profitability?",
                    "Summarize the risk factors",
                    "Analyze this financial statement"
                ]
            },
            WorkflowType.DATA_ANALYSIS.value: {
                "name": "Data Analysis", 
                "description": "Statistical analysis of CSV and Excel files with financial calculations",
                "use_cases": [
                    "Process multi-sheet Excel financial models",
                    "Calculate financial ratios and metrics",
                    "Generate data visualizations and charts",
                    "Perform statistical analysis on datasets"
                ],
                "example_queries": [
                    "Analyze this financial data",
                    "What are the profitability trends?",
                    "Create a summary of each table"
                ]
            },
            WorkflowType.MULTI_DOC_COMPARISON.value: {
                "name": "Multi-Document Comparison",
                "description": "Compare and contrast multiple documents for similarities and differences",
                "use_cases": [
                    "Compare financial statements across periods",
                    "Analyze different company performance",
                    "Identify trends across multiple reports",
                    "Benchmark analysis between documents"
                ],
                "example_queries": [
                    "Compare these two financial reports",
                    "What are the similarities and differences?",
                    "How do these companies compare?"
                ]
            },
            WorkflowType.MEMORY_SEARCH.value: {
                "name": "Memory Search",
                "description": "Search previous conversations and build on prior context",
                "use_cases": [
                    "Recall previous analysis results",
                    "Continue interrupted conversations", 
                    "Reference earlier calculations",
                    "Build on previous insights"
                ],
                "example_queries": [
                    "What did we discuss about risk?",
                    "Remember our previous analysis",
                    "Recall what we said about profitability"
                ]
            },
            WorkflowType.QA_FALLBACK_CHAIN.value: {
                "name": "Q&A Fallback Chain",
                "description": "Answer general questions using comprehensive knowledge sources",
                "use_cases": [
                    "General financial knowledge questions",
                    "Technical definitions and explanations",
                    "Industry best practices",
                    "Educational content"
                ],
                "example_queries": [
                    "What is a CET1 ratio?",
                    "Explain corporate finance basics",
                    "What are financial derivatives?"
                ]
            }
        }
        
        return {
            "total_workflows": len(workflows),
            "workflows": workflows,
            "workflow_selection": "Automatic - based on query type and available documents",
            "capabilities": "Full orchestrator with parallel execution and state management"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving workflow information: {e}")
        return {
            "error": f"Unable to retrieve workflow information: {e}",
            "total_workflows": 0,
            "workflows": {}
        }

async def _get_live_tool_registry_data() -> Dict[str, Any]:
    """Get live tool information from the centralized registry."""
    try:
        from orchestrator_v2.tool_registry import global_tool_registry
        
        if not global_tool_registry or not hasattr(global_tool_registry, '_tools'):
            # Fallback to static info if registry not available
            return {
                "total_tools": 0,
                "tools_by_category": {},
                "all_tools": [],
                "status": "registry_unavailable"
            }
        
        # Get all registered tools
        all_tools = []
        tools_by_category = {}
        
        for tool_name, tool_metadata in global_tool_registry._tools.items():
            category = getattr(tool_metadata, 'category', 'other')
            
            tool_info = {
                "name": tool_name,
                "category": category,
                "description": f"{tool_name} - {_get_tool_description(tool_name)}"
            }
            
            all_tools.append(tool_info)
            
            # Group by category
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool_info["description"])
        
        return {
            "total_tools": len(all_tools),
            "tools_by_category": tools_by_category,
            "all_tools": all_tools,
            "status": "live_registry_data"
        }
        
    except Exception as e:
        logger.warning(f"Could not access tool registry: {e}")
        # Return fallback static info
        return {
            "total_tools": 0,
            "tools_by_category": {
                "status": "error",
                "message": f"Registry access failed: {e}"
            },
            "all_tools": [],
            "status": "fallback_mode"
        }

def _get_tool_description(tool_name: str) -> str:
    """Get a user-friendly description for a tool."""
    descriptions = {
        # Document tools
        "upload_document": "Process and store new documents (PDF, DOCX, TXT, CSV, Excel)",
        "search_uploaded_docs": "Search and retrieve uploaded documents",
        "discover_document_structure": "Analyze document structure and metadata",
        "get_all_documents": "List all available documents",
        "remove_document": "Remove documents from storage",
        
        # Search tools
        "search_multiple_docs": "Compare and analyze multiple documents simultaneously",
        "search_knowledge_base": "Access external knowledge resources",
        "search_conversation_history": "Access previous conversation context",
        
        # Synthesis
        "synthesize_content": "Generate analysis and summaries from documents",
        
        # Computation
        "execute_python_code": "Execute custom calculations and data processing",
        "process_table_data": "Process structured table and spreadsheet data",
        "calculate_statistics": "Calculate financial metrics and statistical measures",
        
        # Visualization
        "create_chart": "Generate charts and graphs from data",
        "create_wordcloud": "Create visual word frequency representations", 
        "create_statistical_plot": "Generate statistical plots and distributions",
        "create_comparison_chart": "Create comparative visualizations",
        
        # Analysis
        "analyze_text_metrics": "Analyze text structure and readability metrics",
        "extract_key_phrases": "Extract important phrases and concepts",
        "analyze_sentiment": "Analyze emotional tone and sentiment",
        "extract_entities": "Extract named entities and key terms",
        
        # System
        "get_agent_capabilities": "Retrieve agent capability information",
        "get_available_documents": "Get information about available documents",
        "get_workflow_information": "Get details about available workflows"
    }
    
    return descriptions.get(tool_name, "Specialized processing tool")

def _get_file_type(filename: str) -> str:
    """Helper function to determine file type from filename."""
    if filename.endswith('.pdf'):
        return 'PDF'
    elif filename.endswith(('.xlsx', '.xls')):
        return 'Excel'
    elif filename.endswith('.csv'):
        return 'CSV'
    elif filename.endswith(('.docx', '.doc')):
        return 'Word Document'
    elif filename.endswith('.txt'):
        return 'Text File'
    else:
        return 'Unknown'

# Register tools when module is imported
_register_tools()