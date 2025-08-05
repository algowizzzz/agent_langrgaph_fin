"""
Unit tests for Execution Engine

Tests the DAG-based execution engine with parallel processing,
dependency management, and error handling capabilities.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from orchestrator_v2.execution_engine import (
    ExecutionEngine, ExecutionStep, ExecutionPlan, ExecutionResult,
    ExecutionStatus, ConditionType
)
from orchestrator_v2.tool_registry import ToolRegistry, ToolReliability


class TestExecutionStep:
    """Test suite for ExecutionStep class"""
    
    def test_step_creation(self):
        """Test basic execution step creation"""
        step = ExecutionStep(
            step_id="test_step",
            tool_name="test_tool",
            parameters={"param1": "value1"},
            dependencies=["step1", "step2"],
            description="Test step description"
        )
        
        assert step.step_id == "test_step"
        assert step.tool_name == "test_tool"
        assert step.parameters == {"param1": "value1"}
        assert step.dependencies == ["step1", "step2"]
        assert step.description == "Test step description"
        assert step.condition == ConditionType.ALWAYS
    
    def test_can_execute_no_dependencies(self):
        """Test execution check with no dependencies"""
        step = ExecutionStep("step1", "tool1", {})
        
        completed_steps = set()
        failed_steps = set()
        
        assert step.can_execute(completed_steps, failed_steps) == True
    
    def test_can_execute_with_completed_dependencies(self):
        """Test execution check with completed dependencies"""
        step = ExecutionStep("step3", "tool3", {}, dependencies=["step1", "step2"])
        
        completed_steps = {"step1", "step2"}
        failed_steps = set()
        
        assert step.can_execute(completed_steps, failed_steps) == True
    
    def test_can_execute_with_pending_dependencies(self):
        """Test execution check with pending dependencies"""
        step = ExecutionStep("step3", "tool3", {}, dependencies=["step1", "step2"])
        
        completed_steps = {"step1"}  # step2 still pending
        failed_steps = set()
        
        assert step.can_execute(completed_steps, failed_steps) == False
    
    def test_can_execute_conditional_on_success(self):
        """Test conditional execution on success"""
        step = ExecutionStep(
            "step2", "tool2", {},
            dependencies=["step1"],
            condition=ConditionType.ON_SUCCESS
        )
        
        # Dependency completed successfully
        completed_steps = {"step1"}
        failed_steps = set()
        assert step.can_execute(completed_steps, failed_steps) == True
        
        # Dependency failed
        completed_steps = set()
        failed_steps = {"step1"}
        assert step.can_execute(completed_steps, failed_steps) == False
    
    def test_can_execute_conditional_on_failure(self):
        """Test conditional execution on failure"""
        step = ExecutionStep(
            "fallback_step", "fallback_tool", {},
            dependencies=["main_step"],
            condition=ConditionType.ON_FAILURE
        )
        
        # Dependency completed successfully - should not execute
        completed_steps = {"main_step"}
        failed_steps = set()
        assert step.can_execute(completed_steps, failed_steps) == False
        
        # Dependency failed - should execute
        completed_steps = set()
        failed_steps = {"main_step"}
        assert step.can_execute(completed_steps, failed_steps) == True


class TestExecutionPlan:
    """Test suite for ExecutionPlan class"""
    
    def test_plan_creation(self):
        """Test execution plan creation"""
        steps = {
            "step1": ExecutionStep("step1", "tool1", {}),
            "step2": ExecutionStep("step2", "tool2", {}, dependencies=["step1"])
        }
        
        plan = ExecutionPlan(
            steps=steps,
            plan_id="test_plan",
            description="Test execution plan"
        )
        
        assert plan.plan_id == "test_plan"
        assert plan.description == "Test execution plan"
        assert len(plan.steps) == 2
        assert "step1" in plan.steps
        assert "step2" in plan.steps
    
    def test_plan_validation_valid(self):
        """Test validation of valid execution plan"""
        steps = {
            "step1": ExecutionStep("step1", "tool1", {}),
            "step2": ExecutionStep("step2", "tool2", {}, dependencies=["step1"]),
            "step3": ExecutionStep("step3", "tool3", {}, dependencies=["step1", "step2"])
        }
        
        plan = ExecutionPlan(steps, "valid_plan")
        is_valid, errors = plan.validate()
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_plan_validation_missing_dependency(self):
        """Test validation with missing dependency"""
        steps = {
            "step1": ExecutionStep("step1", "tool1", {}),
            "step2": ExecutionStep("step2", "tool2", {}, dependencies=["missing_step"])
        }
        
        plan = ExecutionPlan(steps, "invalid_plan")
        is_valid, errors = plan.validate()
        
        assert is_valid == False
        assert len(errors) > 0
        assert any("unknown step" in error.lower() for error in errors)
    
    def test_plan_validation_circular_dependency(self):
        """Test validation with circular dependencies"""
        steps = {
            "step1": ExecutionStep("step1", "tool1", {}, dependencies=["step2"]),
            "step2": ExecutionStep("step2", "tool2", {}, dependencies=["step1"])
        }
        
        plan = ExecutionPlan(steps, "circular_plan")
        is_valid, errors = plan.validate()
        
        assert is_valid == False
        assert len(errors) > 0
    
    def test_get_executable_steps(self):
        """Test getting currently executable steps"""
        steps = {
            "step1": ExecutionStep("step1", "tool1", {}),
            "step2": ExecutionStep("step2", "tool2", {}),
            "step3": ExecutionStep("step3", "tool3", {}, dependencies=["step1"]),
            "step4": ExecutionStep("step4", "tool4", {}, dependencies=["step1", "step2"])
        }
        
        plan = ExecutionPlan(steps, "test_plan")
        
        # Initially, only steps with no dependencies are executable
        completed_steps = set()
        failed_steps = set()
        executable = plan.get_executable_steps(completed_steps, failed_steps)
        
        assert set(executable) == {"step1", "step2"}
        
        # After step1 completes, step3 becomes executable
        completed_steps = {"step1"}
        executable = plan.get_executable_steps(completed_steps, failed_steps)
        
        assert "step3" in executable
        assert "step4" not in executable  # Still waiting for step2
        
        # After both step1 and step2 complete, step4 becomes executable
        completed_steps = {"step1", "step2"}
        executable = plan.get_executable_steps(completed_steps, failed_steps)
        
        assert "step4" in executable
    
    def test_get_execution_order(self):
        """Test topological execution order calculation"""
        steps = {
            "step1": ExecutionStep("step1", "tool1", {}),
            "step2": ExecutionStep("step2", "tool2", {}),
            "step3": ExecutionStep("step3", "tool3", {}, dependencies=["step1", "step2"]),
            "step4": ExecutionStep("step4", "tool4", {}, dependencies=["step3"])
        }
        
        plan = ExecutionPlan(steps, "ordered_plan")
        execution_levels = plan.get_execution_order()
        
        assert len(execution_levels) == 3
        
        # Level 0: Independent steps (can run in parallel)
        assert set(execution_levels[0]) == {"step1", "step2"}
        
        # Level 1: Depends on level 0
        assert execution_levels[1] == ["step3"]
        
        # Level 2: Depends on level 1
        assert execution_levels[2] == ["step4"]


class TestExecutionEngine:
    """Test suite for ExecutionEngine class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tool_registry = ToolRegistry()
        self.execution_engine = ExecutionEngine(self.tool_registry, max_parallel_steps=2)
        
        # Register mock tools
        self._register_mock_tools()
    
    def _register_mock_tools(self):
        """Register mock tools for testing"""
        def mock_tool_1(input_data: str) -> str:
            return f"Tool1 processed: {input_data}"
        
        def mock_tool_2(input_data: str) -> str:
            return f"Tool2 processed: {input_data}"
        
        async def async_mock_tool(input_data: str) -> str:
            await asyncio.sleep(0.1)  # Simulate async work
            return f"AsyncTool processed: {input_data}"
        
        def slow_tool(input_data: str) -> str:
            time.sleep(0.5)  # Simulate slow operation
            return f"SlowTool processed: {input_data}"
        
        def failing_tool(input_data: str) -> str:
            raise Exception("Tool failure simulation")
        
        self.tool_registry.register_function("mock_tool_1", mock_tool_1, reliability=ToolReliability.HIGH)
        self.tool_registry.register_function("mock_tool_2", mock_tool_2, reliability=ToolReliability.HIGH)
        self.tool_registry.register_function("async_mock_tool", async_mock_tool, reliability=ToolReliability.MEDIUM)
        self.tool_registry.register_function("slow_tool", slow_tool, reliability=ToolReliability.LOW)
        self.tool_registry.register_function("failing_tool", failing_tool, reliability=ToolReliability.LOW)
    
    @pytest.mark.asyncio
    async def test_execute_single_step(self):
        """Test execution of a single step"""
        step = ExecutionStep("test_step", "mock_tool_1", {"input_data": "test_input"})
        
        result = await self.execution_engine._execute_step(step)
        
        assert result.step_id == "test_step"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output == "Tool1 processed: test_input"
        assert result.execution_time > 0
        assert result.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_execute_step_with_timeout(self):
        """Test step execution with timeout"""
        step = ExecutionStep("slow_step", "slow_tool", {"input_data": "test"}, timeout=0.1)
        
        result = await self.execution_engine._execute_step(step)
        
        assert result.step_id == "slow_step"
        assert result.status == ExecutionStatus.FAILED
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_step_failure(self):
        """Test handling of step execution failure"""
        step = ExecutionStep("failing_step", "failing_tool", {"input_data": "test"})
        
        result = await self.execution_engine._execute_step(step)
        
        assert result.step_id == "failing_step"
        assert result.status == ExecutionStatus.FAILED
        assert "tool failure simulation" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_plan_sequential(self):
        """Test execution of sequential plan"""
        steps = {
            "step1": ExecutionStep("step1", "mock_tool_1", {"input_data": "input1"}),
            "step2": ExecutionStep("step2", "mock_tool_2", {"input_data": "$step1"}, dependencies=["step1"])
        }
        
        plan = ExecutionPlan(steps, "sequential_plan")
        
        # Mock parameter resolution
        self.execution_engine.step_outputs = {"step1": "Tool1 processed: input1"}
        
        results = await self.execution_engine.execute_plan(plan)
        
        assert len(results) == 2
        assert "step1" in results
        assert "step2" in results
        assert results["step1"].status == ExecutionStatus.COMPLETED
        assert results["step2"].status == ExecutionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_plan_parallel(self):
        """Test parallel execution of independent steps"""
        steps = {
            "step1": ExecutionStep("step1", "mock_tool_1", {"input_data": "input1"}),
            "step2": ExecutionStep("step2", "mock_tool_2", {"input_data": "input2"}),
            "step3": ExecutionStep("step3", "async_mock_tool", {"input_data": "input3"})
        }
        
        plan = ExecutionPlan(steps, "parallel_plan")
        
        start_time = time.time()
        results = await self.execution_engine.execute_plan(plan)
        execution_time = time.time() - start_time
        
        # Should complete faster than sequential execution
        assert execution_time < 1.0  # All tools should run in parallel
        
        assert len(results) == 3
        for step_id in ["step1", "step2", "step3"]:
            assert step_id in results
            assert results[step_id].status == ExecutionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_parameter_resolution(self):
        """Test parameter resolution with step references"""
        # Setup mock step outputs
        self.execution_engine.step_outputs["step1"] = {"result": "test_output", "count": 5}
        
        # Test direct step output reference
        resolved = self.execution_engine._resolve_parameters({"param": "$step1"})
        assert resolved == {"param": {"result": "test_output", "count": 5}}
        
        # Test nested field reference
        self.execution_engine.step_outputs["step2"] = {"nested": {"field": "nested_value"}}
        resolved = self.execution_engine._resolve_parameters({"param": "$step2.nested.field"})
        assert resolved == {"param": "nested_value"}
        
        # Test context variable reference
        self.execution_engine.execution_context["context_var"] = "context_value"
        resolved = self.execution_engine._resolve_parameters({"param": "@context_var"})
        assert resolved == {"param": "context_value"}
    
    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Test progress callback functionality"""
        steps = {
            "step1": ExecutionStep("step1", "mock_tool_1", {"input_data": "test"})
        }
        
        plan = ExecutionPlan(steps, "callback_test")
        
        callback_results = []
        
        async def mock_callback(result):
            callback_results.append(result)
        
        await self.execution_engine.execute_plan(plan, progress_callback=mock_callback)
        
        assert len(callback_results) == 1
        assert callback_results[0].step_id == "step1"
        assert callback_results[0].status == ExecutionStatus.COMPLETED
    
    def test_execution_summary(self):
        """Test execution summary generation"""
        # Mock some execution results
        self.execution_engine.execution_results = {
            "step1": ExecutionResult("step1", ExecutionStatus.COMPLETED, "result1", execution_time=1.0, confidence_score=0.9),
            "step2": ExecutionResult("step2", ExecutionStatus.COMPLETED, "result2", execution_time=0.5, confidence_score=0.8),
            "step3": ExecutionResult("step3", ExecutionStatus.FAILED, error="failed", execution_time=0.2, confidence_score=0.0)
        }
        
        summary = self.execution_engine.get_execution_summary()
        
        assert summary["total_steps"] == 3
        assert summary["completed"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == 2/3
        assert summary["total_execution_time"] == 1.7
        assert summary["average_confidence"] == (0.9 + 0.8 + 0.0) / 3
        
        # Check step details
        assert "step_details" in summary
        assert len(summary["step_details"]) == 3


class TestExecutionResult:
    """Test suite for ExecutionResult class"""
    
    def test_result_creation(self):
        """Test execution result creation"""
        result = ExecutionResult(
            step_id="test_step",
            status=ExecutionStatus.COMPLETED,
            output="test_output",
            execution_time=1.5,
            confidence_score=0.95,
            metadata={"tool_name": "test_tool"}
        )
        
        assert result.step_id == "test_step"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output == "test_output"
        assert result.execution_time == 1.5
        assert result.confidence_score == 0.95
        assert result.metadata["tool_name"] == "test_tool"
        assert result.error is None
        assert result.timestamp > 0
    
    def test_failure_result(self):
        """Test failure result creation"""
        result = ExecutionResult(
            step_id="failed_step",
            status=ExecutionStatus.FAILED,
            error="Execution failed",
            execution_time=0.5
        )
        
        assert result.step_id == "failed_step"
        assert result.status == ExecutionStatus.FAILED
        assert result.error == "Execution failed"
        assert result.output is None
        assert result.confidence_score == 1.0  # Default value


class TestConditionType:
    """Test suite for ConditionType enum"""
    
    def test_condition_values(self):
        """Test condition type values"""
        assert ConditionType.ALWAYS.value == "always"
        assert ConditionType.ON_SUCCESS.value == "on_success"
        assert ConditionType.ON_FAILURE.value == "on_failure"
        assert ConditionType.CUSTOM.value == "custom"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])