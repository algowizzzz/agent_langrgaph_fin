"""
Memory management system for conversation history and long-term storage.
Implements 3-tier memory: short-term (10 messages), rolling summaries, and long-term search.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
from pathlib import Path

class ConversationMemory:
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # File paths
        self.short_term_file = self.memory_dir / "short_term.json"
        self.rolling_summaries_file = self.memory_dir / "rolling_summaries.json"
        self.search_index_file = self.memory_dir / "search_index.json"
        self.conversations_dir = self.memory_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize memory files with empty structures."""
        if not self.short_term_file.exists():
            self._save_json(self.short_term_file, {"messages": [], "count": 0})
        
        if not self.rolling_summaries_file.exists():
            self._save_json(self.rolling_summaries_file, {"summaries": []})
        
        if not self.search_index_file.exists():
            self._save_json(self.search_index_file, {"topics": {}, "conversations": {}})
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def add_message(self, role: str, content: str, session_id: str = None) -> Dict[str, Any]:
        """Add a message to short-term memory."""
        timestamp = datetime.now().isoformat()
        
        # Ensure content is a string and handle any type conversion
        if not isinstance(content, str):
            content = str(content)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "session_id": session_id or "default"
        }
        
        # Load current short-term memory
        short_term = self._load_json(self.short_term_file)
        short_term["messages"].append(message)
        short_term["count"] = len(short_term["messages"])
        
        # Check if we need to create a summary (>10 messages)
        if short_term["count"] > 10:
            await self._create_rolling_summary(short_term["messages"])
            # Keep only the last 5 messages and add the new one
            short_term["messages"] = short_term["messages"][-5:] + [message]
            short_term["count"] = len(short_term["messages"])
        
        # Save updated short-term memory
        self._save_json(self.short_term_file, short_term)
        
        return {"status": "success", "message_added": message, "short_term_count": short_term["count"]}
    
    async def _create_rolling_summary(self, messages: List[Dict]) -> str:
        """Create a summary of messages and store in rolling summaries."""
        # For now, create a simple summary (in production, use LLM)
        summary_id = f"sum_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract key information
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        
        summary_content = f"Conversation with {len(user_messages)} user queries and {len(assistant_messages)} assistant responses. "
        
        # Enhanced business term extraction
        all_text = " ".join([m["content"] for m in messages]).lower()
        
        # Business-focused term detection
        business_terms = {
            "risk_factors": ["risk factors", "risk factor", "risks", "risk management"],
            "regulatory": ["regulatory", "regulation", "regulations", "regulatory landscape", "regulatory requirements"],
            "compliance": ["compliance", "compliant", "comply", "compliance requirements"],
            "wrong_way_risk": ["wrong-way risk", "wrong way risk", "wwr", "wrong-way", "wrong way"],
            "capital": ["capital", "capital requirements", "capital ratio", "capital adequacy"],
            "audit": ["audit", "auditing", "audits", "audit requirements"],
            "governance": ["governance", "oversight", "review board", "internal review"],
            "document_analysis": ["document", "analysis", "analyze", "summarize", "summary"],
            "search_queries": ["search", "find", "mention", "query", "look for"],
            "basel": ["basel", "basel iii", "basel 3", "international banking"],
            "financial": ["financial", "banking", "institution", "bank"],
            "reporting": ["reporting", "report", "reports", "submission"]
        }
        
        # Extract matching business terms
        topics = []
        for category, terms in business_terms.items():
            if any(term in all_text for term in terms):
                topics.append(category)
        
        summary_content += f"Key topics: {', '.join(topics[:5])}"
        
        summary = {
            "summary_id": summary_id,
            "content": summary_content,
            "original_message_count": len(messages),
            "timespan": f"{messages[0]['timestamp']} - {messages[-1]['timestamp']}",
            "topics": topics[:5],
            "created_at": datetime.now().isoformat()
        }
        
        # Save to rolling summaries
        rolling_summaries = self._load_json(self.rolling_summaries_file)
        rolling_summaries["summaries"].append(summary)
        
        # Keep only last 10 summaries
        rolling_summaries["summaries"] = rolling_summaries["summaries"][-10:]
        self._save_json(self.rolling_summaries_file, rolling_summaries)
        
        # Archive full conversation to long-term storage
        await self._archive_conversation(messages, summary)
        
        return summary_content
    
    async def _archive_conversation(self, messages: List[Dict], summary: Dict):
        """Archive conversation to long-term storage."""
        # Create date-based directory
        date_str = datetime.now().strftime('%Y-%m-%d')
        date_dir = self.conversations_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # Save conversation
        conv_id = f"conv_{uuid.uuid4().hex[:8]}"
        conversation = {
            "id": conv_id,
            "messages": messages,
            "summary": summary,
            "created_at": datetime.now().isoformat()
        }
        
        conv_file = date_dir / f"{conv_id}.json"
        self._save_json(conv_file, conversation)
        
        # Update search index
        await self._update_search_index(conv_id, summary["topics"], summary["content"])
        
        return conv_id
    
    async def _update_search_index(self, conv_id: str, topics: List[str], summary: str):
        """Update search index with new conversation."""
        search_index = self._load_json(self.search_index_file)
        
        # Add topics
        for topic in topics:
            if topic not in search_index["topics"]:
                search_index["topics"][topic] = []
            search_index["topics"][topic].append(conv_id)
        
        # Add conversation summary for full-text search
        search_index["conversations"][conv_id] = {
            "summary": summary,
            "topics": topics,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_json(self.search_index_file, search_index)
    
    async def get_context(self, query: str = None) -> Dict[str, Any]:
        """Get conversation context for the agent."""
        # Get short-term memory (recent messages)
        short_term = self._load_json(self.short_term_file)
        
        # Get rolling summaries (medium-term context)
        rolling_summaries = self._load_json(self.rolling_summaries_file)
        recent_summaries = rolling_summaries.get("summaries", [])[-3:]  # Last 3 summaries
        
        # Search long-term memory if query provided
        relevant_history = []
        if query:
            relevant_history = await self.search_long_term(query)
        
        return {
            "short_term": short_term["messages"],
            "recent_summaries": recent_summaries,
            "relevant_history": relevant_history,
            "context_summary": f"Short-term: {len(short_term['messages'])} messages, Recent summaries: {len(recent_summaries)}, Relevant history: {len(relevant_history)}"
        }
    
    async def search_long_term(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search long-term memory for relevant conversations."""
        search_index = self._load_json(self.search_index_file)
        
        results = []
        query_lower = query.lower()
        
        # Search by topics
        for topic, conv_ids in search_index.get("topics", {}).items():
            if topic.lower() in query_lower:
                for conv_id in conv_ids[-max_results:]:  # Recent conversations first
                    if conv_id in search_index.get("conversations", {}):
                        conv_summary = search_index["conversations"][conv_id]
                        results.append({
                            "conversation_id": conv_id,
                            "relevance_reason": f"Topic match: {topic}",
                            "summary": conv_summary["summary"],
                            "created_at": conv_summary["created_at"]
                        })
        
        # Search by content
        for conv_id, conv_data in search_index.get("conversations", {}).items():
            if query_lower in conv_data["summary"].lower():
                if not any(r["conversation_id"] == conv_id for r in results):  # Avoid duplicates
                    results.append({
                        "conversation_id": conv_id,
                        "relevance_reason": "Content match",
                        "summary": conv_data["summary"],
                        "created_at": conv_data["created_at"]
                    })
        
        # Sort by creation date (most recent first) and limit results
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results[:max_results]
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        short_term = self._load_json(self.short_term_file)
        rolling_summaries = self._load_json(self.rolling_summaries_file)
        search_index = self._load_json(self.search_index_file)
        
        # Count conversation files
        total_conversations = 0
        for date_dir in self.conversations_dir.iterdir():
            if date_dir.is_dir():
                total_conversations += len(list(date_dir.glob("*.json")))
        
        return {
            "short_term_messages": len(short_term.get("messages", [])),
            "rolling_summaries": len(rolling_summaries.get("summaries", [])),
            "total_conversations": total_conversations,
            "indexed_topics": len(search_index.get("topics", {})),
            "storage_location": str(self.memory_dir.absolute()),
            "files": {
                "short_term": str(self.short_term_file),
                "rolling_summaries": str(self.rolling_summaries_file),
                "search_index": str(self.search_index_file),
                "conversations_dir": str(self.conversations_dir)
            }
        }

# Global memory instance - lazy loaded to avoid slow imports
_conversation_memory = None

def get_conversation_memory():
    """Get the global conversation memory instance, creating it if needed."""
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory

# Module-level access that uses lazy loading
class _MemoryProxy:
    def __getattr__(self, name):
        return getattr(get_conversation_memory(), name)
    
    async def add_message(self, *args, **kwargs):
        return await get_conversation_memory().add_message(*args, **kwargs)
    
    async def get_context(self, *args, **kwargs):
        return await get_conversation_memory().get_context(*args, **kwargs)
        
    async def search_long_term(self, *args, **kwargs):
        return await get_conversation_memory().search_long_term(*args, **kwargs)
        
    async def get_memory_stats(self, *args, **kwargs):
        return await get_conversation_memory().get_memory_stats(*args, **kwargs)

conversation_memory = _MemoryProxy()

# Tool functions for orchestrator
async def add_conversation_message(role: str, content: str, session_id: str = None) -> Dict[str, Any]:
    """Add a message to conversation memory."""
    return await conversation_memory.add_message(role, content, session_id)

async def get_conversation_context(query: str = None) -> Dict[str, Any]:
    """Get conversation context for the agent."""
    return await conversation_memory.get_context(query)

async def search_conversation_history(query: str) -> List[Dict]:
    """Search long-term conversation history."""
    return await conversation_memory.search_long_term(query)

async def get_memory_statistics() -> Dict[str, Any]:
    """Get memory system statistics."""
    return await conversation_memory.get_memory_stats()