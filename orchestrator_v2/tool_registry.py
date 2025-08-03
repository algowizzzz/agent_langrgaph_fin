"""
Tool Registry System for Orchestrator 2.0

This module provides a comprehensive tool introspection and registration system
that enables dynamic discovery of tool capabilities, input validation, and 
dependency management.
"""

import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, get_type_hints
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ToolReliability(Enum):
    """Tool reliability scoring for confidence calculations."""
    HIGH = 0.95
    MEDIUM = 0.80
    LOW = 0.60
    EXPERIMENTAL = 0.40


@dataclass
class ToolParameter:
    """Represents a tool parameter with validation and metadata."""
    name: str
    param_type: type
    required: bool = True
    default_value: Any = None
    description: str = ""
    validation_rules: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate parameter value against type and rules."""
        try:
            # Type validation
            if value is None and not self.required:
                return True, ""
            
            if value is None and self.required:
                return False, f"Required parameter '{self.name}' is missing"
            
            # Custom validation rules (before type conversion)
            for rule in self.validation_rules:
                if not self._validate_rule(value, rule):
                    return False, f"Parameter '{self.name}' failed validation: {rule}"
            
            # Basic type checking
            if hasattr(self.param_type, '__origin__'):
                # Handle generic types like list[str]
                if not isinstance(value, self.param_type.__origin__):
                    return False, f"Parameter '{self.name}' must be {self.param_type}, got {type(value).__name__}"
            elif not isinstance(value, self.param_type):
                # Try type conversion for common cases
                if self.param_type == str and not isinstance(value, str):
                    value = str(value)
                elif self.param_type == int and isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError:
                        return False, f"Parameter '{self.name}' must be {self.param_type.__name__}"
                else:
                    return False, f"Parameter '{self.name}' must be {self.param_type.__name__}, got {type(value).__name__}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error for '{self.name}': {str(e)}"
    
    def _validate_rule(self, value: Any, rule: str) -> bool:
        """Apply custom validation rule."""
        try:
            # Simple rule parsing - can be extended
            if rule.startswith("min_length:"):
                min_len = int(rule.split(":")[1])
                return len(value) >= min_len
            elif rule.startswith("max_length:"):
                max_len = int(rule.split(":")[1])
                return len(value) <= max_len
            elif rule.startswith("min_value:"):
                min_val = float(rule.split(":")[1])
                return value >= min_val
            elif rule.startswith("max_value:"):
                max_val = float(rule.split(":")[1])
                return value <= max_val
            elif rule == "non_empty":
                if value is None:
                    return False
                if isinstance(value, str):
                    return len(value) > 0
                if isinstance(value, (list, dict, tuple)):
                    return len(value) > 0
                return bool(value)
            
            return True
        except:
            return False


@dataclass
class ParameterValidationResult:
    """Result of parameter validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ToolMetadata:
    """Comprehensive tool metadata for introspection."""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, ToolParameter]
    return_type: type
    category: str = "general"
    reliability: ToolReliability = ToolReliability.MEDIUM
    estimated_duration: float = 1.0  # seconds
    requires_async: bool = False
    postconditions: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    
    def validate_inputs(self, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate all input parameters."""
        errors = []
        
        # Check required parameters
        for param_name, param_def in self.parameters.items():
            if param_def.required and param_name not in params:
                errors.append(f"Missing required parameter: {param_name}")
                continue
            
            if param_name in params:
                is_valid, error_msg = param_def.validate(params[param_name])
                if not is_valid:
                    errors.append(error_msg)
        
        # Check for unexpected parameters
        for param_name in params:
            if param_name not in self.parameters:
                logger.warning(f"Unexpected parameter '{param_name}' for tool '{self.name}'")
        
        return len(errors) == 0, errors
    
    def get_confidence_score(self) -> float:
        """Calculate confidence score for this tool."""
        return self.reliability.value


class ToolRegistry:
    """Central registry for all available tools with introspection capabilities."""
    
    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._categories: Dict[str, List[str]] = {}
        
    def register_tool(self, tool_metadata: ToolMetadata) -> None:
        """Register a tool with metadata."""
        self._tools[tool_metadata.name] = tool_metadata
        
        # Update category index
        category = tool_metadata.category
        if category not in self._categories:
            self._categories[category] = []
        if tool_metadata.name not in self._categories[category]:
            self._categories[category].append(tool_metadata.name)
            
        logger.info(f"Registered tool: {tool_metadata.name} (category: {category})")
    
    def register_function(self, 
                         name: str,
                         func: Callable,
                         description: str = "",
                         category: str = "general",
                         reliability: ToolReliability = ToolReliability.MEDIUM,
                         **kwargs) -> None:
        """Register a function with automatic introspection."""
        
        # Extract parameter information from function signature
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        parameters = {}
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls']:  # Skip self/cls parameters
                continue
            
            # Skip *args and **kwargs parameters
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
                
            param_type = type_hints.get(param_name, Any)
            if isinstance(param.default, bool):
                param_type = bool
            required = param.default == inspect.Parameter.empty
            default_value = None if required else param.default
            
            parameters[param_name] = ToolParameter(
                name=param_name,
                param_type=param_type,
                required=required,
                default_value=default_value,
                description=kwargs.get(f"{param_name}_description", "")
            )
        
        # Get return type
        return_type = type_hints.get('return', Any)
        
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        tool_metadata = ToolMetadata(
            name=name,
            function=func,
            description=description,
            parameters=parameters,
            return_type=return_type,
            category=category,
            reliability=reliability,
            requires_async=is_async,
            **{k: v for k, v in kwargs.items() if not k.endswith('_description')}
        )
        
        self.register_tool(tool_metadata)
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[ToolMetadata]:
        """Get all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]
    
    def find_tools_for_task(self, query: str, context: Dict[str, Any] = None) -> List[str]:
        """Find relevant tools for a given task/query."""
        query_lower = query.lower()
        relevant_tools = []
        
        for tool_name, tool_meta in self._tools.items():
            # Simple relevance scoring based on keywords
            relevance_score = 0
            
            # Check tool name
            if any(word in tool_name.lower() for word in query_lower.split()):
                relevance_score += 2
            
            # Check description
            if any(word in tool_meta.description.lower() for word in query_lower.split()):
                relevance_score += 1
            
            # Check category relevance
            category_keywords = {
                'document': ['document', 'pdf', 'text', 'file'],
                'search': ['search', 'find', 'lookup'],
                'analysis': ['analyze', 'metrics', 'statistics'],
                'synthesis': ['summarize', 'combine', 'synthesize'],
                'visualization': ['chart', 'plot', 'visual', 'graph']
            }
            
            for category, keywords in category_keywords.items():
                if tool_meta.category == category and any(kw in query_lower for kw in keywords):
                    relevance_score += 1
            
            if relevance_score > 0:
                relevant_tools.append((tool_name, relevance_score))
        
        # Sort by relevance score
        relevant_tools.sort(key=lambda x: x[1], reverse=True)
        return [tool_name for tool_name, _ in relevant_tools]
    
    def validate_tool_chain(self, tool_chain: List[str]) -> tuple[bool, List[str]]:
        """Validate that a chain of tools can work together."""
        errors = []
        
        for i, tool_name in enumerate(tool_chain):
            if tool_name not in self._tools:
                errors.append(f"Unknown tool: {tool_name}")
                continue
            
            tool_meta = self._tools[tool_name]
            
            # Check preconditions for tools after the first
            if i > 0:
                for precondition in tool_meta.preconditions:
                    # Simple precondition checking - can be enhanced
                    if "requires_previous_output" in precondition:
                        prev_tool = self._tools.get(tool_chain[i-1])
                        if not prev_tool:
                            errors.append(f"Tool {tool_name} requires previous output but previous tool not found")
        
        return len(errors) == 0, errors
    
    def get_tool_suggestions(self, failed_tool: str, context: Dict[str, Any] = None) -> List[str]:
        """Get alternative tool suggestions when a tool fails."""
        if failed_tool not in self._tools:
            return []
        
        failed_tool_meta = self._tools[failed_tool]
        suggestions = []
        
        # Find tools in the same category
        for tool_name in self._categories.get(failed_tool_meta.category, []):
            if tool_name != failed_tool:
                suggestions.append(tool_name)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry."""
        return {
            "total_tools": len(self._tools),
            "categories": dict(self._categories),
            "reliability_distribution": {
                rel.name: len([t for t in self._tools.values() if t.reliability == rel])
                for rel in ToolReliability
            },
            "async_tools": len([t for t in self._tools.values() if t.requires_async])
        }
    
    def validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> 'ParameterValidationResult':
        """Validate parameters for a specific tool."""
        if tool_name not in self._tools:
            return ParameterValidationResult(
                is_valid=False,
                errors=[f"Unknown tool: {tool_name}"],
                warnings=[],
                suggestions=[]
            )
        
        tool_meta = self._tools[tool_name]
        is_valid, errors = tool_meta.validate_inputs(parameters)
        
        return ParameterValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=[],
            suggestions=[]
        )
    
    def export_tool_definitions(self) -> Dict[str, Any]:
        """Export tool definitions for LLM prompts."""
        tool_definitions = {}
        
        for tool_name, tool_meta in self._tools.items():
            params_info = {}
            for param_name, param in tool_meta.parameters.items():
                params_info[param_name] = {
                    "type": param.param_type.__name__,
                    "required": param.required,
                    "description": param.description,
                    "default": param.default_value
                }
            
            tool_definitions[tool_name] = {
                "description": tool_meta.description,
                "parameters": params_info,
                "category": tool_meta.category,
                "reliability": tool_meta.reliability.name,
                "estimated_duration": tool_meta.estimated_duration
            }
        
        return tool_definitions


# Global tool registry instance
global_tool_registry = ToolRegistry()


def register_tool(name: str = None, 
                 category: str = "general",
                 reliability: ToolReliability = ToolReliability.MEDIUM,
                 **kwargs):
    """Decorator for registering tools automatically."""
    def decorator(func):
        tool_name = name or func.__name__
        global_tool_registry.register_function(
            name=tool_name,
            func=func,
            category=category,
            reliability=reliability,
            **kwargs
        )
        return func
    return decorator
