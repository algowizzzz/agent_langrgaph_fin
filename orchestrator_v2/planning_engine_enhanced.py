"""
Enhanced Planning Engine with AI Finance and Risk Agent Integration

This module extends the planning engine with intelligent query routing,
structured prompts, and comprehensive fallback chain support.
"""

import logging
import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from .planning_engine import PlanningEngine, PlanningContext, PlanningStrategy, QueryType
from .execution_engine import ExecutionStep, ExecutionPlan, ConditionType
from .tool_registry import ToolRegistry
from .state_management import StateManager
from .agent_identity import agent_identity, WorkflowType, MemorySource

logger = logging.getLogger(__name__)


class EnhancedPlanningEngine(PlanningEngine):
    """
    Enhanced planning engine with AI Finance and Risk Agent capabilities.
    
    Features:
    - Intelligent query routing based on workflow classification
    - Structured prompt generation for financial analysis
    - Comprehensive memory fallback chain implementation
    - Context-aware planning with agent identity integration
    """
    
    def __init__(self, tool_registry: ToolRegistry, state_manager: StateManager, llm: Any = None):
        super().__init__(tool_registry, state_manager, llm)
        self.agent_identity = agent_identity
        logger.info(f"Enhanced Planning Engine initialized with {self.agent_identity.agent_name}")
    
    async def create_execution_plan(self, context: PlanningContext, strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE) -> ExecutionPlan:
        """
        Create an execution plan using AI Finance and Risk Agent intelligence.
        
        Enhanced with:
        - Workflow classification
        - Memory source routing
        - Structured prompt generation
        - Agent identity integration
        """
        logger.info(f"🎯 AI Finance and Risk Agent creating plan for: '{context.user_query[:100]}...'")
        
        try:
            # Classify workflow type using agent identity
            workflow_type = self.agent_identity.classify_query_workflow(
                context.user_query, 
                context.active_documents
            )
            logger.info(f"📋 Classified workflow: {workflow_type.value}")
            
            # Determine memory source based on workflow and context
            primary_memory_source = self.agent_identity.get_memory_source_for_query(
                workflow_type, 
                context.active_documents
            )
            logger.info(f"💾 Primary memory source: {primary_memory_source.value}")
            
            # Create workflow-specific execution plan
            plan = await self._create_workflow_specific_plan(context, workflow_type, strategy)
            
            # Validate plan
            if plan and len(plan.steps) > 0:
                logger.info(f"✅ Created {workflow_type.value} plan with {len(plan.steps)} steps")
                return plan
            
            # Fallback to parent planning if enhanced planning fails
            logger.warning("Enhanced planning failed, falling back to standard planning")
            return await super().create_execution_plan(context, strategy)
            
        except Exception as e:
            logger.error(f"Enhanced planning error: {e}")
            return await super().create_execution_plan(context, strategy)
    
    async def _create_workflow_specific_plan(self, context: PlanningContext, workflow_type: WorkflowType, strategy: PlanningStrategy) -> ExecutionPlan:
        """Create execution plan based on specific workflow type."""
        
        if workflow_type == WorkflowType.DOCUMENT_ANALYSIS:
            return await self._create_document_analysis_plan(context)
        
        elif workflow_type == WorkflowType.MULTI_DOC_COMPARISON:
            return await self._create_multi_doc_comparison_plan(context)
        
        elif workflow_type == WorkflowType.QA_FALLBACK_CHAIN:
            return await self._create_qa_fallback_plan(context)
        
        elif workflow_type == WorkflowType.DATA_ANALYSIS:
            return await self._create_data_analysis_plan(context)
        
        
        elif workflow_type == WorkflowType.MEMORY_SEARCH:
            return await self._create_memory_search_plan(context)
        
        elif workflow_type == WorkflowType.SYSTEM_AWARENESS:
            return await self._create_system_awareness_plan(context)
        
        else:
            # Fallback to standard template planning
            return await self._create_template_plan(context, strategy)
    
    async def _create_document_analysis_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for single document analysis workflow."""
        plan_id = f"doc_analysis_{int(time.time())}"
        steps = {}
        
        if not context.active_documents:
            # No documents - route to knowledge base
            return await self._create_qa_fallback_plan(context)
        
        # Generate structured prompt for document analysis
        structured_prompt = self.agent_identity.get_structured_prompt(
            WorkflowType.DOCUMENT_ANALYSIS,
            document=context.active_documents[0],
            analysis_type="comprehensive financial analysis"
        )
        
        # Step 1: Search uploaded document
        doc_name = context.active_documents[0] if context.active_documents else None
        logger.info(f"🔍 DOCUMENT ANALYSIS DEBUG: active_documents={context.active_documents}, doc_name={doc_name}")
        
        step_1 = ExecutionStep(
            step_id="search_document",
            tool_name="search_uploaded_docs",
            parameters={
                "doc_name": doc_name,
                "query": None  # No query filter for comprehensive document analysis
            },
            condition=ConditionType.ALWAYS,
            description="Search uploaded document for comprehensive analysis (no filtering)"
        )
        steps["search_document"] = step_1
        
        # Step 2: Synthesize response with structured prompt  
        step_2 = ExecutionStep(
            step_id="synthesize_analysis",
            tool_name="synthesize_content",
            parameters={
                "documents": "$search_document",
                "query": context.user_query,
                "synthesis_type": "analysis"
            },
            dependencies=["search_document"],
            condition=ConditionType.ON_SUCCESS,
            description="Synthesize document analysis with financial expertise"
        )
        steps["synthesize_analysis"] = step_2
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "workflow_type": WorkflowType.DOCUMENT_ANALYSIS.value,
                "strategy": "document_analysis",
                "documents": context.active_documents,
                "agent_identity": "AI Finance and Risk Agent"
            }
        )
    
    async def _create_multi_doc_comparison_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for multi-document financial comparison workflow."""
        plan_id = f"multi_doc_comparison_{int(time.time())}"
        steps = {}
        
        if len(context.active_documents) < 2:
            # Not enough documents for comparison
            logger.warning("Financial comparison requires 2+ documents, falling back to document analysis")
            return await self._create_document_analysis_plan(context)
        
        # Generate structured prompt for financial comparison
        structured_prompt = self.agent_identity.get_structured_prompt(
            WorkflowType.MULTI_DOC_COMPARISON,
            documents=", ".join(context.active_documents),
            comparison_type="similarities and differences"
        )
        
        # Step 1: Search multiple documents with 10k word context consideration
        # For comparison, we need broader content, so use a general search or no query filter
        step_1 = ExecutionStep(
            step_id="search_multi_docs",
            tool_name="search_multiple_docs",
            parameters={
                "doc_names": context.active_documents,
                "query": None  # No query filter to get more comprehensive content
            },
            condition=ConditionType.ALWAYS,
            description="Search multiple documents for financial comparison analysis"
        )
        steps["search_multi_docs"] = step_1
        
        # Step 2: Apply synthesize_content for financial analysis
        step_2 = ExecutionStep(
            step_id="refine_analysis",
            tool_name="synthesize_content",
            parameters={
                "documents": "$search_multi_docs",
                "query": context.user_query,
                "synthesis_type": "multi_doc_comparison"
            },
            dependencies=["search_multi_docs"],
            condition=ConditionType.ON_SUCCESS,
            description="Apply refine method with financial analyst expertise"
        )
        steps["refine_analysis"] = step_2
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "workflow_type": WorkflowType.MULTI_DOC_COMPARISON.value,
                "strategy": "multi_doc_comparison",
                "documents": context.active_documents,
                "chunk_size": 5000,
                "agent_identity": "AI Finance and Risk Agent"
            }
        )
    
    async def _create_qa_fallback_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for Q&A with comprehensive fallback chain."""
        plan_id = f"qa_fallback_{int(time.time())}"
        steps = {}
        
        # Create simple Q&A fallback with available tools
        step_count = 1
        first_step_added = False
        
        # Step 1: Try knowledge base first
        step_1 = ExecutionStep(
            step_id="knowledge_search",
            tool_name="search_knowledge_base",
            parameters={
                "query": context.user_query
            },
            condition=ConditionType.ALWAYS,
            description="Search knowledge base for financial information"
        )
        steps["knowledge_search"] = step_1
        first_step_added = True
        
        # Step 2: Try conversation history
        step_2 = ExecutionStep(
            step_id="conversation_search",
            tool_name="search_conversation_history",
            parameters={
                "query": context.user_query
            },
            condition=ConditionType.ON_FAILURE,
            description="Search conversation history for context"
        )
        steps["conversation_search"] = step_2
        
        # Step 3: Synthesize final answer
        step_3 = ExecutionStep(
            step_id="synthesize_fallback",
            tool_name="synthesize_content",
            parameters={
                "documents": "$knowledge_search",
                "query": context.user_query,
                "synthesis_type": "qa_response"
            },
            dependencies=["knowledge_search"],
            condition=ConditionType.ON_SUCCESS,
            description="Synthesize response with financial expertise"
        )
        steps["synthesize_fallback"] = step_3
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "workflow_type": WorkflowType.QA_FALLBACK_CHAIN.value,
                "strategy": "qa_fallback_chain",
                "fallback_chain": ["knowledge_base", "conversation_history", "synthesis"],
                "agent_identity": "AI Finance and Risk Agent"
            }
        )
    
    async def _create_data_analysis_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for progressive data analysis workflow."""
        plan_id = f"data_analysis_{int(time.time())}"
        steps = {}
        
        # Generate structured prompt for data analysis
        structured_prompt = self.agent_identity.get_structured_prompt(
            WorkflowType.DATA_ANALYSIS
        )
        
        # Step 1: Search uploaded CSV/table data  
        doc_name = context.active_documents[0] if context.active_documents else "table_data"
        
        # BUGFIX: If no active_documents but user query mentions a specific Excel file, try to extract it
        if not context.active_documents and any(ext in context.user_query.lower() for ext in ['.xlsx', '.csv', 'techtrend', 'financials']):
            # Try to extract document name from query
            from tools.document_tools import document_chunk_store
            try:
                available_docs = list(document_chunk_store.keys())
                for query_word in context.user_query.lower().split():
                    for doc in available_docs:
                        if 'techtrend' in query_word and 'techtrend' in doc.lower():
                            doc_name = doc
                            logger.info(f"🔧 AUTO-DETECTED DOCUMENT: {doc_name} from query: {context.user_query}")
                            break
                        elif query_word.replace('.xlsx', '').replace('.csv', '') in doc.lower():
                            doc_name = doc
                            logger.info(f"🔧 AUTO-DETECTED DOCUMENT: {doc_name} from query: {context.user_query}")
                            break
                    if doc_name != "table_data":
                        break
            except Exception as e:
                logger.warning(f"Failed to auto-detect document: {e}")
        
        logger.info(f"🔍 DATA ANALYSIS DEBUG: active_documents={context.active_documents}, doc_name={doc_name}")
        
        step_1 = ExecutionStep(
            step_id="search_table_data",
            tool_name="search_uploaded_docs",
            parameters={
                "doc_name": doc_name,
                "query": context.user_query
            },
            condition=ConditionType.ALWAYS,
            description="Search uploaded table/CSV data"
        )
        steps["search_table_data"] = step_1
        
        # Step 2: Synthesize table summary
        step_2 = ExecutionStep(
            step_id="table_summary",
            tool_name="synthesize_content",
            parameters={
                "documents": "$search_table_data",
                "query": context.user_query,
                "synthesis_type": "data_summary"
            },
            dependencies=["search_table_data"],
            condition=ConditionType.ON_SUCCESS,
            description="Generate table data summary with financial context"
        )
        steps["table_summary"] = step_2
        
        # Step 3: Python calculations (if requested)
        if any(word in context.user_query.lower() for word in ["calculate", "add", "compute", "total"]):
            step_3 = ExecutionStep(
                step_id="python_calculations",
                tool_name="execute_python_code",
                parameters={
                    "code_request": context.user_query,
                    "data_context": "$table_summary"
                },
                dependencies=["table_summary"],
                condition=ConditionType.ON_SUCCESS,
                description="Execute Python calculations based on user request"
            )
            steps["python_calculations"] = step_3
        
        # Step 4: Visualization (if requested)
        if any(word in context.user_query.lower() for word in ["chart", "graph", "plot", "visualize"]):
            step_4 = ExecutionStep(
                step_id="create_visualization",
                tool_name="create_chart",
                parameters={
                    "chart_request": context.user_query,
                    "data_context": "$table_summary"
                },
                dependencies=["table_summary"],
                condition=ConditionType.ON_SUCCESS,
                description="Create visualization based on user request"
            )
            steps["create_visualization"] = step_4
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "workflow_type": WorkflowType.DATA_ANALYSIS.value,
                "strategy": "data_analysis",
                "progressive_workflow": True,
                "agent_identity": "AI Finance and Risk Agent"
            }
        )
    
    async def _create_productivity_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for productivity assistance with financial expertise."""
        plan_id = f"productivity_{int(time.time())}"
        steps = {}
        
        # Step 1: Analyze productivity request with financial context
        step_1 = ExecutionStep(
            step_id="productivity_analysis",
            tool_name="llm_synthesis",
            parameters={
                "query": context.user_query,
                "expertise": "financial analysis and productivity",
                "context": "productivity assistance with financial specialization"
            },
            condition=ConditionType.ALWAYS,
            description="Provide productivity assistance with financial expertise"
        )
        steps["productivity_analysis"] = step_1
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "agent_identity": "AI Finance and Risk Agent"
            }
        )
    
    async def _create_memory_search_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for memory search workflow - search conversation history and saved memories."""
        plan_id = f"memory_search_{int(time.time())}"
        steps = {}
        
        # Step 1: Search conversation history
        step_1 = ExecutionStep(
            step_id="search_conversation",
            tool_name="search_conversation_history",
            parameters={
                "query": context.user_query
            },
            condition=ConditionType.ALWAYS,
            description="Search through conversation history for relevant memories"
        )
        steps["search_conversation"] = step_1
        
        # Step 2: Search knowledge base for long-term memory
        step_2 = ExecutionStep(
            step_id="search_long_term_memory",
            tool_name="search_knowledge_base",
            parameters={
                "query": context.user_query
            },
            condition=ConditionType.ALWAYS,
            description="Search knowledge base for saved long-term memories"
        )
        steps["search_long_term_memory"] = step_2
        
        # Step 3: Synthesize memory results
        step_3 = ExecutionStep(
            step_id="synthesize_memory_results",
            tool_name="synthesize_content",
            parameters={
                "documents": "$search_conversation",
                "query": context.user_query,
                "synthesis_type": "memory_recall"
            },
            dependencies=["search_conversation", "search_long_term_memory"],
            condition=ConditionType.ON_SUCCESS,
            description="Synthesize conversation history and memory results with financial expertise"
        )
        steps["synthesize_memory_results"] = step_3
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "workflow_type": WorkflowType.MEMORY_SEARCH.value,
                "strategy": "memory_search",
                "agent_identity": "AI Finance and Risk Agent",
                "memory_sources": ["conversation_history", "long_term_memory"]
            }
        )
    
    async def _create_system_awareness_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Create plan for system self-awareness queries."""
        plan_id = f"system_awareness_{int(time.time())}"
        steps = {}
        
        query_lower = context.user_query.lower()
        
        # Determine which system tool to call based on query content
        if any(pattern in query_lower for pattern in ["what documents", "documents do you have", "available documents"]):
            tool_name = "get_available_documents"
            description = "Get information about available documents"
        elif any(pattern in query_lower for pattern in ["what tools", "tools do you have", "what capabilities", "capabilities"]):
            tool_name = "get_agent_capabilities" 
            description = "Get comprehensive agent capabilities information"
        elif any(pattern in query_lower for pattern in ["what workflows", "workflows do you have"]):
            tool_name = "get_workflow_information"
            description = "Get detailed workflow information"
        else:
            # Default to comprehensive capabilities for general self-awareness queries
            tool_name = "get_agent_capabilities"
            description = "Get comprehensive agent capabilities information"
        
        # Step 1: Call the appropriate system awareness tool
        step_1 = ExecutionStep(
            step_id="get_system_info",
            tool_name=tool_name,
            parameters={},
            condition=ConditionType.ALWAYS,
            description=description
        )
        steps["get_system_info"] = step_1
        
        # Step 2: Synthesize the system information into a user-friendly response
        step_2 = ExecutionStep(
            step_id="synthesize_system_info",
            tool_name="synthesize_content", 
            parameters={
                "documents": ["$get_system_info"],  # Wrap in list for synthesize_content
                "query": context.user_query,
                "synthesis_type": "system_awareness"
            },
            dependencies=["get_system_info"],
            condition=ConditionType.ON_SUCCESS,
            description="Format system information into user-friendly response"
        )
        steps["synthesize_system_info"] = step_2
        
        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            metadata={
                "workflow_type": WorkflowType.SYSTEM_AWARENESS.value,
                "strategy": "system_awareness",
                "agent_identity": "AI Finance and Risk Agent",
                "system_tool": tool_name
            }
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent identity information."""
        return self.agent_identity.get_agent_info()
    
    def get_workflow_capabilities(self) -> List[str]:
        """Get list of available workflow capabilities."""
        return self.agent_identity.list_all_capabilities()