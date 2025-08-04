"""
Unit tests for State Management System

Tests the enhanced state management with multi-scope support,
persistence, and context tracking capabilities.
"""

import pytest
import tempfile
import os
import time
import json
from pathlib import Path

from orchestrator_v2.state_management import (
    StateManager, StateScope, StateEntry, ExecutionContext,
    global_state_manager
)


class TestStateEntry:
    """Test suite for StateEntry class"""
    
    def test_state_entry_creation(self):
        """Test basic state entry creation"""
        entry = StateEntry(
            key="test_key",
            value="test_value",
            scope=StateScope.SESSION,
            metadata={"source": "test"}
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.scope == StateScope.SESSION
        assert entry.metadata["source"] == "test"
        assert entry.version == 1
        assert entry.timestamp > 0
        assert entry.expires_at is None
    
    def test_state_entry_expiration(self):
        """Test state entry expiration"""
        # Create entry that expires immediately
        entry = StateEntry(
            key="temp_key",
            value="temp_value",
            scope=StateScope.STEP,
            expires_at=time.time() - 1  # Already expired
        )
        
        assert entry.is_expired() == True
        
        # Create entry that expires in future
        entry = StateEntry(
            key="future_key",
            value="future_value",
            scope=StateScope.STEP,
            expires_at=time.time() + 3600  # Expires in 1 hour
        )
        
        assert entry.is_expired() == False
    
    def test_state_entry_serialization(self):
        """Test state entry serialization"""
        entry = StateEntry(
            key="serialization_test",
            value={"nested": {"data": "value"}},
            scope=StateScope.GLOBAL,
            metadata={"version": "1.0"}
        )
        
        # Test to_dict
        entry_dict = entry.to_dict()
        
        assert entry_dict["key"] == "serialization_test"
        assert entry_dict["value"] == {"nested": {"data": "value"}}
        assert entry_dict["scope"] == "global"
        assert entry_dict["metadata"]["version"] == "1.0"
        
        # Test from_dict
        reconstructed = StateEntry.from_dict(entry_dict)
        
        assert reconstructed.key == entry.key
        assert reconstructed.value == entry.value
        assert reconstructed.scope == entry.scope
        assert reconstructed.metadata == entry.metadata


class TestExecutionContext:
    """Test suite for ExecutionContext class"""
    
    def test_context_creation(self):
        """Test execution context creation"""
        context = ExecutionContext(
            execution_id="exec_123",
            session_id="session_456",
            user_query="Test query",
            active_documents=["doc1.pdf", "doc2.pdf"]
        )
        
        assert context.execution_id == "exec_123"
        assert context.session_id == "session_456"
        assert context.user_query == "Test query"
        assert context.active_documents == ["doc1.pdf", "doc2.pdf"]
        assert context.start_time > 0
        assert len(context.step_outputs) == 0
        assert len(context.traceability_log) == 0
    
    def test_add_step_output(self):
        """Test adding step output to context"""
        context = ExecutionContext("exec_1", "session_1", "query")
        
        context.add_step_output(
            step_id="step1",
            output="step1_result",
            confidence=0.9,
            metadata={"tool": "test_tool"}
        )
        
        assert context.step_outputs["step1"] == "step1_result"
        assert context.confidence_scores["step1"] == 0.9
        assert context.step_metadata["step1"]["tool"] == "test_tool"
        assert len(context.traceability_log) == 1
        
        trace_entry = context.traceability_log[0]
        assert trace_entry["step_id"] == "step1"
        assert trace_entry["confidence"] == 0.9
        assert trace_entry["output_type"] == "str"
    
    def test_get_step_output(self):
        """Test retrieving step output"""
        context = ExecutionContext("exec_1", "session_1", "query")
        
        # Test with default value
        assert context.get_step_output("nonexistent") is None
        assert context.get_step_output("nonexistent", "default") == "default"
        
        # Add output and test retrieval
        context.add_step_output("step1", {"result": "data"})
        assert context.get_step_output("step1") == {"result": "data"}
    
    def test_overall_confidence(self):
        """Test overall confidence calculation"""
        context = ExecutionContext("exec_1", "session_1", "query")
        
        # No steps - should return 0
        assert context.get_overall_confidence() == 0.0
        
        # Add steps with different confidence scores
        context.add_step_output("step1", "result1", confidence=0.9)
        context.add_step_output("step2", "result2", confidence=0.7)
        context.add_step_output("step3", "result3", confidence=0.8)
        
        expected_avg = (0.9 + 0.7 + 0.8) / 3
        actual_confidence = context.get_overall_confidence()
        assert abs(actual_confidence - expected_avg) < 1e-10, f"Expected {expected_avg}, got {actual_confidence}"
    
    def test_context_serialization(self):
        """Test context serialization"""
        context = ExecutionContext("exec_1", "session_1", "test query")
        context.add_step_output("step1", "result1", confidence=0.8)
        
        context_dict = context.to_dict()
        
        assert context_dict["execution_id"] == "exec_1"
        assert context_dict["session_id"] == "session_1"
        assert context_dict["user_query"] == "test query"
        assert "step_outputs" in context_dict
        assert "confidence_scores" in context_dict
        assert "traceability_log" in context_dict


class TestStateManager:
    """Test suite for StateManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = StateManager(persistence_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_execution_context(self):
        """Test execution context creation"""
        context = self.state_manager.create_execution_context(
            execution_id="exec_123",
            session_id="session_456",
            user_query="Test query",
            active_documents=["doc1.pdf"]
        )
        
        assert context.execution_id == "exec_123"
        assert context.session_id == "session_456"
        assert context.user_query == "Test query"
        assert context.active_documents == ["doc1.pdf"]
        
        # Verify storage in manager
        retrieved = self.state_manager.get_execution_context("exec_123")
        assert retrieved is not None
        assert retrieved.execution_id == "exec_123"
    
    def test_set_and_get_state_global(self):
        """Test global state management"""
        self.state_manager.set_state(
            key="global_config",
            value={"setting": "value"},
            scope=StateScope.GLOBAL
        )
        
        retrieved = self.state_manager.get_state("global_config", StateScope.GLOBAL)
        assert retrieved == {"setting": "value"}
    
    def test_set_and_get_state_session(self):
        """Test session-scoped state management"""
        session_id = "test_session_123"
        
        self.state_manager.set_state(
            key="session_data",
            value="session_value",
            scope=StateScope.SESSION,
            session_id=session_id
        )
        
        # Should retrieve with correct session ID
        retrieved = self.state_manager.get_state(
            "session_data", 
            StateScope.SESSION, 
            session_id=session_id
        )
        assert retrieved == "session_value"
        
        # Should not retrieve with different session ID
        retrieved = self.state_manager.get_state(
            "session_data",
            StateScope.SESSION,
            session_id="different_session"
        )
        assert retrieved is None
    
    def test_set_and_get_state_execution(self):
        """Test execution-scoped state management"""
        execution_id = "exec_789"
        
        self.state_manager.set_state(
            key="exec_data",
            value=["item1", "item2"],
            scope=StateScope.EXECUTION,
            execution_id=execution_id
        )
        
        retrieved = self.state_manager.get_state(
            "exec_data",
            StateScope.EXECUTION,
            execution_id=execution_id
        )
        assert retrieved == ["item1", "item2"]
    
    def test_state_expiration(self):
        """Test automatic state expiration"""
        self.state_manager.set_state(
            key="temp_data",
            value="temporary",
            scope=StateScope.STEP,
            execution_id="exec_1",
            expires_in=0.1  # Expires in 0.1 seconds
        )
        
        # Should exist initially
        assert self.state_manager.has_state("temp_data", StateScope.STEP, execution_id="exec_1")
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be gone after expiration
        assert not self.state_manager.has_state("temp_data", StateScope.STEP, execution_id="exec_1")
    
    def test_state_versioning(self):
        """Test state versioning on updates"""
        key = "versioned_data"
        
        # Set initial value
        self.state_manager.set_state(key, "value1", StateScope.GLOBAL)
        
        # Get the state entry to check version
        scoped_key = self.state_manager._create_scoped_key(key, StateScope.GLOBAL)
        entry1 = self.state_manager._states[StateScope.GLOBAL][scoped_key]
        assert entry1.version == 1
        
        # Update value
        self.state_manager.set_state(key, "value2", StateScope.GLOBAL)
        
        # Check version incremented
        entry2 = self.state_manager._states[StateScope.GLOBAL][scoped_key]
        assert entry2.version == 2
        assert entry2.value == "value2"
    
    def test_delete_state(self):
        """Test state deletion"""
        self.state_manager.set_state("delete_test", "value", StateScope.GLOBAL)
        
        # Verify exists
        assert self.state_manager.has_state("delete_test", StateScope.GLOBAL)
        
        # Delete
        deleted = self.state_manager.delete_state("delete_test", StateScope.GLOBAL)
        assert deleted == True
        
        # Verify gone
        assert not self.state_manager.has_state("delete_test", StateScope.GLOBAL)
        
        # Try to delete non-existent
        deleted = self.state_manager.delete_state("nonexistent", StateScope.GLOBAL)
        assert deleted == False
    
    def test_cleanup_execution(self):
        """Test execution cleanup"""
        execution_id = "cleanup_test_exec"
        
        # Create execution context and states
        context = self.state_manager.create_execution_context(
            execution_id=execution_id,
            session_id="session_1",
            user_query="cleanup test"
        )
        
        self.state_manager.set_state(
            "exec_state", "value", StateScope.EXECUTION, execution_id=execution_id
        )
        
        # Verify exists
        assert self.state_manager.get_execution_context(execution_id) is not None
        assert self.state_manager.has_state("exec_state", StateScope.EXECUTION, execution_id=execution_id)
        
        # Cleanup
        self.state_manager.cleanup_execution(execution_id)
        
        # Verify cleaned up
        assert self.state_manager.get_execution_context(execution_id) is None
        assert not self.state_manager.has_state("exec_state", StateScope.EXECUTION, execution_id=execution_id)
    
    def test_cleanup_session(self):
        """Test session cleanup"""
        session_id = "cleanup_test_session"
        
        # Create session state
        self.state_manager.set_state(
            "session_state", "value", StateScope.SESSION, session_id=session_id
        )
        
        # Verify exists
        assert self.state_manager.has_state("session_state", StateScope.SESSION, session_id=session_id)
        
        # Cleanup
        self.state_manager.cleanup_session(session_id)
        
        # Verify cleaned up
        assert not self.state_manager.has_state("session_state", StateScope.SESSION, session_id=session_id)
    
    def test_cleanup_expired(self):
        """Test expired state cleanup"""
        # Create states with different expiration times
        self.state_manager.set_state("permanent", "value1", StateScope.GLOBAL)
        self.state_manager.set_state(
            "short_lived", "value2", StateScope.GLOBAL, expires_in=0.1
        )
        self.state_manager.set_state(
            "already_expired", "value3", StateScope.GLOBAL, expires_in=-1
        )
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Cleanup expired
        removed_count = self.state_manager.cleanup_expired()
        
        # Should have removed 2 expired states
        assert removed_count == 2
        
        # Permanent state should still exist
        assert self.state_manager.has_state("permanent", StateScope.GLOBAL)
        assert not self.state_manager.has_state("short_lived", StateScope.GLOBAL)
        assert not self.state_manager.has_state("already_expired", StateScope.GLOBAL)
    
    def test_state_summary(self):
        """Test state summary generation"""
        # Add various states
        self.state_manager.set_state("global1", "value1", StateScope.GLOBAL)
        self.state_manager.set_state("global2", "value2", StateScope.GLOBAL)
        self.state_manager.set_state("session1", "value3", StateScope.SESSION, session_id="session1")
        
        context = self.state_manager.create_execution_context("exec1", "session1", "query")
        
        summary = self.state_manager.get_state_summary()
        
        assert summary["total_entries"] >= 3
        assert summary["active_executions"] == 1
        assert "scopes" in summary
        assert "global" in summary["scopes"]
        assert "session" in summary["scopes"]
    
    def test_state_persistence(self):
        """Test state persistence to disk"""
        # Set persistent states
        self.state_manager.set_state("persistent_global", "global_value", StateScope.GLOBAL)
        self.state_manager.set_state("persistent_session", "session_value", StateScope.SESSION, session_id="session1")
        
        # Create new state manager with same persistence directory
        new_manager = StateManager(persistence_dir=self.temp_dir)
        
        # Verify states were loaded
        assert new_manager.get_state("persistent_global", StateScope.GLOBAL) == "global_value"
        assert new_manager.get_state("persistent_session", StateScope.SESSION, session_id="session1") == "session_value"
    
    def test_scoped_key_creation(self):
        """Test scoped key creation"""
        # Global scope - no modification
        global_key = self.state_manager._create_scoped_key("key", StateScope.GLOBAL)
        assert global_key == "key"
        
        # Session scope - append session ID
        session_key = self.state_manager._create_scoped_key("key", StateScope.SESSION, session_id="session123")
        assert session_key == "key:session123"
        
        # Execution scope - append execution ID
        exec_key = self.state_manager._create_scoped_key("key", StateScope.EXECUTION, execution_id="exec456")
        assert exec_key == "key:exec456"
        
        # Step scope - same as execution
        step_key = self.state_manager._create_scoped_key("key", StateScope.STEP, execution_id="exec789")
        assert step_key == "key:exec789"
    
    def test_missing_ids_error(self):
        """Test error handling for missing IDs"""
        # Session scope without session_id should raise error
        with pytest.raises(ValueError, match="session_id required"):
            self.state_manager.set_state("key", "value", StateScope.SESSION)
        
        # Execution scope without execution_id should raise error
        with pytest.raises(ValueError, match="execution_id required"):
            self.state_manager.set_state("key", "value", StateScope.EXECUTION)


class TestStateScope:
    """Test suite for StateScope enum"""
    
    def test_scope_values(self):
        """Test state scope enum values"""
        assert StateScope.GLOBAL.value == "global"
        assert StateScope.SESSION.value == "session"
        assert StateScope.EXECUTION.value == "execution"
        assert StateScope.STEP.value == "step"


class TestGlobalStateManager:
    """Test suite for global state manager instance"""
    
    def test_global_instance_exists(self):
        """Test that global state manager instance exists"""
        assert global_state_manager is not None
        assert isinstance(global_state_manager, StateManager)
    
    def test_global_instance_functionality(self):
        """Test basic functionality of global instance"""
        # This test should be careful not to interfere with other tests
        test_key = "global_test_key_unique"
        
        global_state_manager.set_state(test_key, "test_value", StateScope.GLOBAL)
        
        retrieved = global_state_manager.get_state(test_key, StateScope.GLOBAL)
        assert retrieved == "test_value"
        
        # Cleanup
        global_state_manager.delete_state(test_key, StateScope.GLOBAL)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])