"""
🤖 AI Finance and Risk Agent - Streamlit Chat Interface
Real-time streaming chatbot with document management
"""

import streamlit as st
import requests
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
import asyncio
import aiohttp
import sseclient
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Finance & Risk Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #fafafa;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        text-align: right;
    }
    
    .assistant-message {
        background-color: #f8f9fa;
        color: #333;
        padding: 0.75rem 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border-left: 4px solid #28a745;
    }
    
    .reasoning-step {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        font-size: 0.9em;
        color: #856404;
    }
    
    .streaming-indicator {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .document-chip {
        display: inline-block;
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        margin: 0.25rem;
        font-size: 0.8em;
        border: 1px solid #c8e6c9;
    }
    
    .status-info {
        background-color: #e8f4fd;
        border: 1px solid #b3d9ff;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []
if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = False

# Configuration
API_BASE_URL = "http://localhost:8000"  # Adjust this to your backend URL

def get_system_status() -> Dict[str, Any]:
    """Get system status from backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/system/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "unknown", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def upload_document(file, session_id: str) -> Dict[str, Any]:
    """Upload document to backend."""
    try:
        files = {"file": (file.name, file, file.type)}
        data = {"session_id": session_id}
        
        response = requests.post(
            f"{API_BASE_URL}/upload", 
            files=files, 
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_available_documents() -> List[Dict[str, Any]]:
    """Get list of available documents."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents", timeout=10)
        if response.status_code == 200:
            return response.json().get("documents", [])
        return []
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        return []

def stream_chat_response(query: str, session_id: str, active_documents: List[str] = None) -> None:
    """Stream chat response from backend."""
    try:
        payload = {
            "query": query,
            "session_id": session_id,
            "active_documents": active_documents or []
        }
        
        # Create placeholder for streaming content
        streaming_placeholder = st.empty()
        reasoning_placeholder = st.empty()
        
        with streaming_placeholder.container():
            st.markdown('<div class="streaming-indicator">🤖 AI is thinking...</div>', unsafe_allow_html=True)
        
        response = requests.post(
            f"{API_BASE_URL}/chat/stream",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            streaming_placeholder.error(f"Error: HTTP {response.status_code}")
            return
        
        # Parse SSE stream
        client = sseclient.SSEClient(response)
        final_answer = ""
        reasoning_steps = []
        
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    event_type = data.get("type", "")
                    
                    if event_type == "status":
                        with streaming_placeholder.container():
                            st.markdown(f'<div class="streaming-indicator">🔄 {data.get("message", "Processing...")}</div>', unsafe_allow_html=True)
                    
                    elif event_type == "step":
                        step_info = {
                            "tool_name": data.get("tool_name", "Unknown"),
                            "message": data.get("message", ""),
                            "timestamp": data.get("timestamp", "")
                        }
                        reasoning_steps.append(step_info)
                        
                        # Update reasoning steps display
                        with reasoning_placeholder.container():
                            st.markdown("**🔍 Reasoning Steps:**")
                            for i, step in enumerate(reasoning_steps, 1):
                                st.markdown(f'<div class="reasoning-step">**Step {i}:** {step["tool_name"]} - {step["message"]}</div>', unsafe_allow_html=True)
                    
                    elif event_type == "final_answer":
                        content = data.get("content", {})
                        final_answer = content.get("final_answer", "")
                        
                        # Clear streaming indicator and show final answer
                        streaming_placeholder.empty()
                        
                        # Add to session messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": final_answer,
                            "reasoning_steps": reasoning_steps,
                            "timestamp": datetime.now().isoformat(),
                            "processing_time": content.get("processing_time_ms", 0)
                        })
                        
                        # Force rerun to display the message
                        st.rerun()
                        
                    elif event_type == "complete":
                        reasoning_placeholder.empty()
                        processing_time = data.get("processing_time_ms", 0)
                        st.success(f"✅ Response completed in {processing_time}ms")
                        break
                        
                    elif event_type == "error":
                        streaming_placeholder.error(f"❌ Error: {data.get('message', 'Unknown error')}")
                        break
                        
                except json.JSONDecodeError:
                    continue
        
    except Exception as e:
        st.error(f"Streaming error: {str(e)}")
        logger.error(f"Streaming error: {e}")

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header"><h1>🤖 AI Finance & Risk Agent</h1><p>Intelligent Document Analysis with Real-time Streaming</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 System Status")
        
        # System status check
        with st.spinner("Checking system status..."):
            status = get_system_status()
        
        if status.get("status") == "operational":
            st.success("✅ System Operational")
            features = status.get("features", {})
            st.markdown(f"""
            **Features:**
            - Orchestrator V2: {'✅' if features.get('orchestrator_v2') else '❌'}
            - Streaming: {'✅' if features.get('streaming_support') else '❌'}
            - Memory: {'✅' if features.get('memory_integration') else '❌'}
            - Multi-docs: {'✅' if features.get('multi_document_analysis') else '❌'}
            """)
        else:
            st.error(f"❌ System Status: {status.get('status', 'Unknown')}")
            if 'error' in status:
                st.error(f"Error: {status['error']}")
        
        st.divider()
        
        # Document Management
        st.header("📄 Document Management")
        
        # Upload new document
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'docx', 'csv', 'txt'],
            help="Supported formats: PDF, DOCX, CSV, TXT"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Upload Document"):
                with st.spinner("Uploading document..."):
                    result = upload_document(uploaded_file, st.session_state.session_id)
                
                if result.get("status") == "success":
                    st.success(f"✅ Uploaded: {result.get('filename')}")
                    st.info(f"📊 Created {result.get('chunks_created')} chunks ({result.get('file_size')})")
                    st.session_state.uploaded_documents.append(result.get('filename'))
                else:
                    st.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
        
        # Available documents
        st.subheader("📚 Available Documents")
        available_docs = get_available_documents()
        
        if available_docs:
            selected_docs = st.multiselect(
                "Select documents for analysis:",
                options=[doc.get("doc_name", doc.get("filename", "Unknown")) for doc in available_docs],
                default=[],
                help="Select one or more documents to analyze"
            )
            
            if selected_docs:
                st.markdown("**Selected documents:**")
                for doc in selected_docs:
                    st.markdown(f'<span class="document-chip">📄 {doc}</span>', unsafe_allow_html=True)
        else:
            st.info("No documents available. Upload a document to get started.")
        
        st.divider()
        
        # Session Info
        st.header("🔧 Session Info")
        st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            # Display chat messages
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message">👤 **You:** {message["content"]}</div>', unsafe_allow_html=True)
                    
                    # Show selected documents for this query
                    if "active_documents" in message and message["active_documents"]:
                        docs_html = "".join([f'<span class="document-chip">📄 {doc}</span>' for doc in message["active_documents"]])
                        st.markdown(f'<div style="text-align: right; margin-right: 20%;">{docs_html}</div>', unsafe_allow_html=True)
                
                elif message["role"] == "assistant":
                    st.markdown(f'<div class="assistant-message">🤖 **AI Agent:** {message["content"]}</div>', unsafe_allow_html=True)
                    
                    # Show reasoning steps in expander
                    if message.get("reasoning_steps"):
                        with st.expander(f"🔍 View Reasoning Steps ({len(message['reasoning_steps'])} steps)"):
                            for j, step in enumerate(message["reasoning_steps"], 1):
                                st.markdown(f"**Step {j}:** {step.get('tool_name', 'Unknown')} - {step.get('message', '')}")
                    
                    # Show processing time
                    if message.get("processing_time"):
                        st.caption(f"⏱️ Processed in {message['processing_time']}ms")
        
        # Chat input
        st.markdown("---")
        
        # Query input
        query = st.text_area(
            "💭 Ask me anything about your documents:",
            placeholder="E.g., 'What are the main risk factors mentioned?' or 'Compare these two financial reports'",
            height=100,
            disabled=st.session_state.streaming_active
        )
        
        # Send button
        col_send, col_clear = st.columns([3, 1])
        
        with col_send:
            if st.button("📤 Send Message", disabled=st.session_state.streaming_active or not query.strip()):
                if query.strip():
                    # Add user message
                    user_message = {
                        "role": "user",
                        "content": query,
                        "timestamp": datetime.now().isoformat(),
                        "active_documents": selected_docs if 'selected_docs' in locals() else []
                    }
                    st.session_state.messages.append(user_message)
                    
                    # Start streaming response
                    st.session_state.streaming_active = True
                    
                    # Stream the response
                    stream_chat_response(
                        query=query,
                        session_id=st.session_state.session_id,
                        active_documents=selected_docs if 'selected_docs' in locals() else []
                    )
                    
                    st.session_state.streaming_active = False
        
        with col_clear:
            if st.button("🔄 New Chat"):
                st.session_state.messages = []
                st.rerun()
    
    with col2:
        st.header("📊 Analytics")
        
        # Chat statistics
        total_messages = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        ai_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        st.metric("Total Messages", total_messages)
        st.metric("Your Questions", user_messages)
        st.metric("AI Responses", ai_messages)
        
        # Recent activity
        if st.session_state.messages:
            st.subheader("🕒 Recent Activity")
            recent_messages = st.session_state.messages[-3:]
            for msg in reversed(recent_messages):
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                timestamp = msg.get("timestamp", "").split("T")[1][:8] if msg.get("timestamp") else "Unknown"
                st.markdown(f"**{role_icon} {timestamp}:** {content_preview}")

if __name__ == "__main__":
    main()