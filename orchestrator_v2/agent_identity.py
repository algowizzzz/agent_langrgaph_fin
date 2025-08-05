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
    MULTI_DOC_COMPARISON = "multi_doc_comparison"
    QA_FALLBACK_CHAIN = "qa_fallback_chain"
    DATA_ANALYSIS = "data_analysis"
    MEMORY_SEARCH = "memory_search"
    SYSTEM_AWARENESS = "system_awareness"


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
            
            "multi_doc_comparison": AgentCapability(
                name="Multi-Document Financial Comparison",
                description="Compare multiple financial documents using 5k word chunks and refine method",
                workflow_type=WorkflowType.MULTI_DOC_COMPARISON,
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
            ),
            
            "system_awareness": AgentCapability(
                name="System Self-Awareness",
                description="Provide accurate information about agent capabilities, tools, documents, and workflows",
                workflow_type=WorkflowType.SYSTEM_AWARENESS,
                trigger_patterns=["what documents", "what tools", "what workflows", "what capabilities", "what can you", "what do you have access"],
                tools_required=["get_agent_capabilities", "get_available_documents", "get_workflow_information"],
                examples=[
                    "What documents do you have access to?",
                    "What tools do you have access to?",
                    "What workflows do you have access to?",
                    "What are your capabilities?"
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
            "multi_doc_comparison": {
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
    
    def _auto_discover_documents_from_query(self, user_query: str) -> List[str]:
        """
        Intelligent document discovery based on query content.
        
        Strategy:
        1. Check for specific document names/keywords in query
        2. If specific documents found, use those
        3. If no specific documents but query suggests document analysis, use all documents
        4. If query is general knowledge, return empty list (use LLM knowledge)
        """
        from tools.document_tools import document_chunk_store
        
        try:
            all_docs = list(document_chunk_store.keys())
            if not all_docs:
                return []
            
            query_lower = user_query.lower()
            specific_docs = []
            
            # 🎯 STEP 1: Look for specific document references
            for doc in all_docs:
                doc_lower = doc.lower()
                # Extract readable parts of filename for matching
                readable_parts = []
                
                # Extract original filename parts (after timestamps and UUIDs)
                if '_' in doc:
                    parts = doc.split('_')
                    for part in parts:
                        if len(part) > 3 and not part.replace('-', '').isalnum():
                            readable_parts.append(part.lower())
                
                # Check for matches
                for part in readable_parts:
                    if part in query_lower:
                        specific_docs.append(doc)
                        print(f"🎯 Auto-discovered document: {doc} (matched: {part})")
                        break
                
                # Check for common patterns
                if any(keyword in query_lower for keyword in ['techtrend', 'financials', 'excel']) and 'techtrend' in doc_lower:
                    if doc not in specific_docs:
                        specific_docs.append(doc)
                        print(f"🎯 Auto-discovered document: {doc} (TechTrend pattern)")
                
                if any(keyword in query_lower for keyword in ['bmo', 'bank', 'annual']) and 'bmo' in doc_lower:
                    if doc not in specific_docs:
                        specific_docs.append(doc)
                        print(f"🎯 Auto-discovered document: {doc} (BMO pattern)")
                
                if any(keyword in query_lower for keyword in ['risk', 'finance']) and 'risk' in doc_lower:
                    if doc not in specific_docs:
                        specific_docs.append(doc)
                        print(f"🎯 Auto-discovered document: {doc} (Risk pattern)")
                
                if any(keyword in query_lower for keyword in ['car24', 'capital', 'regulatory']) and 'car24' in doc_lower:
                    if doc not in specific_docs:
                        specific_docs.append(doc)
                        print(f"🎯 Auto-discovered document: {doc} (CAR24 pattern)")
            
            # 🎯 STEP 2: If specific documents found, use those
            if specific_docs:
                return specific_docs
            
            # 🎯 STEP 3: If query suggests document analysis but no specific docs, use all
            document_indicators = [
                'analyze', 'summary', 'summarize', 'document', 'file', 'report', 'data',
                'table', 'excel', 'csv', 'financial', 'metrics', 'compare', 'contrast'
            ]
            
            if any(indicator in query_lower for indicator in document_indicators):
                print(f"🎯 Query suggests document analysis, using all {len(all_docs)} documents")
                return all_docs
            
            # 🎯 STEP 4: General knowledge query - no documents needed
            print(f"🎯 General knowledge query detected, no documents needed")
            return []
            
        except Exception as e:
            print(f"⚠️ Error in auto-discovery: {e}")
            return []
    
    def classify_query_workflow(self, user_query: str, active_documents: List[str] = None) -> WorkflowType:
        """
        Classify user query to determine appropriate workflow based on FILE TYPE.
        Smart document scoping: auto-discover relevant documents from query content.
        
        Args:
            user_query: The user's question or request
            active_documents: List of uploaded documents (if None, auto-discover from query)
            
        Returns:
            WorkflowType for the most appropriate workflow
        """
        query_lower = user_query.lower()
        
        # 🧠 SMART DOCUMENT SCOPING: Auto-discover if not explicitly provided
        if not active_documents:
            active_docs = self._auto_discover_documents_from_query(user_query)
        else:
            active_docs = active_documents
        
        # 🤖 PRIORITY 0: System self-awareness queries (takes precedence over all others)
        if any(pattern in query_lower for pattern in ["what documents", "what tools", "what workflows", "what capabilities", "what can you", "what do you have access"]):
            print(f"🤖 Self-awareness query detected → SYSTEM_AWARENESS")
            return WorkflowType.SYSTEM_AWARENESS
        
        # 🎯 DETERMINISTIC FILE-TYPE + COUNT CLASSIFICATION
        if active_docs:
            
            # 📊 PRIORITY 1: Multiple documents (any type) → MULTI_DOC_COMPARISON
            if len(active_docs) > 1:
                return WorkflowType.MULTI_DOC_COMPARISON
            
            # 📊 PRIORITY 2: Single document → Route by file type
            single_doc = active_docs[0].lower()
            
            # CSV/Excel files → Always DATA_ANALYSIS (multi-sheet Excel handled within data analysis)
            if any(single_doc.endswith(ext) for ext in ['.csv', '.xlsx', '.xls']):
                chunk_count = self._get_document_chunk_count(active_docs[0]) if single_doc.endswith(('.xlsx', '.xls')) else 1
                print(f"📊 Excel/CSV file {active_docs[0]} has {chunk_count} chunks → DATA_ANALYSIS")
                return WorkflowType.DATA_ANALYSIS
            
            # PDF/DOCX/TXT files → DOCUMENT_ANALYSIS  
            if any(single_doc.endswith(ext) for ext in ['.pdf', '.docx', '.txt', '.doc']):
                return WorkflowType.DOCUMENT_ANALYSIS
            
            # Unknown file type → Default to DOCUMENT_ANALYSIS
            return WorkflowType.DOCUMENT_ANALYSIS
        
        # 🔍 INTELLIGENT DOCUMENT DISCOVERY: Auto-discover relevant documents based on query content
        if not active_docs:
            discovered_docs = self._discover_relevant_documents(user_query)
            if discovered_docs:
                print(f"🔍 Auto-discovered {len(discovered_docs)} relevant documents: {[doc.split('_')[-1] for doc in discovered_docs[:3]]}")
                # Re-classify with discovered documents
                return self.classify_query_workflow(user_query, discovered_docs)
        
        # 🧠 NO DOCUMENTS: Check for explicit memory search patterns
        if any(pattern in query_lower for pattern in ["remember", "memory", "mentioned", "said before", "recall", "previous", "discussed", "discuss", "mention", "what did we"]):
            return WorkflowType.MEMORY_SEARCH
        
        # 📊 NO DOCUMENTS: Check for data analysis keywords (for general data questions)
        if any(pattern in query_lower for pattern in ["table", "csv", "data analysis", "calculate", "chart", "graph", "statistics"]):
            return WorkflowType.DATA_ANALYSIS
        
        # ❓ DEFAULT: Q&A Fallback Chain (no documents, no special patterns)
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
        if workflow_type == WorkflowType.MULTI_DOC_COMPARISON:
            template = self.prompt_templates["multi_doc_comparison"]
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
    
    def _get_document_chunk_count(self, doc_name: str) -> int:
        """Get the number of chunks for a document from the document store."""
        try:
            from tools.document_tools import document_chunk_store
            if doc_name in document_chunk_store:
                return len(document_chunk_store[doc_name])
            return 0
        except Exception as e:
            print(f"Error getting chunk count for {doc_name}: {e}")
            return 0


# Global instance for the agent identity
agent_identity = FinanceRiskAgentIdentity()