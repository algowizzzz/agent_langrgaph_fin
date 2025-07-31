"""
Professional Document Intelligence Agent - Streamlit UI
Sleek, minimal interface with chat history, document upload, and reasoning display.
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
import uuid
import tempfile

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator
from tools.memory_tools import conversation_memory
from tools.document_tools import upload_document

# Page configuration
st.set_page_config(
    page_title="Document Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2E3B4E;
        --secondary-color: #4A90B8;
        --accent-color: #7ED321;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
        --border-color: #E1E8ED;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom sidebar styling */
    .css-1d391kg {
        background-color: var(--primary-color);
    }
    
    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        margin-left: 20%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        margin-right: 20%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .reasoning-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 15px;
        margin: 8px 0;
        margin-right: 25%;
        font-size: 0.9em;
        opacity: 0.9;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Upload area styling */
    .upload-area {
        border: 2px dashed var(--secondary-color);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin: 10px 0;
    }
    
    /* Chat input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid var(--border-color);
        padding: 12px 20px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        border: none;
        background: linear-gradient(135deg, var(--secondary-color) 0%, var(--accent-color) 100%);
        color: white;
        font-weight: 600;
        padding: 10px 25px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* Sidebar chat list styling */
    .chat-item {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border-left: 3px solid transparent;
    }
    
    .chat-item:hover {
        background: rgba(255,255,255,0.2);
        border-left-color: var(--accent-color);
    }
    
    .chat-item.active {
        background: rgba(126, 211, 33, 0.2);
        border-left-color: var(--accent-color);
    }
    
    /* Status indicators */
    .status-thinking {
        color: #ffa726;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .status-success {
        color: #66bb6a;
    }
    
    .status-error {
        color: #ef5350;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .user-message, .assistant-message {
            margin-left: 5%;
            margin-right: 5%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}
if 'uploaded_documents' not in st.session_state:
    st.session_state.uploaded_documents = []
if 'active_document' not in st.session_state:
    st.session_state.active_document = None
if 'chat_documents' not in st.session_state:
    st.session_state.chat_documents = {}  # Maps chat_id to active document

async def initialize_orchestrator():
    """Initialize the orchestrator asynchronously."""
    if st.session_state.orchestrator is None:
        st.session_state.orchestrator = Orchestrator()
    return st.session_state.orchestrator

async def load_chat_history():
    """Load chat history from memory system."""
    try:
        stats = await conversation_memory.get_memory_stats()
        # Get recent conversations from memory
        context = await conversation_memory.get_context()
        
        # Build chat history from memory
        if context.get('short_term'):
            chat_id = "current_session"
            if chat_id not in st.session_state.chat_history:
                st.session_state.chat_history[chat_id] = {
                    'messages': [],
                    'first_query': 'Current Session',
                    'created_at': datetime.now().isoformat()
                }
            
            # Convert memory messages to chat format
            for msg in context['short_term']:
                if msg['role'] in ['user', 'assistant']:
                    st.session_state.chat_history[chat_id]['messages'].append({
                        'role': msg['role'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp']
                    })
    except Exception as e:
        st.error(f"Error loading chat history: {e}")

def create_new_chat():
    """Create a new chat session."""
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []
    st.session_state.chat_history[chat_id] = {
        'messages': [],
        'first_query': 'New Chat',
        'created_at': datetime.now().isoformat()
    }

def switch_to_chat(chat_id):
    """Switch to an existing chat."""
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = st.session_state.chat_history[chat_id]['messages'].copy()
    
    # Restore active document for this chat
    if chat_id in st.session_state.chat_documents:
        st.session_state.active_document = st.session_state.chat_documents[chat_id]
    else:
        st.session_state.active_document = None

async def process_uploaded_file(uploaded_file):
    """Process uploaded file through the document system."""
    if uploaded_file is not None:
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Upload document using our system
            result = await upload_document(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            if result.get('status') == 'success':
                doc_info = {
                    'name': uploaded_file.name,
                    'doc_name': result.get('doc_name'),
                    'chunks_created': result.get('chunks_created'),
                    'uploaded_at': datetime.now().isoformat()
                }
                st.session_state.uploaded_documents.append(doc_info)
                
                # Set as active document for current chat
                st.session_state.active_document = result.get('doc_name')
                if st.session_state.current_chat_id:
                    st.session_state.chat_documents[st.session_state.current_chat_id] = result.get('doc_name')
                
                return True, f"✅ Successfully uploaded '{uploaded_file.name}' ({result.get('chunks_created')} chunks created)"
            else:
                return False, f"❌ Failed to upload '{uploaded_file.name}': {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            return False, f"❌ Error uploading '{uploaded_file.name}': {str(e)}"
    
    return False, "No file provided"

async def process_user_message(user_input):
    """Process user message through the orchestrator."""
    if not user_input.strip():
        return
    
    # Add user message
    user_msg = {
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.messages.append(user_msg)
    
    # Update chat history
    if st.session_state.current_chat_id:
        st.session_state.chat_history[st.session_state.current_chat_id]['messages'].append(user_msg)
        # Update first query if this is the first message
        if len(st.session_state.chat_history[st.session_state.current_chat_id]['messages']) == 1:
            st.session_state.chat_history[st.session_state.current_chat_id]['first_query'] = user_input[:50] + "..." if len(user_input) > 50 else user_input
    
    # Add to memory system
    await conversation_memory.add_message('user', user_input, st.session_state.current_chat_id)
    
    # Show thinking status
    thinking_placeholder = st.empty()
    thinking_placeholder.markdown(
        '<div class="reasoning-message"><span class="status-thinking">🤔 Agent is thinking...</span></div>',
        unsafe_allow_html=True
    )
    
    try:
        # Get orchestrator
        orchestrator = await initialize_orchestrator()
        
        # Get active document for this chat
        active_doc = None
        if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chat_documents:
            active_doc = st.session_state.chat_documents[st.session_state.current_chat_id]
        elif st.session_state.active_document:
            active_doc = st.session_state.active_document
        
        # Process through orchestrator with context
        result = await orchestrator.run(user_input, st.session_state.current_chat_id or 'default', active_document=active_doc)
        
        # Clear thinking indicator
        thinking_placeholder.empty()
        
        # Show reasoning if available
        if result.get('reasoning_log'):
            reasoning_content = "**Reasoning Steps:**\n"
            for i, step in enumerate(result['reasoning_log'], 1):
                if isinstance(step, dict) and 'tool_name' in step:
                    reasoning_content += f"{i}. Used **{step['tool_name']}** with parameters: {step.get('tool_params', {})}\n"
            
            reasoning_msg = {
                'role': 'reasoning',
                'content': reasoning_content,
                'timestamp': datetime.now().isoformat()
            }
            st.session_state.messages.append(reasoning_msg)
        
        # Add assistant response
        response_content = result.get('final_answer', 'No response generated')
        assistant_msg = {
            'role': 'assistant',
            'content': response_content,
            'timestamp': datetime.now().isoformat(),
            'status': result.get('status', 'unknown')
        }
        st.session_state.messages.append(assistant_msg)
        
        # Update chat history
        if st.session_state.current_chat_id:
            st.session_state.chat_history[st.session_state.current_chat_id]['messages'].extend([
                reasoning_msg if 'reasoning_msg' in locals() else None,
                assistant_msg
            ])
            st.session_state.chat_history[st.session_state.current_chat_id]['messages'] = [
                msg for msg in st.session_state.chat_history[st.session_state.current_chat_id]['messages'] if msg is not None
            ]
        
        # Add to memory system
        await conversation_memory.add_message('assistant', response_content, st.session_state.current_chat_id)
        
    except Exception as e:
        thinking_placeholder.empty()
        error_msg = {
            'role': 'assistant',
            'content': f"❌ Error processing your request: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }
        st.session_state.messages.append(error_msg)
        await conversation_memory.add_message('assistant', f"Error: {str(e)}", st.session_state.current_chat_id)

def render_sidebar():
    """Render the sidebar with chat history."""
    with st.sidebar:
        st.markdown("### 🤖 Document Intelligence Agent")
        
        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            create_new_chat()
            st.rerun()
        
        st.markdown("---")
        
        # Document Upload Section
        st.markdown("### 📄 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'txt', 'csv'],
            help="Upload PDF, DOCX, TXT, or CSV files"
        )
        
        if uploaded_file:
            if st.button("Upload Document", use_container_width=True):
                success, message = asyncio.run(process_uploaded_file(uploaded_file))
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        
        # Show uploaded documents
        if st.session_state.uploaded_documents:
            st.markdown("### 📚 Uploaded Documents")
            
            # Get active document for current chat
            active_doc = None
            if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chat_documents:
                active_doc = st.session_state.chat_documents[st.session_state.current_chat_id]
            elif st.session_state.active_document:
                active_doc = st.session_state.active_document
            
            for doc in st.session_state.uploaded_documents[-5:]:  # Show last 5
                if doc['doc_name'] == active_doc:
                    st.markdown(f"🎯 **{doc['name']}** ({doc['chunks_created']} chunks) *- ACTIVE*")
                else:
                    st.markdown(f"• **{doc['name']}** ({doc['chunks_created']} chunks)")
            
            # Show active document info
            if active_doc:
                st.markdown(f"**Current Focus:** `{active_doc}`")
                st.markdown("*Queries about 'the document' will use this file*")
        
        st.markdown("---")
        
        # Chat History
        st.markdown("### 💬 Chat History")
        
        # Load chat history
        asyncio.run(load_chat_history())
        
        if st.session_state.chat_history:
            for chat_id, chat_data in sorted(
                st.session_state.chat_history.items(),
                key=lambda x: x[1]['created_at'],
                reverse=True
            ):
                is_active = chat_id == st.session_state.current_chat_id
                button_type = "primary" if is_active else "secondary"
                
                if st.button(
                    f"💬 {chat_data['first_query']}",
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type=button_type
                ):
                    switch_to_chat(chat_id)
                    st.rerun()
        else:
            st.markdown("*No previous chats*")

def render_chat_messages():
    """Render chat messages in the main area."""
    st.markdown("### 💬 Chat with Document Intelligence Agent")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 50px; color: #666;">
                <h3>👋 Welcome to Document Intelligence Agent</h3>
                <p>Upload a document and start asking questions, or begin a conversation!</p>
                <p><strong>Example queries:</strong></p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Summarize the entire document</li>
                    <li>Find all regulatory requirements</li>
                    <li>Analyze risk factors in the document</li>
                    <li>Extract key financial data</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display messages
            for message in st.session_state.messages:
                if message['role'] == 'user':
                    st.markdown(
                        f'<div class="user-message">👤 **You:** {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                elif message['role'] == 'reasoning':
                    st.markdown(
                        f'<div class="reasoning-message">🧠 {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                elif message['role'] == 'assistant':
                    status_icon = "✅" if message.get('status') == 'success' else "❌" if message.get('status') == 'error' else "🤖"
                    st.markdown(
                        f'<div class="assistant-message">{status_icon} **Agent:** {message["content"]}</div>',
                        unsafe_allow_html=True
                    )

def main():
    """Main application function."""
    # Render sidebar
    render_sidebar()
    
    # Main chat area
    render_chat_messages()
    
    # Chat input at bottom
    st.markdown("---")
    
    # Create new chat if none exists
    if not st.session_state.current_chat_id:
        create_new_chat()
    
    # Chat input
    user_input = st.text_input(
        "Type your message...",
        placeholder="Ask about your documents or start a conversation...",
        key="chat_input"
    )
    
    col1, col2 = st.columns([6, 1])
    
    with col2:
        send_button = st.button("Send", use_container_width=True, type="primary")
    
    # Process message
    if send_button and user_input:
        asyncio.run(process_user_message(user_input))
        st.rerun()

if __name__ == "__main__":
    main()