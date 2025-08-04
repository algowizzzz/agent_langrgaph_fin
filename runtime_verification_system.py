#!/usr/bin/env python3
"""
Runtime Verification System for AI Finance & Risk Agent

This system ensures that the correct functions are being called at runtime
and detects any execution pipeline bypasses or function hijacking.
"""

import functools
import inspect
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FunctionCallRecord:
    """Record of a function call for verification."""
    function_name: str
    function_id: str
    module_name: str
    call_id: str
    timestamp: float
    parameters: Dict[str, Any]
    caller_info: str
    execution_time: Optional[float] = None
    result_type: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

class RuntimeVerificationSystem:
    """
    Comprehensive runtime verification system that ensures correct function execution.
    """
    
    def __init__(self):
        self.call_records: List[FunctionCallRecord] = []
        self.verified_functions: Dict[str, str] = {}  # function_name -> function_id
        self.bypass_detections: List[Dict] = []
        
    def register_function(self, func: Callable, name: str = None) -> str:
        """Register a function for verification and return unique function ID."""
        function_name = name or func.__name__
        function_id = f"{function_name}_{id(func)}_{int(time.time())}"
        
        # Store function identity
        self.verified_functions[function_name] = function_id
        
        logger.info(f"🔒 VERIFICATION: Registered function '{function_name}' with ID {function_id}")
        logger.info(f"🔒 VERIFICATION: Function module: {func.__module__}")
        logger.info(f"🔒 VERIFICATION: Function file: {func.__code__.co_filename}")
        logger.info(f"🔒 VERIFICATION: Function line: {func.__code__.co_firstlineno}")
        
        return function_id
    
    def create_verified_wrapper(self, func: Callable, name: str = None) -> Callable:
        """Create a wrapper that verifies function calls and logs execution."""
        function_name = name or func.__name__
        function_id = self.register_function(func, function_name)
        
        @functools.wraps(func)
        async def async_verified_wrapper(*args, **kwargs):
            return await self._execute_with_verification(
                func, function_name, function_id, args, kwargs, is_async=True
            )
        
        @functools.wraps(func)
        def sync_verified_wrapper(*args, **kwargs):
            return self._execute_with_verification(
                func, function_name, function_id, args, kwargs, is_async=False
            )
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_verified_wrapper
        else:
            return sync_verified_wrapper
    
    async def _execute_with_verification(self, func: Callable, function_name: str, 
                                       function_id: str, args: tuple, kwargs: dict, 
                                       is_async: bool) -> Any:
        """Execute function with comprehensive verification and logging."""
        call_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Get caller information
        caller_frame = inspect.currentframe().f_back.f_back
        caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        
        # Create call record
        call_record = FunctionCallRecord(
            function_name=function_name,
            function_id=function_id,
            module_name=func.__module__,
            call_id=call_id,
            timestamp=start_time,
            parameters=dict(kwargs),
            caller_info=caller_info
        )
        
        # Log function call
        print(f"🔒 VERIFICATION ACTIVE: {function_name} called with ID {function_id}")
        print(f"🔒 VERIFICATION: Call ID {call_id}")
        print(f"🔒 VERIFICATION: Parameters: {kwargs}")
        print(f"🔒 VERIFICATION: Caller: {caller_info}")
        
        logger.info(f"🔒 VERIFICATION: Function '{function_name}' called with verified ID {function_id}")
        
        try:
            # Execute the actual function
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record successful execution
            execution_time = time.time() - start_time
            call_record.execution_time = execution_time
            call_record.result_type = type(result).__name__
            call_record.success = True
            
            print(f"✅ VERIFICATION SUCCESS: {function_name} completed in {execution_time:.3f}s")
            logger.info(f"✅ VERIFICATION: Function '{function_name}' completed successfully")
            
            return result
            
        except Exception as e:
            # Record failed execution
            execution_time = time.time() - start_time
            call_record.execution_time = execution_time
            call_record.success = False
            call_record.error = str(e)
            
            print(f"❌ VERIFICATION ERROR: {function_name} failed after {execution_time:.3f}s: {e}")
            logger.error(f"❌ VERIFICATION: Function '{function_name}' failed: {e}")
            
            raise
            
        finally:
            # Always record the call
            self.call_records.append(call_record)
    
    def detect_bypass(self, expected_function: str, actual_result: Any) -> bool:
        """Detect if a function call was bypassed by checking call records."""
        recent_calls = [r for r in self.call_records if r.function_name == expected_function and 
                       time.time() - r.timestamp < 10]  # Last 10 seconds
        
        if not recent_calls:
            # No recent calls detected - possible bypass
            bypass_record = {
                "timestamp": time.time(),
                "expected_function": expected_function,
                "actual_result": str(actual_result)[:200],
                "detection_reason": "No verified function calls in recent history"
            }
            self.bypass_detections.append(bypass_record)
            
            print(f"🚨 BYPASS DETECTED: Function '{expected_function}' expected but no verified calls found!")
            logger.warning(f"🚨 BYPASS DETECTED: Expected '{expected_function}' but no verified calls")
            
            return True
        
        return False
    
    def get_verification_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report."""
        total_calls = len(self.call_records)
        successful_calls = len([r for r in self.call_records if r.success])
        failed_calls = total_calls - successful_calls
        
        # Group calls by function
        function_stats = {}
        for record in self.call_records:
            func_name = record.function_name
            if func_name not in function_stats:
                function_stats[func_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "avg_execution_time": 0,
                    "last_call": None
                }
            
            stats = function_stats[func_name]
            stats["total_calls"] += 1
            if record.success:
                stats["successful_calls"] += 1
            else:
                stats["failed_calls"] += 1
            
            if record.execution_time:
                # Calculate running average
                current_avg = stats["avg_execution_time"]
                new_avg = (current_avg * (stats["total_calls"] - 1) + record.execution_time) / stats["total_calls"]
                stats["avg_execution_time"] = new_avg
            
            stats["last_call"] = record.timestamp
        
        return {
            "verification_active": True,
            "total_function_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "registered_functions": len(self.verified_functions),
            "bypass_detections": len(self.bypass_detections),
            "function_statistics": function_stats,
            "recent_bypasses": self.bypass_detections[-5:],  # Last 5 bypasses
            "verification_timestamp": datetime.now().isoformat()
        }
    
    def verify_function_identity(self, func: Callable, expected_name: str) -> bool:
        """Verify that a function is the correct one we expect."""
        actual_id = f"{expected_name}_{id(func)}_{int(time.time())}"
        expected_id = self.verified_functions.get(expected_name)
        
        if not expected_id:
            logger.warning(f"⚠️ VERIFICATION: No registered ID for function '{expected_name}'")
            return False
        
        # Check function properties
        checks = {
            "module": func.__module__ == "tools.document_tools",
            "name": func.__name__ == expected_name,
            "is_coroutine": inspect.iscoroutinefunction(func)
        }
        
        all_passed = all(checks.values())
        
        print(f"🔍 IDENTITY VERIFICATION for '{expected_name}':")
        print(f"  Module: {func.__module__} ✅" if checks["module"] else f"  Module: {func.__module__} ❌")
        print(f"  Name: {func.__name__} ✅" if checks["name"] else f"  Name: {func.__name__} ❌")
        print(f"  Async: {checks['is_coroutine']} ✅" if checks["is_coroutine"] else f"  Async: {checks['is_coroutine']} ❌")
        print(f"  Overall: {'✅ VERIFIED' if all_passed else '❌ FAILED'}")
        
        return all_passed

# Global verification system instance
verification_system = RuntimeVerificationSystem()

def verify_function(name: str = None):
    """Decorator to add runtime verification to functions."""
    def decorator(func):
        return verification_system.create_verified_wrapper(func, name)
    return decorator

def check_for_bypasses(expected_function: str, result: Any) -> bool:
    """Check if a function call was bypassed."""
    return verification_system.detect_bypass(expected_function, result)

def get_verification_status() -> Dict[str, Any]:
    """Get current verification system status."""
    return verification_system.get_verification_report()