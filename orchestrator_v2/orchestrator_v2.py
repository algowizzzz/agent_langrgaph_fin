"""
Orchestrator 2.0 - Next Generation Document Intelligence Engine

This is the main orchestrator class that integrates all the enhanced components:
- Tool introspection and dynamic registration
- DAG-based execution with parallel processing
- Enhanced state management with context tracking
- Step-wise planning with validation and fallback
- Real-time feedback and confidence scoring
- Execution traceability and monitoring
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator, Callable
from dataclasses import dataclass
import json

from .agent_identity import WorkflowType

from langchain_anthropic import ChatAnthropic

from .tool_registry import ToolRegistry, ToolReliability, register_tool
from .execution_engine import ExecutionEngine, ExecutionStatus
from .state_management import StateManager, StateScope, ExecutionContext
from .planning_engine_enhanced import EnhancedPlanningEngine
from .planning_engine import PlanningContext, PlanningStrategy, QueryType

# Import existing tools to register them
from tools.document_tools import (
    upload_document, discover_document_structure, 
    search_uploaded_docs, search_multiple_docs,
    get_all_documents, remove_document
)
from tools.synthesis_tools import synthesize_content
from tools.search_tools import search_knowledge_base, search_conversation_history
from tools.code_execution_tools import execute_python_code, process_table_data, calculate_statistics
from tools.visualization_tools import create_chart, create_wordcloud, create_statistical_plot, create_comparison_chart
from tools.text_analytics_tools import analyze_text_metrics, extract_key_phrases, analyze_sentiment, extract_entities
from tools.system_tools import get_agent_capabilities, get_available_documents, get_workflow_information

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for Orchestrator 2.0"""
    max_parallel_steps: int = 3
    max_retries: int = 3
    default_timeout: float = 300.0  # 5 minutes
    enable_streaming: bool = True
    enable_persistence: bool = True
    persistence_dir: str = "./orchestrator_state"
    confidence_threshold: float = 0.7
    planning_strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE


class OrchestratorV2:
    """
    Next-generation orchestrator with enhanced capabilities:
    - 🔧 Step-wise planning with validation
    - 🚀 DAG-based parallel execution  
    - 🧠 Enhanced state management
    - 📊 Real-time feedback and confidence scoring
    - 🔍 Execution traceability
    - 🛡️ Preventive error handling
    """
    
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()
        
        # Initialize core components
        from .tool_registry import global_tool_registry
        self.tool_registry = global_tool_registry
        self.state_manager = StateManager(
            persistence_dir=self.config.persistence_dir if self.config.enable_persistence else None
        )
        
        # Initialize LLM
        try:
            self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
            logger.info(f"Orchestrator 2.0 LLM initialized: {self.llm.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
        
        # Initialize engines
        self.planning_engine = EnhancedPlanningEngine(self.tool_registry, self.state_manager, self.llm)
        self.execution_engine = ExecutionEngine(self.tool_registry, self.config.max_parallel_steps)
        
        # Rate limiting
        self.api_semaphore = asyncio.Semaphore(2)
        
        # Register all available tools
        self._register_all_tools()
        
        logger.info("Orchestrator 2.0 initialized successfully")
    
    def _register_all_tools(self):
        """Register all available tools with metadata."""
        
        # Document tools
        self.tool_registry.register_function(
            name="upload_document",
            func=upload_document,
            description="Process and store a document for analysis",
            category="document",
            reliability=ToolReliability.HIGH,
            estimated_duration=2.0
        )
        
        self.tool_registry.register_function(
            name="discover_document_structure",
            func=discover_document_structure,
            description="Analyze document structure and extract metadata",
            category="document",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.0
        )
        
        self.tool_registry.register_function(
            name="search_uploaded_docs",
            func=search_uploaded_docs,
            description="Search within uploaded documents with filtering options",
            category="search",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.5,
            retrieve_full_doc_description="Set to True to retrieve the entire document content."
        )
        
        self.tool_registry.register_function(
            name="search_multiple_docs",
            func=search_multiple_docs,
            description="Search across multiple documents simultaneously",
            category="search",
            reliability=ToolReliability.HIGH,
            estimated_duration=2.0
        )
        
        self.tool_registry.register_function(
            name="get_all_documents",
            func=get_all_documents,
            description="Get list of all uploaded documents across sessions",
            category="document",
            reliability=ToolReliability.HIGH,
            estimated_duration=0.5
        )
        
        self.tool_registry.register_function(
            name="remove_document",
            func=remove_document,
            description="Remove a specific document from storage",
            category="document",
            reliability=ToolReliability.HIGH,
            estimated_duration=0.5
        )
        
        # Synthesis tools
        self.tool_registry.register_function(
            name="synthesize_content",
            func=synthesize_content,
            description="Generate cohesive synthesis from multiple content chunks",
            category="synthesis",
            reliability=ToolReliability.HIGH,
            estimated_duration=3.0
        )
        
        # Search tools
        self.tool_registry.register_function(
            name="search_knowledge_base",
            func=search_knowledge_base,
            description="Search the general knowledge base",
            category="search",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=1.0
        )
        
        self.tool_registry.register_function(
            name="search_conversation_history",
            func=search_conversation_history,
            description="Search previous conversation history",
            category="search",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=0.5
        )
        
        # Code execution tools
        self.tool_registry.register_function(
            name="execute_python_code",
            func=execute_python_code,
            description="Execute Python code for data analysis and calculations",
            category="computation",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=2.0
        )
        
        self.tool_registry.register_function(
            name="process_table_data",
            func=process_table_data,
            description="Process and analyze tabular data",
            category="computation",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.5
        )
        
        self.tool_registry.register_function(
            name="calculate_statistics",
            func=calculate_statistics,
            description="Calculate statistical metrics for numerical data",
            category="computation",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.0
        )
        
        # Visualization tools
        self.tool_registry.register_function(
            name="create_chart",
            func=create_chart,
            description="Create various types of charts and graphs",
            category="visualization",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=2.0
        )
        
        self.tool_registry.register_function(
            name="create_wordcloud",
            func=create_wordcloud,
            description="Generate word cloud visualizations",
            category="visualization",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=1.5
        )
        
        self.tool_registry.register_function(
            name="create_statistical_plot",
            func=create_statistical_plot,
            description="Create statistical plots for data analysis",
            category="visualization",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=2.0
        )
        
        self.tool_registry.register_function(
            name="create_comparison_chart",
            func=create_comparison_chart,
            description="Create comparison charts with multiple datasets",
            category="visualization",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=2.5
        )
        
        # Text analytics tools
        self.tool_registry.register_function(
            name="analyze_text_metrics",
            func=analyze_text_metrics,
            description="Analyze comprehensive text metrics and readability",
            category="analysis",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.0
        )
        
        self.tool_registry.register_function(
            name="extract_key_phrases",
            func=extract_key_phrases,
            description="Extract key phrases and important terms",
            category="analysis",
            reliability=ToolReliability.HIGH,
            estimated_duration=1.5
        )
        
        self.tool_registry.register_function(
            name="analyze_sentiment",
            func=analyze_sentiment,
            description="Perform sentiment analysis on text content",
            category="analysis",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=1.0
        )
        
        self.tool_registry.register_function(
            name="extract_entities",
            func=extract_entities,
            description="Extract named entities from text",
            category="analysis",
            reliability=ToolReliability.MEDIUM,
            estimated_duration=1.0
        )
        
        logger.info(f"Registered {len(self.tool_registry._tools)} tools across {len(self.tool_registry._categories)} categories")
    
    async def execute_query(self, 
                           user_query: str,
                           session_id: str,
                           active_documents: List[str] = None,
                           memory_context: Dict[str, Any] = None,
                           planning_strategy: PlanningStrategy = None) -> Dict[str, Any]:
        """
        Execute a user query with the enhanced orchestrator.
        
        Returns:
            Dict containing:
            - status: "success" or "error"  
            - final_answer: The synthesized response
            - confidence_score: Overall confidence (0-1)
            - execution_summary: Detailed execution metrics
            - traceability_log: Step-by-step execution trace
        """
        
        execution_id = str(uuid.uuid4())
        strategy = planning_strategy or self.config.planning_strategy
        
        logger.info(f"🚀 Orchestrator 2.0 executing query: {user_query[:100]}...")
        logger.info(f"📋 Execution ID: {execution_id}, Strategy: {strategy.value}")
        
        try:
            # Create execution context
            context = self.state_manager.create_execution_context(
                execution_id=execution_id,
                session_id=session_id,
                user_query=user_query,
                active_documents=active_documents or []
            )
            
            # Create planning context
            planning_context = PlanningContext(
                user_query=user_query,
                session_id=session_id,
                active_documents=active_documents or [],
                conversation_history=memory_context.get('conversation_history', []) if memory_context else [],
                available_tools=set(self.tool_registry._tools.keys())
            )
            
            # Generate execution plan
            logger.info("🤔 Generating execution plan...")
            execution_plan = await self.planning_engine.create_execution_plan(planning_context, strategy)
            
            logger.info(f"📋 Created plan with {len(execution_plan.steps)} steps")
            
            # Execute the plan
            logger.info("⚡ Starting plan execution...")
            execution_results = await self.execution_engine.execute_plan(
                plan=execution_plan,
                context={
                    "session_id": session_id,
                    "active_documents": active_documents or [],
                    "user_query": user_query
                }
            )
            
            # Generate final response - skip final synthesis for system_awareness to preserve detailed tool listings  
            # Check if this is a system awareness query based on patterns (same logic as agent_identity)
            query_lower = user_query.lower()
            is_system_awareness = any(pattern in query_lower for pattern in ["what documents", "what tools", "what workflows", "what capabilities", "what can you", "what do you have access"])
            
            logger.info(f"🔧 BYPASS DEBUG: user_query={user_query}, is_system_awareness={is_system_awareness}")
            
            if is_system_awareness:
                logger.info("🚀 BYPASSING final synthesis for system_awareness - using direct extraction")
                final_answer = self._extract_system_awareness_response(execution_results)
                confidence_score = self._calculate_overall_confidence(execution_results)
            else:
                logger.info(f"🔄 Using normal final synthesis for non-system-awareness query")
                final_answer = await self._synthesize_final_response(
                    user_query=user_query,
                    execution_results=execution_results,
                    context=context
                )
                # Calculate overall confidence
                confidence_score = self._calculate_overall_confidence(execution_results)
            
            # Get execution summary
            execution_summary = self.execution_engine.get_execution_summary()
            
            # Get traceability log
            traceability_log = context.traceability_log
            
            # Clean up execution state
            self.state_manager.cleanup_execution(execution_id)
            
            logger.info(f"✅ Execution completed with {confidence_score:.2f} confidence")
            
            return {
                "status": "success",
                "final_answer": final_answer,
                "confidence_score": confidence_score,
                "execution_summary": execution_summary,
                "traceability_log": traceability_log,
                "query_type": planning_context.get_query_type().value,
                "execution_id": execution_id
            }
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")
            
            # Clean up on error
            self.state_manager.cleanup_execution(execution_id)
            
            return {
                "status": "error",
                "final_answer": f"I encountered an error while processing your query: {str(e)}",
                "confidence_score": 0.0,
                "execution_summary": {"error": str(e)},
                "traceability_log": [],
                "execution_id": execution_id
            }
    
    async def execute_query_streaming(self, 
                                    user_query: str,
                                    session_id: str,
                                    active_documents: List[str] = None,
                                    memory_context: Dict[str, Any] = None,
                                    planning_strategy: PlanningStrategy = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute a query with real-time streaming feedback.
        
        Yields:
            Dict containing:
            - type: "reasoning_step", "tool_execution", "progress", "final_answer", "error"
            - step: Current step identifier
            - message: Human-readable progress message
            - confidence: Current confidence score
            - timestamp: Execution timestamp
            - metadata: Additional context information
        """
        
        if not self.config.enable_streaming:
            # Fall back to non-streaming execution
            result = await self.execute_query(user_query, session_id, active_documents, memory_context, planning_strategy)
            yield {
                "type": "final_answer",
                "content": result,
                "timestamp": time.time()
            }
            return
        
        execution_id = str(uuid.uuid4())
        strategy = planning_strategy or self.config.planning_strategy
        
        yield {
            "type": "reasoning_step",
            "step": "initialization",
            "message": f"🚀 Orchestrator 2.0 analyzing your query...",
            "confidence": 0.0,
            "timestamp": time.time(),
            "metadata": {"execution_id": execution_id, "strategy": strategy.value}
        }
        
        try:
            # Create contexts
            context = self.state_manager.create_execution_context(
                execution_id=execution_id,
                session_id=session_id,
                user_query=user_query,
                active_documents=active_documents or []
            )
            
            planning_context = PlanningContext(
                user_query=user_query,
                session_id=session_id,
                active_documents=active_documents or [],
                conversation_history=memory_context.get('conversation_history', []) if memory_context else [],
                available_tools=set(self.tool_registry._tools.keys())
            )
            
            # Query analysis
            query_type = planning_context.get_query_type()
            yield {
                "type": "reasoning_step",
                "step": "analysis",
                "message": f"🎯 Detected query type: {query_type.value}",
                "confidence": 0.2,
                "timestamp": time.time(),
                "metadata": {"query_type": query_type.value}
            }
            
            # Planning phase
            yield {
                "type": "reasoning_step",
                "step": "planning",
                "message": f"📋 Creating execution plan using {strategy.value} strategy...",
                "confidence": 0.3,
                "timestamp": time.time()
            }
            
            execution_plan = await self.planning_engine.create_execution_plan(planning_context, strategy)
            
            yield {
                "type": "reasoning_step",
                "step": "plan_ready",
                "message": f"✅ Plan created with {len(execution_plan.steps)} steps",
                "confidence": 0.4,
                "timestamp": time.time(),
                "metadata": {"step_count": len(execution_plan.steps)}
            }
            
            # Execute with streaming progress using asyncio.Queue
            progress_queue = asyncio.Queue()
            
            async def progress_callback(result):
                """Non-generator progress callback that puts events into queue"""
                confidence = result.confidence_score
                
                if result.status == ExecutionStatus.COMPLETED:
                    event = {
                        "type": "tool_execution",
                        "step": result.step_id,
                        "message": f"✅ {result.step_id} completed",
                        "confidence": confidence,
                        "timestamp": time.time(),
                        "metadata": {
                            "tool_name": result.metadata.get("tool_name", "unknown"),
                            "execution_time": result.execution_time
                        }
                    }
                else:
                    event = {
                        "type": "tool_execution", 
                        "step": result.step_id,
                        "message": f"❌ {result.step_id} failed: {result.error}",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "metadata": {"error": result.error}
                    }
                
                await progress_queue.put(event)
            
            yield {
                "type": "reasoning_step",
                "step": "execution",
                "message": "⚡ Starting plan execution...",
                "confidence": 0.5,
                "timestamp": time.time()
            }
            
            # Start execution as a background task
            execution_task = asyncio.create_task(
                self.execution_engine.execute_plan(
                    plan=execution_plan,
                    context={
                        "session_id": session_id,
                        "active_documents": active_documents or [],
                        "user_query": user_query
                    },
                    progress_callback=progress_callback
                )
            )
            
            # Process events from queue while execution runs
            execution_results = None
            while not execution_task.done():
                try:
                    # Wait for either an event or execution completion
                    event = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                    yield event
                    progress_queue.task_done()
                except asyncio.TimeoutError:
                    # No event available, continue checking if execution is done
                    continue
            
            # Get the final execution results
            execution_results = await execution_task
            
            # Process any remaining events in queue
            while not progress_queue.empty():
                try:
                    event = progress_queue.get_nowait()
                    yield event
                    progress_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Synthesis phase
            yield {
                "type": "reasoning_step",
                "step": "synthesis",
                "message": "🧠 Synthesizing final response...",
                "confidence": 0.8,
                "timestamp": time.time()
            }
            
            # For system_awareness queries, skip final synthesis to preserve detailed tool listings
            if query_type.value == "system_awareness":
                # Extract the synthesis result directly without re-processing
                final_answer = self._extract_system_awareness_response(execution_results)
                final_confidence = self._calculate_overall_confidence(execution_results)
            else:
                final_answer = await self._synthesize_final_response(user_query, execution_results, context)
                final_confidence = self._calculate_overall_confidence(execution_results)
            
            # Final result
            yield {
                "type": "final_answer",
                "content": {
                    "status": "success",
                    "final_answer": final_answer,
                    "confidence_score": final_confidence,
                    "execution_summary": self.execution_engine.get_execution_summary(),
                    "traceability_log": context.traceability_log,
                    "query_type": query_type.value,
                    "execution_id": execution_id
                },
                "confidence": final_confidence,
                "timestamp": time.time()
            }
            
            # Cleanup
            self.state_manager.cleanup_execution(execution_id)
            
        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            
            yield {
                "type": "error",
                "message": f"❌ Execution failed: {str(e)}",
                "confidence": 0.0,
                "timestamp": time.time(),
                "metadata": {"error": str(e), "execution_id": execution_id}
            }
            
            self.state_manager.cleanup_execution(execution_id)
    
    async def _synthesize_final_response(self, 
                                       user_query: str,
                                       execution_results: Dict[str, Any],
                                       context: ExecutionContext) -> str:
        """Synthesize the final response from execution results."""
        
        # Collect successful outputs
        successful_outputs = []
        for step_id, result in execution_results.items():
            if result.status == ExecutionStatus.COMPLETED:
                successful_outputs.append({
                    "step_id": step_id,
                    "output": result.output,
                    "confidence": result.confidence_score,
                    "tool_name": result.metadata.get("tool_name", "unknown")
                })
        
        if not successful_outputs:
            return "I was unable to process your query successfully. Please try rephrasing or check the available documents."
        
        # Always synthesize responses for better user experience
        # Even single outputs should be processed for readability
        if len(successful_outputs) == 1:
            output = successful_outputs[0]["output"]
            tool_name = successful_outputs[0]["tool_name"]
            
            # If it's already a synthesized response (string), return it
            if isinstance(output, str) and len(output) > 50 and not output.startswith('[{'):
                return output
            # If it's a synthesis result dict, extract the result
            elif isinstance(output, dict) and "result" in output:
                return str(output["result"])
            # If it's raw document chunks or other structured data, synthesize it
            else:
                # Create synthesis prompt for single output
                try:
                    synthesis_prompt = f"""
User Query: "{user_query}"

I have gathered the following information using {tool_name}:

{str(output)[:2000]}

Please create a comprehensive, well-structured response that directly answers the user's query using this information.

Requirements:
- Start with a direct answer to their question
- Include the most relevant details from the information
- Be concise but thorough  
- Use a professional, helpful tone
- Structure the response logically
- If the information contains raw document chunks, synthesize them into readable prose

Final Response:"""
                    
                    async with self.api_semaphore:
                        response = await self.llm.ainvoke(synthesis_prompt)
                        return response.content if hasattr(response, 'content') else str(response)
                        
                except Exception as e:
                    logger.error(f"Failed to synthesize single output: {e}")
                    # Fallback to raw output as string
                    return str(output)
        
        # For multiple outputs, synthesize intelligently
        try:
            synthesis_prompt = f"""
User Query: "{user_query}"

I have gathered the following information using multiple analysis tools:

"""
            
            for i, output_data in enumerate(successful_outputs, 1):
                tool_name = output_data["tool_name"]
                output = output_data["output"]
                confidence = output_data["confidence"]
                
                synthesis_prompt += f"## Analysis {i} ({tool_name}, confidence: {confidence:.2f}):\n"
                synthesis_prompt += f"{str(output)[:1000]}...\n\n"
            
            synthesis_prompt += """
Please create a comprehensive, well-structured response that directly answers the user's query by intelligently combining the above information.

Requirements:
- Start with a direct answer to their question
- Include the most relevant details from the analysis
- Be concise but thorough
- Use a professional, helpful tone
- Structure the response logically

Final Response:"""
            
            async with self.api_semaphore:
                response = await self.llm.ainvoke(synthesis_prompt)
                return response.content if hasattr(response, 'content') else str(response)
                
        except Exception as e:
            logger.error(f"Failed to synthesize final response: {e}")
            
            # Fallback to the best single output
            best_output = max(successful_outputs, key=lambda x: x["confidence"])
            output = best_output["output"]
            
            if isinstance(output, str):
                return output
            else:
                return str(output)
    
    def _extract_system_awareness_response(self, execution_results: Dict[str, Any]) -> str:
        """Extract system awareness response directly without re-synthesis to preserve detailed tool listings."""
        
        logger.info(f"🔍 EXTRACTION DEBUG: execution_results keys: {list(execution_results.keys()) if execution_results else 'None'}")
        
        if not execution_results:
            return "No system information available."
        
        # Debug: log the structure of execution results
        for key, value in execution_results.items():
            logger.info(f"🔍 EXTRACTION DEBUG: {key} -> {type(value)} -> {str(value)[:200]}...")
        
        # Look for the synthesize_system_info step result
        if "synthesize_system_info" in execution_results:
            synthesis_result = execution_results["synthesize_system_info"]
            logger.info(f"🔍 EXTRACTION DEBUG: Found synthesize_system_info -> {type(synthesis_result)}")
            
            # Handle ExecutionResult objects
            if hasattr(synthesis_result, 'output'):
                output_data = synthesis_result.output
                logger.info(f"🔍 EXTRACTION DEBUG: Got output -> {type(output_data)} -> {str(output_data)[:200]}...")
                if isinstance(output_data, dict) and "result" in output_data:
                    result_content = output_data["result"]
                    logger.info(f"🔍 EXTRACTION DEBUG: Extracted result content length: {len(result_content)}")
                    return result_content
            # Handle direct dict (fallback)
            elif isinstance(synthesis_result, dict) and "result" in synthesis_result:
                result_content = synthesis_result["result"]
                logger.info(f"🔍 EXTRACTION DEBUG: Extracted result content length: {len(result_content)}")
                return result_content
        
        # Fallback: look for any synthesis-related results
        for step_name, result in execution_results.items():
            if "synthesis" in step_name.lower() or "system" in step_name.lower():
                logger.info(f"🔍 EXTRACTION DEBUG: Checking fallback {step_name} -> {type(result)}")
                # Handle ExecutionResult objects
                if hasattr(result, 'output'):
                    output_data = result.output
                    if isinstance(output_data, dict) and "result" in output_data:
                        return output_data["result"]
                    elif isinstance(output_data, str):
                        return output_data
                # Handle direct data
                elif isinstance(result, dict) and "result" in result:
                    return result["result"]
                elif isinstance(result, str):
                    return result
        
        # Final fallback
        logger.warning("🔍 EXTRACTION DEBUG: Could not find synthesis result in execution_results")
        return "System information is available but could not be properly extracted."
    
    def _calculate_overall_confidence(self, execution_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score from execution results."""
        
        if not execution_results:
            return 0.0
        
        successful_results = [
            result for result in execution_results.values() 
            if result.status == ExecutionStatus.COMPLETED
        ]
        
        if not successful_results:
            return 0.0
        
        # Calculate weighted average confidence
        total_confidence = sum(result.confidence_score for result in successful_results)
        average_confidence = total_confidence / len(successful_results)
        
        # Apply success rate penalty
        success_rate = len(successful_results) / len(execution_results)
        final_confidence = average_confidence * success_rate
        
        return min(1.0, max(0.0, final_confidence))
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status and metrics."""
        
        return {
            "orchestrator_version": "2.0",
            "status": "active",
            "configuration": {
                "max_parallel_steps": self.config.max_parallel_steps,
                "planning_strategy": self.config.planning_strategy.value,
                "streaming_enabled": self.config.enable_streaming,
                "persistence_enabled": self.config.enable_persistence
            },
            "tool_registry": self.tool_registry.get_registry_stats(),
            "state_management": self.state_manager.get_state_summary(),
            "llm_status": "connected" if self.llm else "disconnected"
        }
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up all session-related state."""
        self.state_manager.cleanup_session(session_id)
        logger.info(f"Cleaned up session: {session_id}")
    
    def get_execution_trace(self, execution_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get detailed execution trace for debugging."""
        return self.state_manager.get_execution_trace(execution_id)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get AI Finance and Risk Agent identity and capabilities information.
        
        Returns:
            Dict containing agent name, version, specialization, and capabilities
        """
        return self.planning_engine.get_agent_info()
    
    def get_workflow_capabilities(self) -> List[str]:
        """
        Get list of available workflow capabilities.
        
        Returns:
            List of workflow capability names
        """
        return self.planning_engine.get_workflow_capabilities()
    
    def describe_agent(self) -> str:
        """
        Get a human-readable description of the agent's capabilities.
        
        Returns:
            Formatted string describing the agent
        """
        info = self.get_agent_info()
        capabilities = ", ".join(info.get("core_capabilities", []))
        
        return f"""
🤖 {info.get('name', 'AI Agent')} v{info.get('version', '1.0')}

🎯 Specialization: {info.get('specialization', 'General AI Assistant')}

🔧 Core Capabilities:
{capabilities}

💾 Memory Sources: {', '.join(info.get('memory_sources', []))}

🔄 Workflow Types: {', '.join(info.get('workflow_types', []))}
"""