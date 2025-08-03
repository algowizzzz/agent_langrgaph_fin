"""
DAG-based Execution Engine for Orchestrator 2.0

This module provides a directed acyclic graph (DAG) execution engine that handles
tool dependencies, conditional execution, and parallel processing capabilities.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Callable, Union
from enum import Enum
import json
try:
    import networkx as nx
except ImportError:
    # Fallback implementation if networkx is not available
    class DummyNetworkX:
        class DiGraph:
            def __init__(self):
                self.nodes = set()
                self.edges = set()
            
            def add_node(self, node):
                self.nodes.add(node)
            
            def add_edge(self, from_node, to_node):
                self.edges.add((from_node, to_node))
        
        class NetworkXError(Exception):
            pass
            
        def simple_cycles(self, graph):
            return []
            
        def topological_sort(self, graph):
            return list(graph.nodes)
    
    nx = DummyNetworkX()

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of execution steps."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ConditionType(Enum):
    """Types of conditional execution."""
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    CUSTOM = "custom"


@dataclass
class ExecutionResult:
    """Result of a step execution."""
    step_id: str
    status: ExecutionStatus
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExecutionStep:
    """Represents a single execution step in the DAG."""
    step_id: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    condition: ConditionType = ConditionType.ALWAYS
    condition_expression: Optional[str] = None
    timeout: Optional[float] = None
    retry_count: int = 0
    fallback_steps: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def can_execute(self, completed_steps: Set[str], failed_steps: Set[str]) -> bool:
        """Check if this step can be executed based on dependencies and conditions."""
        # Check dependencies
        for dep in self.dependencies:
            if dep not in completed_steps and dep not in failed_steps:
                return False
        
        # Check condition
        if self.condition == ConditionType.ALWAYS:
            return True
        elif self.condition == ConditionType.ON_SUCCESS:
            return all(dep not in failed_steps for dep in self.dependencies)
        elif self.condition == ConditionType.ON_FAILURE:
            return any(dep in failed_steps for dep in self.dependencies)
        elif self.condition == ConditionType.CUSTOM:
            return self._evaluate_custom_condition(completed_steps, failed_steps)
        
        return True
    
    def _evaluate_custom_condition(self, completed_steps: Set[str], failed_steps: Set[str]) -> bool:
        """Evaluate custom condition expression."""
        if not self.condition_expression:
            return True
        
        try:
            # Simple expression evaluation - can be enhanced with a proper parser
            expr = self.condition_expression
            
            # Replace step references with boolean values
            for step_id in completed_steps.union(failed_steps):
                success_var = f"step_{step_id}_success"
                failed_var = f"step_{step_id}_failed"
                expr = expr.replace(success_var, str(step_id in completed_steps))
                expr = expr.replace(failed_var, str(step_id in failed_steps))
            
            # Evaluate the expression safely
            allowed_names = {"True", "False", "and", "or", "not"}
            code = compile(expr, "<condition>", "eval")
            
            # Check that only allowed names are used
            for name in code.co_names:
                if name not in allowed_names:
                    logger.warning(f"Potentially unsafe name in condition: {name}")
                    return True
            
            return eval(code, {"__builtins__": {}})
        except Exception as e:
            logger.error(f"Error evaluating condition '{self.condition_expression}': {e}")
            return True


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan as a DAG."""
    steps: Dict[str, ExecutionStep]
    plan_id: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate the execution plan for cycles and consistency."""
        errors = []
        
        # Build networkx graph for cycle detection
        graph = nx.DiGraph()
        
        for step_id, step in self.steps.items():
            graph.add_node(step_id)
            for dep in step.dependencies:
                if dep not in self.steps:
                    errors.append(f"Step '{step_id}' depends on unknown step '{dep}'")
                else:
                    graph.add_edge(dep, step_id)
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                errors.append(f"Execution plan contains cycles: {cycles}")
        except Exception as e:
            errors.append(f"Error checking for cycles: {e}")
        
        # Check for fallback step validity
        for step_id, step in self.steps.items():
            for fallback_id in step.fallback_steps:
                if fallback_id not in self.steps:
                    errors.append(f"Step '{step_id}' references unknown fallback step '{fallback_id}'")
        
        return len(errors) == 0, errors
    
    def get_executable_steps(self, completed_steps: Set[str], failed_steps: Set[str]) -> List[str]:
        """Get list of steps that can be executed now."""
        executable = []
        
        for step_id, step in self.steps.items():
            if (step_id not in completed_steps and 
                step_id not in failed_steps and 
                step.can_execute(completed_steps, failed_steps)):
                executable.append(step_id)
        
        return executable
    
    def get_execution_order(self) -> List[List[str]]:
        """Get topological execution order, grouped by parallelizable steps."""
        graph = nx.DiGraph()
        
        for step_id, step in self.steps.items():
            graph.add_node(step_id)
            for dep in step.dependencies:
                graph.add_edge(dep, step_id)
        
        try:
            # Get topological sort
            topo_order = list(nx.topological_sort(graph))
            
            # Group steps that can run in parallel
            levels = []
            completed = set()
            
            while len(completed) < len(self.steps):
                current_level = []
                
                for step_id in topo_order:
                    if step_id not in completed:
                        step = self.steps[step_id]
                        if all(dep in completed for dep in step.dependencies):
                            current_level.append(step_id)
                
                if not current_level:
                    # Shouldn't happen with a valid DAG
                    break
                
                levels.append(current_level)
                completed.update(current_level)
            
            return levels
        except nx.NetworkXError as e:
            logger.error(f"Error computing execution order: {e}")
            return []


class ExecutionEngine:
    """DAG-based execution engine with parallel processing and error handling."""
    
    def __init__(self, tool_registry, max_parallel_steps: int = 3):
        self.tool_registry = tool_registry
        self.max_parallel_steps = max_parallel_steps
        self.execution_results: Dict[str, ExecutionResult] = {}
        self.step_outputs: Dict[str, Any] = {}
        self.execution_context: Dict[str, Any] = {}
        
    async def execute_plan(self, 
                          plan: ExecutionPlan,
                          context: Dict[str, Any] = None,
                          progress_callback: Optional[Callable] = None) -> Dict[str, ExecutionResult]:
        """Execute a complete plan with parallel processing and error handling."""
        
        self.execution_context.update(context or {})
        self.execution_results.clear()
        self.step_outputs.clear()
        
        # Validate plan
        is_valid, errors = plan.validate()
        if not is_valid:
            error_msg = f"Invalid execution plan: {errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Starting execution of plan: {plan.plan_id}")
        
        completed_steps = set()
        failed_steps = set()
        running_steps = set()
        
        # Main execution loop
        while len(completed_steps) + len(failed_steps) < len(plan.steps):
            # Get executable steps
            executable_steps = plan.get_executable_steps(completed_steps, failed_steps)
            
            # Filter out already running steps
            executable_steps = [s for s in executable_steps if s not in running_steps]
            
            if not executable_steps:
                # Check if we have running steps
                if running_steps:
                    # Wait a bit for running steps to complete
                    await asyncio.sleep(0.1)
                    continue
                else:
                    # No executable or running steps - execution is stuck
                    logger.error("Execution stuck - no executable steps available")
                    break
            
            # Limit parallel execution
            available_slots = self.max_parallel_steps - len(running_steps)
            steps_to_execute = executable_steps[:available_slots]
            
            # Start execution of selected steps
            tasks = []
            for step_id in steps_to_execute:
                running_steps.add(step_id)
                task = asyncio.create_task(self._execute_step(plan.steps[step_id]))
                tasks.append((step_id, task))
            
            # Wait for at least one step to complete
            if tasks:
                done, pending = await asyncio.wait(
                    [task for _, task in tasks],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for step_id, task in tasks:
                    if task in done:
                        try:
                            result = await task
                            self.execution_results[step_id] = result
                            
                            if result.status == ExecutionStatus.COMPLETED:
                                completed_steps.add(step_id)
                                self.step_outputs[step_id] = result.output
                                logger.info(f"Step '{step_id}' completed successfully")
                            else:
                                failed_steps.add(step_id)
                                logger.error(f"Step '{step_id}' failed: {result.error}")
                                
                                # Try fallback steps
                                await self._handle_step_failure(plan.steps[step_id], plan)
                            
                            running_steps.remove(step_id)
                            
                            # Call progress callback
                            if progress_callback:
                                await progress_callback(result)
                                
                        except Exception as e:
                            logger.error(f"Unexpected error in step '{step_id}': {e}")
                            failed_steps.add(step_id)
                            running_steps.remove(step_id)
                            
                            self.execution_results[step_id] = ExecutionResult(
                                step_id=step_id,
                                status=ExecutionStatus.FAILED,
                                error=str(e)
                            )
        
        logger.info(f"Plan execution completed. Success: {len(completed_steps)}, Failed: {len(failed_steps)}")
        return self.execution_results
    
    async def _execute_step(self, step: ExecutionStep) -> ExecutionResult:
        """Execute a single step."""
        start_time = time.time()
        
        try:
            logger.info(f"Executing step: {step.step_id} ({step.tool_name})")
            
            # Get tool metadata
            tool_meta = self.tool_registry.get_tool(step.tool_name)
            if not tool_meta:
                raise ValueError(f"Unknown tool: {step.tool_name}")
            
            # Resolve parameters
            resolved_params = self._resolve_parameters(step.parameters)
            
            # Validate parameters
            is_valid, errors = tool_meta.validate_inputs(resolved_params)
            if not is_valid:
                raise ValueError(f"Parameter validation failed: {errors}")
            
            # Execute with timeout
            if step.timeout:
                result = await asyncio.wait_for(
                    self._call_tool(tool_meta.function, resolved_params),
                    timeout=step.timeout
                )
            else:
                result = await self._call_tool(tool_meta.function, resolved_params)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.COMPLETED,
                output=result,
                execution_time=execution_time,
                confidence_score=tool_meta.get_confidence_score(),
                metadata={
                    "tool_name": step.tool_name,
                    "parameters": resolved_params
                }
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return ExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                error=f"Step timed out after {step.timeout}s",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Step '{step.step_id}' failed: {e}")
            
            return ExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _call_tool(self, tool_function: Callable, parameters: Dict[str, Any]) -> Any:
        """Call a tool function, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(tool_function):
            return await tool_function(**parameters)
        else:
            # Run sync function in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: tool_function(**parameters))
    
    def _resolve_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter placeholders with actual values."""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to previous step output
                ref = value[1:]  # Remove $ prefix
                if "." in ref:
                    step_id, field = ref.split(".", 1)
                    if step_id in self.step_outputs:
                        step_output = self.step_outputs[step_id]
                        resolved[key] = self._get_nested_value(step_output, field)
                    else:
                        raise ValueError(f"Referenced step '{step_id}' not found")
                else:
                    # Direct step output reference
                    if ref in self.step_outputs:
                        resolved[key] = self.step_outputs[ref]
                    else:
                        raise ValueError(f"Referenced step '{ref}' not found")
            elif isinstance(value, str) and value.startswith("@"):
                # Context variable reference
                context_key = value[1:]
                if context_key in self.execution_context:
                    resolved[key] = self.execution_context[context_key]
                else:
                    raise ValueError(f"Context variable '{context_key}' not found")
            else:
                resolved[key] = value
        
        return resolved
    
    def _get_nested_value(self, obj: Any, field_path: str) -> Any:
        """Get nested value from object using dot notation."""
        try:
            current = obj
            for field in field_path.split("."):
                if isinstance(current, dict):
                    current = current[field]
                elif hasattr(current, field):
                    current = getattr(current, field)
                else:
                    raise KeyError(f"Field '{field}' not found")
            return current
        except Exception as e:
            raise ValueError(f"Could not resolve field path '{field_path}': {e}")
    
    async def _handle_step_failure(self, failed_step: ExecutionStep, plan: ExecutionPlan) -> None:
        """Handle step failure by executing fallback steps."""
        if not failed_step.fallback_steps:
            return
        
        logger.info(f"Executing fallback steps for failed step: {failed_step.step_id}")
        
        for fallback_id in failed_step.fallback_steps:
            if fallback_id in plan.steps:
                fallback_step = plan.steps[fallback_id]
                
                try:
                    result = await self._execute_step(fallback_step)
                    self.execution_results[fallback_id] = result
                    
                    if result.status == ExecutionStatus.COMPLETED:
                        self.step_outputs[fallback_id] = result.output
                        logger.info(f"Fallback step '{fallback_id}' completed successfully")
                        break  # Stop after first successful fallback
                    
                except Exception as e:
                    logger.error(f"Fallback step '{fallback_id}' also failed: {e}")
                    continue
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution results."""
        total_steps = len(self.execution_results)
        completed = len([r for r in self.execution_results.values() if r.status == ExecutionStatus.COMPLETED])
        failed = len([r for r in self.execution_results.values() if r.status == ExecutionStatus.FAILED])
        
        total_time = sum(r.execution_time for r in self.execution_results.values())
        avg_confidence = sum(r.confidence_score for r in self.execution_results.values()) / total_steps if total_steps > 0 else 0
        
        return {
            "total_steps": total_steps,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total_steps if total_steps > 0 else 0,
            "total_execution_time": total_time,
            "average_confidence": avg_confidence,
            "step_details": {step_id: {
                "status": result.status.value,
                "execution_time": result.execution_time,
                "confidence": result.confidence_score
            } for step_id, result in self.execution_results.items()}
        }