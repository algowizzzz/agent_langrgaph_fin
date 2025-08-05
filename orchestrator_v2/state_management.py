"""
Enhanced State Management for Orchestrator 2.0

This module provides comprehensive state management with context tracking,
versioned outputs, and persistent session memory across executions.
"""

import time
import logging
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum
import threading
from collections import defaultdict
import pickle
import os

logger = logging.getLogger(__name__)


class StateScope(Enum):
    """Scope levels for state management."""
    SESSION = "session"      # Persists across multiple queries in same session
    EXECUTION = "execution"  # Persists for one execution cycle
    STEP = "step"           # Temporary within a single step
    GLOBAL = "global"       # Persists across all sessions


@dataclass
class StateEntry:
    """Represents a single state entry with metadata."""
    key: str
    value: Any
    scope: StateScope
    timestamp: float = field(default_factory=time.time)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if this state entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "metadata": self.metadata,
            "expires_at": self.expires_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateEntry':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            scope=StateScope(data["scope"]),
            timestamp=data["timestamp"],
            version=data["version"],
            metadata=data["metadata"],
            expires_at=data.get("expires_at")
        )


@dataclass
class ExecutionContext:
    """Context for a single execution with step tracking."""
    execution_id: str
    session_id: str
    user_query: str
    start_time: float = field(default_factory=time.time)
    active_documents: List[str] = field(default_factory=list)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    step_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    traceability_log: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def add_step_output(self, step_id: str, output: Any, confidence: float = 1.0, metadata: Dict[str, Any] = None):
        """Add output from a completed step."""
        self.step_outputs[step_id] = output
        self.confidence_scores[step_id] = confidence
        
        if metadata:
            self.step_metadata[step_id] = metadata
        
        # Add to traceability log
        self.traceability_log.append({
            "step_id": step_id,
            "timestamp": time.time(),
            "output_type": type(output).__name__,
            "confidence": confidence,
            "metadata": metadata or {}
        })
    
    def get_step_output(self, step_id: str, default: Any = None) -> Any:
        """Get output from a specific step."""
        return self.step_outputs.get(step_id, default)
    
    def get_overall_confidence(self) -> float:
        """Calculate overall confidence score for the execution."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class StateManager:
    """Comprehensive state management system with multi-scope support."""
    
    def __init__(self, persistence_dir: Optional[str] = None):
        self.persistence_dir = persistence_dir
        self._states: Dict[StateScope, Dict[str, StateEntry]] = {
            scope: {} for scope in StateScope
        }
        self._execution_contexts: Dict[str, ExecutionContext] = {}
        self._session_data: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = threading.RLock()
        
        # Load persisted state if directory provided
        if persistence_dir:
            os.makedirs(persistence_dir, exist_ok=True)
            self._load_persistent_state()
    
    def create_execution_context(self, 
                                execution_id: str,
                                session_id: str,
                                user_query: str,
                                active_documents: List[str] = None) -> ExecutionContext:
        """Create a new execution context."""
        with self._lock:
            context = ExecutionContext(
                execution_id=execution_id,
                session_id=session_id,
                user_query=user_query,
                active_documents=active_documents or []
            )
            self._execution_contexts[execution_id] = context
            return context
    
    def get_execution_context(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get execution context by ID."""
        with self._lock:
            return self._execution_contexts.get(execution_id)
    
    def set_state(self, 
                  key: str, 
                  value: Any, 
                  scope: StateScope = StateScope.EXECUTION,
                  session_id: Optional[str] = None,
                  execution_id: Optional[str] = None,
                  expires_in: Optional[float] = None,
                  metadata: Dict[str, Any] = None) -> None:
        """Set a state value with specified scope."""
        with self._lock:
            # Calculate expiration time
            expires_at = None
            if expires_in:
                expires_at = time.time() + expires_in
            
            # Create scoped key for session/execution scopes
            scoped_key = self._create_scoped_key(key, scope, session_id, execution_id)
            
            # Get or create state entry
            if scoped_key in self._states[scope]:
                entry = self._states[scope][scoped_key]
                entry.value = value
                entry.version += 1
                entry.timestamp = time.time()
                if expires_at:
                    entry.expires_at = expires_at
                if metadata:
                    entry.metadata.update(metadata)
            else:
                entry = StateEntry(
                    key=scoped_key,
                    value=value,
                    scope=scope,
                    expires_at=expires_at,
                    metadata=metadata or {}
                )
                self._states[scope][scoped_key] = entry
            
            logger.debug(f"Set state: {scoped_key} (scope: {scope.value}, version: {entry.version})")
            
            # Persist if needed
            if scope in [StateScope.SESSION, StateScope.GLOBAL] and self.persistence_dir:
                self._persist_state_entry(entry)
    
    def get_state(self, 
                  key: str, 
                  scope: StateScope = StateScope.EXECUTION,
                  session_id: Optional[str] = None,
                  execution_id: Optional[str] = None,
                  default: Any = None) -> Any:
        """Get a state value by key and scope."""
        with self._lock:
            scoped_key = self._create_scoped_key(key, scope, session_id, execution_id)
            
            if scoped_key in self._states[scope]:
                entry = self._states[scope][scoped_key]
                
                # Check if expired
                if entry.is_expired():
                    del self._states[scope][scoped_key]
                    return default
                
                return entry.value
            
            return default
    
    def has_state(self, 
                  key: str, 
                  scope: StateScope = StateScope.EXECUTION,
                  session_id: Optional[str] = None,
                  execution_id: Optional[str] = None) -> bool:
        """Check if a state key exists."""
        with self._lock:
            scoped_key = self._create_scoped_key(key, scope, session_id, execution_id)
            return scoped_key in self._states[scope] and not self._states[scope][scoped_key].is_expired()
    
    def delete_state(self, 
                     key: str, 
                     scope: StateScope = StateScope.EXECUTION,
                     session_id: Optional[str] = None,
                     execution_id: Optional[str] = None) -> bool:
        """Delete a state entry."""
        with self._lock:
            scoped_key = self._create_scoped_key(key, scope, session_id, execution_id)
            
            if scoped_key in self._states[scope]:
                del self._states[scope][scoped_key]
                
                # Remove from persistence if needed
                if scope in [StateScope.SESSION, StateScope.GLOBAL] and self.persistence_dir:
                    self._remove_persistent_state(scoped_key, scope)
                
                return True
            
            return False
    
    def cleanup_execution(self, execution_id: str) -> None:
        """Clean up all execution-scoped state for a specific execution."""
        with self._lock:
            # Remove execution context
            if execution_id in self._execution_contexts:
                del self._execution_contexts[execution_id]
            
            # Remove execution-scoped states
            keys_to_remove = []
            for key in self._states[StateScope.EXECUTION]:
                if key.endswith(f":{execution_id}"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._states[StateScope.EXECUTION][key]
            
            logger.debug(f"Cleaned up execution state for: {execution_id}")
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up all session-scoped state for a specific session."""
        with self._lock:
            # Remove session data
            if session_id in self._session_data:
                del self._session_data[session_id]
            
            # Remove session-scoped states
            keys_to_remove = []
            for key in self._states[StateScope.SESSION]:
                if key.endswith(f":{session_id}"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._states[StateScope.SESSION][key]
                
                # Remove from persistence
                if self.persistence_dir:
                    self._remove_persistent_state(key, StateScope.SESSION)
            
            logger.debug(f"Cleaned up session state for: {session_id}")
    
    def cleanup_expired(self) -> int:
        """Clean up all expired state entries."""
        with self._lock:
            removed_count = 0
            
            for scope in StateScope:
                keys_to_remove = []
                for key, entry in self._states[scope].items():
                    if entry.is_expired():
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self._states[scope][key]
                    removed_count += 1
                    
                    # Remove from persistence if needed
                    if scope in [StateScope.SESSION, StateScope.GLOBAL] and self.persistence_dir:
                        self._remove_persistent_state(key, scope)
            
            logger.debug(f"Cleaned up {removed_count} expired state entries")
            return removed_count
    
    def get_state_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of current state."""
        with self._lock:
            summary = {
                "scopes": {},
                "total_entries": 0,
                "active_executions": len(self._execution_contexts),
                "sessions": len(self._session_data)
            }
            
            for scope in StateScope:
                scope_entries = 0
                scope_size = 0
                
                for key, entry in self._states[scope].items():
                    if not entry.is_expired():
                        # Filter by session if specified
                        if session_id and scope == StateScope.SESSION:
                            if not key.endswith(f":{session_id}"):
                                continue
                        
                        scope_entries += 1
                        try:
                            scope_size += len(str(entry.value))
                        except:
                            scope_size += 1  # Fallback for non-serializable objects
                
                summary["scopes"][scope.value] = {
                    "entries": scope_entries,
                    "estimated_size": scope_size
                }
                summary["total_entries"] += scope_entries
            
            return summary
    
    def get_execution_trace(self, execution_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get execution trace for debugging."""
        context = self.get_execution_context(execution_id)
        if context:
            return context.traceability_log
        return None
    
    def _create_scoped_key(self, 
                          key: str, 
                          scope: StateScope, 
                          session_id: Optional[str] = None,
                          execution_id: Optional[str] = None) -> str:
        """Create a scoped key based on scope type."""
        if scope == StateScope.GLOBAL:
            return key
        elif scope == StateScope.SESSION:
            if not session_id:
                raise ValueError("session_id required for SESSION scope")
            return f"{key}:{session_id}"
        elif scope == StateScope.EXECUTION:
            if not execution_id:
                raise ValueError("execution_id required for EXECUTION scope")
            return f"{key}:{execution_id}"
        elif scope == StateScope.STEP:
            if not execution_id:
                raise ValueError("execution_id required for STEP scope")
            return f"{key}:{execution_id}"
        
        return key
    
    def _load_persistent_state(self) -> None:
        """Load persistent state from disk."""
        try:
            # Load session state
            session_file = os.path.join(self.persistence_dir, "session_state.json")
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    for key, entry_data in session_data.items():
                        entry = StateEntry.from_dict(entry_data)
                        if not entry.is_expired():
                            self._states[StateScope.SESSION][key] = entry
            
            # Load global state
            global_file = os.path.join(self.persistence_dir, "global_state.json")
            if os.path.exists(global_file):
                with open(global_file, 'r') as f:
                    global_data = json.load(f)
                    for key, entry_data in global_data.items():
                        entry = StateEntry.from_dict(entry_data)
                        if not entry.is_expired():
                            self._states[StateScope.GLOBAL][key] = entry
            
            logger.info("Loaded persistent state from disk")
            
        except Exception as e:
            logger.error(f"Error loading persistent state: {e}")
    
    def _persist_state_entry(self, entry: StateEntry) -> None:
        """Persist a single state entry to disk."""
        try:
            if entry.scope == StateScope.SESSION:
                file_path = os.path.join(self.persistence_dir, "session_state.json")
            elif entry.scope == StateScope.GLOBAL:
                file_path = os.path.join(self.persistence_dir, "global_state.json")
            else:
                return  # Don't persist other scopes
            
            # Load existing data
            existing_data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Update with new entry
            existing_data[entry.key] = entry.to_dict()
            
            # Save back to file
            with open(file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error persisting state entry: {e}")
    
    def _remove_persistent_state(self, key: str, scope: StateScope) -> None:
        """Remove a state entry from persistent storage."""
        try:
            if scope == StateScope.SESSION:
                file_path = os.path.join(self.persistence_dir, "session_state.json")
            elif scope == StateScope.GLOBAL:
                file_path = os.path.join(self.persistence_dir, "global_state.json")
            else:
                return
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if key in data:
                    del data[key]
                    
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                        
        except Exception as e:
            logger.error(f"Error removing persistent state: {e}")


# Global state manager instance
global_state_manager = StateManager(persistence_dir="./orchestrator_state")