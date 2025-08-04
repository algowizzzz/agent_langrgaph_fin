"""
Unit tests for Tool Registry System

Tests the tool introspection, registration, and validation capabilities
of the Orchestrator 2.0 tool registry system.
"""

import pytest
import tempfile
import os
from typing import List, Dict, Any

from orchestrator_v2.tool_registry import (
    ToolRegistry, ToolMetadata, ToolParameter, ToolReliability,
    register_tool, global_tool_registry
)


class TestToolRegistry:
    """Test suite for the ToolRegistry class"""
    
    def setup_method(self):
        """Setup fresh registry for each test"""
        self.registry = ToolRegistry()
    
    def test_tool_registration_basic(self):
        """Test basic tool registration functionality"""
        def sample_function(param1: str, param2: int = 10) -> str:
            return f"Result: {param1}, {param2}"
        
        self.registry.register_function(
            name="test_tool",
            func=sample_function,
            description="A test tool",
            category="test",
            reliability=ToolReliability.HIGH
        )
        
        # Verify registration
        assert "test_tool" in self.registry._tools
        tool_meta = self.registry.get_tool("test_tool")
        
        assert tool_meta.name == "test_tool"
        assert tool_meta.description == "A test tool"
        assert tool_meta.category == "test"
        assert tool_meta.reliability == ToolReliability.HIGH
        assert len(tool_meta.parameters) == 2
    
    def test_parameter_introspection(self):
        """Test automatic parameter introspection"""
        def complex_function(
            required_str: str,
            optional_int: int = 42,
            optional_list: List[str] = None,
            optional_dict: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            return {}
        
        self.registry.register_function(
            name="complex_tool",
            func=complex_function,
            description="Complex function with various parameter types"
        )
        
        tool_meta = self.registry.get_tool("complex_tool")
        params = tool_meta.parameters
        
        # Check required parameter
        assert "required_str" in params
        assert params["required_str"].required == True
        assert params["required_str"].param_type == str
        
        # Check optional parameters
        assert "optional_int" in params
        assert params["optional_int"].required == False
        assert params["optional_int"].default_value == 42
        
        assert "optional_list" in params
        assert params["optional_list"].required == False
        assert params["optional_list"].default_value is None
    
    def test_parameter_validation_success(self):
        """Test successful parameter validation"""
        def test_function(name: str, age: int = 25, active: bool = True) -> str:
            return f"{name} is {age} years old"
        
        self.registry.register_function("test_func", test_function)
        tool_meta = self.registry.get_tool("test_func")
        
        # Valid parameters
        valid_params = {"name": "John", "age": 30, "active": False}
        is_valid, errors = tool_meta.validate_inputs(valid_params)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_parameter_validation_failures(self):
        """Test parameter validation error cases"""
        def test_function(name: str, age: int) -> str:
            return f"{name} is {age}"
        
        self.registry.register_function("test_func", test_function)
        tool_meta = self.registry.get_tool("test_func")
        
        # Missing required parameter
        invalid_params1 = {"name": "John"}  # Missing 'age'
        is_valid, errors = tool_meta.validate_inputs(invalid_params1)
        assert is_valid == False
        assert len(errors) > 0
        assert "missing required parameter" in errors[0].lower()
        
        # Wrong parameter type
        invalid_params2 = {"name": "John", "age": "thirty"}  # age should be int
        is_valid, errors = tool_meta.validate_inputs(invalid_params2)
        assert is_valid == False
        assert len(errors) > 0
    
    def test_tool_categories(self):
        """Test tool categorization"""
        def doc_tool() -> str:
            return "document"
        
        def search_tool() -> str:
            return "search"
        
        self.registry.register_function("doc_tool", doc_tool, category="document")
        self.registry.register_function("search_tool", search_tool, category="search")
        
        # Test category retrieval
        doc_tools = self.registry.get_tools_by_category("document")
        search_tools = self.registry.get_tools_by_category("search")
        
        assert len(doc_tools) == 1
        assert len(search_tools) == 1
        assert doc_tools[0].name == "doc_tool"
        assert search_tools[0].name == "search_tool"
    
    def test_tool_suggestions(self):
        """Test tool suggestion system"""
        def search_docs() -> str:
            return "search"
        
        def search_multi() -> str:
            return "multi-search"
        
        def analyze_text() -> str:
            return "analysis"
        
        # Register tools in same category
        self.registry.register_function("search_docs", search_docs, category="search")
        self.registry.register_function("search_multi", search_multi, category="search")
        self.registry.register_function("analyze_text", analyze_text, category="analysis")
        
        # Test suggestions for search category tool
        suggestions = self.registry.get_tool_suggestions("search_docs")
        
        assert isinstance(suggestions, list)
        assert "search_multi" in suggestions
        assert "analyze_text" not in suggestions  # Different category
    
    def test_find_tools_for_task(self):
        """Test intelligent tool finding based on query"""
        def search_documents(query: str) -> List[str]:
            return []
        
        def analyze_sentiment(text: str) -> Dict[str, float]:
            return {}
        
        def create_chart(data: Dict) -> str:
            return "chart"
        
        self.registry.register_function(
            "search_documents", search_documents, 
            description="Search through uploaded documents", 
            category="search"
        )
        self.registry.register_function(
            "analyze_sentiment", analyze_sentiment,
            description="Analyze text sentiment and emotions",
            category="analysis"
        )
        self.registry.register_function(
            "create_chart", create_chart,
            description="Create visual charts and graphs",
            category="visualization"
        )
        
        # Test query-based tool finding
        search_query = "find documents about budget"
        relevant_tools = self.registry.find_tools_for_task(search_query)
        
        assert "search_documents" in relevant_tools
        
        analysis_query = "analyze the sentiment of this text"
        relevant_tools = self.registry.find_tools_for_task(analysis_query)
        
        assert "analyze_sentiment" in relevant_tools
    
    def test_tool_chain_validation(self):
        """Test validation of tool chains"""
        def step1_tool() -> str:
            return "step1"
        
        def step2_tool() -> str:
            return "step2"
        
        def step3_tool() -> str:
            return "step3"
        
        self.registry.register_function("step1_tool", step1_tool)
        self.registry.register_function("step2_tool", step2_tool) 
        self.registry.register_function("step3_tool", step3_tool)
        
        # Valid tool chain
        valid_chain = ["step1_tool", "step2_tool", "step3_tool"]
        is_valid, errors = self.registry.validate_tool_chain(valid_chain)
        
        assert is_valid == True
        assert len(errors) == 0
        
        # Invalid tool chain (unknown tool)
        invalid_chain = ["step1_tool", "unknown_tool", "step3_tool"]
        is_valid, errors = self.registry.validate_tool_chain(invalid_chain)
        
        assert is_valid == False
        assert len(errors) > 0
        assert "unknown tool" in errors[0].lower()
    
    def test_registry_stats(self):
        """Test registry statistics generation"""
        def tool1() -> str:
            return "1"
        
        def tool2() -> str:
            return "2"
        
        self.registry.register_function("tool1", tool1, reliability=ToolReliability.HIGH, category="cat1")
        self.registry.register_function("tool2", tool2, reliability=ToolReliability.MEDIUM, category="cat2")
        
        stats = self.registry.get_registry_stats()
        
        assert stats["total_tools"] == 2
        assert "cat1" in stats["categories"]
        assert "cat2" in stats["categories"]
        assert stats["reliability_distribution"]["HIGH"] == 1
        assert stats["reliability_distribution"]["MEDIUM"] == 1
    
    def test_export_tool_definitions(self):
        """Test exporting tool definitions for LLM prompts"""
        def example_tool(text: str, max_words: int = 100) -> Dict[str, Any]:
            return {"summary": text[:max_words]}
        
        self.registry.register_function(
            "example_tool", 
            example_tool,
            description="Example tool for testing",
            category="example"
        )
        
        definitions = self.registry.export_tool_definitions()
        
        assert "example_tool" in definitions
        tool_def = definitions["example_tool"]
        
        assert "description" in tool_def
        assert "parameters" in tool_def
        assert "category" in tool_def
        assert "reliability" in tool_def
        
        params = tool_def["parameters"]
        assert "text" in params
        assert params["text"]["required"] == True
        assert "max_words" in params
        assert params["max_words"]["required"] == False
        assert params["max_words"]["default"] == 100


class TestToolParameter:
    """Test suite for ToolParameter class"""
    
    def test_parameter_creation(self):
        """Test parameter creation with various options"""
        param = ToolParameter(
            name="test_param",
            param_type=str,
            required=True,
            description="A test parameter",
            validation_rules=["min_length:3", "max_length:50"]
        )
        
        assert param.name == "test_param"
        assert param.param_type == str
        assert param.required == True
        assert param.description == "A test parameter"
        assert len(param.validation_rules) == 2
    
    def test_parameter_validation_rules(self):
        """Test custom validation rules"""
        param = ToolParameter(
            name="length_param",
            param_type=str,
            validation_rules=["min_length:5", "max_length:10"]
        )
        
        # Valid value
        is_valid, error = param.validate("hello")
        assert is_valid == True
        assert error == ""
        
        # Too short
        is_valid, error = param.validate("hi")
        assert is_valid == False
        assert "min_length" in error
        
        # Too long
        is_valid, error = param.validate("this is too long")
        assert is_valid == False
        assert "max_length" in error
    
    def test_numeric_validation_rules(self):
        """Test numeric validation rules"""
        param = ToolParameter(
            name="numeric_param",
            param_type=int,
            validation_rules=["min_value:1", "max_value:100"]
        )
        
        # Valid value
        is_valid, error = param.validate(50)
        assert is_valid == True
        
        # Too small
        is_valid, error = param.validate(0)
        assert is_valid == False
        assert "min_value" in error
        
        # Too large
        is_valid, error = param.validate(150)
        assert is_valid == False
        assert "max_value" in error
    
    def test_non_empty_validation(self):
        """Test non-empty validation rule"""
        param = ToolParameter(
            name="non_empty_param",
            param_type=str,
            validation_rules=["non_empty"]
        )
        
        # Valid non-empty value
        is_valid, error = param.validate("content")
        assert is_valid == True
        
        # Invalid empty values
        for empty_value in ["", None, []]:
            is_valid, error = param.validate(empty_value)
            assert is_valid == False
            assert "non_empty" in error


class TestDecoratorRegistration:
    """Test suite for decorator-based tool registration"""
    
    def test_register_tool_decorator(self):
        """Test @register_tool decorator"""
        # Clear global registry for clean test
        global_tool_registry._tools.clear()
        global_tool_registry._categories.clear()
        
        @register_tool(name="decorated_tool", category="test", reliability=ToolReliability.HIGH)
        def decorated_function(input_text: str) -> str:
            return f"Processed: {input_text}"
        
        # Verify registration
        assert "decorated_tool" in global_tool_registry._tools
        tool_meta = global_tool_registry.get_tool("decorated_tool")
        
        assert tool_meta.name == "decorated_tool"
        assert tool_meta.category == "test"
        assert tool_meta.reliability == ToolReliability.HIGH
        assert callable(tool_meta.function)
    
    def test_decorator_with_defaults(self):
        """Test decorator with default values"""
        global_tool_registry._tools.clear()
        
        @register_tool()
        def simple_function() -> str:
            return "simple"
        
        # Should use function name as tool name
        assert "simple_function" in global_tool_registry._tools
        tool_meta = global_tool_registry.get_tool("simple_function")
        
        assert tool_meta.category == "general"  # Default category
        assert tool_meta.reliability == ToolReliability.MEDIUM  # Default reliability


class TestToolReliability:
    """Test suite for ToolReliability enum"""
    
    def test_reliability_values(self):
        """Test reliability score values"""
        assert ToolReliability.HIGH.value == 0.95
        assert ToolReliability.MEDIUM.value == 0.80
        assert ToolReliability.LOW.value == 0.60
        assert ToolReliability.EXPERIMENTAL.value == 0.40
    
    def test_confidence_scoring(self):
        """Test confidence score calculation"""
        def high_reliability_tool() -> str:
            return "reliable"
        
        registry = ToolRegistry()
        registry.register_function(
            "reliable_tool", 
            high_reliability_tool,
            reliability=ToolReliability.HIGH
        )
        
        tool_meta = registry.get_tool("reliable_tool")
        confidence = tool_meta.get_confidence_score()
        
        assert confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])