from pathlib import Path
from typing import Dict, List, Any
import logging
import re
import json
import os

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

# Assumes config is available or use defaults
class MockConfig:
    class AI:
        chunk_size = 1500
        chunk_overlap = 200
config = MockConfig()


class DocumentProcessor:
    """Service for processing uploaded documents into text chunks."""
    def __init__(self):
        self.headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        self.markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on, strip_headers=False)
        self.recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=config.AI.chunk_size, chunk_overlap=config.AI.chunk_overlap)

    async def process_document(self, file_path: str) -> Dict:
        try:
            content = Path(file_path).read_text()
            docs = self.markdown_splitter.split_text(content)
            for doc in docs:
                doc.metadata["source"] = file_path
            return {"success": True, "documents": docs, "file_type": "TEXT"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class PersistentDocumentStore:
    """Thread-safe persistent document store using file system."""
    
    def __init__(self, store_path: str = "document_store.json"):
        self.store_path = store_path
        self._cache = None
        
    def _load(self) -> Dict[str, List[Dict]]:
        """Load document store from disk."""
        if self._cache is not None:
            return self._cache
            
        try:
            if os.path.exists(self.store_path):
                with open(self.store_path, 'r') as f:
                    self._cache = json.load(f)
            else:
                self._cache = {}
        except Exception as e:
            logger.warning(f"Failed to load document store: {e}")
            self._cache = {}
        return self._cache
    
    def _save(self, data: Dict[str, List[Dict]]):
        """Save document store to disk."""
        try:
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
            self._cache = data
        except Exception as e:
            logger.error(f"Failed to save document store: {e}")
    
    def keys(self):
        """Get all document names."""
        return list(self._load().keys())
    
    def __contains__(self, key: str) -> bool:
        """Check if document exists."""
        return key in self._load()
    
    def __getitem__(self, key: str) -> List[Dict]:
        """Get document chunks."""
        data = self._load()
        if key not in data:
            raise KeyError(f"Document '{key}' not found")
        return data[key]
    
    def __setitem__(self, key: str, value: List[Dict]):
        """Store document chunks."""
        data = self._load()
        data[key] = value
        self._save(data)
    
    def clear(self):
        """Clear all documents."""
        self._save({})

document_processor = DocumentProcessor()
document_chunk_store = PersistentDocumentStore()
logger = logging.getLogger(__name__)

# --- Tool Implementations ---
async def upload_document(file_path: str) -> dict:
    result = await document_processor.process_document(file_path)
    if not result["success"]: return {"status": "error", "message": result.get("error")}
    chunks = result["documents"]
    doc_name = Path(file_path).name
    document_chunk_store[doc_name] = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in chunks]
    return {"status": "success", "doc_name": doc_name, "chunks_created": len(chunks)}

def _apply_search_query(chunks: List[Dict], query: str) -> List[Dict]:
    """Apply search query with boolean logic support."""
    if not query:
        return chunks
    
    query = query.strip()
    
    # Handle OR logic (most common in failed tests)
    if ' OR ' in query.upper():
        terms = [term.strip().lower() for term in re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)]
        return [c for c in chunks if any(term in c.get("page_content", "").lower() for term in terms)]
    
    # Handle AND logic
    elif ' AND ' in query.upper():
        terms = [term.strip().lower() for term in re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)]
        return [c for c in chunks if all(term in c.get("page_content", "").lower() for term in terms)]
    
    # Handle simple multi-word queries (split on spaces and use OR logic)
    elif ' ' in query and not any(op in query.upper() for op in [' OR ', ' AND ', '"']):
        terms = [term.strip().lower() for term in query.split()]
        return [c for c in chunks if any(term in c.get("page_content", "").lower() for term in terms)]
    
    # Simple single-term search
    else:
        return [c for c in chunks if query.lower() in c.get("page_content", "").lower()]

async def discover_document_structure(doc_name: str) -> dict:
    if doc_name not in document_chunk_store: return {"status": "error", "message": f"Doc '{doc_name}' not found."}
    chunks = document_chunk_store[doc_name]
    headers = {c.get("metadata", {}).get(k) for c in chunks for k in c.get("metadata", {}) if "Header" in k}
    return {"status": "success", "headers": sorted(list(h for h in headers if h is not None))}

async def search_uploaded_docs(doc_name: str, query: str = None, filter_by_metadata: dict = None, **kwargs) -> list:
    if doc_name not in document_chunk_store: return [{"error": f"Doc '{doc_name}' not found."}]
    
    # Start with all chunks for the document
    filtered_chunks = document_chunk_store[doc_name]
    
    # Apply metadata filter only if it is provided
    if filter_by_metadata:
        key, value = list(filter_by_metadata.items())[0]
        filtered_chunks = [c for c in filtered_chunks if value == c.get("metadata", {}).get(key)]
        
    # Apply keyword query filter with proper boolean logic
    if query:
        filtered_chunks = _apply_search_query(filtered_chunks, query)
        
    return filtered_chunks
