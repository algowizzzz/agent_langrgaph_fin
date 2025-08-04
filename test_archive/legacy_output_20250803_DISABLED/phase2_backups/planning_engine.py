"""
Step-wise Planning Engine for Orchestrator 2.0

This module provides intelligent planning capabilities with validation,
fallback mechanisms, and adaptive replanning based on execution feedback.
"""

import logging
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, Callable
from enum import Enum
import re

from .tool_registry import ToolRegistry, ToolReliability
from .execution_engine import ExecutionStep, ExecutionPlan, ConditionType
from .state_management import StateManager, StateScope

logger = logging.getLogger(__name__)


class PlanningStrategy(Enum):
    """Different planning strategies based on query complexity."""
    SIMPLE = "simple"           # Linear execution
    PARALLEL = "parallel"       # Parallel execution where possible
    ADAPTIVE = "adaptive"       # Dynamic replanning based on results
    COMPREHENSIVE = "comprehensive"  # Full analysis with multiple approaches


class QueryType(Enum):
    """Types of user queries for planning optimization."""
    SEARCH = "search"
    SUMMARY = "summary"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    EXTRACTION = "extraction"
    VISUALIZATION = "visualization"
    CALCULATION = "calculation"
    UNKNOWN = "unknown"


@dataclass
class PlanningContext:
    """Context information for planning."""
    user_query: str
    session_id: str
    active_documents: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    available_tools: Set[str] = field(default_factory=set)
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def get_query_type(self) -> QueryType:
        """Classify the user query type."""
        query_lower = self.user_query.lower()
        
        # Search patterns
        if any(word in query_lower for word in ['find', 'search', 'look for', 'locate', 'where']):
            return QueryType.SEARCH
        
        # Summary patterns
        if any(word in query_lower for word in ['summarize', 'summary', 'overview', 'brief']):
            return QueryType.SUMMARY
        
        # Analysis patterns
        if any(word in query_lower for word in ['analyze', 'analysis', 'examine', 'metrics', 'statistics']):
            return QueryType.ANALYSIS
        
        # Comparison patterns
        if any(word in query_lower for word in ['compare', 'comparison', 'difference', 'versus', 'vs']):
            return QueryType.COMPARISON
        
        # Extraction patterns
        if any(word in query_lower for word in ['extract', 'get', 'list', 'count', 'frequency']):
            return QueryType.EXTRACTION
        
        # Visualization patterns
        if any(word in query_lower for word in ['chart', 'graph', 'plot', 'visualize', 'show']):
            return QueryType.VISUALIZATION
        
        # Calculation patterns
        if any(word in query_lower for word in ['calculate', 'compute', 'total', 'average', 'sum']):
            return QueryType.CALCULATION
        
        return QueryType.UNKNOWN


@dataclass
class PlanValidationResult:
    """Result of plan validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence_score: float = 1.0


class PlanningEngine:
    """Intelligent planning engine with step-wise validation and adaptive replanning."""
    
    def __init__(self, tool_registry: ToolRegistry, state_manager: StateManager, llm_client):
        self.tool_registry = tool_registry
        self.state_manager = state_manager
        self.llm_client = llm_client
        
        # Planning templates for different query types
        self.planning_templates = self._load_planning_templates()
        
        # Pattern-based tool suggestions
        self.tool_patterns = self._load_tool_patterns()
        
    def create_execution_plan(self, 
                            context: PlanningContext,
                            strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE) -> ExecutionPlan:
        """Create an optimized execution plan based on context and strategy."""
        
        logger.info(f"Creating execution plan for query: {context.user_query[:100]}...")
        
        # Step 1: Analyze query and determine approach
        query_type = context.get_query_type()
        logger.info(f"Detected query type: {query_type.value}")
        
        # Step 2: Generate initial plan using templates and LLM
        initial_plan = self._generate_initial_plan(context, query_type, strategy)
        
        # Step 3: Validate and optimize the plan
        validation_result = self._validate_plan(initial_plan, context)
        
        if not validation_result.is_valid:
            logger.warning(f"Initial plan validation failed: {validation_result.errors}")
            # Try to fix the plan
            initial_plan = self._fix_plan_issues(initial_plan, validation_result, context)
        
        # Step 4: Add fallback strategies
        enhanced_plan = self._add_fallback_strategies(initial_plan, context)
        
        # Step 5: Optimize for parallel execution if possible
        if strategy in [PlanningStrategy.PARALLEL, PlanningStrategy.ADAPTIVE]:
            enhanced_plan = self._optimize_for_parallelism(enhanced_plan)
        
        logger.info(f"Created execution plan with {len(enhanced_plan.steps)} steps")
        return enhanced_plan
    
    def replan(self, 
               original_plan: ExecutionPlan,
               failed_steps: List[str],
               context: PlanningContext,
               execution_results: Dict[str, Any]) -> ExecutionPlan:
        """Create a new plan when the original plan fails or needs adjustment."""
        
        logger.info(f"Replanning due to failed steps: {failed_steps}")
        
        # Analyze what went wrong
        failure_analysis = self._analyze_failures(failed_steps, execution_results, original_plan)
        
        # Generate alternative approach
        new_plan = self._generate_alternative_plan(context, failure_analysis, execution_results)
        
        # Validate the new plan
        validation_result = self._validate_plan(new_plan, context)
        
        if not validation_result.is_valid:
            logger.error(f"Replanning failed validation: {validation_result.errors}")
            # Fall back to conservative approach
            new_plan = self._generate_conservative_plan(context)
        
        return new_plan
    
    def _generate_initial_plan(self, 
                              context: PlanningContext,
                              query_type: QueryType,
                              strategy: PlanningStrategy) -> ExecutionPlan:
        """Generate initial execution plan using templates and LLM reasoning."""
        
        # Try template-based planning first
        template_plan = self._apply_planning_template(context, query_type)
        
        if template_plan and len(template_plan.steps) > 0:
            logger.info("Used template-based planning")
            return template_plan
        
        # Fall back to LLM-based planning
        logger.info("Using LLM-based planning")
        return self._generate_llm_plan(context, strategy)
    
    def _apply_planning_template(self, 
                               context: PlanningContext,
                               query_type: QueryType) -> Optional[ExecutionPlan]:
        """Apply pre-defined planning templates for common query patterns."""
        
        template = self.planning_templates.get(query_type)
        if not template:
            return None
        
        steps = {}
        step_counter = 1
        
        for template_step in template["steps"]:
            step_id = f"step_{step_counter}"
            
            # Resolve template parameters
            parameters = self._resolve_template_parameters(
                template_step["parameters"], 
                context
            )
            
            # Create execution step
            step = ExecutionStep(
                step_id=step_id,
                tool_name=template_step["tool"],
                parameters=parameters,
                dependencies=template_step.get("dependencies", []),
                description=template_step.get("description", "")
            )
            
            steps[step_id] = step
            step_counter += 1
        
        return ExecutionPlan(
            steps=steps,
            plan_id=f"template_{query_type.value}_{int(time.time())}",
            description=f"Template-based plan for {query_type.value} query"
        )
    
    def _generate_llm_plan(self, 
                          context: PlanningContext,
                          strategy: PlanningStrategy) -> ExecutionPlan:
        """Generate execution plan using LLM reasoning."""
        
        # Build prompt for LLM
        available_tools = self.tool_registry.export_tool_definitions()
        
        prompt = f"""
Create an execution plan for the following query:

User Query: "{context.user_query}"
Active Documents: {context.active_documents}
Available Tools: {list(available_tools.keys())}

Planning Strategy: {strategy.value}

Tool Definitions:
{json.dumps(available_tools, indent=2)}

Create a JSON execution plan with the following structure:
{{
  "plan_id": "unique_plan_id",
  "description": "Brief description of the plan",
  "steps": [
    {{
      "step_id": "step_1",
      "tool_name": "tool_name",
      "parameters": {{"param": "value"}},
      "dependencies": [],
      "description": "What this step does",
      "condition": "always"
    }}
  ]
}}

Guidelines:
1. Use appropriate tools based on the query type
2. Consider dependencies between steps
3. Include error handling and fallbacks where needed
4. Optimize for the specified strategy
5. Use parameter references like "$step_1.output" for chaining

Plan:"""
        
        try:
            response = self.llm_client.invoke(prompt)
            plan_data = json.loads(response.content)
            
            # Convert to ExecutionPlan object
            steps = {}
            for step_data in plan_data["steps"]:
                step = ExecutionStep(
                    step_id=step_data["step_id"],
                    tool_name=step_data["tool_name"],
                    parameters=step_data["parameters"],
                    dependencies=step_data.get("dependencies", []),
                    condition=ConditionType(step_data.get("condition", "always")),
                    description=step_data.get("description", "")
                )
                steps[step.step_id] = step
            
            return ExecutionPlan(
                steps=steps,
                plan_id=plan_data["plan_id"],
                description=plan_data["description"]
            )
            
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            # Fall back to conservative plan
            return self._generate_conservative_plan(context)
    
    def _generate_conservative_plan(self, context: PlanningContext) -> ExecutionPlan:
        """Generate a simple, conservative plan as fallback."""
        
        steps = {}
        
        if context.active_documents:
            # Simple document search and synthesis
            steps["step_1"] = ExecutionStep(
                step_id="step_1",
                tool_name="search_uploaded_docs",
                parameters={
                    "doc_name": context.active_documents[0] if len(context.active_documents) == 1 else context.active_documents,
                    "query": context.user_query,
                    "retrieve_full_doc": True
                },
                description="Search document content"
            )
            
            steps["step_2"] = ExecutionStep(
                step_id="step_2",
                tool_name="synthesize_content",
                parameters={
                    "chunks": "$step_1.output",
                    "method": "simple_llm_call",
                    "length": "comprehensive"
                },
                dependencies=["step_1"],
                description="Synthesize search results"
            )
        else:
            # Knowledge base search
            steps["step_1"] = ExecutionStep(
                step_id="step_1",
                tool_name="search_knowledge_base",
                parameters={"query": context.user_query},
                description="Search knowledge base"
            )
        
        return ExecutionPlan(
            steps=steps,
            plan_id=f"conservative_{int(time.time())}",
            description="Conservative fallback plan"
        )
    
    def _validate_plan(self, 
                      plan: ExecutionPlan,
                      context: PlanningContext) -> PlanValidationResult:
        """Validate execution plan for correctness and feasibility."""
        
        errors = []
        warnings = []
        suggestions = []
        
        # Basic plan validation
        is_valid, plan_errors = plan.validate()
        errors.extend(plan_errors)
        
        # Tool availability validation
        for step_id, step in plan.steps.items():
            tool_meta = self.tool_registry.get_tool(step.tool_name)
            if not tool_meta:
                errors.append(f"Unknown tool '{step.tool_name}' in step '{step_id}'")
                continue
            
            # Parameter validation
            param_valid, param_errors = tool_meta.validate_inputs(step.parameters)
            if not param_valid:
                errors.extend([f"Step '{step_id}': {error}" for error in param_errors])
        
        # Context validation
        if not context.active_documents:
            document_tools = ["search_uploaded_docs", "discover_document_structure"]
            for step_id, step in plan.steps.items():
                if step.tool_name in document_tools:
                    warnings.append(f"Step '{step_id}' uses document tool but no active documents")
        
        # Efficiency suggestions
        if len(plan.steps) > 5:
            suggestions.append("Consider breaking down into smaller sub-plans for better error handling")
        
        # Calculate confidence score
        confidence_score = self._calculate_plan_confidence(plan, errors, warnings)
        
        return PlanValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
    
    def _fix_plan_issues(self, 
                        plan: ExecutionPlan,
                        validation_result: PlanValidationResult,
                        context: PlanningContext) -> ExecutionPlan:
        """Attempt to fix issues in the execution plan."""
        
        fixed_steps = plan.steps.copy()
        
        for error in validation_result.errors:
            # Fix unknown tool errors
            if "Unknown tool" in error:
                step_id = self._extract_step_id_from_error(error)
                if step_id and step_id in fixed_steps:
                    old_tool = fixed_steps[step_id].tool_name
                    new_tool = self._suggest_alternative_tool(old_tool, context)
                    if new_tool:
                        fixed_steps[step_id].tool_name = new_tool
                        logger.info(f"Fixed step '{step_id}': {old_tool} -> {new_tool}")
            
            # Fix parameter errors
            if "Parameter validation failed" in error:
                step_id = self._extract_step_id_from_error(error)
                if step_id and step_id in fixed_steps:
                    fixed_steps[step_id].parameters = self._fix_parameters(
                        fixed_steps[step_id].parameters,
                        context
                    )
        
        return ExecutionPlan(
            steps=fixed_steps,
            plan_id=f"{plan.plan_id}_fixed",
            description=f"{plan.description} (with fixes)"
        )
    
    def _add_fallback_strategies(self, 
                               plan: ExecutionPlan,
                               context: PlanningContext) -> ExecutionPlan:
        """Add fallback strategies to the execution plan."""
        
        enhanced_steps = plan.steps.copy()
        
        for step_id, step in plan.steps.items():
            tool_meta = self.tool_registry.get_tool(step.tool_name)
            
            # Add fallbacks for low-reliability tools
            if tool_meta and tool_meta.reliability in [ToolReliability.LOW, ToolReliability.EXPERIMENTAL]:
                fallback_tools = self.tool_registry.get_tool_suggestions(step.tool_name, context.__dict__)
                
                if fallback_tools:
                    fallback_id = f"{step_id}_fallback"
                    fallback_step = ExecutionStep(
                        step_id=fallback_id,
                        tool_name=fallback_tools[0],
                        parameters=step.parameters.copy(),
                        condition=ConditionType.ON_FAILURE,
                        dependencies=[step_id],
                        description=f"Fallback for {step_id}"
                    )
                    enhanced_steps[fallback_id] = fallback_step
                    step.fallback_steps = [fallback_id]
        
        return ExecutionPlan(
            steps=enhanced_steps,
            plan_id=f"{plan.plan_id}_enhanced",
            description=f"{plan.description} (with fallbacks)"
        )
    
    def _optimize_for_parallelism(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize plan for parallel execution where possible."""
        
        # Get execution levels
        execution_levels = plan.get_execution_order()
        
        # Identify steps that can run in parallel
        parallel_opportunities = []
        for level in execution_levels:
            if len(level) > 1:
                parallel_opportunities.extend(level)
        
        if parallel_opportunities:
            logger.info(f"Identified {len(parallel_opportunities)} steps for parallel execution")
        
        # The DAG structure already enables parallelism through dependencies
        # No structural changes needed
        return plan
    
    def _analyze_failures(self, 
                         failed_steps: List[str],
                         execution_results: Dict[str, Any],
                         original_plan: ExecutionPlan) -> Dict[str, Any]:
        """Analyze execution failures to inform replanning."""
        
        analysis = {
            "failed_tools": [],
            "error_patterns": [],
            "successful_steps": [],
            "alternative_approaches": []
        }
        
        for step_id in failed_steps:
            if step_id in original_plan.steps:
                step = original_plan.steps[step_id]
                analysis["failed_tools"].append(step.tool_name)
                
                # Extract error patterns
                if step_id in execution_results:
                    result = execution_results[step_id]
                    if hasattr(result, 'error'):
                        analysis["error_patterns"].append(result.error)
        
        # Identify successful steps
        for step_id, step in original_plan.steps.items():
            if step_id not in failed_steps:
                analysis["successful_steps"].append(step.tool_name)
        
        return analysis
    
    def _generate_alternative_plan(self, 
                                 context: PlanningContext,
                                 failure_analysis: Dict[str, Any],
                                 execution_results: Dict[str, Any]) -> ExecutionPlan:
        """Generate alternative plan based on failure analysis."""
        
        # Avoid failed tools
        avoided_tools = set(failure_analysis["failed_tools"])
        
        # Find alternative tools
        alternative_steps = {}
        step_counter = 1
        
        # Start with successful approaches from original plan
        successful_tools = failure_analysis["successful_steps"]
        
        if successful_tools:
            # Build on successful tools
            for tool_name in successful_tools:
                if tool_name not in avoided_tools:
                    step_id = f"alt_step_{step_counter}"
                    alternative_steps[step_id] = ExecutionStep(
                        step_id=step_id,
                        tool_name=tool_name,
                        parameters=self._infer_parameters_for_tool(tool_name, context),
                        description=f"Alternative approach using {tool_name}"
                    )
                    step_counter += 1
        
        # Add conservative fallback if no alternatives found
        if not alternative_steps:
            return self._generate_conservative_plan(context)
        
        return ExecutionPlan(
            steps=alternative_steps,
            plan_id=f"alternative_{int(time.time())}",
            description="Alternative plan based on failure analysis"
        )
    
    def _load_planning_templates(self) -> Dict[QueryType, Dict[str, Any]]:
        """Load pre-defined planning templates for common query patterns."""
        
        return {
            QueryType.SEARCH: {
                "steps": [
                    {
                        "tool": "search_uploaded_docs",
                        "parameters": {
                            "doc_name": "@active_documents[0]",
                            "query": "@user_query"
                        },
                        "description": "Search for relevant content"
                    }
                ]
            },
            QueryType.SUMMARY: {
                "steps": [
                    {
                        "tool": "search_uploaded_docs",
                        "parameters": {
                            "doc_name": "@active_documents[0]",
                            "retrieve_full_doc": True
                        },
                        "description": "Retrieve full document"
                    },
                    {
                        "tool": "synthesize_content",
                        "parameters": {
                            "chunks": "$step_1.output",
                            "method": "refine",
                            "length": "summary"
                        },
                        "dependencies": ["step_1"],
                        "description": "Create summary"
                    }
                ]
            },
            QueryType.EXTRACTION: {
                "steps": [
                    {
                        "tool": "search_uploaded_docs",
                        "parameters": {
                            "doc_name": "@active_documents[0]",
                            "retrieve_full_doc": True
                        },
                        "description": "Retrieve full document"
                    },
                    {
                        "tool": "extract_key_phrases",
                        "parameters": {
                            "text": "$step_1.output[0].page_content",
                            "top_n": 20
                        },
                        "dependencies": ["step_1"],
                        "description": "Extract key information"
                    }
                ]
            }
        }
    
    def _load_tool_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for tool suggestions."""
        
        return {
            "document_analysis": ["search_uploaded_docs", "discover_document_structure", "synthesize_content"],
            "text_processing": ["extract_key_phrases", "analyze_text_metrics", "analyze_sentiment"],
            "data_analysis": ["process_table_data", "calculate_statistics", "execute_python_code"],
            "visualization": ["create_chart", "create_wordcloud", "create_statistical_plot"]
        }
    
    def _resolve_template_parameters(self, 
                                   parameters: Dict[str, Any],
                                   context: PlanningContext) -> Dict[str, Any]:
        """Resolve template parameter placeholders."""
        
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("@"):
                # Context variable reference
                var_name = value[1:]
                if var_name == "user_query":
                    resolved[key] = context.user_query
                elif var_name == "active_documents[0]":
                    resolved[key] = context.active_documents[0] if context.active_documents else None
                elif var_name == "active_documents":
                    resolved[key] = context.active_documents
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def _calculate_plan_confidence(self, 
                                 plan: ExecutionPlan,
                                 errors: List[str],
                                 warnings: List[str]) -> float:
        """Calculate confidence score for the execution plan."""
        
        base_confidence = 1.0
        
        # Reduce confidence for errors
        base_confidence -= len(errors) * 0.2
        
        # Reduce confidence for warnings
        base_confidence -= len(warnings) * 0.1
        
        # Adjust for tool reliability
        tool_confidence_sum = 0.0
        for step in plan.steps.values():
            tool_meta = self.tool_registry.get_tool(step.tool_name)
            if tool_meta:
                tool_confidence_sum += tool_meta.get_confidence_score()
            else:
                tool_confidence_sum += 0.5  # Unknown tool penalty
        
        if len(plan.steps) > 0:
            avg_tool_confidence = tool_confidence_sum / len(plan.steps)
            base_confidence = (base_confidence + avg_tool_confidence) / 2
        
        return max(0.0, min(1.0, base_confidence))
    
    def _extract_step_id_from_error(self, error: str) -> Optional[str]:
        """Extract step ID from error message."""
        match = re.search(r"step '([^']+)'", error)
        return match.group(1) if match else None
    
    def _suggest_alternative_tool(self, failed_tool: str, context: PlanningContext) -> Optional[str]:
        """Suggest alternative tool for a failed tool."""
        suggestions = self.tool_registry.get_tool_suggestions(failed_tool, context.__dict__)
        return suggestions[0] if suggestions else None
    
    def _fix_parameters(self, 
                       parameters: Dict[str, Any],
                       context: PlanningContext) -> Dict[str, Any]:
        """Fix common parameter issues."""
        
        fixed_params = parameters.copy()
        
        # Add missing required parameters
        if "doc_name" not in fixed_params and context.active_documents:
            fixed_params["doc_name"] = context.active_documents[0]
        
        return fixed_params
    
    def _infer_parameters_for_tool(self, 
                                  tool_name: str,
                                  context: PlanningContext) -> Dict[str, Any]:
        """Infer reasonable parameters for a tool based on context."""
        
        tool_meta = self.tool_registry.get_tool(tool_name)
        if not tool_meta:
            return {}
        
        parameters = {}
        
        # Common parameter patterns
        for param_name, param_def in tool_meta.parameters.items():
            if param_name == "query" and not param_def.required:
                parameters[param_name] = context.user_query
            elif param_name == "doc_name" and context.active_documents:
                parameters[param_name] = context.active_documents[0]
            elif param_name == "doc_names" and context.active_documents:
                parameters[param_name] = context.active_documents
            elif param_def.default_value is not None:
                parameters[param_name] = param_def.default_value
        
        return parameters