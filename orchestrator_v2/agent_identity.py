"""
AI Finance and Risk Agent Identity System

This module defines the agent's identity, capabilities, and specialized knowledge
for financial analysis, risk assessment, and productivity assistance.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MemorySource(Enum):
    """Different memory sources for the fallback chain."""
    UPLOADED_DOCUMENTS = "uploaded_documents"
    KNOWLEDGE_BASE_EMBEDDINGS = "knowledge_base_embeddings"  
    LONG_TERM_CONVERSATION = "long_term_conversation"
    LLM_KNOWLEDGE_BASE = "llm_knowledge_base"


class WorkflowType(Enum):
    """Types of workflows the agent can execute."""
    DOCUMENT_ANALYSIS = "document_analysis"
    FINANCIAL_COMPARISON = "financial_comparison"
    QA_FALLBACK_CHAIN = "qa_fallback_chain"
    DATA_ANALYSIS = "data_analysis"
    PRODUCTIVITY_ASSISTANCE = "productivity_assistance"
    MEMORY_SEARCH = "memory_search"


@dataclass
class AgentCapability:
    """Represents a specific capability of the agent."""
    name: str
    description: str
    workflow_type: WorkflowType
    trigger_patterns: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class MemorySourceConfig:
    """Configuration for a memory source in the fallback chain."""
    source: MemorySource
    priority: int
    condition: str
    description: str
    tools: List[str] = field(default_factory=list)


class FinanceRiskAgentIdentity:
    """
    AI Finance and Risk Agent identity and capabilities system.
    
    Defines agent persona, core capabilities, memory systems, and 
    intelligent query routing with comprehensive fallback chains.
    """
    
    def __init__(self):
        self.agent_name = "AI Finance and Risk Agent"
        self.agent_version = "2.0.0"
        self.specialization = "Financial Analysis, Risk Assessment, and Productivity"
        
        # Initialize capabilities
        self._setup_capabilities()
        
        # Initialize memory fallback chain
        self._setup_memory_fallback_chain()
        
        # Initialize structured prompt templates
        self._setup_prompt_templates()
        
        logger.info(f"Initialized {self.agent_name} v{self.agent_version}")
    
    def _setup_capabilities(self):
        """Initialize core agent capabilities."""
        self.capabilities = {
            "document_analysis": AgentCapability(
                name="Document Analysis & Synthesis",
                description="Analyze single or multiple financial documents with specialized expertise",
                workflow_type=WorkflowType.DOCUMENT_ANALYSIS,
                trigger_patterns=["analyze", "what is", "explain", "summarize"],
                tools_required=["search_uploaded_docs", "synthesize_content"],
                examples=[
                    "What is risk? (with riskandfinace.pdf uploaded)",
                    "Analyze this financial report"
                ]
            ),
            
            "financial_comparison": AgentCapability(
                name="Multi-Document Financial Comparison",
                description="Compare multiple financial documents using 5k word chunks and refine method",
                workflow_type=WorkflowType.FINANCIAL_COMPARISON,
                trigger_patterns=["compare", "differences", "similarities", "versus", "contrast"],
                tools_required=["chunk_documents", "refine_method", "financial_analysis_prompt"],
                examples=[
                    "Compare car24_chpt1_0.pdf and car24_chpt7.pdf for similarities and differences as a financial analyst"
                ]
            ),
            
            "qa_system": AgentCapability(
                name="Q&A with Comprehensive Fallback Chain",
                description="Answer questions using intelligent routing through multiple memory sources",
                workflow_type=WorkflowType.QA_FALLBACK_CHAIN,
                trigger_patterns=["what", "how", "why", "when", "where", "explain"],
                tools_required=["search_knowledge_base", "search_conversation_history"],
                examples=[
                    "What is risk? (no documents uploaded - uses fallback chain)"
                ]
            ),
            
            "data_analysis": AgentCapability(
                name="Progressive Data Analysis",
                description="Analyze CSV/Excel data with Python calculations and visualizations",
                workflow_type=WorkflowType.DATA_ANALYSIS,
                trigger_patterns=["analyze data", "calculate", "chart", "graph", "table"],
                tools_required=["process_table_data", "execute_python_code", "create_chart"],
                examples=[
                    "Give table data summary → Add column A and B → Draw a graph"
                ]
            ),
            
            "productivity": AgentCapability(
                name="Productivity Assistant",
                description="Help with daily tasks integrated with financial and risk expertise",
                workflow_type=WorkflowType.PRODUCTIVITY_ASSISTANCE,
                trigger_patterns=["help me", "assist", "plan", "organize", "schedule"],
                tools_required=["search_knowledge_base"],
                examples=[
                    "Help me analyze this quarterly report",
                    "Plan my financial review process"
                ]
            ),
            
            "memory_search": AgentCapability(
                name="Memory Search",
                description="Search through conversation history and saved memory when user mentions memory",
                workflow_type=WorkflowType.MEMORY_SEARCH,
                trigger_patterns=["remember", "memory", "mentioned", "said before", "recall", "previous"],
                tools_required=["search_conversation_history"],
                examples=[
                    "What did we discuss about risk last week?",
                    "Remember when you mentioned that financial strategy?",
                    "Recall our previous conversation about investments"
                ]
            )
        }
    
    def _setup_memory_fallback_chain(self):
        """Setup the comprehensive memory fallback chain."""
        self.memory_fallback_chain = [
            MemorySourceConfig(
                source=MemorySource.UPLOADED_DOCUMENTS,
                priority=1,
                condition="if active_documents exist",
                description="Search uploaded documents first (highest priority)",
                tools=["search_uploaded_docs", "synthesize_content"]
            ),
            
            MemorySourceConfig(
                source=MemorySource.KNOWLEDGE_BASE_EMBEDDINGS,
                priority=2,
                condition="if no uploaded docs OR step_1 fails",
                description="Search knowledge base embeddings",
                tools=["search_knowledge_base"]
            ),
            
            MemorySourceConfig(
                source=MemorySource.LONG_TERM_CONVERSATION,
                priority=3,
                condition="check for relevant context from conversation history",
                description="Search long-term conversation memory for context",
                tools=["search_conversation_history"]
            ),
            
            MemorySourceConfig(
                source=MemorySource.LLM_KNOWLEDGE_BASE,
                priority=4,
                condition="if knowledge_base returns 'idk'",
                description="Generate answer from LLM knowledge base with financial/risk expertise",
                tools=["llm_synthesis"]
            )
        ]
    
    def _setup_prompt_templates(self):
        """Setup structured prompt templates for financial analysis."""
        self.prompt_templates = {
            "financial_comparison": {
                "objective": "Compare {documents} for {comparison_type} as a financial analyst",
                "persona": "You are an expert financial analyst with deep knowledge of financial markets, risk assessment, and regulatory frameworks.",
                "output_format": """
                **EXECUTIVE SUMMARY**
                Brief overview of key findings

                **SIMILARITIES**
                - Key commonalities between documents
                - Shared financial metrics or approaches

                **DIFFERENCES** 
                - Major differences in approach or content
                - Contrasting financial perspectives

                **FINANCIAL ANALYSIS**
                - Risk assessment implications
                - Financial performance insights
                - Regulatory considerations

                **RECOMMENDATIONS**
                - Strategic recommendations based on analysis
                """
            },
            
            "document_analysis": {
                "objective": "Analyze {document} for {analysis_type} with financial expertise",
                "persona": "You are a senior financial analyst specializing in risk assessment and financial document analysis.",
                "output_format": """
                **DOCUMENT OVERVIEW**
                Summary of document content and purpose

                **KEY FINDINGS**
                - Primary financial insights
                - Risk factors identified
                - Performance metrics

                **ANALYSIS**
                - Detailed financial analysis
                - Risk assessment
                - Market implications

                **CONCLUSIONS**
                - Summary of key takeaways
                - Actionable insights
                """
            },
            
            "data_analysis": {
                "objective": "Analyze data with financial context and generate insights",
                "persona": "You are a financial data analyst expert in statistical analysis and financial modeling.",
                "output_format": """
                **DATA SUMMARY**
                Overview of dataset and key metrics

                **CALCULATIONS**
                ```python
                # Python code for calculations
                ```

                **VISUALIZATIONS**
                [Charts and graphs as requested]

                **FINANCIAL INSIGHTS**
                - Key patterns and trends
                - Financial implications
                - Risk considerations
                """
            }
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information."""
        return {
            "name": self.agent_name,
            "version": self.agent_version,
            "specialization": self.specialization,
            "core_capabilities": [cap.name for cap in self.capabilities.values()],
            "memory_sources": [source.source.value for source in self.memory_fallback_chain],
            "workflow_types": [wf.value for wf in WorkflowType]
        }
    
    def classify_query_workflow(self, user_query: str, active_documents: List[str] = None) -> WorkflowType:
        """
        Classify user query to determine appropriate workflow.
        
        Args:
            user_query: The user's question or request
            active_documents: List of uploaded documents
            
        Returns:
            WorkflowType for the most appropriate workflow
        """
        query_lower = user_query.lower()
        active_docs = active_documents or []
        
        # Priority 1: Document Analysis (if documents exist)
        if active_docs:
            if len(active_docs) > 1:
                # Multi-document analysis
                if any(pattern in query_lower for pattern in ["compare", "difference", "similar", "versus"]):
                    return WorkflowType.FINANCIAL_COMPARISON
            
            # Single document analysis - prioritize when documents are available
            # Check for document-focused keywords OR any content query when docs exist
            doc_keywords = ["analyze", "what is", "explain", "summarize", "mentioned", "types", "kinds", "list", "identify", "find", "show", "tell me about"]
            if any(pattern in query_lower for pattern in doc_keywords):
                return WorkflowType.DOCUMENT_ANALYSIS
        
        # Priority 2: Data Analysis (CSV/Excel detection)
        if any(pattern in query_lower for pattern in ["table", "csv", "data", "calculate", "chart", "graph"]):
            return WorkflowType.DATA_ANALYSIS
        
        # Priority 3: Memory Search (user mentions memory/recall)
        if any(pattern in query_lower for pattern in ["remember", "memory", "mentioned", "said before", "recall", "previous", "discussed"]):
            return WorkflowType.MEMORY_SEARCH
        
        # Priority 4: Productivity Assistance
        if any(pattern in query_lower for pattern in ["help me", "assist", "plan", "organize"]):
            return WorkflowType.PRODUCTIVITY_ASSISTANCE
        
        # Default: Q&A Fallback Chain
        return WorkflowType.QA_FALLBACK_CHAIN
    
    def get_memory_source_for_query(self, workflow_type: WorkflowType, active_documents: List[str] = None) -> MemorySource:
        """
        Determine the appropriate memory source for a query based on workflow and context.
        
        Args:
            workflow_type: The classified workflow type
            active_documents: List of uploaded documents
            
        Returns:
            MemorySource to start the fallback chain
        """
        # If documents are available, start with uploaded documents
        if active_documents:
            return MemorySource.UPLOADED_DOCUMENTS
        
        # Otherwise start with knowledge base embeddings
        return MemorySource.KNOWLEDGE_BASE_EMBEDDINGS
    
    def get_structured_prompt(self, workflow_type: WorkflowType, **kwargs) -> str:
        """
        Generate structured prompt based on workflow type and parameters.
        
        Args:
            workflow_type: The workflow type
            **kwargs: Template variables (documents, analysis_type, etc.)
            
        Returns:
            Structured prompt with objective, persona, and output format
        """
        if workflow_type == WorkflowType.FINANCIAL_COMPARISON:
            template = self.prompt_templates["financial_comparison"]
        elif workflow_type == WorkflowType.DOCUMENT_ANALYSIS:
            template = self.prompt_templates["document_analysis"]
        elif workflow_type == WorkflowType.DATA_ANALYSIS:
            template = self.prompt_templates["data_analysis"]
        else:
            # Default template for other workflows
            return kwargs.get("custom_prompt", "Analyze the provided information with financial expertise.")
        
        # Format the template with provided parameters
        objective = template["objective"].format(**kwargs)
        persona = template["persona"]
        output_format = template["output_format"]
        
        return f"""
OBJECTIVE: {objective}

PERSONA: {persona}

OUTPUT FORMAT:
{output_format}

Please analyze the provided information according to the above structure.
"""

    def get_capability_info(self, capability_name: str) -> Optional[AgentCapability]:
        """Get information about a specific capability."""
        return self.capabilities.get(capability_name)
    
    def list_all_capabilities(self) -> List[str]:
        """List all available capabilities."""
        return list(self.capabilities.keys())


# Global instance for the agent identity
agent_identity = FinanceRiskAgentIdentity()