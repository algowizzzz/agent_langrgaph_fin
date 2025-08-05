"""
Fixed Step-wise Planning Engine for Orchestrator 2.0

This module provides intelligent planning capabilities with validation,
fallback mechanisms, and adaptive replanning based on execution feedback.

Key fixes:
- Proper condition parsing and validation
- Better error handling for LLM responses
- Enhanced condition type mapping
"""

import logging
import json
import time
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, Callable
from enum import Enum

from .tool_registry import ToolRegistry, ToolReliability
from .execution_engine import ExecutionStep, ExecutionPlan, ConditionType, ExecutionStatus
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


class ConditionParser:
    """Parses and validates condition expressions from LLM responses."""
    
    @staticmethod
    def parse_condition(condition_str: str) -> tuple[ConditionType, Optional[str]]:
        """
        Parse condition string and return appropriate ConditionType and expression.
        
        Args:
            condition_str: Condition string from LLM
            
        Returns:
            Tuple of (ConditionType, expression_string)
        """
        if not condition_str or condition_str == "always":
            return ConditionType.ALWAYS, None
        
        condition_lower = condition_str.lower().strip()
        
        # Map common condition patterns to standard types
        success_patterns = [
            "on_success", "if_success", "when_success", "step_success",
            r"\$\w+\.success", r"step_\d+\.success"
        ]
        
        failure_patterns = [
            "on_failure", "if_failure", "when_failure", "step_failure",
            "if_error", "on_error"
        ]
        
        # Check for success conditions
        for pattern in success_patterns:
            if re.search(pattern, condition_lower):
                return ConditionType.ON_SUCCESS, condition_str
        
        # Check for failure conditions
        for pattern in failure_patterns:
            if re.search(pattern, condition_lower):
                return ConditionType.ON_FAILURE, condition_str
        
        # All other conditions are CUSTOM with expression
        return ConditionType.CUSTOM, condition_str
    
    @staticmethod
    def validate_condition_expression(expression: str, available_steps: Set[str]) -> tuple[bool, str]:
        """
        Validate a custom condition expression.
        
        Args:
            expression: Condition expression to validate
            available_steps: Set of available step IDs
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expression:
            return True, ""
        
        try:
            # Basic validation patterns
            valid_patterns = [
                r'\$\w+\.output',           # Step output references
                r'\$\w+\.success',          # Step success references
                r'len\([^)]+\)',           # Length checks
                r'exists\([^)]+\)',        # Existence checks
                r'active_documents',        # Document state
                r'document_exists',         # Document existence
                r'user_interaction_required', # User interaction
                r'no_active_documents',     # No documents
                r'if_no_active_documents',  # Conditional no documents
                r'on_success',              # Standard success condition
                r'on_failure',              # Standard failure condition
                r'if_success',              # Alternative success condition
                r'if_failure',              # Alternative failure condition
                r'when_success',            # Another success condition
                r'when_failure',            # Another failure condition
            ]
            
            # Check if expression matches known patterns
            for pattern in valid_patterns:
                if re.search(pattern, expression):
                    return True, ""
            
            # If no patterns match, it's still valid but custom
            logger.warning(f"Unknown condition pattern: {expression}")
            return True, f"Unknown condition pattern: {expression}"
            
        except Exception as e:
            return False, f"Invalid condition expression: {str(e)}"


class PlanningEngine:
    """Fixed intelligent planning engine with proper condition handling."""
    
    def __init__(self, tool_registry: ToolRegistry, state_manager: StateManager, llm: Any = None):
        self.tool_registry = tool_registry
        self.state_manager = state_manager
        self.llm = llm
        self.condition_parser = ConditionParser()
        
        # Planning history for learning
        self.planning_history: List[Dict[str, Any]] = []
        
        logger.info("Fixed Planning Engine initialized")
    
    async def create_execution_plan(self, context: PlanningContext, strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE) -> ExecutionPlan:
        """
        Create an execution plan with proper error handling and condition parsing.
        """
        logger.info(f"Creating execution plan for query: '{context.user_query[:100]}...' using {strategy.value} strategy")
        
        try:
            # Get available tools
            available_tools = list(self.tool_registry._tools.keys())
            context.available_tools = set(available_tools)
            
            # Try LLM planning first, with fallback to template-based planning
            plan = await self._try_llm_planning(context, strategy)
            
            if not plan or not plan.steps:
                logger.warning("LLM planning failed, falling back to template-based planning")
                plan = await self._create_template_plan(context, strategy)
            
            # Validate and fix the plan
            validation_result = await self._validate_plan_with_fixes(plan, context)
            
            if not validation_result.is_valid and validation_result.errors:
                logger.warning(f"Plan validation failed: {validation_result.errors}")
                # Try to create a simple fallback plan
                plan = await self._create_simple_fallback_plan(context)
            
            # Log plan details
            logger.info(f"Created execution plan with {len(plan.steps)} steps")
            for step in plan.steps.values():
                logger.debug(f"Step {step.step_id}: {step.tool_name} with condition {step.condition}")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            # Return minimal fallback plan
            return await self._create_simple_fallback_plan(context)
    
    async def _try_llm_planning(self, context: PlanningContext, strategy: PlanningStrategy) -> Optional[ExecutionPlan]:
        """
        Try to create a plan using LLM with proper error handling.
        """
        if not self.llm:
            logger.warning("No LLM available for planning")
            return None
        
        try:
            # Create planning prompt
            prompt = self._create_planning_prompt(context, strategy)
            
            # Get LLM response
            response = await self.llm.ainvoke(prompt)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Parse LLM response
            plan = await self._parse_llm_response(response_text, context)
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM planning failed: JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            return None
    
    async def _parse_llm_response(self, response_text: str, context: PlanningContext) -> Optional[ExecutionPlan]:
        """
        Parse LLM response with improved error handling and condition parsing.
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if not json_match:
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            
            if not json_match:
                logger.error("No JSON found in LLM response")
                return None
            
            # Clean up common JSON malformations before parsing
            json_text = json_match.group(1)
            json_text = self._clean_malformed_json(json_text)
            plan_data = json.loads(json_text)
            
            # Validate plan structure
            if 'steps' not in plan_data:
                logger.error("No 'steps' found in plan data")
                return None
            
            steps = {}
            for step_data in plan_data['steps']:
                try:
                    step = await self._create_step_from_data(step_data, context)
                    if step:
                        steps[step.step_id] = step
                except Exception as e:
                    logger.warning(f"Failed to create step from data: {e}, skipping step")
                    continue
            
            if not steps:
                logger.error("No valid steps created from plan data")
                return None
            
            return ExecutionPlan(
                plan_id=f"plan_{int(time.time())}",
                steps=steps,
                metadata=plan_data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def _clean_malformed_json(self, json_text: str) -> str:
        """
        Clean up common malformations in LLM-generated JSON.
        
        Fixes issues like:
        - Step references with extra braces: "{step_1" -> "step_1"
        - Malformed dependency arrays
        """
        # Fix malformed step references in dependencies
        # Pattern: "dependencies": ["{step_1", "step_2"] -> "dependencies": ["step_1", "step_2"]
        json_text = re.sub(r'"\{(\w+)"', r'"\1"', json_text)
        
        # Fix incomplete step references (missing closing quote)
        # Pattern: "{step_1 -> "step_1"
        json_text = re.sub(r'"\{(\w+)([^"]*)', r'"\1\2', json_text)
        
        # Fix step references with extra characters
        # Pattern: "{step_1' -> "step_1"
        json_text = re.sub(r'"\{([^"]+)[\'"}]', r'"\1"', json_text)
        
        # Clean up any remaining malformed references
        # Pattern: "{anything -> "anything
        json_text = re.sub(r'"\{([^"]+)', r'"\1', json_text)
        
        return json_text
    
    async def _create_step_from_data(self, step_data: Dict, context: PlanningContext) -> Optional[ExecutionStep]:
        """
        Create an execution step with proper condition parsing and parameter validation.
        """
        try:
            step_id = step_data.get('id', step_data.get('step_id', f"step_{len(context.available_tools)}"))
            tool_name = step_data.get('tool', step_data.get('tool_name'))
            
            if not tool_name:
                logger.warning(f"No tool specified for step {step_id}")
                return None
            
            # Check if tool exists
            if tool_name not in self.tool_registry._tools:
                logger.warning(f"Tool '{tool_name}' not available")
                return None
            
            # Parse condition with improved handling
            condition_str = step_data.get('condition', 'always')
            condition_type, condition_expression = self.condition_parser.parse_condition(condition_str)
            
            # Validate parameters
            parameters = step_data.get('parameters', {})
            
            # Handle common parameter issues
            if tool_name == 'search_uploaded_docs' and 'retrieve_full_doc' in parameters:
                # Remove unexpected parameters
                del parameters['retrieve_full_doc']
                logger.debug(f"Removed unexpected parameter 'retrieve_full_doc' from {tool_name}")
            
            # Validate required parameters
            validation_result = self.tool_registry.validate_parameters(tool_name, parameters)
            if not validation_result.is_valid:
                logger.warning(f"Parameter validation failed for {tool_name}: {validation_result.errors}")
                # Try to fix common issues
                parameters = await self._fix_common_parameter_issues(tool_name, parameters, context)
            
            step = ExecutionStep(
                step_id=step_id,
                tool_name=tool_name,
                parameters=parameters,
                dependencies=step_data.get('dependencies', []),
                condition=condition_type,
                condition_expression=condition_expression,
                description=step_data.get('description', ''),
                metadata=step_data.get('metadata', {})
            )
            
            return step
            
        except Exception as e:
            logger.error(f"Error creating step from data: {e}")
            return None
    
    async def _fix_common_parameter_issues(self, tool_name: str, parameters: Dict, context: PlanningContext) -> Dict:
        """
        Fix common parameter validation issues and parameter name mismatches.
        """
        fixed_params = parameters.copy()
        
        # Define parameter name translations (wrong_name -> correct_name)
        parameter_translations = {
            'search_uploaded_docs': {
                'doc_id': 'doc_name',
                'document_id': 'doc_name',
                'document': 'doc_name'
            },
            'discover_document_structure': {
                'doc_id': 'doc_name', 
                'document_id': 'doc_name',
                'document': 'doc_name'
            },
            'extract_key_phrases': {
                'text_input': 'text',
                'input_text': 'text',
                'content': 'text'
            },
            'create_wordcloud': {
                'text_input': 'text',
                'input_text': 'text',
                'content': 'text'
            },
            'synthesize_content': {
                'input_text': 'documents',
                'inputs': 'documents',
                'content': 'documents'
            }
        }
        
        # Apply parameter name translations
        if tool_name in parameter_translations:
            translations = parameter_translations[tool_name]
            for wrong_name, correct_name in translations.items():
                if wrong_name in fixed_params and correct_name not in fixed_params:
                    fixed_params[correct_name] = fixed_params.pop(wrong_name)
                    logger.debug(f"Translated parameter '{wrong_name}' to '{correct_name}' for {tool_name}")
        
        # Remove unexpected parameters that we can't translate
        tool_metadata = self.tool_registry.get_tool(tool_name)
        if tool_metadata:
            valid_params = set(tool_metadata.parameters.keys())
            unexpected_params = set(fixed_params.keys()) - valid_params
            for param in unexpected_params:
                logger.debug(f"Removing unexpected parameter '{param}' from {tool_name}")
                fixed_params.pop(param, None)
        
        # Fix missing doc_name parameter for document tools
        if tool_name in ['search_uploaded_docs', 'discover_document_structure'] and 'doc_name' not in fixed_params:
            if context.active_documents:
                fixed_params['doc_name'] = context.active_documents[0]
                logger.debug(f"Added missing doc_name parameter: {fixed_params['doc_name']}")
            else:
                fixed_params['doc_name'] = "riskandfinace.pdf"  # Use default document name
                logger.debug("Added default doc_name parameter")
        
        # Fix missing query parameter for search tools
        if tool_name in ['search_conversation_history', 'search_knowledge_base', 'search_uploaded_docs']:
            if 'query' not in fixed_params:
                fixed_params['query'] = context.user_query
                logger.debug(f"Added missing query parameter for {tool_name}")
        
        # Fix synthesize_content required parameters
        if tool_name == 'synthesize_content':
            if 'documents' not in fixed_params:
                fixed_params['documents'] = ["Retrieved information from previous steps"]
                logger.debug("Added default documents parameter for synthesize_content")
            if 'query' not in fixed_params:
                fixed_params['query'] = context.user_query
                logger.debug("Added missing query parameter for synthesize_content")
        
        return fixed_params
    
    async def _create_template_plan(self, context: PlanningContext, strategy: PlanningStrategy) -> ExecutionPlan:
        """
        Create a plan using predefined templates based on query type.
        """
        query_type = context.get_query_type()
        logger.info(f"Creating template plan for query type: {query_type}")
        
        steps_list = []
        
        # Common step patterns based on query type
        if query_type == QueryType.SEARCH:
            steps_list = await self._create_search_template_steps(context)
        elif query_type == QueryType.ANALYSIS:
            steps_list = await self._create_analysis_template_steps(context)
        elif query_type == QueryType.SUMMARY:
            steps_list = await self._create_summary_template_steps(context)
        else:
            steps_list = await self._create_general_template_steps(context)
        
        # Convert list to dictionary keyed by step_id
        steps = {step.step_id: step for step in steps_list}
        
        return ExecutionPlan(
            plan_id=f"template_plan_{int(time.time())}",
            steps=steps,
            metadata={"query_type": query_type.value, "template_used": True}
        )
    
    async def _create_search_template_steps(self, context: PlanningContext) -> List[ExecutionStep]:
        """Create template steps for search queries."""
        steps = []
        
        # Step 1: Search uploaded documents (always include - let the tool handle availability)
        steps.append(ExecutionStep(
            step_id="search_docs",
            tool_name="search_uploaded_docs",
            parameters={
                "doc_name": context.active_documents[0] if context.active_documents else "any_document",
                "query": context.user_query
            },
            condition=ConditionType.ALWAYS,
            description="Search uploaded documents"
        ))
        
        # Step 2: Search conversation history
        steps.append(ExecutionStep(
            step_id="search_history",
            tool_name="search_conversation_history",
            parameters={"query": context.user_query},
            condition=ConditionType.ALWAYS,
            description="Search conversation history"
        ))
        
        # Step 3: Synthesize results
        steps.append(ExecutionStep(
            step_id="synthesize",
            tool_name="synthesize_content",
            parameters={
                "documents": "$search_docs",
                "query": context.user_query
            },
            dependencies=["search_docs", "search_history"],
            condition=ConditionType.ALWAYS,
            description="Synthesize search results"
        ))
        
        return steps
    
    async def _create_analysis_template_steps(self, context: PlanningContext) -> List[ExecutionStep]:
        """Create template steps for analysis queries."""
        return await self._create_search_template_steps(context)  # Similar to search for now
    
    async def _create_summary_template_steps(self, context: PlanningContext) -> List[ExecutionStep]:
        """Create template steps for summary queries.""" 
        return await self._create_search_template_steps(context)  # Similar to search for now
    
    async def _create_general_template_steps(self, context: PlanningContext) -> List[ExecutionStep]:
        """Create general template steps."""
        return await self._create_search_template_steps(context)  # Default to search template
    
    async def _create_simple_fallback_plan(self, context: PlanningContext) -> ExecutionPlan:
        """
        Create a minimal fallback plan that should always work.
        """
        logger.info("Creating simple fallback plan")
        
        steps_list = [
            ExecutionStep(
                step_id="fallback_search",
                tool_name="search_knowledge_base",
                parameters={"query": context.user_query},
                condition=ConditionType.ALWAYS,
                description="Fallback knowledge base search"
            )
        ]
        
        # Convert list to dictionary keyed by step_id
        steps = {step.step_id: step for step in steps_list}
        
        return ExecutionPlan(
            plan_id=f"fallback_plan_{int(time.time())}",
            steps=steps,
            metadata={"fallback_plan": True}
        )
    
    async def _validate_plan_with_fixes(self, plan: ExecutionPlan, context: PlanningContext) -> PlanValidationResult:
        """
        Validate plan and attempt to fix common issues.
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Validate each step
            for step_id, step in plan.steps.items():
                # Check tool availability
                if step.tool_name not in self.tool_registry._tools:
                    errors.append(f"Tool '{step.tool_name}' not available")
                    continue
                
                # Validate parameters
                param_validation = self.tool_registry.validate_parameters(step.tool_name, step.parameters)
                if not param_validation.is_valid:
                    for error in param_validation.errors:
                        if "Required parameter" in error and "missing" in error:
                            warnings.append(f"Step '{step.step_id}': {error}")
                        else:
                            errors.append(f"Step '{step.step_id}': {error}")
                
                # Validate condition
                if step.condition_expression:
                    is_valid, error_msg = self.condition_parser.validate_condition_expression(
                        step.condition_expression, 
                        {s_id for s_id in plan.steps.keys()}
                    )
                    if not is_valid:
                        warnings.append(f"Step '{step.step_id}': {error_msg}")
            
            # Check for circular dependencies
            if self._has_circular_dependencies(plan):
                errors.append("Circular dependencies detected in plan")
            
            is_valid = len(errors) == 0
            confidence = 1.0 - (len(errors) * 0.3 + len(warnings) * 0.1)
            
            return PlanValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                confidence_score=max(0.0, confidence)
            )
            
        except Exception as e:
            logger.error(f"Error during plan validation: {e}")
            return PlanValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                confidence_score=0.0
            )
    
    def _has_circular_dependencies(self, plan: ExecutionPlan) -> bool:
        """Check for circular dependencies in the plan."""
        try:
            # Simple cycle detection
            visited = set()
            rec_stack = set()
            
            def has_cycle(step_id: str) -> bool:
                if step_id in rec_stack:
                    return True
                if step_id in visited:
                    return False
                
                visited.add(step_id)
                rec_stack.add(step_id)
                
                # Find step and check its dependencies
                if step_id in plan.steps:
                    step = plan.steps[step_id]
                    for dep in step.dependencies:
                        if has_cycle(dep):
                            return True
                
                rec_stack.remove(step_id)
                return False
            
            for step_id in plan.steps.keys():
                if step_id not in visited:
                    if has_cycle(step_id):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking circular dependencies: {e}")
            return False
    
    def _create_planning_prompt(self, context: PlanningContext, strategy: PlanningStrategy) -> str:
        """Create planning prompt for LLM with clear condition guidelines and tool specifications."""
        
        # Get detailed tool definitions with correct parameter names
        tool_definitions = self.tool_registry.export_tool_definitions()
        
        # Format tool specifications for the prompt
        tool_specs = []
        for tool_name in context.available_tools:
            if tool_name in tool_definitions:
                tool_def = tool_definitions[tool_name]
                params_spec = []
                for param_name, param_info in tool_def["parameters"].items():
                    required_str = "REQUIRED" if param_info["required"] else "optional"
                    params_spec.append(f'"{param_name}": {param_info["type"]} ({required_str})')
                
                tool_specs.append(f"""- {tool_name}: {tool_def["description"]}
  Parameters: {{{', '.join(params_spec)}}}""")
        
        tools_specification = "\n".join(tool_specs)
        
        prompt = f"""Create an execution plan for the user query using available tools.

User Query: {context.user_query}
Session ID: {context.session_id}
Active Documents: {context.active_documents}
Strategy: {strategy.value}

AVAILABLE TOOLS WITH EXACT PARAMETER NAMES:
{tools_specification}

CRITICAL PARAMETER RULES:
- ALWAYS use exact parameter names shown above
- For search_uploaded_docs: use "doc_name" (NOT "doc_id")
- For synthesize_content: use "documents" and "query" (REQUIRED)
- For extract_key_phrases: use "text" (NOT "text_input" or "input_text")
- For create_wordcloud: use "text" (NOT "text_input")
- For discover_document_structure: use "doc_name" (NOT "doc_id")

CONDITION GUIDELINES:
- Use "always" for steps that should always execute
- Use "on_success" for steps that depend on previous step success
- Use "on_failure" for error handling steps

Return a JSON plan with this structure:
{{
    "strategy": "{strategy.value}",
    "steps": [
        {{
            "id": "step_1",
            "tool": "tool_name",
            "parameters": {{"exact_param_name": "value"}},
            "dependencies": [],
            "condition": "always",
            "description": "What this step does"
        }}
    ]
}}

Create a plan that addresses the user query effectively using the available tools with EXACT parameter names."""
        
        return prompt